"""Milestone 45G.1 observer ephemeris resource contracts."""

from wenu import Observer


def test_observer_close_is_idempotent():
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )

    assert observer._ephemeris_finalizer.alive
    observer.close()
    assert not observer._ephemeris_finalizer.alive
    observer.close()


def test_observer_context_manager_closes_ephemeris():
    with Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    ) as observer:
        finalizer = observer._ephemeris_finalizer
        assert finalizer.alive

    assert not finalizer.alive
