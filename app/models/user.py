from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, suspended, deleted
    is_super_user = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=timezone.utc)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_admin_user():
    email = 'admin@geodonis.com'
    username='geodonis_admin'
    password = None
    if not email or not username or not password:
        raise ValueError("Action can not be done!")
    new_user = User(
        email=email,
        username=username,
        password_hash=generate_password_hash(password),
        is_super_user=True
    )
    db.session.add(new_user)
    db.session.commit()
