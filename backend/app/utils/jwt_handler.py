from flask_jwt_extended import JWTManager
from datetime import timedelta

jwt = JWTManager()

def init_jwt(app):
    app.config['JWT_SECRET_KEY'] = app.config.get('JWT_SECRET_KEY', 'your-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    jwt.init_app(app)