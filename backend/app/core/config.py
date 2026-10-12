import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base application configuration."""
    APP_ENV = os.getenv('APP_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'pixel-t-dev-secret-change-in-production')
    BACKEND_HOST = os.getenv('BACKEND_HOST', '127.0.0.1')
    BACKEND_PORT = int(os.getenv('BACKEND_PORT', 5000))
    MAX_CONTENT_LENGTH = 11 * 1024 * 1024

    # Centralized CORS Configuration
    CORS_ORIGINS = os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173'
    ).split(',')

    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    SUPABASE_STORAGE_BUCKET = os.getenv('SUPABASE_STORAGE_BUCKET', 'analysis-assets')
    MODEL_CHECKPOINT_PATH = os.getenv('MODEL_CHECKPOINT_PATH', '')
    MODEL_DEVICE = os.getenv('MODEL_DEVICE', 'auto')
    MODEL_INFERENCE_ENABLED = os.getenv('MODEL_INFERENCE_ENABLED', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    APP_ENV = 'testing'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config():
    """Retrieve configuration based on APP_ENV."""
    env = os.getenv('APP_ENV', 'development').lower()
    return config_by_name.get(env, DevelopmentConfig)
