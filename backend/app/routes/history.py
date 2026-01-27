from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Translation

history_bp = Blueprint('history', __name__)

@history_bp.route('/', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    user = db.session.query(db.session.query(User).filter_by(google_id=user_id).first()).first()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    translations = Translation.query.filter_by(user_id=user.id)\
        .order_by(Translation.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    history = [{
        'id': t.id,
        'original_text': t.original_text[:100] + '...' if len(t.original_text) > 100 else t.original_text,
        'translated_text': t.translated_text[:100] + '...' if len(t.translated_text) > 100 else t.translated_text,
        'source_lang': t.source_lang,
        'target_lang': t.target_lang,
        'created_at': t.created_at.isoformat(),
        'has_file': t.file_path is not None
    } for t in translations.items]
    
    return jsonify({
        'translations': history,
        'total': translations.total,
        'pages': translations.pages,
        'current_page': page
    }), 200

@history_bp.route('/<int:translation_id>', methods=['DELETE'])
@jwt_required()
def delete_translation(translation_id):
    user_id = get_jwt_identity()
    user = db.session.query(db.session.query(User).filter_by(google_id=user_id).first()).first()
    
    translation = Translation.query.filter_by(id=translation_id, user_id=user.id).first()
    if translation:
        db.session.delete(translation)
        db.session.commit()
        return jsonify({"message": "Translation deleted"}), 200
    return jsonify({"error": "Translation not found"}), 404