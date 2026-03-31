"""
Authentication Routes
Login, Logout, dan fungsi auth lainnya
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')

# ==================== DECORATOR ====================
def admin_required(f):
    """Decorator untuk memeriksa apakah admin sudah login"""
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Silakan login terlebih dahulu!', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrap

# ==================== ROOT ROUTE ====================
@auth_bp.route('/')
def admin_root():
    """Redirect /admin ke /admin/login atau /admin/dashboard"""
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

# ==================== LOGIN ====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login admin"""
    from flask import current_app as app
    
    # Redirect jika sudah login
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username dan password harus diisi!', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check credentials
        db = app.db
        user = db.check_login(username, password)
        
        if user:
            session['admin_logged_in'] = True
            session['admin_username'] = user['username']
            session['admin_role'] = user['role']
            session.permanent = True
            
            flash(f'Selamat datang, {user["username"]}!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Username atau password salah!', 'danger')
    
    return render_template('admin/login.html')

# ==================== LOGOUT ====================
@auth_bp.route('/logout')
def logout():
    """Logout admin"""
    username = session.get('admin_username', 'Admin')
    session.clear()
    flash(f'{username}, Anda telah logout.', 'info')
    return redirect(url_for('auth.login'))

# ==================== CHANGE PASSWORD ====================
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@admin_required
def change_password():
    """Halaman ganti password"""
    from flask import current_app as app
    db = app.db
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validasi input
        if not current_password or not new_password or not confirm_password:
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('auth.change_password'))
        
        # Cek current password
        username = session.get('admin_username')
        user = db.users.find_one({'username': username})
        
        if not user or not check_password_hash(user['password'], current_password):
            flash('Password saat ini salah!', 'danger')
            return redirect(url_for('auth.change_password'))
        
        # Cek new password match
        if new_password != confirm_password:
            flash('Password baru dan konfirmasi tidak cocok!', 'danger')
            return redirect(url_for('auth.change_password'))
        
        # Cek minimal length
        if len(new_password) < 6:
            flash('Password minimal 6 karakter!', 'danger')
            return redirect(url_for('auth.change_password'))
        
        # Update password
        db.users.update_one(
            {'username': username},
            {'$set': {'password': generate_password_hash(new_password)}}
        )
        
        flash('Password berhasil diubah! Silakan login kembali.', 'success')
        session.clear()  # Force logout
        return redirect(url_for('auth.login'))
    
    return render_template('admin/change_password.html')