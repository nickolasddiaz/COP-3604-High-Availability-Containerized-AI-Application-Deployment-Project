import os

class Config:
    OPENROUTER_API_KEY: str = os.getenv('OPENROUTER_API_KEY', 'key-does-not-exist')
    OPENROUTER_MODEL: str = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct')

    LOCAL_AI_DEV: bool = os.getenv('LOCAL_AI_DEV', 'false').lower() == 'true'
    LOCAL_MODEL: str = os.getenv('LOCAL_MODEL', 'llama3.2')
    LOCAL_MODEL_URL: str = os.getenv('LOCAL_MODEL_URL', 'http://localhost:11434')

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False