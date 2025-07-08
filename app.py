from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
from sqlalchemy.orm import joinedload
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import re
import os

from config import Config
from models import db, User, RoomPreference, SwapRequest  # type: ignore

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
async_mode = 'threading'  # Default to threading if not set by environment
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
    errors = {}
    values = {}
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        college_id = request.form.get('college_id', '').strip().upper()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        values = {'name': name, 'college_id': college_id, 'email': email, 'phone': phone}

        existing_college_id = User.query.filter_by(college_id=college_id).first()
        existing_email = User.query.filter_by(email=email).first()
        existing_phone = User.query.filter_by(phone=phone).first()

        if existing_college_id:
            errors['college_id'] = 'College ID already exists. Please use another.'
            values['college_id'] = ''
        if existing_email:
            errors['email'] = 'Email already exists. Please use another.'
            values['email'] = ''
        if existing_phone:
            errors['phone'] = 'Phone number already exists. Please use another.'
            values['phone'] = ''

        if errors:
            flash('Some fields already exist. Please correct them and try again.', 'danger')
            return render_template('register.html', errors=errors, values=values)
        try:
            user = User(  # type: ignore
                name=name,
                college_id=college_id,
                password=password,
                email=email,
                phone=phone
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created. Please login.', 'success')
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('Something went wrong. Please try again.', 'danger')
    return render_template('register.html', errors=errors, values=values)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        college_id = request.form.get('college_id', '').strip().upper()
        password = request.form.get('password', '')
        user = User.query.filter_by(college_id=college_id, password=password).first()
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
        if user:
            user.password = new_password
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
            user_id=current_user.id,
            available=available,
            needed=needed
        ).first()

        if existing:
            flash('You already posted this preference.', 'warning')
        else:
            pref = RoomPreference(  # type: ignore
                user_id=current_user.id,
                available=available,
                needed=needed
            )
            db.session.add(pref)
            db.session.commit()
            flash('Preference posted!', 'success')

    search_needed = request.args.get('search_needed', '').strip().upper()
    my_prefs = RoomPreference.query.filter_by(user_id=current_user.id).order_by(RoomPreference.id.desc()).all()
    other_prefs_query = RoomPreference.query.options(joinedload(RoomPreference.user)).filter(RoomPreference.user_id != current_user.id)

    if search_needed:
        other_prefs_query = other_prefs_query.filter(RoomPreference.available.ilike(f'%{search_needed}%'))

    other_prefs = other_prefs_query.order_by(RoomPreference.id.desc()).limit(50).all()

    return render_template(
        'dashboard.html',
        my_prefs=my_prefs,
        other_prefs=other_prefs,
        search_needed=search_needed
    )


@app.route('/accept/<int:pref_id>')
@login_required
def accept(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    # Check if already requested by this user
    existing_request = SwapRequest.query.filter_by(preference_id=pref.id, requester_id=current_user.id, status='pending').first()
    if not existing_request:
        swap_request = SwapRequest(  # type: ignore
            preference_id=pref.id,
            requester_id=current_user.id,
            status='pending'
        )
        db.session.add(swap_request)
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
        flash('You have already sent a request for this preference.', 'info')
    return redirect(url_for('dashboard'))


@app.route('/commit_request/<int:req_id>', methods=['POST'])
@login_required
def commit_request(req_id):
    req = SwapRequest.query.get_or_404(req_id)
    pref = req.preference
    if pref.user_id == current_user.id and req.status == 'pending':
        # Mark this request as committed
        req.status = 'committed'
        # Delete the preference and all requests for it
        for r in pref.requests:
            db.session.delete(r)
        db.session.delete(pref)
        # Optionally, delete the requester's own preference
        requester_pref = RoomPreference.query.filter_by(user_id=req.requester_id).first()
        if requester_pref:
            for r in requester_pref.requests:
                db.session.delete(r)
            db.session.delete(requester_pref)
        db.session.commit()
        flash('Swap committed and preferences removed.', 'success')
    else:
        flash('Invalid commit action.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/reject_request/<int:req_id>', methods=['POST'])
@login_required
def reject_request(req_id):
    req = SwapRequest.query.get_or_404(req_id)
    pref = req.preference
    if pref.user_id == current_user.id and req.status == 'pending':
        req.status = 'rejected'
        db.session.commit()
        flash('Request marked as not interested.', 'info')
    else:
        flash('Invalid reject action.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/cancel/<int:req_id>', methods=['POST'])
@login_required
def cancel(req_id):
    req = SwapRequest.query.get_or_404(req_id)
    if req.requester_id == current_user.id and req.status == 'pending':
        db.session.delete(req)
        db.session.commit()
        flash('Request cancelled successfully.', 'info')
    else:
        flash('You can only cancel your own pending requests.', 'warning')
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
    print('Client disconnected')


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
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
