from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # Default role is 'student'
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Reference to another User (instructor)
    groups = db.relationship('Group', secondary='group_student', backref='group_students', lazy='dynamic')  # Many-to-many with Group

# Group model
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Reference to instructor (User)
    students = db.relationship('User', secondary='group_student', backref='student_groups', lazy='dynamic')  # Many-to-many with User

# GroupStudent model to handle the many-to-many relationship between users (students) and groups
class GroupStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    file_url = db.Column(db.String(200), nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Reference to instructor (User)

# Discussion model
class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))  # Reference to Group
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Reference to User (sender of the message)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp for when the message was sent
