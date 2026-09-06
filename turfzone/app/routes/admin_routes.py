from datetime import date, datetime
from flask import Blueprint, request, jsonify
from app.models import db, User, Turf, Booking, Tournament, TournamentRegistration
from app.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    today = date.today()

    # Users
    total_users = User.query.count()
    regular_users = User.query.filter_by(role='USER').count()

    # Turfs
    total_turfs = Turf.query.count()
    active_turfs = Turf.query.filter_by(is_active=True).count()

    # Bookings
    total_bookings = Booking.query.count()
    confirmed_bookings = Booking.query.filter_by(status='CONFIRMED').count()
    cancelled_bookings = Booking.query.filter_by(status='CANCELLED').count()
    completed_bookings = Booking.query.filter_by(status='COMPLETED').count()

    todays_bookings = Booking.query.filter(
        Booking.booking_date == today,
        Booking.status == 'CONFIRMED'
    ).count()

    upcoming_bookings = Booking.query.filter(
        Booking.booking_date > today,
        Booking.status == 'CONFIRMED'
    ).count()

    # Revenue from CONFIRMED and COMPLETED bookings
    revenue_records = Booking.query.filter(Booking.status.in_(['CONFIRMED', 'COMPLETED'])).all()
    total_revenue = sum(b.price for b in revenue_records)

    # Tournaments
    total_tournaments = Tournament.query.count()
    active_tournaments = Tournament.query.filter(Tournament.tournament_date >= today).count()
    total_registrations = TournamentRegistration.query.count()

    # Recent Activity
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(6).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(6).all()

    return jsonify({
        'success': True,
        'message': 'Admin statistics retrieved successfully',
        'data': {
            'stats': {
                'total_users': total_users,
                'regular_users': regular_users,
                'total_turfs': total_turfs,
                'active_turfs': active_turfs,
                'total_bookings': total_bookings,
                'confirmed_bookings': confirmed_bookings,
                'cancelled_bookings': cancelled_bookings,
                'completed_bookings': completed_bookings,
                'todays_bookings': todays_bookings,
                'upcoming_bookings': upcoming_bookings,
                'total_revenue': round(total_revenue, 2),
                'total_tournaments': total_tournaments,
                'active_tournaments': active_tournaments,
                'total_tournament_registrations': total_registrations
            },
            'recent_bookings': [b.to_dict() for b in recent_bookings],
            'recent_users': [u.to_dict() for u in recent_users]
        }
    }), 200


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    user_list = []
    for u in users:
        u_dict = u.to_dict()
        u_dict['booking_count'] = len(u.bookings)
        u_dict['tournament_count'] = len(u.tournament_registrations)
        user_list.append(u_dict)

    return jsonify({
        'success': True,
        'data': {
            'users': user_list,
            'count': len(user_list)
        }
    }), 200


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['PUT'])
@admin_required
def toggle_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found',
            'error': 'USER_NOT_FOUND'
        }), 404

    if user.role == 'ADMIN':
        return jsonify({
            'success': False,
            'message': 'Cannot deactivate administrator account.',
            'error': 'CANNOT_DEACTIVATE_ADMIN'
        }), 400

    user.is_active = not user.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'User "{user.name}" {"activated" if user.is_active else "deactivated"}.',
        'data': {
            'user': user.to_dict()
        }
    }), 200


@admin_bp.route('/bookings', methods=['GET'])
@admin_required
def get_admin_bookings():
    status_filter = request.args.get('status', '').strip().upper()
    query = Booking.query

    if status_filter and status_filter != 'ALL':
        query = query.filter_by(status=status_filter)

    bookings = query.order_by(Booking.booking_date.desc(), Booking.created_at.desc()).all()

    return jsonify({
        'success': True,
        'data': {
            'bookings': [b.to_dict() for b in bookings],
            'count': len(bookings)
        }
    }), 200


@admin_bp.route('/bookings/<int:booking_id>/status', methods=['PUT'])
@admin_required
def update_booking_status(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({
            'success': False,
            'message': 'Booking not found',
            'error': 'BOOKING_NOT_FOUND'
        }), 404

    data = request.get_json() or {}
    new_status = (data.get('status') or '').strip().upper()

    if new_status not in ['CONFIRMED', 'CANCELLED', 'COMPLETED']:
        return jsonify({
            'success': False,
            'message': 'Invalid status. Allowed values: CONFIRMED, CANCELLED, COMPLETED.',
            'error': 'INVALID_STATUS'
        }), 400

    booking.status = new_status
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Booking {booking.booking_reference} status updated to {new_status}.',
        'data': {
            'booking': booking.to_dict()
        }
    }), 200
