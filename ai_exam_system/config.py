import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///ai_exam.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # AI Model configurations
    BERT_MODEL_PATH = os.environ.get('BERT_MODEL_PATH', 'bert-base-uncased')
    GPT2_MODEL_PATH = os.environ.get('GPT2_MODEL_PATH', 'gpt2')
    
    # Proctoring configurations
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'mp4', 'webm'}

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DEVELOPMENT = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DEVELOPMENT = False
    
    # Override these in production environment
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
