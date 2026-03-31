"""
Routes Package
Mengorganisir semua routes aplikasi
"""

from flask import Blueprint

# Import blueprints dari admin package (MODULAR)
from .admin.auth import auth_bp
from .admin.about import about_bp
from .admin.dashboard import dashboard_bp
from .admin.settings import settings_bp
from .admin.menu import menu_bp
from .admin.gallery import gallery_bp
from .admin.promo import promo_bp
from .admin.social import social_bp
from .admin.users import users_bp

# Import main blueprint (frontend)
from .main import main_bp

# Gabungkan semua blueprints
__all__ = [
    'main_bp',
    'auth_bp',
    'about_bp',
    'dashboard_bp',
    'settings_bp',
    'menu_bp',
    'gallery_bp',
    'promo_bp',
    'social_bp',
    'users_bp'
]