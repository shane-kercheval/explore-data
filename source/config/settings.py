"""
Contains the settings, tokens, etc. for the app.

To add a new setting:
    - 1) create an instance variable below
    - 2) create the corresponding field in `settings.env`.
"""
import os
import os.path
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Defines the settings for the app."""

    # directories for source code and data
    DIR_NOTEBOOKS: str
    DIR_DATA_RAW: str
    DIR_DATA_INTERIM: str
    DIR_DATA_EXTERNAL: str
    DIR_DATA_PROCESSED: str

    # output & logging
    DIR_OUTPUT: str
    LOGGING_CONFIG_PATH: str
    LOGGING_FILE_NAME: str

    # tokens
    # OPENAI_TOKEN: str = '**SECRET**'

settings_path = '/code/settings.env'
assert os.path.isfile(settings_path)

settings = Settings(_env_file=settings_path, _env_file_encoding='utf-8')

# settings.OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN')
# assert settings.OPENAI_TOKEN
