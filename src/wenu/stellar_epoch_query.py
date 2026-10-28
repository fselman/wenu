"""Explicit fixed-window reuse or original-model evaluation of stellar products.

The saved product stays immutable. Reuse is a declared position approximation;
advancement composes existing source admission and typed SDK services only.
"""
from dataclasses import asdict, dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from io import BytesIO
from numbers import Real
from pathlib import Path

from wenu.stellar_enrichment import decode, encode, require
from wenu.stellar_epoch import StellarEpochCatalogue
from wenu_kernel.records import TimePoint, TimeSpan


def _day(instant):
    return Fraction(instant.jd1) + Fraction(instant.jd2)


def _ratio(value):
    return dict(numerator=value.numerator, denominator=value.denominator)


@dataclass(frozen=True, slots=True)
class StellarEpochResolution:
    """Detached immutable query output; no provider/session remains live."""
    source: object
    _rows_payload: bytes
    _receipt_payload: bytes

    def rows(self):
        return (decode(line) for line in BytesIO(self._rows_payload))

    def receipt(self):
        return decode(self._receipt_payload)


def _restore(catalogue, models):
    # Public admission reconstructs from preserved sources, never saved states.
    from wenu.stellar_state import (
        admit_stellar_motion, admit_stellar_angular_motion,
        admit_stellar_hipparcos2_motion,
    )
    restored = []
    for model in models:
        admission = model['admission']
        coverage = TimeSpan(*(TimePoint(*t) for t in admission['coverage']))
        policies = admission['policies']
        if model['kind'] == 'cartesian-affine':
            current = admit_stellar_motion(catalogue.source, coverage=coverage,
                distance_policy=policies['distance'],
                radial_velocity_policy=policies['radial_velocity'])
        elif 'model_reference' in admission:
            current = admit_stellar_hipparcos2_motion(catalogue.source,
                coverage=coverage, epoch_policy=policies['epoch'])
        else:
            current = admit_stellar_angular_motion(catalogue.source, coverage=coverage)
        require(current.to_record() == admission, 'Reconstructed stellar admission differs')
        full = model['kind'] == 'cartesian-affine'
        coefficients = [dict(identifier=r.identifier,
            source_epoch=None if r.source_epoch is None else
                [r.source_epoch.jd1, r.source_epoch.jd2, r.source_epoch.scale],
            initial=r.position_m if full else r.direction,
            derivative=r.velocity_m_s if full else r.tangent_per_s,
            unavailable_reason=r.unavailable_reason) for r in current.rows]
        require(encode(coefficients) == encode(model['coefficients']),
                'Reconstructed original stellar coefficients differ')
        restored.append(current)
    return tuple(restored)


def _advance(catalogue, instant, identifiers, manifest):
    from wenu.stellar_state import (
        StellarMotionRequest, StellarMotionProvider, stellar_model_selection,
    )
    from wenu_kernel import Kernel
    from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateQuery
    models = catalogue.models()
    request = StellarMotionRequest(_restore(catalogue, models), instant,
        manifest['motion_identity']['input_document_sha256'])
    selection = stellar_model_selection(request, identifiers)
    evaluated = {}
    for index, current in enumerate(request.catalogues):
        chosen = tuple(hip for hip, selected, _ in selection if selected == index)
        # No SDK query for empty selections; no output can claim those references.
        if not chosen:
            continue
        representations = ('direction', 'cartesian') if current.motion_policy == 'full-input-rectilinear' else ('direction',)
        for representation in representations:
            provider = StellarMotionProvider(current, representation=representation)
            try:
                admission = provider.describe().admissions[0]
                require(asdict(admission.reference) == models[index]['references'][representation],
                        'Reconstructed stellar reference differs')
                by_hip = {key.value.rsplit(':', 1)[1]: key for key in admission.objects}
                query = StateQuery(admission.catalogue, admission.model,
                    tuple(by_hip[hip] for hip in chosen), (instant,), admission.reference,
                    AccuracyRequest(metric='euclidean_norm') if representation == 'cartesian' else AccuracyRequest(),
                    require_velocity=representation == 'cartesian')
                with Kernel(references=(admission.reference,)) as kernel:
                    kernel.register(provider, ownership='borrowed')
                    with kernel.open_session(SessionPolicy((admission.catalogue,))) as session:
                        batch = session.evaluate(query)
                for hip, state in zip(chosen, batch.states, strict=True):
                    evaluated.setdefault(hip, {})[representation] = asdict(state)
            finally:
                provider.close()
    return b''.join(encode(dict(identifier=hip, model_index=index,
        status='unavailable' if index is None else 'evaluated', reasons=list(reasons),
        direction=evaluated.get(hip, {}).get('direction'),
        cartesian=evaluated.get(hip, {}).get('cartesian'))) + b'\n'
        for hip, index, reasons in selection)


def resolve_stellar_epoch(catalogue, instant, *, reuse_window_julian_years, identifiers=None):
    """Resolve native TCB positions using an inclusive, explicitly chosen window.

    The anchor never slides. A reused state retains its saved time even outside
    requested-event model coverage; the receipt discloses that approximation.
    Outside the window all original model domains must admit the target.
    """
    require(type(catalogue) is StellarEpochCatalogue, 'A validated stellar epoch catalogue is required')
    require(type(instant) is TimePoint and instant.scale == 'tcb', 'A resolved native TCB event is required')
    window = reuse_window_julian_years
    require(not isinstance(window, bool) and isinstance(window, (Real, Decimal)),
            'A finite nonnegative numeric Julian-year window is required')
    try:
        years = Fraction(window)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError('A finite nonnegative numeric Julian-year window is required') from error
    require(years >= 0, 'A finite nonnegative numeric Julian-year window is required')
    manifest = decode(catalogue.manifest)
    anchor = catalogue.instant
    separation = abs(_day(instant) - _day(anchor))
    reused = separation <= years * Fraction(1461, 4)
    models = manifest['motion_identity']['models']
    coverage = [dict(policy=m['policy'], contains_requested_event=
        TimeSpan(*(TimePoint(*t) for t in m['admission']['coverage'])).contains(instant)) for m in models]
    if not reused:
        require(all(m['contains_requested_event'] for m in coverage),
                'Requested event outside an original stellar model domain')
    # Validate all identifiers before reconstruction or any SDK work.
    ids = None if identifiers is None else tuple(identifiers)
    subset = None if ids is None else catalogue.at(anchor, ids)
    if reused:
        payload = catalogue.states_payload if subset is None else b''.join(encode(r)+b'\n' for r in subset)
    else:
        payload = _advance(catalogue, instant, ids, manifest)
    receipt = dict(schema='wenu-stellar-epoch-resolution/1', mode='reused' if reused else 'advanced',
        epoch_manifest_sha256=sha256(catalogue.manifest).hexdigest(),
        motion_identity=manifest['motion_identity'],
        code_identity=dict(saved_product=manifest['code_identity'],
            query_sha256=sha256(Path(__file__).read_bytes()).hexdigest()),
        policy='fixed-original-anchor-inclusive-julian-year-window/1',
        catalogue_event=asdict(anchor), requested_event=asdict(instant),
        actual_position_event=asdict(anchor if reused else instant),
        reuse_window=dict(value=str(window), units='Julian year (365.25 SI days)', exact_value=_ratio(years)),
        separation_days=_ratio(separation), identifiers=None if ids is None else list(ids),
        requested_event_model_coverage=coverage,
        approximation=dict(kind='fixed-position' if reused else 'original-admitted-model',
            requested_event_error='not-quantified',
            saved_state_evidence='retained' if reused else 'existing model evidence at requested event',
            physical_accuracy='not-qualified'))
    return StellarEpochResolution(catalogue.source, payload, encode(receipt))
