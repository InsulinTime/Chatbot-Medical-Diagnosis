#this file is models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    user_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    medical_aid_number = db.Column(db.String(100))
    id_number = db.Column(db.String(13))
    
    practice_number = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    clinic_name = db.Column(db.String(200))
    
    consultations = db.relationship('Consultation', backref='user', lazy=True, 
                                  foreign_keys='Consultation.user_id')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True,
                                    foreign_keys='MedicalRecord.patient_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100))
    symptoms = db.Column(db.Text)
    diagnosis_suggestion = db.Column(db.Text)
    urgency_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transcript = db.Column(db.Text)

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    practitioner_id = db.Column(db.Integer, nullable=True)
    record_type = db.Column(db.String(50))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(10), default='en')
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)