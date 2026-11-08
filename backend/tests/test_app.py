import unittest
import os
import sys
import tempfile
import sqlite3
from werkzeug.security import generate_password_hash

# Set up paths so we can import the project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from config import Config
from utils.db import get_db
from utils.model_loader import ModelLoader
from utils.preprocess import SymptomPreprocessor
from utils.recommendations import get_recommendation
from utils.pdf_generator import generate_pdf_report

class MediPredictTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temp database file
        self.db_fd, self.db_filename = tempfile.mkstemp()
        app.config['DATABASE_PATH'] = self.db_filename
        Config.DATABASE_PATH = self.db_filename
        
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Initialize temp database schema
        self.init_temp_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_filename)

    def init_temp_db(self):
        conn = sqlite3.connect(self.db_filename)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symptoms TEXT NOT NULL,
            predicted_disease TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        # Seed test admin
        admin_pass = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("testadmin", "admin@test.com", admin_pass, "admin")
        )
        # Seed test user
        user_pass = generate_password_hash("user123")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("testuser", "user@test.com", user_pass, "user")
        )
        conn.commit()
        conn.close()

    def test_landing_page(self):
        """Test that the landing page renders correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MediPredict', response.data)
        self.assertIn(b'Predict Your Health', response.data)

    def test_user_registration(self):
        """Test user registration process."""
        response = self.client.post('/register', data={
            'username': 'newpatient',
            'email': 'patient@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

        # Verify in DB
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ('newpatient',))
        user = cursor.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'patient@test.com')
        conn.close()

    def test_user_login_and_logout(self):
        """Test logging in and logging out."""
        # Standard login
        response = self.client.post('/login', data={
            'login_input': 'testuser',
            'password': 'user123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, testuser', response.data)

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'logged out successfully', response.data)

    def test_route_protection(self):
        """Test that protected pages redirect anonymous users to login."""
        endpoints = ['/dashboard', '/predict', '/history', '/admin']
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login', response.headers['Location'])

    def test_model_loading_and_prediction(self):
        """Test that the model loader unpickles correctly and runs mock predictions."""
        # 1. Test loader loads correctly
        model = ModelLoader.get_model()
        self.assertIsNotNone(model)
        self.assertEqual(model.n_features_in_, 377)

        # 2. Test preprocessor mapping
        symptoms_input = ["anxiety and nervousness", "depression"]
        vector = SymptomPreprocessor.preprocess(symptoms_input)
        self.assertEqual(vector.shape, (1, 377))
        self.assertEqual(vector[0, 0], 1.0) # Index for anxiety and nervousness
        self.assertEqual(vector[0, 1], 1.0) # Index for depression
        self.assertEqual(vector[0, 2], 0.0)

        # 3. Run mock prediction
        pred = model.predict(vector)[0]
        self.assertIn(pred, model.classes_)

    def test_prediction_api_and_history(self):
        """Test prediction processing, DB logs storage, and history querying."""
        # Log in
        self.client.post('/login', data={
            'login_input': 'testuser',
            'password': 'user123'
        })

        # Run Prediction POST
        response = self.client.post('/predict', json={
            'symptoms': ["anxiety and nervousness", "depression"]
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('predicted_disease', data)
        self.assertIn('confidence_score', data)
        self.assertIn('prediction_id', data)
        pred_id = data['prediction_id']

        # Verify record in DB
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
        record = cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record['user_id'], 2) # testuser is second user registered
        self.assertEqual(record['symptoms'], "anxiety and nervousness, depression")
        conn.close()

        # Query history
        response = self.client.get('/history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MPR-', response.data)

    def test_pdf_report_compilation(self):
        """Test that the PDF report compiles into bytes without raising exceptions."""
        user_details = {"username": "John Doe", "email": "john@test.com"}
        prediction_data = {
            "id": 42,
            "symptoms": "anxiety and nervousness, depression",
            "predicted_disease": "panic disorder",
            "confidence_score": 0.85,
            "created_at": "2026-06-23 22:00:00"
        }
        rec = get_recommendation("panic disorder")
        
        pdf_data = generate_pdf_report(user_details, prediction_data, rec)
        self.assertIsNotNone(pdf_data)
        self.assertTrue(len(pdf_data) > 0)
        # Verify PDF header
        self.assertEqual(pdf_data[:4], b'%PDF')

    def test_admin_dashboard_authorization(self):
        """Test that only admins can access admin blueprints."""
        # Login as normal user
        self.client.post('/login', data={
            'login_input': 'testuser',
            'password': 'user123'
        })
        # Try accessing admin
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'do not have permission to access the administrator panel', response.data)

        # Login as admin
        self.client.get('/logout')
        self.client.post('/login', data={
            'login_input': 'testadmin',
            'password': 'admin123'
        })
        # Access admin dashboard
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
