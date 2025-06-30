from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from sqlalchemy.orm import joinedload
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import re
import os

from config import Config
from models import db, User, RoomPreference

app = Flask(__name__)
app.config.from_object(Config)

# Debug environment
print("=" * 60)
print("ENVIRONMENT DEBUG INFO:")
print(f"PORT: {os.getenv('PORT')}")
print(f"RAILWAY_ENVIRONMENT_NAME: {os.getenv('RAILWAY_ENVIRONMENT_NAME')}")
print("=" * 60)

# Init
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# SocketIO
async_mode = None
is_railway = (os.getenv('PORT') or os.getenv('RAILWAY_ENVIRONMENT_NAME') or os.getenv('RAILWAY_PROJECT_NAME'))

if is_railway:
    print("PRODUCTION ENVIRONMENT DETECTED")
    try:
        import eventlet
        async_mode = 'eventlet'
        print("USING eventlet")
    except ImportError:
        async_mode = 'threading'
        print("FALLBACK threading")
else:
    print("LOCAL DEVELOPMENT")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name').strip().upper()
        password = request.form.get('password')
        email = request.form.get('email').strip()
        phone = request.form.get('phone').strip()

        if not re.match(r'^[A-Z0-9]{8}$', name):
            flash('Name must be exactly 8 characters: uppercase letters and numbers only.', 'warning')
            return redirect(url_for('register'))

        existing_name = User.query.filter_by(name=name).first()
        existing_email = User.query.filter_by(email=email).first()
        existing_phone = User.query.filter_by(phone=phone).first()

        if existing_name:
            flash('Name already exists. Try another.', 'danger')
        elif existing_email:
            flash('Email already in use. Try another.', 'danger')
        elif existing_phone:
            flash('Phone already in use. Try another.', 'danger')
        else:
            user = User(name=name, password=password, email=email, phone=phone)
            db.session.add(user)
            db.session.commit()
            flash('Account created. Please login.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip().upper()
        password = request.form['password']
        user = User.query.filter_by(name=name, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email, salt='reset-password')
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Reset Your Password', recipients=[email], sender=app.config['MAIL_USERNAME'])
            msg.body = f'Click the link to reset your password: {reset_link}'
            mail.send(msg)
            flash('Password reset link sent! Check your email.', 'success')
        else:
            flash('Email not found', 'danger')
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        new_password = request.form['password']
        user.set_password(new_password)
        db.session.commit()
        flash('Password updated! You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        available = request.form['available'].strip().upper()
        needed = request.form['needed'].strip().upper()

        existing = RoomPreference.query.filter_by(
            user_name=current_user.name,
            available=available,
            needed=needed
        ).first()

        if existing:
            flash('You already posted this preference.', 'warning')
        else:
            pref = RoomPreference(
                user_name=current_user.name,
                available=available,
                needed=needed,
                selected=False
            )
            db.session.add(pref)
            db.session.commit()
            flash('Preference posted!', 'success')

    floor_filter = request.args.get('floor')
    my_prefs = RoomPreference.query.filter_by(user_name=current_user.name).order_by(RoomPreference.created_at.desc()).all()
    other_prefs_query = RoomPreference.query.options(joinedload(RoomPreference.user)).filter(RoomPreference.user_name != current_user.name)

    if floor_filter:
        other_prefs_query = other_prefs_query.filter(RoomPreference.available.like(f'{floor_filter}%'))

    other_prefs = other_prefs_query.order_by(RoomPreference.created_at.desc()).limit(50).all()

    notifications = RoomPreference.query.options(joinedload(RoomPreference.accepted_user)) \
        .filter(RoomPreference.user_name == current_user.name, RoomPreference.selected == True) \
        .order_by(RoomPreference.created_at.desc()).all()

    return render_template('dashboard.html',
                           my_prefs=my_prefs,
                           other_prefs=other_prefs,
                           notifications=notifications,
                           floor_filter=floor_filter)


@app.route('/accept/<int:pref_id>')
@login_required
def accept(pref_id):
    pref = RoomPreference.query.options(joinedload(RoomPreference.user)).get_or_404(pref_id)
    if pref and not pref.selected:
        pref.selected = True
        pref.accepted_by_name = current_user.name
        db.session.commit()
        socketio.emit('swap_request_notification', {
            'message': f"{current_user.name} wants to swap rooms with you!",
            'requester': current_user.name,
            'requester_phone': current_user.phone,
            'available': pref.needed,
            'needed': pref.available,
            'original_poster': pref.user.name,
            'timestamp': str(db.func.current_timestamp())
        })
        flash('Swap request sent!', 'success')
    else:
        flash('This preference is already accepted.', 'info')
    return redirect(url_for('dashboard'))


@app.route('/cancel/<int:pref_id>', methods=['POST'])
@login_required
def cancel(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    if pref.selected and pref.accepted_by_name == current_user.name:
        pref.selected = False
        pref.accepted_by_name = None
        db.session.commit()
        flash('Request cancelled successfully.', 'info')
    else:
        flash('You can only cancel your own requests.', 'warning')
    return redirect(url_for('dashboard'))


@app.route('/edit/<int:pref_id>', methods=['GET', 'POST'])
@login_required
def edit(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    if request.method == 'POST':
        pref.available = request.form['available'].strip().upper()
        pref.needed = request.form['needed'].strip().upper()
        db.session.commit()
        flash('Preference updated.')
        return redirect(url_for('dashboard'))
    return render_template('edit.html', pref=pref)


@app.route('/delete/<int:pref_id>')
@login_required
def delete(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    db.session.delete(pref)
    db.session.commit()
    flash('Preference deleted.')
    return redirect(url_for('dashboard'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to server!', 'status': 'success'})


@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')


@socketio.on('new_preference')
def handle_new_preference(data):
    emit('preference_update', {
        'message': f"New room preference posted: {data.get('available')} -> {data.get('needed')}",
        'user': data.get('user', 'Someone'),
        'available': data.get('available', ''),
        'needed': data.get('needed', ''),
        'timestamp': str(db.func.current_timestamp())
    }, broadcast=True)


@socketio.on('request_sent')
def handle_request_sent(data):
    emit('swap_request_notification', {
        'message': f"{data.get('requester', 'Someone')} wants to swap rooms with you!",
        'requester': data.get('requester', ''),
        'available': data.get('available', ''),
        'needed': data.get('needed', ''),
        'timestamp': str(db.func.current_timestamp())
    }, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
