from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User model for students and administrators."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    exams_taken = db.relationship('ExamSession', backref='student', lazy=True)
    
    def set_password(self, password):
        """Set hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches."""
        return check_password_hash(self.password_hash, password)

class Exam(db.Model):
    """Exam model containing exam metadata."""
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='exam', lazy=True)
    sessions = db.relationship('ExamSession', backref='exam', lazy=True)

class Question(db.Model):
    """Question model for storing exam questions."""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'multiple_choice' or 'essay'
    correct_answer = db.Column(db.Text)  # For multiple choice questions
    points = db.Column(db.Integer, nullable=False, default=1)
    
    # For multiple choice questions
    options = db.relationship('QuestionOption', backref='question', lazy=True)

class QuestionOption(db.Model):
    """Options for multiple choice questions."""
    __tablename__ = 'question_options'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

class ExamSession(db.Model):
    """Model for tracking student exam sessions."""
    __tablename__ = 'exam_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Float)
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed', 'terminated'
    
    # Relationships
    answers = db.relationship('Answer', backref='session', lazy=True)
    proctoring_logs = db.relationship('ProctoringLog', backref='session', lazy=True)

class Answer(db.Model):
    """Model for storing student answers."""
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float)  # AI-graded score for essays
    feedback = db.Column(db.Text)  # AI-generated feedback
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProctoringLog(db.Model):
    """Model for storing proctoring session logs."""
    __tablename__ = 'proctoring_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_sessions.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'face_detected', 'multiple_faces', 'no_face', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON)  # Store additional event details as JSON
    severity = db.Column(db.String(20), default='info')  # 'info', 'warning', 'critical'
