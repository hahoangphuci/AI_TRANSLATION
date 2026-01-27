from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Translation, User
from app.services.translation_service import TranslationService
from werkzeug.utils import secure_filename
import os

translation_bp = Blueprint('translation', __name__)
translation_service = TranslationService()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@translation_bp.route('/text', methods=['POST'])
@jwt_required(optional=True)
def translate_text():
    data = request.json
    text = data.get('text')
    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang')

    if not text or not str(text).strip():
        return jsonify({"error": "No text provided"}), 400
    if not target_lang or not str(target_lang).strip():
        return jsonify({"error": "target_lang is required"}), 400

    user_id = get_jwt_identity()
    user = User.query.filter_by(google_id=user_id).first() if user_id else None

    try:
        translated_text = translation_service.translate_text(text, source_lang, target_lang)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    translation = Translation(
        user_id=user.id if user else None,
        original_text=text,
        translated_text=translated_text,
        source_lang=source_lang,
        target_lang=target_lang
    )
    db.session.add(translation)
    db.session.commit()

    return jsonify({"translated_text": translated_text}), 200

@translation_bp.route('/document', methods=['POST'])
@jwt_required(optional=True)
def translate_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    target_lang = request.form.get('target_lang')

    if not target_lang or not str(target_lang).strip():
        return jsonify({"error": "target_lang is required"}), 400
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    user_id = get_jwt_identity()
    user = User.query.filter_by(google_id=user_id).first() if user_id else None

    # Create DB record indicating processing started
    translation = Translation(
        user_id=user.id if user else None,
        original_text=f"File: {filename}",
        translated_text=f"Processing file...",
        source_lang='auto',
        target_lang=target_lang,
        file_path=filepath
    )
    db.session.add(translation)
    db.session.commit()

    # Start background job
    job_id = translation_service.translate_document_background(filepath, target_lang, user_id=user_id)

    return jsonify({"job_id": job_id, "status_url": f"/api/translation/document/status/{job_id}"}), 202

@translation_bp.route('/document/status/<job_id>', methods=['GET'])
@jwt_required(optional=True)
def document_status(job_id):
    job = translation_service.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    # When completed, include download_url
    download_url = None
    if job.get('status') == 'completed' and job.get('download_path'):
        download_url = f"/downloads/{os.path.basename(job.get('download_path'))}"
    return jsonify({
        'job_id': job_id,
        'status': job.get('status'),
        'progress': job.get('progress'),
        'message': job.get('message'),
        'download_url': download_url,
        'error': job.get('error'),
        'fallback': job.get('fallback', False),
        'fallback_reason': job.get('fallback_reason')
    }), 200


@translation_bp.route('/history', methods=['GET'])
@jwt_required(optional=True)
def get_history():
    user_id = get_jwt_identity()
    user = User.query.filter_by(google_id=user_id).first() if user_id else None
    if not user:
        return jsonify({'translations': []}), 200

    translations = Translation.query.filter_by(user_id=user.id).order_by(Translation.created_at.desc()).all()
    history = [{
        'id': t.id,
        'original_text': t.original_text,
        'translated_text': t.translated_text,
        'source_lang': t.source_lang,
        'target_lang': t.target_lang,
        'created_at': t.created_at.isoformat(),
        'has_file': bool(t.file_path)
    } for t in translations]
    
    return jsonify({'translations': history}), 200