"""
Cafe CMS - Main Application
Flask application dengan MongoDB untuk manajemen website cafe
"""
from flask import Flask, render_template
from config import Config
from models import CafeDB
from datetime import datetime
from routes import (
    main_bp,
    auth_bp,
    about_bp,
    dashboard_bp,
    settings_bp,
    menu_bp,
    gallery_bp,
    promo_bp,
    social_bp
)
import os
import base64

def create_app():
    """Factory function untuk membuat Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    Config.init_app(app)
    
    # Initialize MongoDB
    db = CafeDB(app.config['MONGODB_URI'], app.config['MONGODB_DATABASE'])
    
    # Create default admin
    db.create_default_admin()
    
    # Attach db to app for access in routes
    app.db = db
    
    # ==================== CUSTOM FILTERS ====================
    @app.template_filter('b64encode')
    def base64_encode_filter(data):
        """
        Custom Jinja2 filter untuk base64 encoding
        Digunakan untuk menampilkan gambar dari MongoDB
        """
        if data is None:
            return ''
        if isinstance(data, str):
            return base64.b64encode(data.encode()).decode()
        return base64.b64encode(data).decode()
    
    @app.template_filter('datetimeformat')
    def datetimeformat_filter(value, format='%d %B %Y'):
        """
        Custom Jinja2 filter untuk format datetime
        Handle: string, datetime, dict (MongoDB format), None
        """
        from datetime import datetime
        
        if not value:
            return '-'
        
        # ✅ Jika sudah datetime object
        if hasattr(value, 'strftime'):
            return value.strftime(format)
        
        # ✅ Jika string
        if isinstance(value, str):
            try:
                dt_value = datetime.strptime(value, '%Y-%m-%d')
                return dt_value.strftime(format)
            except:
                try:
                    dt_value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    return dt_value.strftime(format)
                except:
                    return value
        
        # ✅ Jika dict (MongoDB date format dengan $date)
        if isinstance(value, dict):
            date_str = value.get('$date')
            if date_str:
                try:
                    # Handle ISO format dengan timezone
                    if 'T' in str(date_str):
                        dt_value = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
                        # Remove timezone info for formatting
                        dt_value = dt_value.replace(tzinfo=None)
                    else:
                        dt_value = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
                    return dt_value.strftime(format)
                except:
                    return str(value)
        
        return str(value)
    
    @app.template_filter('is_promo_active')
    def is_promo_active_filter(valid_until):
        """
        Cek apakah promo masih aktif
        Handle: string, datetime, dict (MongoDB format), None
        """
        from datetime import datetime
        
        if not valid_until:
            return True
        
        # ✅ Jika sudah datetime object
        if hasattr(valid_until, 'strftime'):
            return valid_until.replace(tzinfo=None) > datetime.now()
        
        # ✅ Jika string
        if isinstance(valid_until, str):
            try:
                valid_date = datetime.strptime(valid_until, '%Y-%m-%d')
                return valid_date > datetime.now()
            except:
                try:
                    valid_date = datetime.strptime(valid_until, '%Y-%m-%d %H:%M:%S')
                    return valid_date > datetime.now()
                except:
                    return True
        
        # ✅ Jika dict (MongoDB date format dengan $date) - FIX UTAMA!
        if isinstance(valid_until, dict):
            date_str = valid_until.get('$date')
            if date_str:
                try:
                    # Handle ISO format dengan timezone
                    if 'T' in str(date_str):
                        valid_date = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
                        valid_date = valid_date.replace(tzinfo=None)
                    else:
                        valid_date = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
                    return valid_date > datetime.now()
                except:
                    return True
        
        return True
    
    # ==================== CONTEXT PROCESSORS ====================
    @app.context_processor
    def inject_globals():
        """Inject settings & social ke semua templates"""
        return dict(
            settings=db.get_settings(),
            social=db.get_social_links()  # ✅ Otomatis tersedia di semua template
        )
    
    @app.context_processor
    def inject_now():
        """Inject current datetime ke semua templates"""
        from datetime import datetime
        return {'now': datetime.now}
    
    # ==================== BEFORE REQUEST ====================
    @app.before_request
    def log_visitor():
        """Log visitor setiap request ke halaman frontend"""
        from flask import request
        
        # Skip logging untuk static files dan API calls
        if request.path.startswith('/static/') or request.path.startswith('/api/'):
            return
        
        # Skip logging untuk admin panel
        if request.path.startswith('/admin'):
            return
        
        # Log visitor
        ip_address = request.remote_addr
        db.log_visitor(ip_address)
    
    # ==================== ERROR HANDLERS ====================
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found error"""
        settings = db.get_settings()
        return render_template('404.html', settings=settings), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error"""
        settings = db.get_settings()
        return render_template('500.html', settings=settings), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden error"""
        settings = db.get_settings()
        return render_template('403.html', settings=settings), 403
    
    @app.context_processor
    def inject_helpers():
        """Inject helper functions ke semua templates"""
        def is_promo_active(valid_until):
            if not valid_until:
                return True
            if hasattr(valid_until, 'strftime'):
                return valid_until > datetime.now()
            if isinstance(valid_until, str):
                try:
                    return datetime.strptime(valid_until, '%Y-%m-%d') > datetime.now()
                except:
                    return True
            return True
        
        return {
            'is_promo_active': is_promo_active,
            'now': datetime.now
        }
    # ==================== REGISTER BLUEPRINTS ====================
    # URUTAN PENTING!
    app.register_blueprint(auth_bp, url_prefix='/admin')
    app.register_blueprint(about_bp, url_prefix='/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/admin')
    app.register_blueprint(settings_bp, url_prefix='/admin')
    app.register_blueprint(menu_bp, url_prefix='/admin')
    app.register_blueprint(gallery_bp, url_prefix='/admin')
    app.register_blueprint(promo_bp, url_prefix='/admin')
    app.register_blueprint(social_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    
    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print(" " * 15 + "☕ CAFE CMS APPLICATION ☕ ")
    print("=" * 60)
    print()
    print("📊 DATABASE INFORMATION ")
    print(f"   • MongoDB Atlas: {app.config['MONGODB_URI']} ")
    print(f"   • Database Name: {app.config['MONGODB_DATABASE']} ")
    print()
    print("🔐 ADMIN LOGIN ")
    print(f"   • URL: http://localhost:5000/admin ")
    print(f"   • Username: admin ")
    print(f"   • Password: admin123 ")
    print()
    print("🌐 PUBLIC WEBSITE ")
    print(f"   • Home: http://localhost:5000/ ")
    print()
    print("=" * 60)
    print("🚀 Starting Flask development server... ")
    print("=" * 60)
    print()
    app.run(debug=True, host='0.0.0.0', port=5000)