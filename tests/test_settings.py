"""Test settings load properly."""


def test_settings() -> None:
    """Test settings load properly."""
    from source.config.settings import settings
    assert settings.DIR_OUTPUT
    assert settings.dict()['DIR_OUTPUT']
    assert settings.DIR_DATA_RAW
    assert settings.DIR_DATA_INTERIM
    assert settings.DIR_DATA_PROCESSED
    assert settings.DIR_DATA_EXTERNAL
    assert settings.DIR_NOTEBOOKS
    # assert settings.OPENAI_TOKEN
    # assert settings.OPENAI_TOKEN != "**SECRET**"
