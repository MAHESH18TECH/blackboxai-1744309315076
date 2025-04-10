from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Exam, Question, QuestionOption, ExamSession, db
from ..utils.auth import admin_required
from ..utils.ai_models import get_question_generator

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/exams', methods=['POST'])
@admin_required
def create_exam():
    """Create a new exam."""
    try:
        data = request.get_json()
        
        new_exam = Exam(
            title=data['title'],
            description=data.get('description', ''),
            duration_minutes=data['duration_minutes']
        )
        
        db.session.add(new_exam)
        db.session.commit()
        
        return jsonify({
            'message': 'Exam created successfully',
            'exam_id': new_exam.id
        }), 201
        
    except KeyError as e:
        return jsonify({'message': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating exam: {str(e)}'}), 500

@admin_bp.route('/exams/<int:exam_id>/questions', methods=['POST'])
@admin_required
def add_question(exam_id):
    """Add a question to an exam."""
    try:
        data = request.get_json()
        exam = Exam.query.get_or_404(exam_id)
        
        # If AI-generated question is requested
        if data.get('generate', False):
            question_generator = get_question_generator()
            generated = question_generator.generate_question(
                topic=data['topic'],
                question_type=data.get('question_type', 'multiple_choice')
            )
            
            question = Question(
                exam_id=exam_id,
                question_text=generated['question_text'],
                question_type=generated['question_type'],
                points=data.get('points', 1)
            )
            
            if generated['question_type'] == 'multiple_choice':
                question.correct_answer = generated['correct_answer']
                db.session.add(question)
                db.session.flush()  # Get question.id without committing
                
                # Add options
                for option_text in generated['options']:
                    option = QuestionOption(
                        question_id=question.id,
                        option_text=option_text,
                        is_correct=(option_text == generated['correct_answer'])
                    )
                    db.session.add(option)
            else:
                question.correct_answer = generated['reference_answer']
                db.session.add(question)
        
        # If manual question is provided
        else:
            question = Question(
                exam_id=exam_id,
                question_text=data['question_text'],
                question_type=data['question_type'],
                correct_answer=data.get('correct_answer'),
                points=data.get('points', 1)
            )
            db.session.add(question)
            db.session.flush()
            
            if data['question_type'] == 'multiple_choice':
                for option in data.get('options', []):
                    opt = QuestionOption(
                        question_id=question.id,
                        option_text=option['text'],
                        is_correct=option.get('is_correct', False)
                    )
                    db.session.add(opt)
        
        db.session.commit()
        return jsonify({'message': 'Question added successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding question: {str(e)}'}), 500

@admin_bp.route('/exams/<int:exam_id>', methods=['GET'])
@admin_required
def get_exam_details(exam_id):
    """Get detailed information about an exam."""
    exam = Exam.query.get_or_404(exam_id)
    
    questions = [{
        'id': q.id,
        'text': q.question_text,
        'type': q.question_type,
        'points': q.points,
        'options': [{'id': opt.id, 'text': opt.option_text} 
                   for opt in q.options] if q.question_type == 'multiple_choice' else None
    } for q in exam.questions]
    
    return jsonify({
        'id': exam.id,
        'title': exam.title,
        'description': exam.description,
        'duration_minutes': exam.duration_minutes,
        'questions': questions
    }), 200

@admin_bp.route('/exams/<int:exam_id>/results', methods=['GET'])
@admin_required
def get_exam_results(exam_id):
    """Get results for all students who took the exam."""
    sessions = ExamSession.query.filter_by(exam_id=exam_id).all()
    
    results = []
    for session in sessions:
        student = User.query.get(session.student_id)
        answers = [{
            'question_id': answer.question_id,
            'answer_text': answer.answer_text,
            'score': answer.score,
            'feedback': answer.feedback
        } for answer in session.answers]
        
        results.append({
            'session_id': session.id,
            'student': {
                'id': student.id,
                'username': student.username,
                'email': student.email
            },
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'score': session.score,
            'status': session.status,
            'answers': answers
        })
    
    return jsonify(results), 200

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get list of all users."""
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    } for user in users]), 200

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """Update a user's role."""
    try:
        data = request.get_json()
        user = User.query.get_or_404(user_id)
        
        if 'role' not in data:
            return jsonify({'message': 'Role is required'}), 400
        
        if data['role'] not in ['student', 'admin']:
            return jsonify({'message': 'Invalid role'}), 400
        
        user.role = data['role']
        db.session.commit()
        
        return jsonify({'message': 'User role updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating user role: {str(e)}'}), 500
