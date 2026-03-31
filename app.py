"""
Cafe CMS - Main Application (Flask + Streamlit FIXED)
"""

from flask import Flask, render_template
from config import Config
from models import CafeDB
from datetime import datetime
from routes import (
    main_bp,
    auth_bp,
    about_bp,
    dashboard_bp,
    settings_bp,
    menu_bp,
    gallery_bp,
    promo_bp,
    social_bp
)

import base64
import threading
import time
import socket
import streamlit as st


# ================= FLASK =================
def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)
    Config.init_app(app)

    db = CafeDB(app.config['MONGODB_URI'], app.config['MONGODB_DATABASE'])
    db.create_default_admin()
    app.db = db

    # ================= FILTER =================
    @app.template_filter('b64encode')
    def base64_encode_filter(data):
        if data is None:
            return ''
        if isinstance(data, str):
            return base64.b64encode(data.encode()).decode()
        return base64.b64encode(data).decode()

    @app.template_filter('datetimeformat')
    def datetimeformat_filter(value, format='%d %B %Y'):
        if not value:
            return '-'
        if hasattr(value, 'strftime'):
            return value.strftime(format)
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').strftime(format)
            except:
                return value
        return str(value)

    @app.context_processor
    def inject_globals():
        return dict(
            settings=db.get_settings(),
            social=db.get_social_links()
        )

    @app.context_processor
    def inject_now():
        return {'now': datetime.now}

    # ================= VISITOR =================
    @app.before_request
    def log_visitor():
        from flask import request
        if request.path.startswith('/static/') or request.path.startswith('/admin'):
            return
        db.log_visitor(request.remote_addr)

    # ================= ERROR =================
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    # ================= ROUTES =================
    app.register_blueprint(auth_bp, url_prefix='/admin')
    app.register_blueprint(about_bp, url_prefix='/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/admin')
    app.register_blueprint(settings_bp, url_prefix='/admin')
    app.register_blueprint(menu_bp, url_prefix='/admin')
    app.register_blueprint(gallery_bp, url_prefix='/admin')
    app.register_blueprint(promo_bp, url_prefix='/admin')
    app.register_blueprint(social_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)

    return app


# ================= AUTO PORT =================
def get_free_port(start=5000):
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
        port += 1


# ================= RUN FLASK =================
def run_flask(port):
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# ================= STREAMLIT =================
def run_streamlit():
    st.set_page_config(layout="wide")

    # Start Flask sekali saja
    if "flask_started" not in st.session_state:
        port = get_free_port()
        st.session_state.flask_port = port

        thread = threading.Thread(target=run_flask, args=(port,))
        thread.daemon = True
        thread.start()

        st.session_state.flask_started = True
        time.sleep(2)

    # Navigation (fix warning)
    mode = st.radio(
        "Navigation",
        ["Customer", "Admin"],
        horizontal=True,
        label_visibility="collapsed"
    )

    base_url = f"http://localhost:{st.session_state.flask_port}"

    if mode == "Customer":
        st.components.v1.iframe(
            f"{base_url}/",
            height=1000,
            scrolling=True
        )
    else:
        # 🔥 ADMIN TANPA IFRAME (BIAR LOGIN BERHASIL)
        st.markdown(
            f'<meta http-equiv="refresh" content="0; url={base_url}/admin">',
            unsafe_allow_html=True
        )


# ================= ENTRY =================
if __name__ == "__main__":
    try:
        if st.runtime.exists():
            run_streamlit()
        else:
            app = create_app()
            app.run(host='0.0.0.0', port=5000, debug=True)
    except:
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True)
