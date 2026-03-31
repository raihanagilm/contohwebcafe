"""
Configuration Module
Konfigurasi untuk Flask application
"""

import os
from datetime import timedelta

class Config:
    """Konfigurasi aplikasi Flask"""
    
    # Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cafe-cms-secret-key-change-in-production-2024'
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set True di production dengan HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # MongoDB Atlas Configuration
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE') or 'cafe_cms'
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size (setelah kompresi)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Upload Subdirectories
    UPLOAD_SUBDIRS = {
        'menu': os.path.join(UPLOAD_FOLDER, 'menu'),
        'gallery': os.path.join(UPLOAD_FOLDER, 'gallery'),
        'promo': os.path.join(UPLOAD_FOLDER, 'promo'),
        'logo': os.path.join(UPLOAD_FOLDER, 'logo')
    }
    
    # Image Compression Settings
    IMAGE_MAX_WIDTH = 1200
    IMAGE_MAX_HEIGHT = 800
    IMAGE_QUALITY = 85
    IMAGE_FORMAT = 'JPEG'
    
    # Application Settings
    APP_NAME = 'Cafe CMS'
    APP_VERSION = '1.0.0'
    
    # Admin Default Credentials
    ADMIN_DEFAULT_USERNAME = 'admin'
    ADMIN_DEFAULT_PASSWORD = 'admin123'
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create upload directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        for subdir in Config.UPLOAD_SUBDIRS.values():
            os.makedirs(subdir, exist_ok=True)