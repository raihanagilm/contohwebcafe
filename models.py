"""
Database Models Module
Model untuk MongoDB collections
"""
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import base64

class CafeDB:
    """Database handler untuk Cafe CMS"""
    
    def __init__(self, uri, database_name):
        """Initialize MongoDB connection"""
        self.client = MongoClient(uri)
        self.db = self.client[database_name]
        
        # Collections
        self.users = self.db['users']
        self.settings = self.db['settings']
        self.menu = self.db['menu']
        self.gallery = self.db['gallery']
        self.promo = self.db['promo']
        self.social = self.db['social']
        self.visitors = self.db['visitors']
        self.categories = self.db['categories']  # COLLECTION BARU UNTUK KATEGORI

    # ========== USER MANAGEMENT ==========
    def create_default_admin(self):
        """Create default admin user if not exists"""
        if self.users.count_documents({}) == 0:
            admin_user = {
                'username': 'admin',
                'password': generate_password_hash('admin123'),
                'email': 'admin@cafeanda.com',
                'role': 'admin',
                'active': True,
                'created_at': datetime.now()
            }
            self.users.insert_one(admin_user)
            print("✓ Default admin created: username='admin', password='admin123'")

    def check_login(self, username, password):
        """Check user credentials"""
        user = self.users.find_one({'username': username, 'active': True})
        if user and check_password_hash(user['password'], password):
            return {
                '_id': str(user['_id']),
                'username': user['username'],
                'email': user.get('email', ''),
                'role': user.get('role', 'admin')
            }
        return None

    def get_all_users(self):
        """Get all users"""
        users = list(self.users.find({}, {'password': 0}))
        for user in users:
            user['_id'] = str(user['_id'])
        return users

    # ========== SETTINGS MANAGEMENT ==========
    def get_settings(self):
        """Get website settings (BASIC SETTINGS ONLY - Logo, Cafe Info, Contact)"""
        settings = self.settings.find_one()
        
        if not settings:
            # Default settings - HANYA BASIC SETTINGS
            settings = {
                'cafe_name': 'Cafe Kita',
                'tagline': 'Tempat Ngopi Paling Nyaman',
                'description': 'Selamat datang di Cafe Kita! Kami adalah cafe yang berdedikasi untuk memberikan pengalaman kopi terbaik dalam suasana yang nyaman dan cozy.',
                'address': 'Jl. Kebon Jeruk Raya No. 123, Jakarta Barat',
                'phone': '021-1234-5678',
                'email': 'info@cafeanda.com',
                'opening_hours': 'Senin - Jumat: 08:00 - 22:00\nSabtu - Minggu: 09:00 - 23:00',
                'whatsapp_number': '6281234567890',
                'google_maps_url': '',
                'google_maps_iframe': '',
                'logo_data': None,
                'logo_filename': None,
                'logo_mime': 'image/png',
                'logo_size': 0,
                'created_at': datetime.now()
            }
            self.settings.insert_one(settings)
        
        settings['_id'] = str(settings['_id'])
        return settings

    def update_settings(self, data):
        """Update website settings (BASIC SETTINGS ONLY)"""
        self.settings.update_one({}, {'$set': data}, upsert=True)

    # ========== ABOUT PAGE MANAGEMENT ==========
    def get_about(self):
        """Get About Page content"""
        # Cek apakah collection about sudah ada
        if 'about' not in self.db.list_collection_names():
            self.db.create_collection('about')
        
        about_data = self.db.about.find_one()
        
        if not about_data:
            # Default about content
            about_data = {
                'about_story': 'Welcome to our cafe! We are dedicated to providing you with the best coffee experience in a cozy and comfortable atmosphere. Our cafe offers a wide selection of premium coffee, delicious food, and a warm environment perfect for relaxing, working, or meeting with friends.',
                'about_image_data': None,
                'about_image_mime': 'image/jpeg',
                'our_team': [
                    {
                        'name': 'John Doe',
                        'position': 'Head Barista',
                        'description': 'Crafting perfect cups with passion and expertise',
                        'image_data': None,
                        'image_mime': 'image/jpeg'
                    },
                    {
                        'name': 'Jane Smith',
                        'position': 'Chef',
                        'description': 'Creating delicious dishes with fresh, local ingredients',
                        'image_data': None,
                        'image_mime': 'image/jpeg'
                    },
                    {
                        'name': 'Mike Johnson',
                        'position': 'Manager',
                        'description': 'Dedicated to providing exceptional service and hospitality',
                        'image_data': None,
                        'image_mime': 'image/jpeg'
                    }
                ],
                'our_values': [
                    {
                        'icon': 'fa-seedling',
                        'title': 'Sustainability',
                        'description': 'We\'re committed to sustainable practices, from ethically sourced coffee beans to eco-friendly packaging.'
                    },
                    {
                        'icon': 'fa-heart',
                        'title': 'Community',
                        'description': 'We believe in building strong community connections and creating a welcoming space for everyone.'
                    },
                    {
                        'icon': 'fa-mug-hot',
                        'title': 'Quality',
                        'description': 'Every cup of coffee and every dish is crafted with the highest quality ingredients and attention to detail.'
                    }
                ],
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            self.db.about.insert_one(about_data)
        
        about_data['_id'] = str(about_data['_id'])
        return about_data

    def update_about(self, data):
        """Update About Page content"""
        self.db.about.update_one({}, {'$set': data}, upsert=True)

    def update_about_story(self, story, image_data=None, image_mime=None):
        """Update only about story"""
        update_data = {'about_story': story, 'updated_at': datetime.now()}
        if image_data is not None:
            update_data['about_image_data'] = image_data
            update_data['about_image_mime'] = image_mime
        self.db.about.update_one({}, {'$set': update_data}, upsert=True)

    def update_our_team(self, team_data):
        """Update only our team"""
        self.db.about.update_one({}, {'$set': {'our_team': team_data, 'updated_at': datetime.now()}}, upsert=True)

    def update_our_values(self, values_data):
        """Update only our values"""
        self.db.about.update_one({}, {'$set': {'our_values': values_data, 'updated_at': datetime.now()}}, upsert=True)

    # ========== MENU MANAGEMENT ==========
    def get_all_menu(self, sort_by='created_at', sort_order='desc'):
        """Get all menu items dengan sorting support"""
        # Validasi field sorting
        valid_sort_fields = ['name', 'price', 'category', 'created_at', 'available']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        # Validasi order
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # Convert ke MongoDB sort direction
        mongo_order = 1 if sort_order == 'asc' else -1
        
        # Query dengan sorting
        menu = list(self.menu.find().sort(sort_by, mongo_order))
        
        for item in menu:
            item['_id'] = str(item['_id'])
            
            # Encode image_data ke base64 jika ada
            if 'image_data' in item and item['image_data']:
                try:
                    import base64
                    item['image_base64'] = base64.b64encode(item['image_data']).decode('utf-8')
                    item['image_mime'] = item.get('image_mime', 'image/jpeg')
                    item['image_url'] = f"data:{item['image_mime']};base64,{item['image_base64']}"
                except Exception as e:
                    print(f"Error encoding image: {e}")
                    item['image_url'] = None
            else:
                item['image_url'] = None
        
        return menu

    def get_categories(self):
        """Get all unique categories"""
        categories = self.menu.distinct('category')
        return [cat for cat in categories if cat]

    def get_category_counts(self):
        """Get count menu per category"""
        pipeline = [
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$project': {'category': '$_id', 'count': 1, '_id': 0}}
        ]
        result = list(self.menu.aggregate(pipeline))
        return {item['category']: item['count'] for item in result if item.get('category')}

    def add_menu_item(self, data):
        """Add new menu item"""
        self.menu.insert_one(data)

    def update_menu_item(self, menu_id, data):
        """Update menu item"""
        from bson import ObjectId
        self.menu.update_one({'_id': ObjectId(menu_id)}, {'$set': data})

    def delete_menu_item(self, menu_id):
        """Delete menu item"""
        from bson import ObjectId
        self.menu.delete_one({'_id': ObjectId(menu_id)})

    # ========== GALLERY MANAGEMENT ==========
    def get_all_gallery(self):
        """Get all gallery images dengan base64 encoding"""
        import base64
        
        gallery = list(self.gallery.find().sort('created_at', -1))
        
        for item in gallery:
            item['_id'] = str(item['_id'])
            
            if 'image_data' in item and item['image_data']:
                try:
                    item['image_base64'] = base64.b64encode(item['image_data']).decode('utf-8')
                    item['image_mime'] = item.get('image_mime', 'image/jpeg')
                    item['image_url'] = f"data:{item['image_mime']};base64,{item['image_base64']}"
                except Exception as e:
                    print(f"Error encoding gallery image: {e}")
                    item['image_url'] = None
                    item['image_base64'] = None
            else:
                item['image_url'] = None
                item['image_base64'] = None
        
        return gallery

    def get_gallery_image(self, image_id):
        """Get single gallery image by ID"""
        from bson import ObjectId
        try:
            item = self.gallery.find_one({'_id': ObjectId(image_id)})
            if item:
                item['_id'] = str(item['_id'])
            return item
        except Exception:
            return None

    def add_gallery_image(self, data):
        """Add gallery image"""
        self.gallery.insert_one(data)

    def update_gallery_image(self, image_id, data):
        """Update gallery image - termasuk gambar, caption, dan visibility"""
        from bson import ObjectId
        try:
            result = self.gallery.update_one(
                {'_id': ObjectId(image_id)}, 
                {'$set': data}
            )
            return result.modified_count
        except Exception as e:
            print(f"Error updating gallery: {str(e)}")
            return 0

    def delete_gallery_image(self, image_id):
        """Delete gallery image - HAPUS SEMUA DATA DARI MONGODB"""
        from bson import ObjectId
        try:
            result = self.gallery.delete_one({'_id': ObjectId(image_id)})
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting gallery: {str(e)}")
            return 0

    # ========== CATEGORY MANAGEMENT ==========
    def get_all_categories(self):
        """Get all categories (termasuk yang tidak digunakan)"""
        # Cek apakah ada collection kategori terpisah
        if 'categories' not in self.db.list_collection_names():
            # Buat collection kategori jika belum ada
            self.db.create_collection('categories')
        
        # Ambil semua kategori dari collection terpisah
        categories = list(self.db.categories.find().sort('name', 1))
        
        # Jika kosong, ambil dari menu yang ada
        if not categories:
            distinct_categories = self.menu.distinct('category')
            for cat in distinct_categories:
                self.db.categories.insert_one({
                    'name': cat,
                    'created_at': datetime.now()
                })
            categories = list(self.db.categories.find().sort('name', 1))
        
        # Return list of category names (bukan list of dicts)
        return [cat['name'] for cat in categories]

    def add_category(self, category_name):
        """Add new category"""
        category_name = category_name.lower().strip()
        
        # Cek apakah sudah ada
        existing = self.db.categories.find_one({'name': category_name})
        if existing:
            return False
        
        self.db.categories.insert_one({
            'name': category_name,
            'created_at': datetime.now()
        })
        return True

    def delete_category(self, category_name):
        """Delete category if not used by any menu"""
        # Cek apakah masih digunakan oleh menu
        menu_count = self.menu.count_documents({'category': category_name})
        
        if menu_count > 0:
            return False  # Tidak bisa dihapus karena masih digunakan
        
        self.db.categories.delete_one({'name': category_name})
        return True

    def get_category_counts(self):
        """Get count menu per category - RETURN DICTIONARY"""
        pipeline = [
            {'$group': {
                '_id': '$category', 
                'count': {'$sum': 1},
                'available_count': {'$sum': {'$cond': [{'$eq': ['$available', True]}, 1, 0]}}
            }},
            {'$sort': {'count': -1}}
        ]
        result = list(self.menu.aggregate(pipeline))
        
        # Convert ke dictionary: {'category_name': count, ...}
        counts = {}
        for item in result:
            category = item['_id'] or 'uncategorized'
            counts[category] = {
                'total': item['count'],
                'available': item['available_count'],
                'unavailable': item['count'] - item['available_count']
            }
        
        return counts

    # ========== PROMO MANAGEMENT ==========
    def get_all_promo(self):
        """Get all promo items dengan base64 encoding untuk image"""
        promo = list(self.promo.find().sort('created_at', -1))
        
        for item in promo:
            item['_id'] = str(item['_id'])
            
            # Encode image_data ke base64 jika ada
            if 'image_data' in item and item['image_data']:
                try:
                    item['image_base64'] = base64.b64encode(item['image_data']).decode('utf-8')
                    item['image_mime'] = item.get('image_mime', 'image/jpeg')
                    item['image_url'] = f"data:{item['image_mime']};base64,{item['image_base64']}"
                except Exception as e:
                    print(f"Error encoding promo image: {e}")
                    item['image_url'] = None
            else:
                item['image_url'] = None
        
        return promo

    def add_promo(self, data):
        """Add new promo"""
        self.promo.insert_one(data)

    def update_promo(self, promo_id, data):
        """Update promo item"""
        from bson import ObjectId
        self.promo.update_one({'_id': ObjectId(promo_id)}, {'$set': data})

    def delete_promo(self, promo_id):
        """Delete promo"""
        from bson import ObjectId
        self.promo.delete_one({'_id': ObjectId(promo_id)})

    # ========== SOCIAL MEDIA MANAGEMENT ==========
    def get_social_links(self):
        """Get all social media links"""
        social = list(self.social.find().sort('created_at', -1))
        for link in social:
            link['_id'] = str(link['_id'])
        return social

    def add_social_link(self, data):
        """Add social media link"""
        self.social.insert_one(data)

    def update_social_link(self, link_id, data):
        """Update social media link"""
        from bson import ObjectId
        self.social.update_one({'_id': ObjectId(link_id)}, {'$set': data})

    def delete_social_link(self, link_id):
        """Delete social media link"""
        from bson import ObjectId
        self.social.delete_one({'_id': ObjectId(link_id)})

    # ========== VISITOR TRACKING ==========
    def log_visitor(self, ip_address):
        """Log visitor IP"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.visitors.update_one(
            {'date': today},
            {
                '$inc': {'count': 1},
                '$addToSet': {'ips': ip_address}
            },
            upsert=True
        )

    def get_visitor_stats(self, days=30):
        """Get visitor statistics"""
        pipeline = [
            {'$sort': {'date': -1}},
            {'$limit': days},
            {'$project': {
                'date': 1,
                'count': 1,
                'unique_visitors': {'$size': '$ips'}
            }}
        ]
        return list(self.visitors.aggregate(pipeline))