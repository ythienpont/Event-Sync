from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()
'''
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    public = db.Column(db.Boolean, default=False, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    invites = db.relationship('RSVP', backref='event', lazy=True)

class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum('Will Attend', 'Maybe', 'Will Not Attend', name='rsvp_status'), default='Maybe', nullable=False)

    user = db.relationship('User', backref=db.backref('rsvps', lazy=True))
'''
