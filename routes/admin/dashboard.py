"""
Dashboard Route
Menampilkan statistik dan informasi overview
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, session, current_app
from datetime import datetime, timedelta
from bson import ObjectId, Binary
from functools import wraps
import json
import base64
import re

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/admin')

# ==================== HELPER FUNCTIONS ====================
def admin_required(f):
    """Decorator untuk memeriksa apakah admin sudah login"""
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Silakan login terlebih dahulu!', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def serialize_object(obj):
    """Serialize MongoDB document untuk JSON export"""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Binary):
        return {'__binary__': True, 'data': base64.b64encode(obj).decode('utf-8')}
    if isinstance(obj, bytes):
        return {'__binary__': True, 'data': base64.b64encode(obj).decode('utf-8')}
    if isinstance(obj, dict):
        return {k: serialize_object(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_object(item) for item in obj]
    return obj

def parse_datetime_string(value):
    """
    Parse string ke datetime object jika formatnya ISO datetime
    Handle berbagai format datetime string
    """
    if not isinstance(value, str):
        return value
    
    # Cek apakah string ini adalah ISO datetime format
    # Format: 2026-02-22T16:12:52.029+00:00 atau 2026-02-22T16:12:52.029Z
    iso_patterns = [
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}$',  # Dengan timezone
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$',  # Dengan Z
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}$',  # Tanpa timezone
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',  # Tanpa milisecond
        r'^\d{4}-\d{2}-\d{2}$',  # Tanggal saja
    ]
    
    for pattern in iso_patterns:
        if re.match(pattern, value):
            try:
                # Handle timezone
                if value.endswith('Z'):
                    value = value[:-1] + '+00:00'
                
                # Parse dengan timezone
                if '+' in value or (value.count('-') > 2):
                    # Ada timezone info
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.replace(tzinfo=None)  # Convert ke naive datetime
                else:
                    # Tanpa timezone
                    if 'T' in value:
                        if '.' in value:
                            return datetime.strptime(value[:23], '%Y-%m-%dT%H:%M:%S.%f')
                        else:
                            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                    else:
                        return datetime.strptime(value, '%Y-%m-%d')
            except Exception as e:
                print(f"Error parsing datetime '{value}': {str(e)}")
                return value
    
    return value

def deserialize_object(obj):
    """
    Deserialize JSON import kembali ke format MongoDB
    Handle: binary data, datetime strings, ObjectId strings
    """
    if isinstance(obj, dict):
        # Handle binary data
        if obj.get('__binary__'):
            return Binary(base64.b64decode(obj['data']))
        
        # Handle MongoDB ObjectId format
        if obj.get('$oid'):
            return ObjectId(obj['$oid'])
        
        # Handle MongoDB date format
        if obj.get('$date'):
            date_str = obj['$date']
            if isinstance(date_str, dict) and date_str.get('$numberLong'):
                # MongoDB extended JSON format
                from bson.timestamp import Timestamp
                return datetime.fromtimestamp(int(date_str['$numberLong']) / 1000)
            else:
                return parse_datetime_string(date_str)
        
        # Recursively deserialize dict values
        return {k: deserialize_object(v) for k, v in obj.items()}
    
    if isinstance(obj, list):
        return [deserialize_object(item) for item in obj]
    
    if isinstance(obj, str):
        # Try to parse datetime strings
        return parse_datetime_string(obj)
    
    return obj

def get_collection_key_fields(collection_name):
    """Return field kunci untuk cek duplikat per collection"""
    key_fields = {
        'menu': ['name', 'category', 'price'],
        'gallery': ['filename', 'caption'],
        'promo': ['title', 'valid_until'],
        'social': ['platform', 'url'],
        'categories': ['name'],
        'settings': ['cafe_name', 'phone', 'email'],
        'about': ['about_story'],
        'users': ['username', 'email']
    }
    return key_fields.get(collection_name, ['_id'])

def check_duplicate(db, collection_name, new_doc, existing_docs):
    """
    Cek apakah dokumen baru duplikat dengan yang sudah ada
    Return: True jika duplikat, False jika unik
    """
    key_fields = get_collection_key_fields(collection_name)
    
    for existing in existing_docs:
        match_count = 0
        for field in key_fields:
            if field in new_doc and field in existing:
                if str(new_doc[field]) == str(existing[field]):
                    match_count += 1
        
        if match_count == len(key_fields):
            return True
    
    return False

def merge_settings_data(existing, new_data):
    """
    Merge data untuk settings & about
    Update hanya field yang kosong di existing
    """
    merged = existing.copy()
    for key, value in new_data.items():
        if key not in existing or existing[key] is None or existing[key] == '' or existing[key] == []:
            merged[key] = value
    return merged

# ==================== DASHBOARD ROUTE ====================
@dashboard_bp.route('/dashboard')
@admin_required
def dashboard():
    """Halaman dashboard admin"""
    db = current_app.db

    # ========== VISITOR STATISTICS (7 days) ==========
    stats_raw = db.get_visitor_stats(7)
    stats = []
    total_visitors = 0

    for day in stats_raw:
        date_value = day.get('date', '')
        if hasattr(date_value, 'strftime'):
            date_str = date_value.strftime('%Y-%m-%d')
        else:
            date_str = str(date_value)
        
        day_data = {
            'date': date_str,
            'count': int(day.get('count', 0)),
            'unique_visitors': int(day.get('unique_visitors', 0))
        }
        stats.append(day_data)
        total_visitors += day_data['count']

    stats_chart = stats[::-1]

    # ========== PROMO EXPIRING SOON & EXPIRED ==========
    promo_expiring = []
    promo_expired = []
    today = datetime.now()

    for promo in db.promo.find({'valid_until': {'$ne': '', '$exists': True}}):
        valid_until = promo.get('valid_until')
        valid_date = parse_datetime_string(valid_until) if isinstance(valid_until, str) else valid_until
        
        if valid_date is None:
            continue
        
        if hasattr(valid_date, 'strftime'):
            days_left = (valid_date.replace(tzinfo=None) - today).days
        else:
            continue
        
        if days_left < 0:
            promo_expired.append({
                '_id': str(promo['_id']),
                'title': promo.get('title', 'Promo'),
                'valid_until': valid_until,
                'days_expired': abs(days_left)
            })
        elif 0 <= days_left <= 3:
            promo_expiring.append({
                '_id': str(promo['_id']),
                'title': promo.get('title', 'Promo'),
                'valid_until': valid_until,
                'days_left': days_left
            })

    # ========== STORAGE USAGE ==========
    storage_info = {
        'menu': 0, 'gallery': 0, 'promo': 0, 'settings': 0,
        'social': 0, 'visitors': 0, 'categories': 0, 'users': 0,
        'about': 0, 'total': 0, 'total_mb': 0, 'limit_mb': 512, 'percentage': 0
    }

    collections_to_check = [
        ('menu', 'menu'), ('gallery', 'gallery'), ('promo', 'promo'),
        ('settings', 'settings'), ('social', 'social'), ('visitors', 'visitors'),
        ('categories', 'categories'), ('users', 'users'), ('about', 'about')
    ]

    for attr_name, collection_name in collections_to_check:
        if collection_name not in db.db.list_collection_names():
            continue
        
        collection = db.db[collection_name]
        total_size = 0
        
        for doc in collection.find({}):
            for key, value in doc.items():
                if isinstance(value, (bytes, Binary)):
                    total_size += len(value)
                elif isinstance(value, str):
                    total_size += len(value.encode('utf-8'))
                elif isinstance(value, (dict, list)):
                    total_size += len(str(value).encode('utf-8'))
        
        storage_info[attr_name] = total_size
        storage_info['total'] += total_size

    storage_info['total_mb'] = round(storage_info['total'] / (1024 * 1024), 2)
    storage_info['percentage'] = round(
        (storage_info['total'] / (storage_info['limit_mb'] * 1024 * 1024)) * 100, 1
    )

    # ========== RECENT ITEMS ==========
    recent_menu = list(db.menu.find().sort('created_at', -1).limit(5))
    for item in recent_menu:
        item['_id'] = str(item['_id'])

    recent_promo = list(db.promo.find().sort('created_at', -1).limit(5))
    for promo in recent_promo:
        promo['_id'] = str(promo['_id'])

    menu_count = db.menu.count_documents({})
    gallery_count = db.gallery.count_documents({})
    promo_count = db.promo.count_documents({})

    return render_template('admin/dashboard.html',
                         recent_menu=recent_menu,
                         recent_promo=recent_promo,
                         total_visitors=total_visitors,
                         stats=stats,
                         stats_chart=stats_chart,
                         promo_expiring=promo_expiring,
                         promo_expired=promo_expired,
                         storage_info=storage_info,
                         menu_count=menu_count,
                         gallery_count=gallery_count,
                         promo_count=promo_count)

# ==================== EXPORT DATABASE ====================
@dashboard_bp.route('/export', methods=['GET', 'POST'])
@admin_required
def export_database():
    """Export data database ke file JSON dengan pilihan collection"""
    db = current_app.db
    
    if request.method == 'POST':
        collections_to_export = request.form.getlist('collections')
        
        if not collections_to_export:
            collections_to_export = ['settings', 'menu', 'gallery', 'promo', 'social', 'categories', 'about']
    else:
        available_collections = []
        db_collections = db.db.list_collection_names()
        
        for coll in ['settings', 'menu', 'gallery', 'promo', 'social', 'categories', 'about', 'users']:
            if coll in db_collections:
                count = db.db[coll].count_documents({})
                available_collections.append({
                    'name': coll,
                    'count': count,
                    'disabled': coll == 'users'
                })
        
        return render_template('admin/dashboard.html', 
                             available_collections=available_collections,
                             show_export_modal=True)
    
    export_data = {
        'export_date': datetime.now().isoformat(),
        'version': '2.0',
        'collections': {}
    }
    
    for collection_name in collections_to_export:
        if collection_name == 'users':
            continue
            
        if collection_name not in db.db.list_collection_names():
            continue
        
        collection = db.db[collection_name]
        documents = []
        
        for doc in collection.find({}):
            if 'password' in doc:
                doc['password'] = '[REDACTED]'
            documents.append(serialize_object(doc))
        
        export_data['collections'][collection_name] = {
            'count': len(documents),
            'data': documents
        }
    
    json_data = json.dumps(export_data, indent=2, default=str)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'cafe_cms_backup_{timestamp}.json'
    
    return Response(
        json_data,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Length': len(json_data)
        }
    )

# ==================== IMPORT DATABASE ====================
@dashboard_bp.route('/import', methods=['GET', 'POST'])
@admin_required
def import_database():
    """Import data dari file JSON dengan logika pintar"""
    db = current_app.db
    
    if request.method == 'POST':
        if 'import_file' not in request.files:
            flash('Tidak ada file yang diupload!', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        file = request.files['import_file']
        
        if file.filename == '':
            flash('Silakan pilih file untuk diimport!', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        if not file.filename.endswith('.json'):
            flash('File harus berformat JSON!', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        try:
            import_data = json.load(file)
            
            if 'collections' not in import_data:
                flash('Format file tidak valid! File backup harus memiliki field "collections".', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            import_mode = request.form.get('import_mode', 'smart')
            collections_to_import = request.form.getlist('collections')
            
            if not collections_to_import:
                collections_to_import = list(import_data['collections'].keys())
            
            import_stats = {
                'success': 0,
                'skipped': 0,
                'failed': 0,
                'updated': 0,
                'collections': {}
            }
            
            for collection_name in collections_to_import:
                if collection_name not in import_data['collections']:
                    continue
                
                if collection_name == 'users':
                    import_stats['skipped'] += 1
                    continue
                
                collection_data = import_data['collections'][collection_name]
                new_documents = collection_data.get('data', [])
                
                if collection_name not in db.db.list_collection_names():
                    db.db.create_collection(collection_name)
                
                collection = db.db[collection_name]
                collection_stats = {'imported': 0, 'skipped': 0, 'updated': 0, 'failed': 0}
                
                existing_docs = list(collection.find({}))
                
                for new_doc in new_documents:
                    try:
                        # Deserialize data (binary, datetime, dll)
                        new_doc = deserialize_object(new_doc)
                        
                        if new_doc.get('password') == '[REDACTED]':
                            collection_stats['skipped'] += 1
                            continue
                        
                        # Handle khusus untuk settings & about (merge update)
                        if collection_name in ['settings', 'about']:
                            if existing_docs:
                                existing = existing_docs[0]
                                merged_doc = merge_settings_data(existing, new_doc)
                                
                                if '_id' in merged_doc:
                                    del merged_doc['_id']
                                
                                collection.update_one({}, {'$set': merged_doc})
                                collection_stats['updated'] += 1
                                import_stats['success'] += 1
                            else:
                                if '_id' in new_doc:
                                    del new_doc['_id']
                                collection.insert_one(new_doc)
                                collection_stats['imported'] += 1
                                import_stats['success'] += 1
                            continue
                        
                        # Handle collection lainnya (cek duplikat)
                        if import_mode == 'smart':
                            is_duplicate = check_duplicate(db, collection_name, new_doc, existing_docs)
                            
                            if is_duplicate:
                                collection_stats['skipped'] += 1
                                import_stats['skipped'] += 1
                                continue
                        
                        # Insert data baru
                        if '_id' in new_doc:
                            del new_doc['_id']
                        
                        collection.insert_one(new_doc)
                        collection_stats['imported'] += 1
                        import_stats['success'] += 1
                        
                        existing_docs = list(collection.find({}))
                        
                    except Exception as e:
                        print(f"Error importing document to {collection_name}: {str(e)}")
                        collection_stats['failed'] += 1
                        import_stats['failed'] += 1
                
                import_stats['collections'][collection_name] = collection_stats
            
            flash_msg = f"✅ Import selesai! {import_stats['success']} data berhasil."
            if import_stats['skipped'] > 0:
                flash_msg += f" ⚠️ {import_stats['skipped']} data di-skip (duplikat)."
            if import_stats['failed'] > 0:
                flash_msg += f" ❌ {import_stats['failed']} data gagal."
            if import_stats['updated'] > 0:
                flash_msg += f" 🔄 {import_stats['updated']} data di-update (settings/about)."
            
            flash(flash_msg, 'success')
            
        except json.JSONDecodeError:
            flash('File JSON tidak valid!', 'danger')
        except Exception as e:
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('admin/dashboard.html')

# ==================== VISITOR MANAGEMENT ====================
@dashboard_bp.route('/visitors/clear', methods=['POST'])
@admin_required
def clear_visitors():
    """Hapus semua data visitor"""
    db = current_app.db
    result = db.visitors.delete_many({})
    flash(f'Berhasil menghapus {result.deleted_count} data visitor!', 'success')
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/visitors/clear/<int:days>', methods=['POST'])
@admin_required
def clear_visitors_old(days):
    """Hapus data visitor lebih dari N hari"""
    db = current_app.db
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    result = db.visitors.delete_many({'date': {'$lt': cutoff_date}})
    flash(f'Berhasil menghapus {result.deleted_count} data visitor lama!', 'success')
    return redirect(url_for('dashboard.dashboard'))