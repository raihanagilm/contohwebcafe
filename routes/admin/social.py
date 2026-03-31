"""
Social Media Management Routes
CRUD untuk social media links dengan fitur Edit & Visible/Hidden
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from bson import ObjectId
from datetime import datetime
from .auth import admin_required

social_bp = Blueprint('social', __name__, url_prefix='/admin')

# Mapping platform ke icon Font Awesome
PLATFORM_ICONS = {
    'facebook': 'fab fa-facebook',
    'instagram': 'fab fa-instagram',
    'twitter': 'fab fa-twitter',
    'x': 'fab fa-x-twitter',
    'whatsapp': 'fab fa-whatsapp',
    'youtube': 'fab fa-youtube',
    'tiktok': 'fab fa-tiktok',
    'linkedin': 'fab fa-linkedin',
    'github': 'fab fa-github',
    'pinterest': 'fab fa-pinterest',
    'reddit': 'fab fa-reddit',
    'snapchat': 'fab fa-snapchat',
    'telegram': 'fab fa-telegram',
    'discord': 'fab fa-discord',
    'spotify': 'fab fa-spotify'
}

# ==================== VIEW SOCIAL ====================
@social_bp.route('/social')
@admin_required
def social():
    """Halaman manajemen social media"""
    from flask import current_app as app
    db = app.db
    social_links = db.get_social_links()
    return render_template('admin/social.html', social=social_links, platform_icons=PLATFORM_ICONS)

# ==================== API GET SOCIAL (untuk Edit) ====================
@social_bp.route('/api/social/<link_id>')
@admin_required
def api_get_social(link_id):
    """API endpoint untuk get social media data"""
    from flask import current_app as app
    db = app.db
    
    try:
        link = db.social.find_one({'_id': ObjectId(link_id)})
        if link:
            link['_id'] = str(link['_id'])
            return jsonify({'success': True, 'data': link})
        else:
            return jsonify({'success': False, 'message': 'Link tidak ditemukan'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ADD SOCIAL ====================
@social_bp.route('/social/add', methods=['POST'])
@admin_required
def social_add():
    """Tambah social media link"""
    from flask import current_app as app
    db = app.db
    
    try:
        platform = request.form.get('platform', '').strip().lower()
        icon_from_form = request.form.get('icon', '').strip()
        
        # ✅ Auto-fill icon dari platform jika tidak diisi
        if icon_from_form:
            icon = icon_from_form
        elif platform in PLATFORM_ICONS:
            icon = PLATFORM_ICONS[platform]
        else:
            icon = 'fas fa-link'
        
        social_data = {
            'platform': request.form.get('platform', '').strip(),
            'url': request.form.get('url', '').strip(),
            'icon': icon,  # ✅ Icon dengan format Font Awesome lengkap
            'visible': request.form.get('visible') == 'on',
            'created_at': datetime.now()
        }
        
        # Validasi
        if not social_data['platform'] or not social_data['url']:
            flash('Platform dan URL harus diisi!', 'danger')
            return redirect(url_for('social.social'))
        
        # Tambahkan ke database
        db.add_social_link(social_data)
        flash(f'Social media {social_data["platform"]} berhasil ditambahkan!', 'success')
        return redirect(url_for('social.social'))
    
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('social.social'))

# ==================== UPDATE SOCIAL ====================
@social_bp.route('/social/update/<link_id>', methods=['POST'])
@admin_required
def social_update(link_id):
    """Update social media link"""
    from flask import current_app as app
    db = app.db
    
    try:
        platform = request.form.get('platform', '').strip().lower()
        icon_from_form = request.form.get('icon', '').strip()
        
        # ✅ Auto-fill icon dari platform jika tidak diisi
        if icon_from_form:
            icon = icon_from_form
        elif platform in PLATFORM_ICONS:
            icon = PLATFORM_ICONS[platform]
        else:
            icon = 'fas fa-link'
        
        update_data = {
            'platform': request.form.get('platform', '').strip(),
            'url': request.form.get('url', '').strip(),
            'icon': icon,  # ✅ Icon dengan format Font Awesome lengkap
            'visible': request.form.get('visible') == 'on',
            'updated_at': datetime.now()
        }
        
        # Validasi
        if not update_data['platform'] or not update_data['url']:
            flash('Platform dan URL harus diisi!', 'danger')
            return redirect(url_for('social.social'))
        
        # Update database
        db.update_social_link(link_id, update_data)
        flash(f'Social media {update_data["platform"]} berhasil diupdate!', 'success')
        return redirect(url_for('social.social'))
    
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('social.social'))

# ==================== DELETE SOCIAL ====================
@social_bp.route('/social/delete/<link_id>', methods=['POST'])
@admin_required
def social_delete(link_id):
    """Hapus social media link - menggunakan POST method"""
    from flask import current_app as app
    db = app.db
    
    try:
        # Get link name before delete
        link = db.social.find_one({'_id': ObjectId(link_id)})
        platform_name = link['platform'] if link else 'Social Media'
        
        # Delete from database
        db.delete_social_link(link_id)
        flash(f'Social media {platform_name} berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
    
    return redirect(url_for('social.social'))

# ==================== TOGGLE VISIBLE ====================
@social_bp.route('/social/toggle-visible/<link_id>', methods=['POST'])
@admin_required
def social_toggle_visible(link_id):
    """Toggle visibility social media link"""
    from flask import current_app as app, jsonify
    db = app.db
    
    try:
        link = db.social.find_one({'_id': ObjectId(link_id)})
        if not link:
            return jsonify({'success': False, 'message': 'Link tidak ditemukan'}), 404
        
        new_visible = not link.get('visible', True)
        
        db.social.update_one(
            {'_id': ObjectId(link_id)},
            {'$set': {'visible': new_visible, 'updated_at': datetime.now()}}
        )
        
        status = 'Visible' if new_visible else 'Hidden'
        return jsonify({
            'success': True, 
            'message': f'Visibility berhasil diubah ke {status}',
            'visible': new_visible
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500