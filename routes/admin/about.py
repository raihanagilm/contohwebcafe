"""
About Page Management Routes
Mengelola konten halaman About (Story, Team, Values)
DATA DISIMPAN DI COLLECTION 'about' YANG TERPISAH
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from .helpers import admin_required, compress_image_to_bytes

about_bp = Blueprint('about', __name__, url_prefix='/admin')

@about_bp.route('/about', methods=['GET', 'POST'])
@admin_required
def about_settings():
    """
    Halaman pengaturan About Page dengan 3 tab terpisah
    URL: /admin/about
    """
    from flask import current_app as app
    db = app.db
    
    if request.method == 'POST':
        # ========== HANDLE DELETE TEAM MEMBER ==========
        if 'delete_team_index' in request.form:
            index = int(request.form.get('delete_team_index'))
            about_data = db.get_about()
            our_team = about_data.get('our_team', [])
            
            if 0 <= index < len(our_team):
                deleted_name = our_team[index].get('name', 'Team Member')
                our_team.pop(index)
                db.update_our_team(our_team)
                flash(f'Team member "{deleted_name}" berhasil dihapus!', 'success')
            return redirect(url_for('about.about_settings') + '#team')

        # ========== HANDLE DELETE VALUE ==========
        if 'delete_value_index' in request.form:
            index = int(request.form.get('delete_value_index'))
            about_data = db.get_about()
            our_values = about_data.get('our_values', [])
            
            if 0 <= index < len(our_values):
                deleted_title = our_values[index].get('title', 'Value')
                our_values.pop(index)
                db.update_our_values(our_values)
                flash(f'Value "{deleted_title}" berhasil dihapus!', 'success')
            return redirect(url_for('about.about_settings') + '#values')

        # ========== HANDLE SAVE STORY ==========
        if 'about_story' in request.form:
            about_image_bytes = None
            about_image_mime = None
            
            if 'about_image' in request.files:
                file = request.files['about_image']
                if file and file.filename != '':
                    about_image_bytes = compress_image_to_bytes(file, app)
                    if about_image_bytes:
                        about_image_mime = file.content_type or 'image/jpeg'
            
            about_story = request.form.get('about_story', '').strip()
            db.update_about_story(about_story, about_image_bytes, about_image_mime)
            
            flash('About Story berhasil disimpan!', 'success')
            return redirect(url_for('about.about_settings') + '#story')

        # ========== HANDLE SAVE/UPDATE TEAM MEMBER ==========
        if 'team_name' in request.form:
            team_index = request.form.get('team_index', '').strip()
            name = request.form.get('team_name', '').strip()
            position = request.form.get('team_position', '').strip()
            description = request.form.get('team_description', '').strip()
            
            member = {
                'name': name,
                'position': position,
                'description': description
            }
            
            # Handle image upload
            if 'team_image' in request.files:
                file = request.files['team_image']
                if file and file.filename != '':
                    img_bytes = compress_image_to_bytes(file, app)
                    if img_bytes:
                        member['image_data'] = img_bytes
                        member['image_mime'] = file.content_type or 'image/jpeg'
            
            about_data = db.get_about()
            our_team = about_data.get('our_team', [])
            
            if team_index and team_index.isdigit():  # Update existing
                index = int(team_index)
                if 0 <= index < len(our_team):
                    our_team[index] = member
                    flash('Team member berhasil diupdate!', 'success')
            else:  # Add new
                our_team.append(member)
                flash('Team member berhasil ditambahkan!', 'success')
            
            db.update_our_team(our_team)
            return redirect(url_for('about.about_settings') + '#team')

        # ========== HANDLE SAVE/UPDATE VALUE ==========
        if 'value_title' in request.form:
            value_index = request.form.get('value_index', '').strip()
            icon = request.form.get('value_icon', '').strip()
            title = request.form.get('value_title', '').strip()
            description = request.form.get('value_description', '').strip()
            
            value = {
                'icon': icon,
                'title': title,
                'description': description
            }
            
            about_data = db.get_about()
            our_values = about_data.get('our_values', [])
            
            if value_index and value_index.isdigit():  # Update existing
                index = int(value_index)
                if 0 <= index < len(our_values):
                    our_values[index] = value
                    flash('Value berhasil diupdate!', 'success')
            else:  # Add new
                our_values.append(value)
                flash('Value berhasil ditambahkan!', 'success')
            
            db.update_our_values(our_values)
            return redirect(url_for('about.about_settings') + '#values')

    # GET request
    settings = db.get_about()
    
    # BUAT DUA VERSI DATA:
    # 1. settings_for_display - untuk ditampilkan di template (dengan image_data)
    # 2. settings_for_json - untuk di-pass ke JavaScript (tanpa image_data)
    settings_for_display = settings.copy()
    
    # Hanya hapus image_data untuk JSON serialization (untuk tombol edit)
    settings_for_json = {}
    for key, value in settings.items():
        if key == 'our_team' and value:
            settings_for_json[key] = []
            for member in value:
                member_copy = member.copy()
                if 'image_data' in member_copy:
                    del member_copy['image_data']
                settings_for_json[key].append(member_copy)
        elif key == 'about_image_data':
            # Skip field ini untuk JSON
            continue
        elif key == 'our_values':
            settings_for_json[key] = value
        else:
            settings_for_json[key] = value
    
    return render_template('admin/about.html', settings=settings_for_display, settings_json=settings_for_json)