from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Extended length for hashed password
    avatar = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='Viewer')
    status = db.Column(db.String(50), nullable=False, default='active')

    # Single definition using datetime.now
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, raw_password):
        """Hashes the password before storing it."""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verifies the entered password against the stored hash."""
        return check_password_hash(self.password, raw_password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'avatar': self.avatar or '',
            'role': self.role,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else ''
        }