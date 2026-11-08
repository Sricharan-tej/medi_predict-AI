from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from utils.decorators import login_required
from utils.db import get_db
from utils.recommendations import get_recommendation
from utils.pdf_generator import generate_pdf_report
import io

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
@login_required
def view_history():
    user_id = session['user_id']
    search_query = request.args.get('search', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if search_query:
            # Search query matching symptoms or predicted_disease
            cursor.execute(
                """
                SELECT * FROM predictions 
                WHERE user_id = ? AND (symptoms LIKE ? OR predicted_disease LIKE ?)
                ORDER BY created_at DESC
                """,
                (user_id, f"%{search_query}%", f"%{search_query}%")
            )
        else:
            cursor.execute(
                "SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            
        history = [dict(row) for row in cursor.fetchall()]
        return render_template('history.html', history=history, search=search_query)
    except Exception as e:
        flash(f"Error loading history: {e}", "danger")
        return render_template('history.html', history=[], search="")
    finally:
        conn.close()

@history_bp.route('/history/<int:pred_id>', methods=['DELETE', 'POST'])
@login_required
def delete_prediction(pred_id):
    # Support both DELETE method (for AJAX fetch) and POST method (for standard forms if needed)
    user_id = session['user_id']
    role = session.get('role')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check ownership unless admin
        cursor.execute("SELECT user_id FROM predictions WHERE id = ?", (pred_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"error": "Record not found."}), 404
            
        if row['user_id'] != user_id and role != 'admin':
            return jsonify({"error": "Unauthorized deletion request."}), 403
            
        cursor.execute("DELETE FROM predictions WHERE id = ?", (pred_id,))
        conn.commit()
        
        # If request is AJAX, return JSON, else redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'DELETE':
            return jsonify({"success": "Prediction history deleted successfully."})
            
        flash("Record deleted successfully.", "success")
        return redirect(url_for('history.view_history'))
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'DELETE':
            return jsonify({"error": f"Deletion failed: {e}"}), 500
        flash(f"Deletion failed: {e}", "danger")
        return redirect(url_for('history.view_history'))
    finally:
        conn.close()

@history_bp.route('/report/<int:pred_id>')
@login_required
def download_report(pred_id):
    user_id = session['user_id']
    role = session.get('role')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 1. Fetch prediction data
        cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
        pred_row = cursor.fetchone()
        
        if not pred_row:
            flash("Prediction record not found.", "danger")
            return redirect(url_for('history.view_history'))
            
        pred_data = dict(pred_row)
        
        # 2. Check ownership
        if pred_data['user_id'] != user_id and role != 'admin':
            flash("Unauthorized access to report.", "danger")
            return redirect(url_for('history.view_history'))
            
        # 3. Fetch user details
        cursor.execute("SELECT username, email FROM users WHERE id = ?", (pred_data['user_id'],))
        user_row = cursor.fetchone()
        user_details = dict(user_row) if user_row else {"username": "Unknown Patient", "email": "N/A"}
        
        # 4. Fetch recommendations
        rec = get_recommendation(pred_data['predicted_disease'])
        
        # 5. Generate PDF
        pdf_bytes = generate_pdf_report(user_details, pred_data, rec)
        
        # 6. Return PDF as attachment
        filename = f"MediPredict_Report_{pred_id}.pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Failed to generate report PDF: {e}", "danger")
        return redirect(url_for('history.view_history'))
    finally:
        conn.close()
