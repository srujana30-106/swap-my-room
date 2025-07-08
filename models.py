from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(10), unique=True, nullable=False, index=True)

    def get_id(self):
        return str(self.id)

    def set_password(self, new_password):
        self.password = new_password

    def __repr__(self):
        return f'<User {self.name}>'

class RoomPreference(db.Model):
    __tablename__ = 'room_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    available = db.Column(db.String(20), nullable=False, index=True)
    needed = db.Column(db.String(20), nullable=False, index=True)
    selected = db.Column(db.Boolean, default=False, index=True)
    accepted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref='room_preferences')
    accepted_user = relationship('User', foreign_keys=[accepted_by_id], post_update=True)

    def __repr__(self):
        return f'<RoomPreference {self.available} -> {self.needed}>'

class SwapRequest(db.Model):
    __tablename__ = 'swap_requests'

    id = db.Column(db.Integer, primary_key=True)
    preference_id = db.Column(db.Integer, db.ForeignKey('room_preferences.id'), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # pending, committed, rejected

    # Relationships
    requester = relationship('User', foreign_keys=[requester_id])
    preference = relationship('RoomPreference', foreign_keys=[preference_id], backref='requests')

    def __repr__(self):
        return f'<SwapRequest {self.id} by {self.requester_id} for {self.preference_id}>'
