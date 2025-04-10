from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Exam, ExamSession, Answer, db
from ..utils.ai_models import get_essay_grader, get_question_generator

exam_bp = Blueprint('exam', __name__)

@exam_bp.route('/', methods=['GET'])
@jwt_required()
def get_exams():
    """Retrieve available exams for the logged-in user."""
    user_id = get_jwt_identity()
    exams = Exam.query.all()
    return jsonify([{
        'id': exam.id,
        'title': exam.title,
        'description': exam.description,
        'duration_minutes': exam.duration_minutes
    } for exam in exams]), 200

@exam_bp.route('/<int:exam_id>/start', methods=['POST'])
@jwt_required()
def start_exam(exam_id):
    """Start an exam session for the logged-in user."""
    user_id = get_jwt_identity()
    exam = Exam.query.get_or_404(exam_id)
    
    # Create a new exam session
    session = ExamSession(student_id=user_id, exam_id=exam.id)
    db.session.add(session)
    db.session.commit()
    
    return jsonify({'session_id': session.id, 'message': 'Exam started successfully'}), 201

@exam_bp.route('/<int:session_id>/submit', methods=['POST'])
@jwt_required()
def submit_exam(session_id):
    """Submit answers for the exam session."""
    user_id = get_jwt_identity()
    session = ExamSession.query.get_or_404(session_id)
    
    if session.student_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    answers = data.get('answers', [])
    
    for answer_data in answers:
        answer = Answer(
            session_id=session.id,
            question_id=answer_data['question_id'],
            answer_text=answer_data['answer_text']
        )
        db.session.add(answer)
    
    # Grade essay answers using BERT
    essay_grader = get_essay_grader()
    for answer in answers:
        if answer['question_type'] == 'essay':
            score, feedback = essay_grader.grade_essay(answer['answer_text'], answer['reference_answer'])
            answer.score = score
            answer.feedback = feedback
    
    db.session.commit()
    
    return jsonify({'message': 'Exam submitted successfully'}), 200
