from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Payment
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
    user = db.session.query(db.session.query(User).filter_by(google_id=user_id).first()).first()
    
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