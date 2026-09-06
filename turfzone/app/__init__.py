import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from app.models import db
from app.seed import seed_database


def create_app(config_override=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    )

    # Base configuration
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'turfzone.db')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'turfzone-production-secret-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    if config_override:
        app.config.update(config_override)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # Register API blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.turf_routes import turf_bp
    from app.routes.booking_routes import booking_bp
    from app.routes.tournament_routes import tournament_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.chatbot_routes import chatbot_bp
    from app.routes.frontend_routes import frontend_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(turf_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(tournament_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(frontend_bp)

    # Global JSON error handlers for API endpoints
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'message': 'Resource not found',
                'error': 'NOT_FOUND'
            }), 404
        return e

    @app.errorhandler(405)
    def handle_405(e):
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'message': 'Method not allowed',
                'error': 'METHOD_NOT_ALLOWED'
            }), 405
        return e

    @app.errorhandler(500)
    def handle_500(e):
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'message': 'An internal server error occurred',
                'error': 'INTERNAL_SERVER_ERROR'
            }), 500
        return e

    # Create tables and auto-seed on startup
    with app.app_context():
        db.create_all()
        if not app.config.get('TESTING'):
            seed_database()

    return app
