from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10), nullable=False, default='staff')  # 'admin' or 'staff'
    payments = db.relationship('Payment', backref='recorded_by_user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    daily_fee = db.Column(db.Float, nullable=False, default=0.0)
    students = db.relationship('Student', backref='default_course', lazy=True)

class Student(db.Model):
    id = db.Column(db.String(10), primary_key=True)  # e.g., S0001
    full_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=True)  # 'ប្រុស' or 'ស្រី'
    grade_level = db.Column(db.String(50), nullable=True)  # e.g., 'ថ្នាក់ទី 10', 'ថ្នាក់ទី 11'
    default_course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    qr_code_filename = db.Column(db.String(100))
    registration_date = db.Column(db.Date, default=date.today)
    is_active = db.Column(db.Boolean, default=True)
    payments = db.relationship('Payment', backref='student', lazy=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(10), db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    is_paid = db.Column(db.Boolean, default=True)
    total_amount = db.Column(db.Float, nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    courses = db.relationship('PaymentCourse', backref='payment', lazy=True, cascade='all, delete-orphan')

class PaymentCourse(db.Model):
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    course = db.relationship('Course')