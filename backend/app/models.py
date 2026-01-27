from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    original_text = db.Column(db.Text)
    translated_text = db.Column(db.Text)
    source_lang = db.Column(db.String(10))
    target_lang = db.Column(db.String(10))
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='VND')
    status = db.Column(db.String(50), default='pending')
    sepay_transaction_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)