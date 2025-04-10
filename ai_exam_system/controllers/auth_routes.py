from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from ..models import User, db
from ..utils.auth import (
    generate_token, token_required, create_user,
    validate_email, validate_password
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        # Check required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        role = data.get('role', 'student')  # Default role is student
        
        # Create user
        success, message = create_user(username, email, password, role)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error during registration: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token."""
    try:
        data = request.get_json()
        
        # Check required fields
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Missing email or password'
            }), 400
        
        # Find user by email
        user = User.query.filter_by(email=data['email']).first()Next, I will create the routes for user authentication, which will handle registration, login, and token management.

<create_file>
<path>ai_exam_system/controllers/auth_routes.py</path>
<content>
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..models import User, db
from ..utils.auth import create_user, validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    success, message = create_user(username, email, password)
    
    if success:
        return jsonify({'message': message}), 201
    return jsonify({'message': message}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (invalidate token)."""
    # In a real application, you would implement token blacklisting here.
    return jsonify({'message': 'Successfully logged out'}), 200
