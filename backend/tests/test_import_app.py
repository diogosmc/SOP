"""Test application import."""

from app.main import app, create_app


def test_import_app() -> None:
    assert app is not None
    assert app.title == "COPILOTO"


def test_create_app_factory() -> None:
    instance = create_app()
    assert instance.title == "COPILOTO"
