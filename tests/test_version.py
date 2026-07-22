import wenu


def test_package_exposes_version() -> None:
    assert isinstance(wenu.__version__, str)
    assert wenu.__version__
    assert wenu.__version__ != "0+unknown"
