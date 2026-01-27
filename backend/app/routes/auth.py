from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import db, User
import google.auth.transport.requests
import google.oauth2.id_token
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/google', methods=['POST'])
def google_auth():
    token = request.json.get('token')
    try:
        idinfo = google.oauth2.id_token.verify_oauth2_token(
            token, 
            google.auth.transport.requests.Request(), 
            os.getenv('GOOGLE_CLIENT_ID')
        )
        user_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']
        
        user = User.query.filter_by(google_id=user_id).first()
        if not user:
            user = User(google_id=user_id, email=email, name=name)
            db.session.add(user)
            db.session.commit()
        
        access_token = create_access_token(identity=user_id)
        return jsonify(access_token=access_token), 200
    except ValueError:
        return jsonify({"error": "Invalid token"}), 400

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.filter_by(google_id=user_id).first()
    if user:
        return jsonify({
            'id': user.id,
            'email': user.email,
            'name': user.name
        }), 200
    return jsonify({"error": "User not found"}), 404