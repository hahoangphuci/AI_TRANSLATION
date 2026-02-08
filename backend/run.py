import os
from dotenv import load_dotenv

# Load .env từ thư mục backend (nơi có run.py) – bắt buộc trước khi import config hoặc TranslationService
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
# override=True so changes in backend/.env take effect even if the variable already exists in OS env
load_dotenv(_env_path, override=True)

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from app.routes.auth import auth_bp
from app.routes.translation import translation_bp
from app.routes.payment import payment_bp
from app.routes.history import history_bp
from app.routes.ai import ai_bp

# Đường dẫn tới thư mục frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
PAGES_DIR = os.path.join(FRONTEND_DIR, 'pages')
STATIC_DIR = FRONTEND_DIR

app = Flask(__name__, static_folder=os.path.join(FRONTEND_DIR, ''))
CORS(app)

# Dev: avoid stale browser cache for JS/CSS during frequent edits
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configure session for OAuth flow
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Load config
app.config.from_object('config.DevelopmentConfig')

# Initialize extensions
from app.models import db
from app.utils.jwt_handler import init_jwt
db.init_app(app)
init_jwt(app)

# Create database tables
with app.app_context():
    db.create_all()

    # Schema migration for MySQL compatibility
    try:
        if db.engine.dialect.name == 'mysql':
            from sqlalchemy import text
            with db.engine.begin() as conn:
                # Check if avatar_url column exists in user table
                result = conn.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='user' AND COLUMN_NAME='avatar_url'"))
                if not result.fetchone():
                    conn.execute(text('ALTER TABLE user ADD COLUMN avatar_url VARCHAR(500)'))
    except Exception as e:
        print(f"[WARN] Schema check/migration failed: {e}")


# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(translation_bp, url_prefix='/api/translation')
app.register_blueprint(payment_bp, url_prefix='/api/payment')
app.register_blueprint(history_bp, url_prefix='/api/history')
# AI/config endpoints
app.register_blueprint(ai_bp, url_prefix='/api/ai')

# Route cho trang chủ trả về home.html
@app.route('/')
def home():
    return send_from_directory(PAGES_DIR, 'home.html')

# Route cho trang đăng ký/đăng nhập
@app.route('/auth')
def auth_page():
    return send_from_directory(PAGES_DIR, 'auth.html')

# Route cho trang dashboard
@app.route('/dashboard')
def dashboard_page():
    return send_from_directory(PAGES_DIR, 'dashboard.html')

# Route cho trang about
@app.route('/about')
def about_page():
    return send_from_directory(PAGES_DIR, 'about.html')

# Route cho trang contact
@app.route('/contact')
def contact_page():
    return send_from_directory(PAGES_DIR, 'contact.html')

# Route cho trang profile
@app.route('/profile')
def profile_page():
    return send_from_directory(PAGES_DIR, 'profile.html')

# Route cho trang history
@app.route('/history')
def history_page():
    return send_from_directory(PAGES_DIR, 'history.html')

# Route phục vụ các file tĩnh (css, js, images)
@app.route('/css/<path:filename>')
def serve_css(filename):
    resp = send_from_directory(os.path.join(FRONTEND_DIR, 'css'), filename)
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/js/<path:filename>')
def serve_js(filename):
    resp = send_from_directory(os.path.join(FRONTEND_DIR, 'js'), filename)
    resp.headers['Cache-Control'] = 'no-store'
    return resp

# Route phục vụ trực tiếp các file HTML (để tương thích với links trong HTML)
@app.route('/<filename>.html')
def serve_html(filename):
    if filename in ['home', 'auth', 'dashboard', 'about', 'contact', 'profile', 'history']:
        return send_from_directory(PAGES_DIR, f'{filename}.html')
    return jsonify({"error": "Page not found"}), 404

# Route phục vụ file đã dịch từ thư mục backend/downloads (serve as attachment to avoid opening inline)
@app.route('/downloads/<path:filename>')
def serve_downloads(filename):
    downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
    # Guess mimetype to send correct Content-Type
    import mimetypes
    mimetype, _ = mimetypes.guess_type(filename)
    return send_from_directory(downloads_dir, filename, as_attachment=True, mimetype=mimetype)

# API cho leaderboard (placeholder)
@app.route('/api/games/leaderboard')
def game_leaderboard():
    leaderboard = [
        {"rank": 1, "username": "Player1", "score": 1000},
        {"rank": 2, "username": "Player2", "score": 950},
        {"rank": 3, "username": "Player3", "score": 900}
    ]
    return jsonify(leaderboard)

if __name__ == '__main__':
    # Chỉ in thông tin Trang chủ để không gây lộn xộn khi khởi động
    print("🏠 Trang chủ: http://127.0.0.1:5000")

    app.run(host='0.0.0.0', port=5000, debug=True)