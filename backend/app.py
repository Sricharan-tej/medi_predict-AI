from flask import Flask, render_template, session, redirect, url_for
from config import Config
from routes.auth import auth_bp
from routes.prediction import prediction_bp
from routes.history import history_bp
from routes.admin import admin_bp
from utils.model_loader import ModelLoader
import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../frontend/templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../frontend/static')
)
app.config.from_object(Config)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(history_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('prediction.dashboard'))
    return render_template('index.html')

# Global context processor to make session variables available in templates
@app.context_processor
def inject_user():
    return dict(
        current_username=session.get('username'),
        current_role=session.get('role'),
        is_logged_in=('user_id' in session)
    )


if __name__ == "__main__":
    # Ensure database exists
    db_path = Config.DATABASE_PATH
    if not os.path.exists(db_path):
        print("Database not found! Initializing database schema...")
        from database.db_setup import init_db
        init_db()
        
    print("Starting MediPredict AI Application...")
    app.run(host="0.0.0.0", port=5000, debug=True)
