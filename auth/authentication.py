import bcrypt
import streamlit as st
from database.connection import get_database_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed_password):
    # Ensure hashed_password is bytes
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


def register_user(username, email, password, role='user'):
    conn = get_database_connection()
    if conn:
        cursor = conn.cursor()
        hashed_pw = hash_password(password)
        
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                (username, email, hashed_pw, role)
            )
            conn.commit()
            return True
        except:
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def login_user(username, password):
    conn = get_database_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, role FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if result and verify_password(password, result[0]):
            return {'username': username, 'role': result[1]}
        
        cursor.close()
        conn.close()
    return None
"""
auth/authentication.py

Simple authentication system for the review analysis platform
Uses in-memory storage for demo purposes
For production, replace with proper database (SQLite, PostgreSQL, etc.)
"""

import hashlib
import logging
from typing import Optional, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory user database (for demo purposes)
# In production, replace with actual database
USERS_DB = {}

# Create default admin user
DEFAULT_ADMIN = {
    'username': 'admin',
    'email': 'admin@example.com',
    'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
    'role': 'admin',
    'created_at': datetime.now().isoformat()
}

# Create default regular user
DEFAULT_USER = {
    'username': 'user',
    'email': 'user@example.com',
    'password_hash': hashlib.sha256('user123'.encode()).hexdigest(),
    'role': 'user',
    'created_at': datetime.now().isoformat()
}

# Initialize with default users
USERS_DB['admin'] = DEFAULT_ADMIN
USERS_DB['user'] = DEFAULT_USER

logger.info("Default users created: admin/admin123 and user/user123")


def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == password_hash


def register_user(username: str, email: str, password: str, role: str = "user") -> bool:
    """
    Register a new user
    
    Args:
        username: User's username
        email: User's email
        password: User's password (will be hashed)
        role: User role ("user" or "admin")
    
    Returns:
        True if registration successful, False otherwise
    """
    try:
        # Check if username already exists
        if username in USERS_DB:
            logger.warning(f"Registration failed: Username '{username}' already exists")
            return False
        
        # Check if email already exists
        for user_data in USERS_DB.values():
            if user_data.get('email') == email:
                logger.warning(f"Registration failed: Email '{email}' already exists")
                return False
        
        # Create new user
        new_user = {
            'username': username,
            'email': email,
            'password_hash': hash_password(password),
            'role': role,
            'created_at': datetime.now().isoformat()
        }
        
        USERS_DB[username] = new_user
        logger.info(f"User '{username}' registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False


def login_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user
    
    Args:
        username: User's username
        password: User's password
    
    Returns:
        User data dict if successful, None otherwise
    """
    try:
        # Check if user exists
        if username not in USERS_DB:
            logger.warning(f"Login failed: Username '{username}' not found")
            return None
        
        user_data = USERS_DB[username]
        
        # Verify password
        if not verify_password(password, user_data['password_hash']):
            logger.warning(f"Login failed: Invalid password for '{username}'")
            return None
        
        # Return user data (without password hash)
        user_info = {
            'username': user_data['username'],
            'email': user_data['email'],
            'role': user_data['role'],
            'created_at': user_data['created_at']
        }
        
        logger.info(f"User '{username}' logged in successfully")
        return user_info
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return None


def get_user(username: str) -> Optional[Dict]:
    """
    Get user data by username
    
    Args:
        username: User's username
    
    Returns:
        User data dict (without password) if found, None otherwise
    """
    if username not in USERS_DB:
        return None
    
    user_data = USERS_DB[username]
    return {
        'username': user_data['username'],
        'email': user_data['email'],
        'role': user_data['role'],
        'created_at': user_data['created_at']
    }


def update_user(username: str, **kwargs) -> bool:
    """
    Update user data
    
    Args:
        username: User's username
        **kwargs: Fields to update (email, password, role)
    
    Returns:
        True if update successful, False otherwise
    """
    try:
        if username not in USERS_DB:
            logger.warning(f"Update failed: Username '{username}' not found")
            return False
        
        user_data = USERS_DB[username]
        
        # Update allowed fields
        if 'email' in kwargs:
            user_data['email'] = kwargs['email']
        
        if 'password' in kwargs:
            user_data['password_hash'] = hash_password(kwargs['password'])
        
        if 'role' in kwargs and kwargs['role'] in ['user', 'admin']:
            user_data['role'] = kwargs['role']
        
        logger.info(f"User '{username}' updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Update error: {e}")
        return False


def delete_user(username: str) -> bool:
    """
    Delete a user
    
    Args:
        username: User's username
    
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        if username not in USERS_DB:
            logger.warning(f"Delete failed: Username '{username}' not found")
            return False
        
        # Don't allow deleting default admin
        if username == 'admin':
            logger.warning("Cannot delete default admin user")
            return False
        
        del USERS_DB[username]
        logger.info(f"User '{username}' deleted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return False


def list_all_users() -> list:
    """
    Get list of all users (for admin dashboard)
    
    Returns:
        List of user dicts (without passwords)
    """
    users = []
    for username, user_data in USERS_DB.items():
        users.append({
            'username': user_data['username'],
            'email': user_data['email'],
            'role': user_data['role'],
            'created_at': user_data['created_at']
        })
    return users


def get_user_count() -> Dict[str, int]:
    """
    Get user statistics
    
    Returns:
        Dict with user counts by role
    """
    total = len(USERS_DB)
    admin_count = sum(1 for u in USERS_DB.values() if u['role'] == 'admin')
    user_count = total - admin_count
    
    return {
        'total': total,
        'admins': admin_count,
        'users': user_count
    }


# Example usage and testing
if __name__ == "__main__":
    print("\n=== Authentication Module Test ===\n")
    
    # Test login with default users
    print("1. Testing login with default admin...")
    admin = login_user('admin', 'admin123')
    if admin:
        print(f"   ✓ Login successful: {admin['username']} ({admin['role']})")
    else:
        print("   ✗ Login failed")
    
    print("\n2. Testing login with default user...")
    user = login_user('user', 'user123')
    if user:
        print(f"   ✓ Login successful: {user['username']} ({user['role']})")
    else:
        print("   ✗ Login failed")
    
    # Test registration
    print("\n3. Testing user registration...")
    if register_user('testuser', 'test@example.com', 'password123', 'user'):
        print("   ✓ Registration successful")
    else:
        print("   ✗ Registration failed")
    
    # Test duplicate registration
    print("\n4. Testing duplicate registration...")
    if not register_user('testuser', 'test2@example.com', 'password123', 'user'):
        print("   ✓ Correctly rejected duplicate username")
    else:
        print("   ✗ Should have rejected duplicate")
    
    # Test wrong password
    print("\n5. Testing wrong password...")
    if not login_user('admin', 'wrongpassword'):
        print("   ✓ Correctly rejected wrong password")
    else:
        print("   ✗ Should have rejected wrong password")
    
    # Test user stats
    print("\n6. User statistics:")
    stats = get_user_count()
    print(f"   Total users: {stats['total']}")
    print(f"   Admins: {stats['admins']}")
    print(f"   Regular users: {stats['users']}")
    
    print("\n=== Test Complete ===\n")