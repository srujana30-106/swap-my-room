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

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
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
    selected = db.Column(db.Boolean, default=False)
    accepted_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = relationship('User', foreign_keys=[user_id])
    accepted_user = relationship('User', foreign_keys=[accepted_by], post_update=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        college_id = request.form.get('college_id').strip().upper()
        password = request.form.get('password')
        email = request.form.get('email').strip()
        phone = request.form.get('phone').strip()

        if not re.match(r'^[A-Z0-9]{8}$', college_id):
            flash('College ID must be exactly 8 characters: uppercase letters and numbers only.', 'warning')
            return redirect(url_for('register'))

        existing_id = User.query.filter_by(college_id=college_id).first()
        existing_email = User.query.filter_by(email=email).first()
        existing_phone = User.query.filter_by(phone=phone).first()

        if existing_id and existing_email and existing_phone:
            flash('College ID, Email, and Phone already exist. Try another.', 'danger')
        elif existing_id:
            flash('College ID already exists. Try another.', 'danger')
        elif existing_email:
            flash('Email already in use. Try another.', 'danger')
        elif existing_phone:
            flash('Phone number already in use. Try another.', 'danger')
        else:
            try:
                user = User(college_id=college_id, password=password, email=email, phone=phone)
                db.session.add(user)
                db.session.commit()
                flash('Account created. Please login.', 'success')
                return redirect(url_for('login'))
            except Exception:
                db.session.rollback()
                flash('Something went wrong. Please try again.', 'danger')
    return render_template('register.html')

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
                needed=needed,
                selected=False
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

    notifications = RoomPreference.query.options(joinedload(RoomPreference.accepted_user)) \
        .filter(RoomPreference.user_id == current_user.id) \
        .filter(RoomPreference.selected == True) \
        .all()

    return render_template(
        'dashboard.html',
        my_prefs=my_prefs,
        other_prefs=other_prefs,
        notifications=notifications,
        floor_filter=floor_filter
    )

@app.route('/accept/<int:pref_id>')
@login_required
def accept(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    if pref and not pref.selected:
        pref.selected = True
        pref.accepted_by = current_user.id
        db.session.commit()
        flash('Swap request sent!', 'success')
    else:
        flash('This preference is already accepted.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/cancel/<int:pref_id>', methods=['POST'])
@login_required
def cancel(pref_id):
    pref = RoomPreference.query.get_or_404(pref_id)
    if pref.selected and pref.accepted_by == current_user.id:
        pref.selected = False
        pref.accepted_by = None
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
    emit('connected', {'data': 'Connected'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
