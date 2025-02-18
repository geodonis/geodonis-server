from app import db
from datetime import datetime, timedelta, timezone
import secrets

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('reset_tokens', lazy='dynamic'))

    @classmethod
    def prune_expired_tokens(cls):
        current_time = datetime.now(timezone.utc)
        expired_tokens = cls.query.filter(
            (cls.expires_at < current_time) | (cls.used == True)
        ).delete()
        db.session.commit()
        return expired_tokens  # Returns the number of deleted tokens

def generate_password_reset_token(user, expiration_hours=24):
    token = secrets.token_urlsafe(32)
    expiration = datetime.now(timezone.utc) + timedelta(hours=expiration_hours)

    # Store the token
    reset_token = PasswordResetToken(user_id=user.id, token=token, expires_at=expiration)
    db.session.add(reset_token)
    db.session.commit()

    return reset_token, expiration