"""Deterministic semantic annotations for Matplotlib SVG output."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from html import escape
from importlib.metadata import PackageNotFoundError, distribution, version
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET


_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_INKSCAPE_NAMESPACE = "http://www.inkscape.org/namespaces/inkscape"
_SODIPODI_NAMESPACE = (
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
)
_WENU_NAMESPACE = "https://github.com/fselman/wenu/ns/provenance/1"
_DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
_CC_NAMESPACE = "http://creativecommons.org/ns#"
_RDF_NAMESPACE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
ET.register_namespace("", _SVG_NAMESPACE)
ET.register_namespace("inkscape", _INKSCAPE_NAMESPACE)
ET.register_namespace("sodipodi", _SODIPODI_NAMESPACE)
ET.register_namespace("wenu", _WENU_NAMESPACE)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("cc", "http://creativecommons.org/ns#")
ET.register_namespace(
    "rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
)


_METADATA_ATTRIBUTE = "_wenu_svg_semantics"


def _default_path_display_name(value):
    words = value.replace("_", " ").split()
    return " ".join(
        word if word in {"and", "of"} else word.capitalize()
        for word in words
    )


def attach_semantic_svg_metadata(
    artist,
    *,
    layer,
    zorder,
    paint_role,
    edit_policy,
    semantic_path,
    lock_owner_path,
    display_name,
    path_display_names=(),
    presentation_order,
    style_role,
):
    """Attach renderer-neutral values for the later SVG export boundary."""
    semantic_path = tuple(semantic_path)
    lock_owner_path = tuple(lock_owner_path)
    if semantic_path[:len(lock_owner_path)] != lock_owner_path:
        raise ValueError(
            "lock_owner_path must be an ancestor of semantic_path."
        )
    if path_display_names:
        path_display_names = tuple(path_display_names)
    else:
        inferred = tuple(
            _default_path_display_name(item) for item in semantic_path
        )
        path_display_names = (*inferred[:-1], str(display_name))
    metadata = {
        "layer": str(layer),
        "zorder": float(zorder),
        "edit_policy": edit_policy.value,
        "semantic_path": "/".join(semantic_path),
        "lock_owner_path": "/".join(lock_owner_path),
        "parent_path": "/".join(semantic_path[:-1]),
        "display_name": str(display_name),
        "path_display_names": path_display_names,
        "style_role": str(style_role),
    }
    if presentation_order is not None:
        metadata["presentation_order"] = int(presentation_order)
    if paint_role is not None:
        metadata["paint_role"] = paint_role.name
    setattr(artist, _METADATA_ATTRIBUTE, metadata)


def annotate_semantic_svg(path, figure, *, provenance=None):
    """Add Wenu classes and data attributes without moving SVG elements."""
    path = Path(path)
    records = []
    find_objects = getattr(figure, "findobj", None)
    if callable(find_objects):
        for artist in find_objects():
            svg_id = getattr(artist, "get_gid", lambda: None)()
            metadata = getattr(artist, _METADATA_ATTRIBUTE, None)
            if svg_id and metadata:
                records.append((str(svg_id), dict(metadata)))
    if records:
        serialized = path.read_text(encoding="utf-8")
        for svg_id, metadata in records:
            classes = [
                "wenu-semantic-artist",
                f"wenu-layer-{metadata['layer'].replace('_', '-')}",
                f"wenu-edit-{metadata['edit_policy']}",
                f"wenu-style-{metadata['style_role'].replace('_', '-')}",
            ]
            attributes = {
                "class": " ".join(classes),
                "data-wenu-layer": metadata["layer"],
                "data-wenu-zorder": f"{metadata['zorder']:.12g}",
                "data-wenu-edit": metadata["edit_policy"],
                "data-wenu-semantic-path": metadata["semantic_path"],
                "data-wenu-lock-owner-path": metadata[
                    "lock_owner_path"
                ],
                "data-wenu-parent-path": metadata["parent_path"],
                "data-wenu-display-name": metadata["display_name"],
                "data-wenu-path-display-names": json.dumps(
                    metadata["path_display_names"],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "data-wenu-style-role": metadata["style_role"],
            }
            if "presentation_order" in metadata:
                attributes["data-wenu-presentation-order"] = (
                    metadata["presentation_order"]
                )
            paint_role = metadata.get("paint_role")
            if paint_role is not None:
                classes.append(f"wenu-paint-{paint_role.replace('_', '-')}")
                attributes["class"] = " ".join(classes)
                attributes["data-wenu-paint-role"] = paint_role
            extra = "".join(
                f' {name}="{escape(str(value), quote=True)}"'
                for name, value in attributes.items()
            )
            pattern = re.compile(
                rf'(<g\s+id="{re.escape(svg_id)}")(?P<rest>[^>]*>)'
            )
            serialized, count = pattern.subn(
                rf"\1{extra}\g<rest>",
                serialized,
                count=1,
            )
            if count != 1:
                raise ValueError(
                    f"Expected exactly one SVG group for Wenu id {svg_id!r}."
                )
        path.write_text(serialized, encoding="utf-8")
        _group_semantics(path)
    if provenance is not None:
        _write_provenance(path, provenance)
    return path


def _canonical_json_value(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): _canonical_json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_canonical_json_value(item) for item in value]
        return (
            sorted(items, key=repr)
            if isinstance(value, (set, frozenset)) else items
        )
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _created_utc(explicit=None):
    if explicit:
        return str(explicit)
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    moment = (
        datetime.fromtimestamp(int(epoch), timezone.utc)
        if epoch is not None
        else datetime.now(timezone.utc)
    )
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _wenu_version():
    try:
        return version("wenu")
    except PackageNotFoundError:
        return "0+unknown"


def _source_revision(explicit=None):
    if explicit:
        return str(explicit)
    configured = os.environ.get("WENU_SOURCE_REVISION")
    if configured:
        return configured
    try:
        direct_url = distribution("wenu").read_text("direct_url.json")
    except PackageNotFoundError:
        direct_url = None
    if direct_url:
        commit_id = json.loads(direct_url).get("vcs_info", {}).get(
            "commit_id"
        )
        if commit_id:
            return str(commit_id)
    return "unknown"


def _write_provenance(path, provenance):
    """Merge one Wenu provenance record into the existing SVG metadata."""
    tree = ET.parse(path)
    root = tree.getroot()
    metadata_tag = f"{{{_SVG_NAMESPACE}}}metadata"
    metadata_elements = [child for child in root if child.tag == metadata_tag]
    if len(metadata_elements) > 1:
        raise ValueError("SVG must contain at most one metadata element.")
    if metadata_elements:
        metadata = metadata_elements[0]
    else:
        metadata = ET.Element(metadata_tag)
        root.insert(0, metadata)
    record_tag = f"{{{_WENU_NAMESPACE}}}provenance"
    for existing in list(metadata):
        if existing.tag == record_tag:
            metadata.remove(existing)
    record = ET.SubElement(metadata, record_tag, {"schema-version": "1"})
    values = {
        "product-name": provenance.product_name,
        "title": provenance.title,
        "creator": provenance.creator,
        "wenu-version": _wenu_version(),
        "source-revision": _source_revision(provenance.source_revision),
        "created-utc": _created_utc(provenance.created_utc),
        "credit": provenance.credit,
        "copyright": provenance.copyright,
        "license": provenance.license,
    }
    rdf = metadata.find(f"{{{_RDF_NAMESPACE}}}RDF")
    if rdf is None:
        rdf = ET.SubElement(metadata, f"{{{_RDF_NAMESPACE}}}RDF")
    work = rdf.find(f"{{{_CC_NAMESPACE}}}Work")
    if work is None:
        work = ET.SubElement(rdf, f"{{{_CC_NAMESPACE}}}Work")

    def set_dc(name, value, *, only_if_missing=False):
        if value is None:
            return
        tag = f"{{{_DC_NAMESPACE}}}{name}"
        element = work.find(tag)
        if element is None:
            element = ET.SubElement(work, tag)
        elif only_if_missing:
            return
        element.text = str(value)

    set_dc("title", provenance.title, only_if_missing=True)
    set_dc("date", values["created-utc"])
    set_dc("format", "image/svg+xml")
    set_dc("rights", provenance.copyright)
    set_dc("description", provenance.credit, only_if_missing=True)
    if work.find(f"{{{_DC_NAMESPACE}}}creator") is None and provenance.creator:
        creator = ET.SubElement(work, f"{{{_DC_NAMESPACE}}}creator")
        agent = ET.SubElement(creator, f"{{{_CC_NAMESPACE}}}Agent")
        ET.SubElement(agent, f"{{{_DC_NAMESPACE}}}title").text = (
            provenance.creator
        )
    for name, value in values.items():
        if value is not None:
            ET.SubElement(
                record, f"{{{_WENU_NAMESPACE}}}{name}"
            ).text = str(value)
    parameters = ET.SubElement(
        record,
        f"{{{_WENU_NAMESPACE}}}parameters",
        {"media-type": "application/json"},
    )
    parameters.text = json.dumps(
        _canonical_json_value(provenance.parameters),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _group_semantics(path):
    """Materialize supplied semantic paths without reclassification."""
    tree = ET.parse(path)
    root = tree.getroot()
    parent_of = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    candidates_by_parent = {}
    for element in root.iter():
        classes = element.get("class", "").split()
        semantic_path = element.get("data-wenu-semantic-path", "")
        order = element.get("data-wenu-presentation-order")
        if (
            "wenu-semantic-artist" in classes
            and semantic_path.startswith(
                ("page/", "sky/", "chart/", "furniture/")
            )
            and order is not None
        ):
            candidates_by_parent.setdefault(
                parent_of[element], []
            ).append(element)
    if not candidates_by_parent:
        return path

    for parent, candidates in candidates_by_parent.items():
        _group_semantic_siblings(parent, candidates)
    _flatten_semantic_text_artists(root)
    _promote_common_label_typography(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


def _group_semantic_siblings(parent, candidates):
    """Group one sibling set while preserving its supplied root paths."""
    original_children = list(parent)
    insertion_index = min(
        original_children.index(element) for element in candidates
    )
    by_path = {}
    for element in candidates:
        semantic_path = tuple(
            item
            for item in element.get(
                "data-wenu-semantic-path", ""
            ).split("/")
            if item
        )
        by_path.setdefault(semantic_path, []).append(element)

    orders = {
        semantic_path: min(
            int(element.get("data-wenu-presentation-order"))
            for element in elements
        )
        for semantic_path, elements in by_path.items()
    }
    policies = {
        semantic_path: frozenset(
            element.get("data-wenu-edit") for element in elements
        )
        for semantic_path, elements in by_path.items()
    }
    lock_owner_paths = {
        tuple(
            element.get(
                "data-wenu-lock-owner-path",
                element.get("data-wenu-semantic-path", ""),
            ).split("/")
        )
        for element in candidates
    }

    def descendant_order(path_parts):
        return min(
            order
            for semantic_path, order in orders.items()
            if semantic_path[:len(path_parts)] == path_parts
        )

    def descendant_policies(path_parts):
        return frozenset().union(*(
            policy
            for semantic_path, policy in policies.items()
            if semantic_path[:len(path_parts)] == path_parts
        ))

    def lockable(path_parts):
        policy = descendant_policies(path_parts)
        return (
            len(path_parts) > 1
            and path_parts in lock_owner_paths
            and bool(policy)
            and policy <= {"style", "none"}
        )

    root_paths = {(semantic_path[0],) for semantic_path in by_path}
    all_paths = set(root_paths)
    for semantic_path in by_path:
        for length in range(2, len(semantic_path) + 1):
            all_paths.add(semantic_path[:length])

    children_by_parent = {}
    for semantic_path in all_paths:
        if len(semantic_path) > 1:
            children_by_parent.setdefault(
                semantic_path[:-1], []
            ).append(semantic_path)

    supplied_path_names = {}
    for element in candidates:
        raw_names = element.get("data-wenu-path-display-names")
        raw_path = element.get("data-wenu-semantic-path", "")
        if not raw_names or not raw_path:
            continue
        names = tuple(json.loads(raw_names))
        parts = tuple(raw_path.split("/"))
        if len(names) != len(parts):
            raise ValueError(
                "Semantic path display names must align with their path."
            )
        for length, name in enumerate(names, start=1):
            child_path = parts[:length]
            previous = supplied_path_names.setdefault(child_path, name)
            if previous != name:
                raise ValueError(
                    "Semantic hierarchy path has conflicting labels: "
                    + "/".join(child_path)
                )

    def display_name(path_parts):
        supplied_path_name = supplied_path_names.get(path_parts)
        if supplied_path_name:
            return supplied_path_name
        elements = by_path.get(path_parts, ())
        if elements:
            supplied = elements[0].get("data-wenu-display-name")
            if supplied:
                return supplied
        return _default_path_display_name(path_parts[-1])

    def build_group(path_parts, *, ancestor_locked=False):
        token = "-".join(path_parts)
        attributes = {
            "id": f"wenu-group-{token}",
            "class": (
                "wenu-semantic-group "
                f"wenu-group-{path_parts[-1].replace('_', '-')}"
            ),
            "data-wenu-semantic-path": "/".join(path_parts),
            "data-wenu-display-name": display_name(path_parts),
            "data-wenu-presentation-order": str(
                descendant_order(path_parts)
            ),
            f"{{{_INKSCAPE_NAMESPACE}}}groupmode": "layer",
            f"{{{_INKSCAPE_NAMESPACE}}}label": display_name(path_parts),
        }
        lock_here = lockable(path_parts) and not ancestor_locked
        if lock_here:
            attributes.update({
                f"{{{_SODIPODI_NAMESPACE}}}insensitive": "true",
                "data-wenu-locked": "true",
            })
        group = ET.Element(f"{{{_SVG_NAMESPACE}}}g", attributes)
        child_paths = sorted(
            children_by_parent.get(path_parts, ()),
            key=lambda item: (descendant_order(item), item),
        )
        child_labels = [display_name(item) for item in child_paths]
        if len(child_labels) != len(set(child_labels)):
            raise ValueError(
                "Semantic hierarchy labels must be unique within "
                f"{'/'.join(path_parts)}."
            )
        for child_path in child_paths:
            group.append(build_group(
                child_path,
                ancestor_locked=ancestor_locked or lock_here,
            ))
        for element in by_path.get(path_parts, ()):
            group.append(element)
        return group

    for element in candidates:
        parent.remove(element)
    for offset, root_path in enumerate(sorted(
        root_paths,
        key=lambda item: (descendant_order(item), item),
    )):
        parent.insert(insertion_index + offset, build_group(root_path))


def _flatten_semantic_text_artists(root):
    """Expose conservatively wrapped semantic text as actual text objects."""
    group_tag = f"{{{_SVG_NAMESPACE}}}g"
    text_tag = f"{{{_SVG_NAMESPACE}}}text"
    parent_of = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    for wrapper in tuple(root.iter(group_tag)):
        if (
            "wenu-semantic-artist"
            not in wrapper.get("class", "").split()
        ):
            continue
        descendants = list(wrapper.iter())
        texts = [
            element for element in descendants if element.tag == text_tag
        ]
        if len(texts) != 1:
            continue
        if any(
            element is not wrapper
            and element.tag not in {group_tag, text_tag}
            for element in descendants
        ):
            continue
        intermediate_groups = [
            element
            for element in descendants
            if element is not wrapper and element.tag == group_tag
        ]
        if any(
            set(element.attrib) - {"clip-path"}
            for element in intermediate_groups
        ):
            continue
        text_element = texts[0]
        clip_paths = {
            element.get("clip-path")
            for element in intermediate_groups
            if element.get("clip-path")
        }
        if len(clip_paths) > 1:
            continue
        if clip_paths:
            text_element.set("clip-path", clip_paths.pop())
        text_attributes = dict(text_element.attrib)
        text_element.attrib.clear()
        text_element.attrib.update(wrapper.attrib)
        text_element.attrib.update(text_attributes)
        parent = parent_of.get(wrapper)
        if parent is None:
            continue
        index = list(parent).index(wrapper)
        for intermediate in intermediate_groups:
            if text_element in list(intermediate):
                intermediate.remove(text_element)
        parent.remove(wrapper)
        parent.insert(index, text_element)


def _style_declarations(element):
    """Return ordered declarations from one SVG style attribute."""
    declarations = []
    for declaration in element.get("style", "").split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        declarations.append((name.strip(), value.strip()))
    return declarations


def _set_style_declarations(element, declarations):
    if declarations:
        element.set(
            "style",
            "; ".join(f"{name}: {value}" for name, value in declarations),
        )
    else:
        element.attrib.pop("style", None)


def _promote_common_label_typography(root):
    """Make common label fonts inheritable from their semantic group."""
    text_tag = f"{{{_SVG_NAMESPACE}}}text"
    for group in root.iter(f"{{{_SVG_NAMESPACE}}}g"):
        classes = group.get("class", "").split()
        semantic_path = group.get("data-wenu-semantic-path", "")
        path_component = semantic_path.rsplit("/", 1)[-1]
        if (
            "wenu-semantic-group" not in classes
            or not (
                path_component == "labels"
                or path_component.startswith("labels_")
            )
        ):
            continue
        texts = list(group.iter(text_tag))
        if not texts:
            continue
        declarations = [
            _style_declarations(element) for element in texts
        ]
        fonts = [
            dict(items).get("font")
            for items in declarations
        ]
        if fonts[0] is None or any(font != fonts[0] for font in fonts[1:]):
            continue
        group_declarations = _style_declarations(group)
        group_declarations = [
            item for item in group_declarations if item[0] != "font"
        ]
        group_declarations.append(("font", fonts[0]))
        _set_style_declarations(group, group_declarations)
        for element, items in zip(texts, declarations):
            _set_style_declarations(
                element,
                [item for item in items if item[0] != "font"],
            )
