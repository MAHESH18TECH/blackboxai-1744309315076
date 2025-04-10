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
        user = User.query.filter_by(email=data['email']).first()
        if user and check_password_hash(user.password, data['password']):
            access_token = generate_token(user.id)
            return jsonify({
                'success': True,
                'token': access_token
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error during login: {str(e)}'
        }), 500
