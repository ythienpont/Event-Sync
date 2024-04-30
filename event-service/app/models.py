from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    public = db.Column(db.Boolean, default=False, nullable=False)
    organizer = db.Column(db.String(80),  nullable=False)
    
    # Relationships
    invites = db.relationship('RSVP', backref='event', lazy=True)

class RSVP(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False, primary_key=True)
    username = db.Column(db.String(80), nullable=False, primary_key=True)
    status = db.Column(db.Enum('Will Attend', 'Maybe', 'Will Not Attend', name='rsvp_status'), default='Maybe', nullable=False)
