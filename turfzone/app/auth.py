from functools import wraps
from flask import request, jsonify, g, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from app.models import User, db

TOKEN_MAX_AGE = 86400 * 7  # 7 days


def generate_token(user_id, role):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps({'user_id': user_id, 'role': role}, salt='turfzone-auth')


def verify_token(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, salt='turfzone-auth', max_age=TOKEN_MAX_AGE)
        return data
    except (SignatureExpired, BadTimeSignature, Exception):
        return None


def get_token_from_request():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
        if len(parts) == 1:
            return parts[0]
    
    custom_header = request.headers.get('X-Auth-Token')
    if custom_header:
        return custom_header
        
    query_token = request.args.get('token')
    if query_token:
        return query_token
        
    return None


def get_current_user():
    token = get_token_from_request()
    if not token:
        return None
    data = verify_token(token)
    if not data or 'user_id' not in data:
        return None
    return db.session.get(User, data['user_id'])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required. Please log in.',
                'error': 'UNAUTHORIZED'
            }), 401

        data = verify_token(token)
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired session. Please log in again.',
                'error': 'INVALID_TOKEN'
            }), 401

        user = db.session.get(User, data['user_id'])
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': 'User account not found or deactivated.',
                'error': 'USER_NOT_FOUND'
            }), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required. Please log in.',
                'error': 'UNAUTHORIZED'
            }), 401

        data = verify_token(token)
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired session. Please log in again.',
                'error': 'INVALID_TOKEN'
            }), 401

        user = db.session.get(User, data['user_id'])
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': 'User account not found or deactivated.',
                'error': 'USER_NOT_FOUND'
            }), 401

        if user.role != 'ADMIN':
            return jsonify({
                'success': False,
                'message': 'Access denied. Administrator privileges required.',
                'error': 'FORBIDDEN'
            }), 403

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
