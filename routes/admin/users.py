"""
Users Management Routes
CRUD untuk admin users
"""

from flask import Blueprint, render_template
from .auth import admin_required

users_bp = Blueprint('users', __name__, url_prefix='/admin')

# ==================== VIEW USERS ====================
@users_bp.route('/users')
@admin_required
def users():
    """Halaman manajemen users"""
    from flask import current_app as app
    db = app.db
    users = db.get_all_users()
    return render_template('admin/users.html', users=users)