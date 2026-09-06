import re
from flask import Blueprint, request, jsonify, g
from app.models import db, User
from app.auth import generate_token, login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    phone = (data.get('phone') or '').strip()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    # Validation
    errors = []
    if not name or len(name) < 2:
        errors.append("Full name is required (minimum 2 characters).")
    if not email or not re.match(EMAIL_REGEX, email):
        errors.append("A valid email address is required.")
    if not phone or len(phone) < 8:
        errors.append("A valid contact phone number is required.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long.")
    if password != confirm_password:
        errors.append("Passwords do not match.")

    if errors:
        return jsonify({
            'success': False,
            'message': errors[0],
            'errors': errors,
            'error': 'VALIDATION_ERROR'
        }), 400

    # Check existing user
    if User.query.filter(db.func.lower(User.email) == email).first():
        return jsonify({
            'success': False,
            'message': 'An account with this email address already exists.',
            'error': 'DUPLICATE_EMAIL'
        }), 400

    user = User(
        name=name,
        email=email,
        phone=phone,
        role='USER',
        is_active=True
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Registration successful! You can now log in.',
        'data': {
            'user': user.to_dict()
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({
            'success': False,
            'message': 'Please provide both email and password.',
            'error': 'MISSING_CREDENTIALS'
        }), 400

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if not user or not user.check_password(password):
        return jsonify({
            'success': False,
            'message': 'Invalid email or password. Please try again.',
            'error': 'INVALID_CREDENTIALS'
        }), 401

    if not user.is_active:
        return jsonify({
            'success': False,
            'message': 'Your account has been deactivated. Please contact support.',
            'error': 'ACCOUNT_DEACTIVATED'
        }), 403

    token = generate_token(user.id, user.role)

    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'data': {
            'token': token,
            'user': user.to_dict()
        }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'success': True,
        'message': 'User profile retrieved',
        'data': {
            'user': g.current_user.to_dict()
        }
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user = g.current_user
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    if name:
        if len(name) < 2:
            return jsonify({'success': False, 'message': 'Name must be at least 2 characters long.', 'error': 'VALIDATION_ERROR'}), 400
        user.name = name

    if phone:
        if len(phone) < 8:
            return jsonify({'success': False, 'message': 'Invalid phone number.', 'error': 'VALIDATION_ERROR'}), 400
        user.phone = phone

    if new_password:
        if not current_password or not user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect.', 'error': 'INVALID_PASSWORD'}), 400
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'New password must be at least 6 characters.', 'error': 'VALIDATION_ERROR'}), 400
        if new_password != confirm_new_password:
            return jsonify({'success': False, 'message': 'New passwords do not match.', 'error': 'PASSWORD_MISMATCH'}), 400
        user.set_password(new_password)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Profile updated successfully.',
        'data': {
            'user': user.to_dict()
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({
        'success': True,
        'message': 'Successfully logged out.'
    }), 200
