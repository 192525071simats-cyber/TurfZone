from flask import Blueprint, render_template

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/')
def home():
    return render_template('index.html')


@frontend_bp.route('/turfs')
def turfs_view():
    return render_template('turfs.html')


@frontend_bp.route('/turf/<int:turf_id>')
def turf_detail_view(turf_id):
    return render_template('turf-detail.html', turf_id=turf_id)


@frontend_bp.route('/tournaments')
def tournaments_view():
    return render_template('tournaments.html')


@frontend_bp.route('/dashboard')
def dashboard_view():
    return render_template('dashboard.html')


@frontend_bp.route('/bookings')
def bookings_view():
    return render_template('bookings.html')


@frontend_bp.route('/profile')
def profile_view():
    return render_template('profile.html')


@frontend_bp.route('/turf-bot')
def turf_bot_view():
    return render_template('turf-bot.html')


@frontend_bp.route('/login')
def login_view():
    return render_template('login.html')


@frontend_bp.route('/register')
def register_view():
    return render_template('register.html')


@frontend_bp.route('/admin')
def admin_view():
    return render_template('admin.html')
