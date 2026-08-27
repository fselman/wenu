"""Deterministic semantic annotations for Matplotlib SVG output."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
import xml.etree.ElementTree as ET


_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_INKSCAPE_NAMESPACE = "http://www.inkscape.org/namespaces/inkscape"
ET.register_namespace("", _SVG_NAMESPACE)
ET.register_namespace("inkscape", _INKSCAPE_NAMESPACE)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("cc", "http://creativecommons.org/ns#")
ET.register_namespace(
    "rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
)


_METADATA_ATTRIBUTE = "_wenu_svg_semantics"


def attach_semantic_svg_metadata(
    artist,
    *,
    layer,
    zorder,
    paint_role,
    edit_policy,
    semantic_path,
    display_name,
    presentation_order,
    style_role,
):
    """Attach renderer-neutral values for the later SVG export boundary."""
    metadata = {
        "layer": str(layer),
        "zorder": float(zorder),
        "edit_policy": edit_policy.value,
        "semantic_path": "/".join(semantic_path),
        "parent_path": "/".join(semantic_path[:-1]),
        "display_name": str(display_name),
        "style_role": str(style_role),
    }
    if presentation_order is not None:
        metadata["presentation_order"] = int(presentation_order)
    if paint_role is not None:
        metadata["paint_role"] = paint_role.name
    setattr(artist, _METADATA_ATTRIBUTE, metadata)


def annotate_semantic_svg(path, figure):
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
    if not records:
        return path

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
            "data-wenu-parent-path": metadata["parent_path"],
            "data-wenu-display-name": metadata["display_name"],
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
    return path


def _group_semantics(path):
    """Materialize supplied sky and chart paths without reclassification."""
    tree = ET.parse(path)
    root = tree.getroot()
    parent_of = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    candidates = []
    for element in root.iter():
        classes = element.get("class", "").split()
        semantic_path = element.get("data-wenu-semantic-path", "")
        order = element.get("data-wenu-presentation-order")
        if (
            "wenu-semantic-artist" in classes
            and semantic_path.startswith(("sky/", "chart/"))
            and order is not None
        ):
            candidates.append(element)
    if not candidates:
        return path

    parents = {parent_of[element] for element in candidates}
    if len(parents) != 1:
        raise ValueError(
            "Semantic artists must share one SVG parent before grouping."
        )
    parent = parents.pop()
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

    def descendant_order(path_parts):
        values = [
            order
            for semantic_path, order in orders.items()
            if semantic_path[:len(path_parts)] == path_parts
        ]
        return min(values)

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

    def display_name(path_parts):
        elements = by_path.get(path_parts, ())
        if elements:
            supplied = elements[0].get("data-wenu-display-name")
            if supplied:
                return supplied
        words = path_parts[-1].replace("_", " ").split()
        return " ".join(
            word if word in {"and", "of"} else word.capitalize()
            for word in words
        )

    def build_group(path_parts):
        token = "-".join(path_parts)
        group = ET.Element(
            f"{{{_SVG_NAMESPACE}}}g",
            {
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
            },
        )
        child_paths = sorted(
            children_by_parent.get(path_parts, ()),
            key=lambda item: (descendant_order(item), item),
        )
        for child_path in child_paths:
            group.append(build_group(child_path))
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
    _flatten_semantic_text_artists(root)
    _promote_common_label_typography(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return path


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
        if (
            "wenu-semantic-group" not in classes
            or not semantic_path.endswith("/labels")
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
