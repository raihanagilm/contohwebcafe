"""
Gallery Management Routes
CRUD untuk gallery photos - Server-Side View dengan Cookie
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response
from werkzeug.utils import secure_filename
from bson import ObjectId
from datetime import datetime
from .auth import admin_required
from .helpers import compress_image_to_bytes

gallery_bp = Blueprint('gallery', __name__, url_prefix='/admin')

# ==================== VIEW GALLERY ====================
@gallery_bp.route('/gallery')
@admin_required
def gallery():
    """Halaman manajemen gallery - View preference dari Cookie"""
    db = current_app.db
    
    # Get view preference from cookie (default: list)
    view = request.cookies.get('gallery_view', 'list')
    if view not in ['grid', 'list']:
        view = 'list'
    
    gallery_items = db.get_all_gallery()
    settings = db.get_settings()
    
    response = make_response(render_template('admin/gallery.html', 
                                           gallery=gallery_items, 
                                           settings=settings,
                                           current_view=view))
    return response


# ==================== SET VIEW PREFERENCE ====================
@gallery_bp.route('/gallery/set-view/<view>')
@admin_required
def set_gallery_view(view):
    """Set view preference ke cookie"""
    if view in ['grid', 'list']:
        response = make_response(redirect(url_for('gallery.gallery')))
        response.set_cookie('gallery_view', view, max_age=30*24*60*60, 
                          path='/admin', httponly=False, samesite='Lax')
        return response
    
    return redirect(url_for('gallery.gallery'))


# ==================== ADD GALLERY ====================
@gallery_bp.route('/gallery/add', methods=['POST'])
@admin_required
def gallery_add():
    """Tambah foto gallery - GAMBAR DISIMPAN KE MONGODB"""
    db = current_app.db
    
    try:
        image_bytes = None
        image_filename = None
        image_mime = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                image_bytes = compress_image_to_bytes(file, current_app)
                if image_bytes:
                    image_filename = secure_filename(file.filename)
                    image_mime = file.content_type or 'image/jpeg'
        
        if not image_bytes:
            flash('Silakan pilih foto untuk diupload!', 'danger')
            return redirect(url_for('gallery.gallery'))
        
        gallery_data = {
            'filename': image_filename,
            'caption': request.form.get('caption', '').strip(),
            'image_data': image_bytes,
            'image_mime': image_mime,
            'image_size': len(image_bytes),
            'is_valid': 1 if request.form.get('is_valid') == '1' else 1,
            'created_at': datetime.now()
        }
        
        db.add_gallery_image(gallery_data)
        flash('Foto gallery berhasil ditambahkan!', 'success')
        
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        print(f"Gallery add error: {str(e)}")
    
    return redirect(url_for('gallery.gallery'))


# ==================== EDIT GALLERY ====================
@gallery_bp.route('/gallery/edit-caption', methods=['POST'])
@admin_required
def gallery_edit_caption():
    """Edit foto gallery - CAPTION, VISIBILITY, dan GAMBAR (opsional)"""
    db = current_app.db
    
    try:
        image_id = request.form.get('image_id')
        if not image_id:
            flash('ID gambar tidak valid!', 'danger')
            return redirect(url_for('gallery.gallery'))
        
        update_data = {
            'caption': request.form.get('caption', '').strip(),
            'is_valid': 1 if request.form.get('is_valid') == '1' else 0,
            'updated_at': datetime.now()
        }
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                image_bytes = compress_image_to_bytes(file, current_app)
                if image_bytes:
                    update_data['image_data'] = image_bytes
                    update_data['filename'] = secure_filename(file.filename)
                    update_data['image_mime'] = file.content_type or 'image/jpeg'
                    update_data['image_size'] = len(image_bytes)
        
        result = db.gallery.update_one({'_id': ObjectId(image_id)}, {'$set': update_data})
        
        if result.modified_count > 0:
            flash('Foto gallery berhasil diupdate!', 'success')
        else:
            flash('Tidak ada perubahan yang dilakukan.', 'info')
            
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        print(f"Gallery edit error: {str(e)}")
    
    return redirect(url_for('gallery.gallery'))


# ==================== DELETE GALLERY ====================
@gallery_bp.route('/gallery/delete/<image_id>')
@admin_required
def gallery_delete(image_id):
    """Hapus foto gallery"""
    db = current_app.db
    
    try:
        try:
            oid = ObjectId(image_id)
        except Exception:
            flash('ID gambar tidak valid!', 'danger')
            return redirect(url_for('gallery.gallery'))
        
        gallery_item = db.gallery.find_one({'_id': oid})
        
        if not gallery_item:
            flash('Foto gallery tidak ditemukan!', 'warning')
            return redirect(url_for('gallery.gallery'))
        
        filename = gallery_item.get('filename', 'unknown')
        result = db.gallery.delete_one({'_id': oid})
        
        if result.deleted_count > 0:
            flash(f'Foto "{filename}" berhasil dihapus dari database!', 'success')
        else:
            flash('Gagal menghapus foto gallery!', 'danger')
            
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        print(f"Gallery delete error: {str(e)}")
    
    return redirect(url_for('gallery.gallery'))