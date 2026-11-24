import os
from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo

class Config:
    OPENROUTER_API_KEY: str = os.getenv('OPENROUTER_API_KEY', ' ')
    OPENROUTER_MODEL: str = os.getenv('OPENROUTER_MODEL', ' ')

    LOCAL_AI_DEV: bool = os.getenv('LOCAL_AI_DEV', 'false').lower() == 'true'
    LOCAL_MODEL: str = os.getenv('LOCAL_MODEL', 'llama3.2')
    LOCAL_MODEL_URL: str = os.getenv('LOCAL_MODEL_URL', 'http://localhost:11434')


    DB_USER: str = os.getenv("DB_USER", ' ')
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", ' ')
    DB_HOST: str = os.getenv("DB_HOST", 'localhost')
    DB_PORT: str = os.getenv("DB_PORT", ' ')
    DB_NAME: str = os.getenv("DB_NAME", ' ')

    if DB_HOST == 'localhost':
        raise Exception("testing")


    CONNECTIONSTRING = make_conninfo(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
    )

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False