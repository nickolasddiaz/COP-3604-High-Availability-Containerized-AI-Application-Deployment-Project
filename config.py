import os
from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo

class Config:
    load_dotenv()
    OPENROUTER_API_KEY:str = os.environ['OPENROUTER_API_KEY']
    OPENROUTER_MODEL:str  = os.environ['OPENROUTER_MODEL']

    LOCAL_AI_DEV:bool = os.environ['LOCAL_AI_DEV'].lower() == 'true'
    LOCAL_MODEL:str  = os.environ['LOCAL_MODEL']
    LOCAL_MODEL_URL:str  = os.environ['LOCAL_MODEL_URL']


    DB_USER:str  = os.environ["DB_USER"]
    DB_PASSWORD:str  = os.environ["DB_PASSWORD"]
    DB_HOST:str  = os.environ["DB_HOST"]
    DB_PORT:str  = os.environ["DB_PORT"]
    DB_NAME:str  = os.environ["DB_NAME"]

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