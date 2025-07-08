from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_socketio import SocketIO, emit
from sqlalchemy.orm import relationship, joinedload
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import re

from config import Config  # import config

app = Flask(__name__)
app.config.from_object(Config)  # load configuration from config.py

# Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
with app.app_context():
    db.create_all()

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    college_id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)  

    def set_password(self, new_password):
        self.password = new_password

class RoomPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    available = db.Column(db.String(20))
    needed = db.Column(db.String(20))
    user = relationship('User', foreign_keys=[user_id])
    requests = relationship('SwapRequest', back_populates='preference', cascade='all, delete-orphan')

class SwapRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preference_id = db.Column(db.Integer, db.ForeignKey('room_preference.id'))
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='pending')  # pending, committed, rejected

    requester = relationship('User', foreign_keys=[requester_id])
    preference = relationship('RoomPreference', foreign_keys=[preference_id], back_populates='requests')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

        existing_id = User.query.filter_by(college_id=college_id).first()
        existing_email = User.query.filter_by(email=email).first()
        existing_phone = User.query.filter_by(phone=phone).first()

        if existing_id:
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
            user = User(name=name, college_id=college_id, password=password, email=email, phone=phone)
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
        college_id = request.form['college_id'].strip().upper()
        password = request.form['password']
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
            user_id=current_user.id,
            available=available,
            needed=needed
        ).first()

        if existing:
            flash('You already posted this preference.', 'warning')
        else:
            pref = RoomPreference(
                user_id=current_user.id,
                available=available,
                needed=needed
            )
            db.session.add(pref)
            db.session.commit()
            flash('Preference posted!', 'success')

    floor_filter = request.args.get('floor')
    my_prefs = RoomPreference.query.filter_by(user_id=current_user.id).all()

    other_prefs_query = RoomPreference.query.filter(RoomPreference.user_id != current_user.id)

    if floor_filter:
        other_prefs_query = other_prefs_query.filter(
            RoomPreference.available.ilike(f'{floor_filter}%')
        )

    other_prefs = other_prefs_query.order_by(RoomPreference.id.desc()).all()

    return render_template(
        'dashboard.html',
        my_prefs=my_prefs,
        other_prefs=other_prefs,
        floor_filter=floor_filter
    )

@app.route('/accept/<int:pref_id>')
@login_required
def accept(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    # Check if already requested by this user
    existing_request = SwapRequest.query.filter_by(preference_id=pref.id, requester_id=current_user.id, status='pending').first()
    if not existing_request:
        swap_request = SwapRequest(preference_id=pref.id, requester_id=current_user.id, status='pending')
        db.session.add(swap_request)
        db.session.commit()
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
    emit('connected', {'data': 'Connected'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
