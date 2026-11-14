import os

class Config:
    # SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-fallback')
    pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False