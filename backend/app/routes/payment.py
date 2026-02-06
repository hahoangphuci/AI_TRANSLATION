from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Payment, User
from app.services.payment_service import PaymentService

payment_bp = Blueprint('payment', __name__)
payment_service = PaymentService()

@payment_bp.route('/create', methods=['POST'])
@jwt_required()
def create_payment():
    data = request.json
    amount = data.get('amount')
    currency = data.get('currency', 'VND')
    
    user_id = get_jwt_identity()
    user = User.query.filter_by(google_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if amount is None:
        return jsonify({"error": "amount is required"}), 400
    
    payment_url = payment_service.create_payment(amount, currency)
    
    payment = Payment(
        user_id=user.id,
        amount=amount,
        currency=currency,
        status='pending'
    )
    db.session.add(payment)
    db.session.commit()
    
    return jsonify({"payment_url": payment_url, "payment_id": payment.id}), 200

@payment_bp.route('/status/<int:payment_id>', methods=['GET'])
@jwt_required()
def check_payment_status(payment_id):
    payment = Payment.query.get(payment_id)
    if payment:
        return jsonify({"status": payment.status}), 200
    return jsonify({"error": "Payment not found"}), 404


@payment_bp.route('/dev/activate-plan', methods=['POST'])
@jwt_required()
def dev_activate_plan():
    """Dev helper: activate a plan immediately (no payment verification).

    This is only enabled when DEBUG=True.
    """
    if not current_app.config.get('DEBUG'):
        return jsonify({"error": "Not available"}), 404

    data = request.get_json(silent=True) or {}
    plan = str(data.get('plan') or '').strip().lower()
    allowed = {'free', 'pro', 'promax'}
    if plan not in allowed:
        return jsonify({"error": "Invalid plan", "allowed": sorted(list(allowed))}), 400

    user_google_id = get_jwt_identity()
    user = User.query.filter_by(google_id=user_google_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.plan = plan
    db.session.commit()

    return jsonify({
        "plan": user.plan,
        "plan_name": {"free": "Free", "pro": "Pro", "promax": "ProMax"}[plan]
    }), 200