from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.decorators import login_required
from utils.db import get_db
from utils.model_loader import ModelLoader
from utils.preprocess import SymptomPreprocessor
from utils.recommendations import get_recommendation
from datetime import datetime

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE user_id = ?", (user_id,))
        total_predictions = cursor.fetchone()[0]
        
        # Get recent predictions
        cursor.execute(
            "SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        )
        recent_predictions = [dict(row) for row in cursor.fetchall()]
        
        # Get latest prediction
        latest_prediction = recent_predictions[0] if recent_predictions else None
        
        # Calculate some stats: most frequent disease predicted for this user
        cursor.execute(
            "SELECT predicted_disease, COUNT(*) as count FROM predictions WHERE user_id = ? GROUP BY predicted_disease ORDER BY count DESC LIMIT 1",
            (user_id,)
        )
        freq_row = cursor.fetchone()
        frequent_disease = freq_row['predicted_disease'] if freq_row else "None"
        
        return render_template(
            'dashboard.html',
            total_predictions=total_predictions,
            recent_predictions=recent_predictions,
            latest_prediction=latest_prediction,
            frequent_disease=frequent_disease
        )
    except Exception as e:
        flash(f"Error loading dashboard: {e}", "danger")
        return render_template('dashboard.html', total_predictions=0, recent_predictions=[], latest_prediction=None, frequent_disease="None")
    finally:
        conn.close()

@prediction_bp.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    symptoms_list = SymptomPreprocessor.get_symptoms_list()
    
    if request.method == 'POST':
        # Can accept JSON or form data
        if request.is_json:
            data = request.get_json()
            selected_symptoms = data.get('symptoms', [])
        else:
            selected_symptoms = request.form.getlist('symptoms')
            
        if not selected_symptoms:
            if request.is_json:
                return jsonify({"error": "No symptoms selected."}), 400
            flash("Please select at least one symptom.", "danger")
            return redirect(url_for('prediction.predict'))
            
        try:
            # 1. Load model
            model = ModelLoader.get_model()
            
            # 2. Preprocess symptoms into feature vector
            input_vector = SymptomPreprocessor.preprocess(selected_symptoms)
            
            # 3. Model Predict
            predicted_disease = model.predict(input_vector)[0]
            
            # Calculate confidence score (probability)
            probabilities = model.predict_proba(input_vector)[0]
            max_idx = model.classes_.tolist().index(predicted_disease)
            confidence_score = float(probabilities[max_idx])
            
            # 4. Get recommendation details
            rec = get_recommendation(predicted_disease)
            
            # 5. Save prediction in database
            conn = get_db()
            cursor = conn.cursor()
            
            # Join symptoms as a comma-separated string for saving
            symptoms_str = ", ".join(selected_symptoms)
            
            cursor.execute(
                "INSERT INTO predictions (user_id, symptoms, predicted_disease, confidence_score) VALUES (?, ?, ?, ?)",
                (session['user_id'], symptoms_str, predicted_disease, confidence_score)
            )
            prediction_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            response_data = {
                "prediction_id": prediction_id,
                "predicted_disease": predicted_disease.title(),
                "confidence_score": confidence_score,
                "description": rec["description"],
                "causes": rec["causes"],
                "precautions": rec["precautions"],
                "diet": rec["diet"],
                "exercises": rec["exercises"],
                "specialist": rec["specialist"]
            }
            
            if request.is_json:
                return jsonify(response_data)
                
            # If standard form submit, render predict with result
            return render_template(
                'predict.html',
                symptoms_list=symptoms_list,
                result=response_data,
                selected_symptoms=selected_symptoms
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            if request.is_json:
                return jsonify({"error": f"Prediction failed: {str(e)}"}), 500
            flash(f"Prediction failed: {e}", "danger")
            return redirect(url_for('prediction.predict'))
            
    return render_template('predict.html', symptoms_list=symptoms_list, result=None)
