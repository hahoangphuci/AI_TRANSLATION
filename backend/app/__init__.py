from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from .models import db
from .utils.jwt_handler import init_jwt
from .routes.auth import auth_bp
from .routes.translation import translation_bp
from .routes.payment import payment_bp
from .routes.history import history_bp

def create_app(config_class='config.DevelopmentConfig'):
    app = Flask(__name__)
    
    # Load config
    if isinstance(config_class, str):
        app.config.from_object(config_class)
    else:
        app.config.update(config_class)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    init_jwt(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(translation_bp, url_prefix='/api/translation')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    
    return app