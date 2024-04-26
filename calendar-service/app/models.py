from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SharedCalendar(db.Model):
    owner = db.Column(db.String(80), primary_key=True)
    shared = db.Column(db.String(80), primary_key=True)
