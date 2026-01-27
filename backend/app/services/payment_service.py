import requests
import os
import hashlib
import hmac
import json

class PaymentService:
    def __init__(self):
        self.api_key = os.getenv('SEPAY_API_KEY')
        self.secret = os.getenv('SEPAY_SECRET')
        self.base_url = "https://my.sepay.vn"
    
    def create_payment(self, amount, currency='VND'):
        # Sepay payment creation
        # This is a placeholder implementation
        # In real implementation, you would call Sepay API
        
        payment_data = {
            "amount": amount,
            "currency": currency,
            "description": "AI Translation Service Payment",
            "return_url": os.getenv('FRONTEND_URL', 'http://localhost:3000') + "/payment/success",
            "cancel_url": os.getenv('FRONTEND_URL', 'http://localhost:3000') + "/payment/cancel"
        }
        
        # Generate signature
        signature = self._generate_signature(payment_data)
        payment_data['signature'] = signature
        
        # In real implementation:
        # response = requests.post(f"{self.base_url}/api/v1/payment/create", json=payment_data)
        # return response.json()['payment_url']
        
        # Placeholder return
        return f"{self.base_url}/pay?amount={amount}&currency={currency}&signature={signature}"
    
    def verify_payment(self, payment_data):
        signature = payment_data.pop('signature', '')
        expected_signature = self._generate_signature(payment_data)
        return hmac.compare_digest(signature, expected_signature)
    
    def _generate_signature(self, data):
        # Sort data by key
        sorted_data = sorted(data.items())
        message = '&'.join(f"{k}={v}" for k, v in sorted_data)
        
        # Create HMAC SHA256 signature
        signature = hmac.new(
            self.secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature