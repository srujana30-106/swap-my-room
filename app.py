from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room
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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = {}
    values = {}
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        college_id = request.form.get('college_id', '').strip().upper()
        email = request.form.get('email', '').strip()
        room_number = request.form.get('room_number', '').strip()
        password = request.form.get('password', '')

        values = {'name': name, 'college_id': college_id, 'email': email, 'room_number': room_number}

        import re
        if not re.match(r'^[A-Z]{2}[0-9]{6}$', college_id):
            errors['college_id'] = 'Invalid college ID. Enter in format: 2 capital letters followed by 6 digits (e.g., RO200000).'
        if not re.match(r'^\d{3}$', room_number):
            errors['room_number'] = 'Invalid room number. Room number should have exactly 3 digits.'

        existing_college_id = User.query.filter_by(college_id=college_id).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_college_id:
            errors['college_id'] = 'College ID already exists. Please use another.'
            values['college_id'] = ''
        if existing_email:
            errors['email'] = 'Email already exists. Please use another.'
            values['email'] = ''

        if errors:
            flash('Please correct the errors below and try again.', 'danger')
            return render_template('register.html', errors=errors, values=values)
        try:
            user = User(
                name=name,
                college_id=college_id,
                password=password,
                email=email,
                room_number=room_number
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

    # Get search parameters
    search_needed = request.args.get('search_needed', '').strip().upper()
    search_room = request.args.get('search_room', '').strip().upper()
    
    # Get user's preferences
    my_prefs = RoomPreference.query.filter_by(user_id=current_user.id).order_by(RoomPreference.id.desc()).all()
    
    # Get all users for the main table
    all_users_query = User.query.filter(User.id != current_user.id)
    if search_room:
        all_users_query = all_users_query.filter(User.room_number.ilike(f'%{search_room}%'))
    all_users = all_users_query.order_by(User.name).all()
    
    # Get requests sent by current user
    my_requests = SwapRequest.query.filter_by(requester_id=current_user.id).order_by(SwapRequest.id.desc()).all()
    
    # Get requests received by current user
    my_invitations = []
    for pref in my_prefs:
        for req in pref.requests:
            if req.status == 'pending':
                my_invitations.append(req)
    
    # Get other users' preferences (for compatibility)
    other_prefs_query = RoomPreference.query.options(joinedload(RoomPreference.user)).filter(RoomPreference.user_id != current_user.id)
    if search_needed:
        other_prefs_query = other_prefs_query.filter(RoomPreference.available.ilike(f'%{search_needed}%'))
    other_prefs = other_prefs_query.order_by(RoomPreference.id.desc()).limit(50).all()

    return render_template(
        'dashboard.html',
        my_prefs=my_prefs,
        other_prefs=other_prefs,
        search_needed=search_needed,
        all_users=all_users,
        my_requests=my_requests,
        my_invitations=my_invitations,
        search_room=search_room,
        active_tab='dashboard'
    )


@app.route('/all_users')
@login_required
def all_users():
    search_room = request.args.get('search_room', '').strip()
    query = User.query
    if search_room:
        query = query.filter(User.room_number.ilike(f'%{search_room}%'))
    query = query.filter(User.id != current_user.id)
    users = query.all()

    # Find all pending requests sent by current user
    sent_requests = SwapRequest.query.join(RoomPreference).filter(
        SwapRequest.requester_id == current_user.id,
        RoomPreference.user_id == User.id,
        SwapRequest.status == 'pending'
    ).all()
    sent_user_ids = [req.preference.user_id for req in sent_requests]
    sent_request_ids = {req.preference.user_id: req.id for req in sent_requests}

    return render_template('all_users.html', users=users, search_room=search_room, sent_user_ids=sent_user_ids, sent_request_ids=sent_request_ids, active_tab='all_users')

@app.route('/available_rooms')
def available_rooms():
    return render_template('available_rooms.html')

@app.route('/my_requests')
@login_required
def my_requests():
    my_requests = SwapRequest.query.filter_by(requester_id=current_user.id).order_by(SwapRequest.id.desc()).all()
    return render_template('my_requests.html', my_requests=my_requests, active_tab='my_requests')

@app.route('/invitations')
@login_required
def invitations():
    my_invitations = SwapRequest.query.join(RoomPreference).filter(RoomPreference.user_id == current_user.id).order_by(SwapRequest.id.desc()).all()
    return render_template('invitations.html', my_invitations=my_invitations, active_tab='invitations')


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
            status='pending',
            from_room_number=current_user.room_number,
            to_room_number=pref.user.room_number
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
        # Swap room numbers between the requester and the preference owner
        requester = req.requester
        owner = pref.user
        requester_room = requester.room_number
        owner_room = owner.room_number
        requester.room_number = owner_room
        owner.room_number = requester_room
        req.status = 'committed'
        db.session.commit()
        flash('Swap committed. Room numbers updated.', 'success')
    else:
        flash('Invalid commit action.', 'danger')
    return redirect(url_for('invitations'))


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
    return redirect(url_for('invitations'))


@app.route('/send_direct_request/<int:user_id>', methods=['POST'])
@login_required
def send_direct_request(user_id):
    target_user = User.query.get_or_404(user_id)
    
    # Check if already sent a request to this user
    existing_request = SwapRequest.query.join(RoomPreference).filter(
        SwapRequest.requester_id == current_user.id,
        RoomPreference.user_id == user_id,
        SwapRequest.status == 'pending'
    ).first()
    
    if existing_request:
        flash('You have already sent a request to this user.', 'warning')
    else:
        # Create a preference for the target user if they don't have one
        target_pref = RoomPreference.query.filter_by(user_id=user_id).first()
        if not target_pref:
            target_pref = RoomPreference(
                user_id=user_id,
                available=target_user.room_number,
                needed='Any'
            )
            db.session.add(target_pref)
            db.session.flush()  # Get the ID
        
        # Create the swap request
        swap_request = SwapRequest(
            preference_id=target_pref.id,
            requester_id=current_user.id,
            status='pending',
            from_room_number=current_user.room_number,
            to_room_number=target_user.room_number
        )
        db.session.add(swap_request)
        db.session.commit()
        
        flash(f'Swap request sent to {target_user.name}!', 'success')
    
    return redirect(url_for('all_users'))


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


# Removed the /edit/<int:pref_id> route and related code for editing user preferences


@app.route('/delete/<int:pref_id>')
@login_required 
def delete(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    db.session.delete(pref)
    db.session.commit()
    flash('Preference deleted.')
    return redirect(url_for('dashboard'))


@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user
    from flask_login import logout_user
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.', 'info')
    return redirect(url_for('home'))


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


@app.route('/swap_history')
@login_required
def swap_history():
    # Get all committed swaps where the user was involved
    committed_swaps = SwapRequest.query.filter(
        (SwapRequest.status == 'committed') &
        ((SwapRequest.requester_id == current_user.id) | (SwapRequest.preference.has(user_id=current_user.id)))
    ).order_by(SwapRequest.id.desc()).all()
    return render_template('swap_history.html', swap_history=committed_swaps, active_tab='swap_history')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', active_tab='profile')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        room_number = request.form.get('room_number', '').strip()
        email = request.form.get('email', '').strip()
        # Optionally, add validation here
        current_user.name = name
        current_user.room_number = room_number
        current_user.email = email
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', active_tab='profile')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
