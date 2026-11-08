import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'medipredict_secure_dev_key_2026_xyz')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'database', 'database.db'))
    MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join(BASE_DIR, 'model', 'disease_model.h5'))
    SYMPTOMS_LIST_PATH = os.environ.get('SYMPTOMS_LIST_PATH', os.path.join(BASE_DIR, 'model', 'symptoms_list.txt'))
