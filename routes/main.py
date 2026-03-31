"""
Frontend Routes
Routes untuk halaman publik website cafe
"""
from flask import Blueprint, render_template, send_file, Response, request, flash, redirect, url_for
from bson import ObjectId
import io

main_bp = Blueprint('main', __name__)

# ==================== HOME PAGE ====================
@main_bp.route('/')
def home():
    """Halaman Home"""
    from flask import current_app as app
    db = app.db
    settings = db.get_settings()
    about = db.get_about()
    menu = db.get_all_menu()
    promo = db.get_all_promo()
    social = db.get_social_links()  # ✅ Ambil social media
    gallery = list(db.gallery.find({'is_valid': 1}).sort('created_at', -1).limit(6))
    categories = db.get_all_categories()
    
    return render_template('index.html',
                         settings=settings,
                         about=about,
                         menu=menu,
                         promo=promo,
                         social=social,
                         gallery=gallery,
                         categories=categories) 

# ==================== MENU PAGE ====================
@main_bp.route('/menu')
def menu_page():
    from flask import current_app as app
    import base64
    
    db = app.db
    settings = db.get_settings()
    menu = db.get_all_menu()
    categories = db.get_all_categories()
    
    # ✅ Convert binary ke base64 untuk template
    for item in menu:
        if 'image_data' in item and item['image_data']:
            item['image_data'] = base64.b64encode(item['image_data']).decode('utf-8')
            item['image_mime'] = item.get('image_mime', 'image/jpeg')
    
    return render_template('menu.html',
                         settings=settings,
                         menu=menu,
                         categories=categories)

# ==================== PROMO PAGE (BARU) ====================
@main_bp.route('/promo')
def promo_page():
    """Halaman Promo - ✅ ROUTE BARU"""
    from flask import current_app as app
    db = app.db
    settings = db.get_settings()
    promo = db.get_all_promo()
    
    return render_template('promo.html',
                         settings=settings,
                         promo=promo)

# ==================== ABOUT PAGE ====================
@main_bp.route('/about')
def about_page():
    from flask import current_app as app
    db = app.db
    settings = db.get_settings()
    about = db.get_about()  # ✅ Pastikan ini return data
    social = db.get_social_links()
    
    return render_template('about.html',
                         settings=settings,
                         about=about,
                         social=social)

# ==================== CONTACT PAGE ====================
@main_bp.route('/contact')
def contact_page():
    from flask import current_app as app
    db = app.db
    settings = db.get_settings()
    social = db.get_social_links()  # ✅ Sudah ada
    
    return render_template('contact.html',
                         settings=settings,
                         social=social)  # ✅ Sudah di-pass

# ==================== CONTACT FORM SUBMISSION ====================
@main_bp.route('/contact', methods=['POST'])
def contact_submit():
    """Handle contact form submission"""
    from flask import current_app as app
    db = app.db
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    message = request.form.get('message', '').strip()

    # Validasi
    if not name or not email or not message:
        flash('Nama, Email, dan Pesan harus diisi!', 'danger')
        return redirect(url_for('main.contact_page'))

    # Simpan pesan ke database
    try:
        from datetime import datetime
        contact_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'status': 'unread',
            'created_at': datetime.now()
        }
        
        # Cek apakah collection contacts ada
        if 'contacts' not in db.db.list_collection_names():
            db.db.create_collection('contacts')
        
        db.db.contacts.insert_one(contact_data)
        
        flash('Pesan Anda telah terkirim! Kami akan segera menghubungi Anda.', 'success')
    except Exception as e:
        print(f"Error saving contact: {e}")
        flash('Terjadi kesalahan saat mengirim pesan. Silakan coba lagi.', 'danger')

    return redirect(url_for('main.contact_page'))

# ==================== IMAGE SERVING ROUTES ====================
@main_bp.route('/images/menu/<menu_id>')
def serve_menu_image(menu_id):
    """Serve menu image from MongoDB"""
    from flask import current_app as app
    db = app.db
    try:
        menu_item = db.menu.find_one({'_id': ObjectId(menu_id)})
        if menu_item and 'image_data' in menu_item:
            return Response(
                menu_item['image_data'],
                mimetype=menu_item.get('image_mime', 'image/jpeg')
            )
        else:
            return send_file('static/images/placeholder-menu.jpg')
    except Exception as e:
        print(f"Error serving menu image: {e}")
        return send_file('static/images/placeholder-menu.jpg')

@main_bp.route('/images/gallery/<image_id>')
def serve_gallery_image(image_id):
    """Serve gallery image from MongoDB"""
    from flask import current_app as app
    db = app.db
    try:
        gallery_item = db.gallery.find_one({'_id': ObjectId(image_id)})
        if gallery_item and 'image_data' in gallery_item:
            return Response(
                gallery_item['image_data'],
                mimetype=gallery_item.get('image_mime', 'image/jpeg')
            )
        else:
            return send_file('static/images/placeholder-gallery.jpg')
    except Exception as e:
        print(f"Error serving gallery image: {e}")
        return send_file('static/images/placeholder-gallery.jpg')

@main_bp.route('/images/promo/<promo_id>')
def serve_promo_image(promo_id):
    """Serve promo image from MongoDB"""
    from flask import current_app as app
    db = app.db
    try:
        promo_item = db.promo.find_one({'_id': ObjectId(promo_id)})
        if promo_item and 'image_data' in promo_item:
            return Response(
                promo_item['image_data'],
                mimetype=promo_item.get('image_mime', 'image/jpeg')
            )
        else:
            return send_file('static/images/placeholder-promo.jpg')
    except Exception as e:
        print(f"Error serving promo image: {e}")
        return send_file('static/images/placeholder-promo.jpg')

@main_bp.route('/images/logo')
def serve_logo():
    """Serve logo from MongoDB - Settings Collection"""
    from flask import current_app as app
    db = app.db
    settings = db.get_settings()
    if settings and 'logo_data' in settings and settings['logo_data']:
        return Response(
            settings['logo_data'],
            mimetype=settings.get('logo_mime', 'image/png')
        )
    else:
        return send_file('static/images/logo-placeholder.png')

@main_bp.route('/images/about')
def serve_about_image():
    """Serve about image from MongoDB - About Collection"""
    from flask import current_app as app
    db = app.db
    about = db.get_about()
    if about and 'about_image_data' in about and about['about_image_data']:
        return Response(
            about['about_image_data'],
            mimetype=about.get('about_image_mime', 'image/jpeg')
        )
    else:
        return send_file('static/images/about-placeholder.jpg')

@main_bp.route('/images/team/<member_index>')
def serve_team_image(member_index):
    """Serve team member image from MongoDB - About Collection"""
    from flask import current_app as app
    db = app.db
    try:
        about = db.get_about()
        member_idx = int(member_index)
        
        if about and 'our_team' in about:
            team = about['our_team']
            if member_idx < len(team) and 'image_data' in team[member_idx] and team[member_idx]['image_data']:
                return Response(
                    team[member_idx]['image_data'],
                    mimetype=team[member_idx].get('image_mime', 'image/jpeg')
                )
        
        return send_file('static/images/team-placeholder.jpg')
    except Exception as e:
        print(f"Error serving team image: {e}")
        return send_file('static/images/team-placeholder.jpg')

# ==================== CATEGORY FILTER ====================
@main_bp.route('/menu/category/<category_name>')
def menu_by_category(category_name):
    """Filter menu by category"""
    from flask import current_app as app
    db = app.db
    settings = db.get_settings()
    categories = db.get_all_categories()

    # Get menu items by category
    menu = list(db.menu.find({'category': category_name}).sort('created_at', -1))
    for item in menu:
        item['_id'] = str(item['_id'])
        if 'image_data' in item and item['image_data']:
            try:
                import base64
                item['image_base64'] = base64.b64encode(item['image_data']).decode('utf-8')
                item['image_mime'] = item.get('image_mime', 'image/jpeg')
                item['image_url'] = f"data:{item['image_mime']};base64,{item['image_base64']}"
            except:
                item['image_url'] = None
        else:
            item['image_url'] = None

    return render_template('menu.html',
                         settings=settings,
                         menu=menu,
                         categories=categories,
                         active_category=category_name)
    
# ==================== AJAX API FOR CATEGORY FILTER ====================
@main_bp.route('/api/menu/filter')
def filter_menu_by_category():
    """API endpoint untuk filter menu by category (AJAX) - Return Base64"""
    from flask import current_app as app, jsonify
    import base64
    
    db = app.db
    
    category = request.args.get('category', 'all')
    
    # Query dari MongoDB berdasarkan kategori
    if category == 'all':
        menu = list(db.menu.find().sort('created_at', -1))
    else:
        menu = list(db.menu.find({'category': category}).sort('created_at', -1))
    
    # ✅ Convert ObjectId + Binary ke Base64 String
    menu_items = []
    for item in menu:
        menu_item = {
            '_id': str(item['_id']),
            'name': item.get('name', ''),
            'description': item.get('description', ''),
            'price': item.get('price', 0),
            'category': item.get('category', ''),
            'available': item.get('available', True),
            'is_recommended': item.get('is_recommended', False),
        }
        
        # ✅ Convert binary image_data ke base64 string (JSON-safe)
        if 'image_data' in item and item['image_data']:
            try:
                menu_item['image_base64'] = base64.b64encode(item['image_data']).decode('utf-8')
                menu_item['image_mime'] = item.get('image_mime', 'image/jpeg')
            except Exception as e:
                print(f"Error encoding image: {e}")
                menu_item['image_base64'] = None
                menu_item['image_mime'] = None
        else:
            menu_item['image_base64'] = None
            menu_item['image_mime'] = None
        
        menu_items.append(menu_item)
    
    return jsonify({
        'success': True,
        'category': category,
        'count': len(menu_items),
        'items': menu_items
    })