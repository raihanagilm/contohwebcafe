"""
Settings Routes
Pengaturan website: Home & About
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from datetime import datetime
import re
from .auth import admin_required
from .helpers import compress_image_to_bytes

settings_bp = Blueprint('settings', __name__, url_prefix='/admin')

# ==================== HOME SETTINGS ====================
@settings_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Halaman pengaturan website - LOGO & ABOUT IMAGE DISIMPAN KE MONGODB"""
    from flask import current_app as app, session  # Pastikan session di-import
    db = app.db

    if request.method == 'POST':
        # Process logo upload
        logo_bytes = None
        logo_filename = None
        logo_mime = None
        
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                logo_bytes = compress_image_to_bytes(file, app)
                if logo_bytes:
                    logo_filename = secure_filename(file.filename)
                    logo_mime = file.content_type or 'image/png'
        
        # Process about image upload
        about_image_bytes = None
        about_image_mime = None
        
        if 'about_image' in request.files:
            file = request.files['about_image']
            if file and file.filename != '':
                about_image_bytes = compress_image_to_bytes(file, app)
                if about_image_bytes:
                    about_image_mime = file.content_type or 'image/jpeg'
        
        # Extract iframe src dari Google Maps iframe
        google_maps_iframe = request.form.get('google_maps_iframe', '').strip()
        
        # Clean iframe code - extract only the src attribute
        import re
        iframe_match = re.search(r'src="([^"]+)"', google_maps_iframe)
        if iframe_match:
            google_maps_iframe_clean = iframe_match.group(1)
        else:
            google_maps_iframe_clean = google_maps_iframe if google_maps_iframe.startswith('http') else ''
        
        settings_data = {
            'cafe_name': request.form.get('cafe_name', 'Cafe Kita'),
            'tagline': request.form.get('tagline', 'Tempat Ngopi Paling Nyaman'),
            'description': request.form.get('description', ''),
            'address': request.form.get('address', ''),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'opening_hours': request.form.get('opening_hours', ''),
            'whatsapp_number': request.form.get('whatsapp_number', ''),
            'google_maps_url': request.form.get('google_maps_url', ''),
            'google_maps_iframe': google_maps_iframe_clean,
            'updated_at': datetime.now()
        }
        
        # Simpan logo ke MongoDB
        if logo_bytes:
            settings_data['logo_data'] = logo_bytes
            settings_data['logo_filename'] = logo_filename
            settings_data['logo_mime'] = logo_mime
            settings_data['logo_size'] = len(logo_bytes)
        
        # Simpan about image ke MongoDB
        if about_image_bytes:
            settings_data['about_image_data'] = about_image_bytes
            settings_data['about_image_mime'] = about_image_mime
        
        # Update settings di database
        db.update_settings(settings_data)
        
        # ✅ SIMPAN TAB AKTIF KE SESSION (INI YANG KURANG!)
        active_tab = request.form.get('active_tab', 'brand')  # Ambil dari hidden input
        session['settings_active_tab'] = active_tab  # Simpan ke session
        
        flash('Pengaturan berhasil disimpan!', 'success')
        return redirect(url_for('settings.settings'))

    # ✅ AMBIL TAB AKTIF DARI SESSION (INI YANG KURANG!)
    active_tab = session.pop('settings_active_tab', 'brand')  # Default 'brand' jika tidak ada
    
    settings = db.get_settings()
    return render_template('admin/settings.html', settings=settings, active_tab=active_tab)  # ✅ Kirim active_tab ke template