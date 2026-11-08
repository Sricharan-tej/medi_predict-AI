import h5py
import joblib
import io
import os
import numpy as np
from config import Config

class ModelLoader:
    _model = None

    @classmethod
    def get_model(cls):
        """Loads and returns the model. Caches the model after the first load."""
        if cls._model is not None:
            return cls._model

        model_path = Config.MODEL_PATH
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")

        print(f"Loading model from H5 container at {model_path}...")
        try:
            with h5py.File(model_path, 'r') as f:
                if 'model_data' not in f:
                    raise KeyError("Dataset 'model_data' not found in model H5 file.")
                raw_data = f['model_data'][()]
                bytes_data = np.void(raw_data).tobytes()
                
            cls._model = joblib.load(io.BytesIO(bytes_data))
            print("Model loaded successfully.")
            return cls._model
        except Exception as e:
            print(f"Error loading model: {e}")
            raise e
