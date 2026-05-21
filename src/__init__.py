from flask import Flask
from src.routes.health_routes import health_bp
from src.routes.account_routes import account_bp
from src.routes.transfer_routes import transfer_bp
from src.routes.quote_routes import quote_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(health_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(transfer_bp)
    app.register_blueprint(quote_bp)
    return app
