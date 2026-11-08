from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import admin_required
from utils.db import get_db
import sqlite3

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin.html')

@admin_bp.route('/admin/dashboard')
@admin_required
def get_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Total users (excluding admins or total)
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        total_users = cursor.fetchone()[0]
        
        # Total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        
        # Top 5 most predicted diseases
        cursor.execute(
            """
            SELECT predicted_disease, COUNT(*) as count 
            FROM predictions 
            GROUP BY predicted_disease 
            ORDER BY count DESC 
            LIMIT 5
            """
        )
        top_diseases_rows = cursor.fetchall()
        top_diseases = [{"disease": row['predicted_disease'].title(), "count": row['count']} for row in top_diseases_rows]
        
        return jsonify({
            "total_users": total_users,
            "total_predictions": total_predictions,
            "top_diseases": top_diseases
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_users():
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC")
        users = [dict(row) for row in cursor.fetchall()]
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE', 'POST'])
@admin_required
def delete_user(user_id):
    # Prevent self-deletion
    if user_id == session['user_id']:
        return jsonify({"error": "You cannot delete your own account."}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if user exists and is not admin
        cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"error": "User not found."}), 404
            
        if user['role'] == 'admin':
            return jsonify({"error": "Administrator accounts cannot be deleted."}), 403
            
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'DELETE':
            return jsonify({"success": "User deleted successfully."})
            
        flash("User deleted successfully.", "success")
        return redirect(url_for('admin.admin_dashboard'))
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'DELETE':
            return jsonify({"error": str(e)}), 500
        flash(f"Error deleting user: {e}", "danger")
        return redirect(url_for('admin.admin_dashboard'))
    finally:
        conn.close()

@admin_bp.route('/admin/analytics')
@admin_required
def get_analytics():
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Disease distribution
        cursor.execute(
            """
            SELECT predicted_disease, COUNT(*) as count 
            FROM predictions 
            GROUP BY predicted_disease 
            ORDER BY count DESC
            """
        )
        disease_rows = cursor.fetchall()
        disease_labels = [row['predicted_disease'].title() for row in disease_rows]
        disease_counts = [row['count'] for row in disease_rows]
        
        # Monthly prediction trend (Grouped by YYYY-MM)
        # Using strftime to extract Year and Month from created_at
        cursor.execute(
            """
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
            FROM predictions 
            GROUP BY month 
            ORDER BY month ASC 
            LIMIT 12
            """
        )
        trend_rows = cursor.fetchall()
        trend_labels = []
        trend_counts = []
        
        for row in trend_rows:
            # Format YYYY-MM to more readable month name (e.g. Jan 2026)
            try:
                dt = datetime.strptime(row['month'], "%Y-%m")
                trend_labels.append(dt.strftime("%b %Y"))
            except:
                trend_labels.append(row['month'])
            trend_counts.append(row['count'])
            
        return jsonify({
            "disease_distribution": {
                "labels": disease_labels,
                "data": disease_counts
            },
            "prediction_trend": {
                "labels": trend_labels,
                "data": trend_counts
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
