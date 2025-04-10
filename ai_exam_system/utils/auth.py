from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from ..models import User, db

def generate_token(user_id):
    """Generate JWT token for user authentication."""
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            current_app.config.get('JWT_SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return str(e)

def decode_token(token):
    """Decode JWT token and return user_id."""
    try:
        payload = jwt.decode(
            token,
            current_app.config.get('JWT_SECRET_KEY'),
            algorithms=['HS256']
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

def token_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token is missing'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            user_id = decode_token(token)
            if isinstance(user_id, str):
                return jsonify({'message': user_id}), 401
            
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            
        except Exception as e:
            return jsonify({'message': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to protect routes that require admin access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Token is missing'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            user_id = decode_token(token)
            if isinstance(user_id, str):
                return jsonify({'message': user_id}), 401
            
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            
            if current_user.role != 'admin':
                return jsonify({'message': 'Admin privileges required'}), 403
            
        except Exception as e:
            return jsonify({'message': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def validate_password(password):
    """
    Validate password strength.
    Returns (bool, str) tuple - (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    return True, "Password is valid"

def validate_email(email):
    """
    Basic email validation.
    Returns (bool, str) tuple - (is_valid, error_message)
    """
    import re
    
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_regex, email):
        return False, "Invalid email format"
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return False, "Email already registered"
    
    return True, "Email is valid"

def create_user(username, email, password, role='student'):
    """
    Create a new user with validated inputs.
    Returns (bool, str) tuple - (success, message)
    """
    try:
        # Validate email
        email_valid, email_msg = validate_email(email)
        if not email_valid:
            return False, email_msg
        
        # Validate password
        password_valid, password_msg = validate_password(password)
        if not password_valid:
            return False, password_msg
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            return False, "Username already exists"
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            role=role
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return True, "User created successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating user: {str(e)}"
