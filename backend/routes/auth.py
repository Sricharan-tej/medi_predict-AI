from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from utils.db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('prediction.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')
            
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')
            
        password_hash = generate_password_hash(password)
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, 'user')
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError as e:
            # Check if username or email is duplicate
            if 'username' in str(e).lower():
                flash("Username already exists.", "danger")
            elif 'email' in str(e).lower():
                flash("Email already registered.", "danger")
            else:
                flash("An integrity error occurred. Username or email might be taken.", "danger")
            return render_template('register.html')
        except Exception as e:
            flash(f"An error occurred during registration: {e}", "danger")
            return render_template('register.html')
        finally:
            conn.close()
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('prediction.dashboard'))
        
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip() # Can be username or email
        password = request.form.get('password', '')
        
        if not login_input or not password:
            flash("Please enter both credentials and password.", "danger")
            return render_template('login.html')
            
        conn = get_db()
        cursor = conn.cursor()
        try:
            # Check if input is email or username
            cursor.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (login_input, login_input)
            )
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Set up session
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                
                flash(f"Welcome back, {user['username']}!", "success")
                if user['role'] == 'admin':
                    return redirect(url_for('admin.admin_dashboard'))
                return redirect(url_for('prediction.dashboard'))
            else:
                flash("Invalid username/email or password.", "danger")
                return render_template('login.html')
        except Exception as e:
            flash(f"An error occurred during login: {e}", "danger")
            return render_template('login.html')
        finally:
            conn.close()
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have logged out successfully.", "info")
    return redirect(url_for('index'))
