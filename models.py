from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    name = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(10), unique=True, nullable=False, index=True)

    def get_id(self):
        # Overriding get_id so Flask-Login knows to use 'name'
        return self.name

    def set_password(self, new_password):
        self.password = new_password

    def __repr__(self):
        return f'<User {self.name}>'

class RoomPreference(db.Model):
    __tablename__ = 'room_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), db.ForeignKey('users.name'), nullable=False, index=True)
    available = db.Column(db.String(20), nullable=False, index=True)
    needed = db.Column(db.String(20), nullable=False, index=True)
    selected = db.Column(db.Boolean, default=False, index=True)
    accepted_by_name = db.Column(db.String(50), db.ForeignKey('users.name'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

    # Relationships
    user = relationship('User', foreign_keys=[user_name], backref='room_preferences')
    accepted_user = relationship('User', foreign_keys=[accepted_by_name], post_update=True)

    def __repr__(self):
        return f'<RoomPreference {self.available} -> {self.needed}>'
