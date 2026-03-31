"""
Helper Functions untuk Admin Routes
Berisi fungsi-fungsi utility yang digunakan di berbagai admin routes
"""
from flask import session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import io
from PIL import Image

def admin_required(f):
    """Decorator untuk memeriksa apakah admin sudah login"""
    def wrap(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Silakan login terlebih dahulu!', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def allowed_file(filename, app):
    """Cek apakah file extension diizinkan"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def compress_image_to_bytes(image_file, app, max_width=None, max_height=None, quality=None):
    """
    Kompres gambar dan return sebagai bytes (untuk disimpan ke MongoDB)
    Returns: bytes atau None jika gagal
    """
    try:
        if max_width is None:
            max_width = app.config['IMAGE_MAX_WIDTH']
        if max_height is None:
            max_height = app.config['IMAGE_MAX_HEIGHT']
        if quality is None:
            quality = app.config['IMAGE_QUALITY']

        # Buka gambar
        img = Image.open(image_file)
        
        # Konversi ke RGB jika RGBA
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize gambar jika terlalu besar
        img_width, img_height = img.size
        if img_width > max_width or img_height > max_height:
            ratio = min(max_width / img_width, max_height / img_height)
            new_size = (int(img_width * ratio), int(img_height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Kompres ke bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=app.config['IMAGE_FORMAT'], quality=quality, optimize=True)
        img_byte_arr.seek(0)
        
        return img_byte_arr.read()  # Return bytes

    except Exception as e:
        print(f"Error compressing image: {str(e)}")
        return None