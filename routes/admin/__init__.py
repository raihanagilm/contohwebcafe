"""
Admin Routes Package
Mengorganisir semua routes admin ke dalam package terpisah
"""
from flask import Blueprint

# Import semua blueprints dari file terpisah
from .auth import auth_bp
from .dashboard import dashboard_bp
from .settings import settings_bp
from .menu import menu_bp
from .gallery import gallery_bp
from .promo import promo_bp
from .social import social_bp
from .users import users_bp
from .about import about_bp  # TAMBAHKAN INI

# Gabungkan semua blueprints ke dalam satu package
__all__ = [
    'auth_bp',
    'dashboard_bp',
    'settings_bp',
    'menu_bp',
    'gallery_bp',
    'promo_bp',
    'social_bp',
    'about_bp'  # TAMBAHKAN INI
]