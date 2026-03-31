"""
Menu Management Routes
CRUD untuk menu items dengan kategori dinamis dari database
"""

from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from bson import ObjectId
from datetime import datetime
from .auth import admin_required
from .helpers import compress_image_to_bytes

menu_bp = Blueprint('menu', __name__, url_prefix='/admin')

# ==================== MENU MANAGEMENT ROUTES ====================
@menu_bp.route('/menu')
@admin_required
def menu():
    """Halaman manajemen menu dengan sorting persisten (session-based)"""
    from flask import current_app as app
    db = app.db
    
    # Get sort parameters from session (BUKAN dari URL)
    sort_by = session.get('menu_sort_by', 'created_at')
    sort_order = session.get('menu_sort_order', 'desc')
    
    # Get all menu items dengan sorting
    menu_items = db.get_all_menu(sort_by=sort_by, sort_order=sort_order)
    
    # Get categories
    categories = db.get_categories()
    
    # Get count menu per category
    category_counts = db.get_category_counts()
    
    return render_template('admin/menu.html', 
                         menu=menu_items, 
                         categories=categories,
                         category_counts=category_counts,
                         current_sort=sort_by,
                         current_order=sort_order)

@menu_bp.route('/menu/sort')
@admin_required
def menu_sort():
    """Endpoint untuk update sort preference (AJAX)"""
    from flask import current_app as app
    
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # Validasi
    valid_sort_fields = ['name', 'price', 'category', 'created_at', 'available']
    if sort_by not in valid_sort_fields:
        sort_by = 'created_at'
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Simpan ke session
    session['menu_sort_by'] = sort_by
    session['menu_sort_order'] = sort_order
    
    return {'success': True, 'sort_by': sort_by, 'sort_order': sort_order}
# ==================== ADD MENU ====================
@menu_bp.route('/menu/add', methods=['POST'])
@admin_required
def menu_add():
    """Tambah menu baru - GAMBAR DISIMPAN KE MONGODB"""
    from flask import current_app as app
    db = app.db
    
    try:
        # Process image untuk disimpan ke MongoDB
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
        
        menu_data = {
            'name': request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'price': int(request.form.get('price', 0)),
            'category': request.form.get('category', 'other').lower().strip(),
            'available': 'available' in request.form,
            'is_recommended': 'is_recommended' in request.form,
            'created_at': datetime.now()
        }
        
        # Simpan image data ke MongoDB (binary)
        if image_bytes:
            menu_data['image_data'] = image_bytes
            menu_data['image_filename'] = image_filename
            menu_data['image_mime'] = image_mime
            menu_data['image_size'] = len(image_bytes)
        
        # Validasi
        if not menu_data['name'] or menu_data['price'] <= 0:
            flash('Nama menu dan harga harus diisi dengan benar!', 'danger')
            return redirect(url_for('menu.menu'))
        
        # Tambahkan ke database
        db.add_menu_item(menu_data)
        
        flash(f'Menu "{menu_data["name"]}" berhasil ditambahkan!', 'success')
        return redirect(url_for('menu.menu'))
    
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('menu.menu'))

# ==================== UPDATE MENU ====================
@menu_bp.route('/menu/update/<menu_id>', methods=['POST'])
@admin_required
def menu_update(menu_id):
    """Update menu item"""
    from flask import current_app as app
    db = app.db
    try:
        # Process image
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
            'name': request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'price': int(request.form.get('price', 0)),
            'category': request.form.get('category', 'other').lower().strip(),
            'available': 'available' in request.form,
            'is_recommended': 'is_recommended' in request.form,  # ✅ TAMBAHKAN INI
            'updated_at': datetime.now()
        }
        
        # Simpan image data ke MongoDB (binary)
        if image_bytes:
            update_data['image_data'] = image_bytes
            update_data['image_filename'] = image_filename
            update_data['image_mime'] = image_mime
            update_data['image_size'] = len(image_bytes)
        
        # Validasi
        if not update_data['name'] or update_data['price'] <= 0:
            flash('Nama menu dan harga harus diisi dengan benar!', 'danger')
            return redirect(url_for('menu.menu'))
        
        db.update_menu_item(menu_id, update_data)
        flash('Menu berhasil diupdate!', 'success')
    
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')

    return redirect(url_for('menu.menu'))

# ==================== DELETE MENU ====================
@menu_bp.route('/menu/delete/<menu_id>', methods=['POST'])
@admin_required
def menu_delete(menu_id):
    """Hapus menu - Menggunakan POST method"""
    from flask import current_app as app
    db = app.db
    
    try:
        # Get menu name before delete
        menu_item = db.menu.find_one({'_id': ObjectId(menu_id)})
        menu_name = menu_item['name'] if menu_item else 'Menu'
        
        # Delete from database
        db.delete_menu_item(menu_id)
        
        flash(f'Menu "{menu_name}" berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
    
    return redirect(url_for('menu.menu'))
# Di menu.py, tambahkan route baru:

# ==================== GET CATEGORIES ====================
@menu_bp.route('/menu/categories')
@admin_required
def get_categories():
    """API untuk mendapatkan semua kategori"""
    from flask import current_app as app, jsonify
    db = app.db
    
    # Ambil dari collection terpisah atau dari menu
    try:
        if 'categories' in db.db.list_collection_names():
            categories = list(db.db.categories.find().sort('name', 1))
            categories_list = [cat['name'] for cat in categories]
        else:
            categories_list = db.menu.distinct('category')
            categories_list.sort()
        
        return jsonify({'success': True, 'categories': categories_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Di routes/admin/menu.py, tambahkan di bagian bawah setelah route menu_delete:

# ==================== EDIT MENU API (AJAX) ====================
@menu_bp.route('/menu/edit/<menu_id>')
@admin_required
def menu_edit_api(menu_id):
    """API endpoint untuk mendapatkan data menu untuk edit - ENCODE IMAGE KE BASE64"""
    from flask import current_app as app, jsonify
    import base64
    db = app.db
    
    try:
        menu_item = db.menu.find_one({'_id': ObjectId(menu_id)})
        
        if not menu_item:
            return jsonify({'success': False, 'message': 'Menu tidak ditemukan'}), 404
        
        # Convert ObjectId to string
        menu_item['_id'] = str(menu_item['_id'])
        
        # Encode image ke base64 jika ada
        if 'image_data' in menu_item and menu_item['image_data']:
            try:
                menu_item['image_base64'] = base64.b64encode(menu_item['image_data']).decode('utf-8')
                menu_item['image_mime'] = menu_item.get('image_mime', 'image/jpeg')
                menu_item['image_url'] = f"data:{menu_item['image_mime']};base64,{menu_item['image_base64']}"
            except Exception as e:
                menu_item['image_url'] = None
        else:
            menu_item['image_url'] = None
        
        # Hapus field bytes agar bisa di-serialize ke JSON
        if 'image_data' in menu_item:
            del menu_item['image_data']
        
        return jsonify({
            'success': True,
            'data': menu_item
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== CATEGORY MANAGEMENT ====================
@menu_bp.route('/menu/categories')
@admin_required
def get_categories_api():
    """API untuk mendapatkan semua kategori"""
    from flask import current_app as app, jsonify
    db = app.db
    
    try:
        categories = db.get_all_categories()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@menu_bp.route('/menu/category/add', methods=['POST'])
@admin_required
def menu_category_add():
    """Tambah kategori baru"""
    from flask import current_app as app, jsonify, request
    db = app.db
    
    category_name = request.form.get('category', '').lower().strip()
    
    if not category_name:
        return jsonify({'success': False, 'message': 'Nama kategori tidak boleh kosong'}), 400
    
    success = db.add_category(category_name)
    
    if success:
        return jsonify({'success': True, 'message': 'Kategori berhasil ditambahkan'})
    else:
        return jsonify({'success': False, 'message': 'Kategori sudah ada'}), 400

@menu_bp.route('/menu/category/delete/<category_name>', methods=['POST'])
@admin_required
def menu_category_delete(category_name):
    """Hapus kategori"""
    from flask import current_app as app, jsonify
    db = app.db
    
    category_name = category_name.lower().strip()
    
    # Cek apakah masih digunakan
    menu_count = db.menu.count_documents({'category': category_name})
    
    if menu_count > 0:
        return jsonify({
            'success': False, 
            'message': f'Kategori masih digunakan oleh {menu_count} menu, tidak bisa dihapus'
        }), 400
    
    success = db.delete_category(category_name)
    
    if success:
        return jsonify({'success': True, 'message': 'Kategori berhasil dihapus'})
    else:
        return jsonify({'success': False, 'message': 'Gagal menghapus kategori'}), 500