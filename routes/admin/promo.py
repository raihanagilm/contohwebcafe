"""
Promo Management Routes
CRUD untuk promo items
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from bson import ObjectId
from datetime import datetime
from .auth import admin_required
from .helpers import compress_image_to_bytes
import base64

promo_bp = Blueprint('promo', __name__, url_prefix='/admin')

# ==================== VIEW PROMO ====================
@promo_bp.route('/promo')
@admin_required
def promo():
    """Halaman manajemen promo"""
    from flask import current_app as app
    db = app.db
    promo_items = db.get_all_promo()
    return render_template('admin/promo.html', promo=promo_items)

# ==================== EDIT PROMO API (AJAX) ====================
@promo_bp.route('/promo/edit/<promo_id>')
@admin_required
def promo_edit_api(promo_id):
    """API endpoint untuk mendapatkan data promo untuk edit - ENCODE IMAGE KE BASE64"""
    from flask import current_app as app
    from bson import ObjectId
    db = app.db
    
    try:
        promo = db.promo.find_one({'_id': ObjectId(promo_id)})
        
        if not promo:
            return jsonify({
                'success': False,
                'message': 'Promo tidak ditemukan'
            }), 404
        
        # Convert ObjectId to string
        promo['_id'] = str(promo['_id'])
        
        # Encode image_data ke base64 jika ada
        if 'image_data' in promo and promo['image_data']:
            try:
                promo['image_base64'] = base64.b64encode(promo['image_data']).decode('utf-8')
                promo['image_mime'] = promo.get('image_mime', 'image/jpeg')
                promo['image_url'] = f"data:{promo['image_mime']};base64,{promo['image_base64']}"
                # Hapus binary data agar bisa di-serialize ke JSON
                del promo['image_data']
            except Exception as e:
                print(f"Error encoding image: {e}")
                promo['image_url'] = None
        
        return jsonify({
            'success': True,
            'data': promo
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ==================== ADD PROMO ====================
@promo_bp.route('/promo/add', methods=['POST'])
@admin_required
def promo_add():
    """Tambah promo baru - GAMBAR DISIMPAN KE MONGODB"""
    from flask import current_app as app
    db = app.db

    try:
        image_bytes = None
        image_filename = None
        image_mime = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                image_bytes = compress_image_to_bytes(file, app)
                if image_bytes:
                    image_filename = secure_filename(file.filename)
                    image_mime = file.content_type or 'image/jpeg'
        
        promo_data = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'discount': request.form.get('discount', ''),
            'valid_until': request.form.get('valid_until', ''),
            'visible': 'visible' in request.form,
            'created_at': datetime.now()
        }
        
        # Simpan image ke MongoDB jika ada
        if image_bytes:
            promo_data['image_data'] = image_bytes
            promo_data['image_filename'] = image_filename
            promo_data['image_mime'] = image_mime
            promo_data['image_size'] = len(image_bytes)
        
        # Validasi
        if not promo_data['title']:
            flash('Judul promo harus diisi!', 'danger')
            return redirect(url_for('promo.promo'))
        
        # Tambahkan ke database
        db.add_promo(promo_data)
        flash(f'Promo "{promo_data["title"]}" berhasil ditambahkan!', 'success')
        return redirect(url_for('promo.promo'))

    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('promo.promo'))

# ==================== UPDATE PROMO ====================
@promo_bp.route('/promo/update/<promo_id>', methods=['POST'])
@admin_required
def promo_update(promo_id):
    """Update promo - GAMBAR BARU DISIMPAN KE MONGODB"""
    from flask import current_app as app
    db = app.db

    try:
        image_bytes = None
        image_filename = None
        image_mime = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                image_bytes = compress_image_to_bytes(file, app)
                if image_bytes:
                    image_filename = secure_filename(file.filename)
                    image_mime = file.content_type or 'image/jpeg'
        
        update_data = {
            'title': request.form.get('title', '').strip(),
            'description': request.form.get('description', '').strip(),
            'discount': request.form.get('discount', ''),
            'valid_until': request.form.get('valid_until', ''),
            'visible': 'visible' in request.form,
            'updated_at': datetime.now()
        }
        
        # Update image jika ada yang baru
        if image_bytes:
            update_data['image_data'] = image_bytes
            update_data['image_filename'] = image_filename
            update_data['image_mime'] = image_mime
            update_data['image_size'] = len(image_bytes)
        
        # Update database
        db.update_promo(promo_id, update_data)
        flash('Promo berhasil diupdate!', 'success')
        return redirect(url_for('promo.promo'))

    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('promo.promo'))

# ==================== DELETE PROMO ====================
@promo_bp.route('/promo/delete/<promo_id>', methods=['POST'])
@admin_required
def promo_delete(promo_id):
    """Hapus promo"""
    from flask import current_app as app
    db = app.db

    try:
        # Get promo title before delete
        promo_item = db.promo.find_one({'_id': ObjectId(promo_id)})
        promo_title = promo_item['title'] if promo_item else 'Promo'
        
        # Delete from database
        db.delete_promo(promo_id)
        
        flash(f'Promo "{promo_title}" berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')

    return redirect(url_for('promo.promo'))