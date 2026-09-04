import os

class Config:
    # Essential security keys (Change these in production)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'platform-super-secret-vibe-key-2026')
    
    # Database Configuration - Defaults to SQLite, structured for easy migration to PostgreSQL/MySQL
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "database", "ihis.db")}')
    
    # Turn off tracking modifications to save system overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Absolute path for secure medical document and imaging uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit for high-res medical images