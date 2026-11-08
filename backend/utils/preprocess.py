import os
import numpy as np
from config import Config

class SymptomPreprocessor:
    _symptoms_list = None
    _symptom_to_idx = None

    @classmethod
    def _load_symptoms(cls):
        """Loads and indexes symptoms from the text file."""
        if cls._symptoms_list is not None:
            return

        symptoms_path = Config.SYMPTOMS_LIST_PATH
        if not os.path.exists(symptoms_path):
            raise FileNotFoundError(f"Symptoms list file not found at {symptoms_path}")

        print(f"Loading symptoms from {symptoms_path}...")
        with open(symptoms_path, 'r', encoding='utf-8') as f:
            # We strip whitespace and quote marks if any
            cls._symptoms_list = [line.strip().strip('"').strip("'").lower() for line in f if line.strip()]

        cls._symptom_to_idx = {symptom: idx for idx, symptom in enumerate(cls._symptoms_list)}
        print(f"Loaded and indexed {len(cls._symptoms_list)} symptoms.")

    @classmethod
    def get_symptoms_list(cls):
        """Returns the sorted/indexed list of symptoms."""
        cls._load_symptoms()
        return cls._symptoms_list

    @classmethod
    def preprocess(cls, selected_symptoms):
        """
        Converts selected symptoms list of strings to a binary numpy array of shape (1, 377).
        """
        cls._load_symptoms()
        num_features = len(cls._symptoms_list)
        
        # Initialize zero vector
        input_vector = np.zeros((1, num_features))
        
        for symptom in selected_symptoms:
            norm_symptom = str(symptom).strip().lower()
            if norm_symptom in cls._symptom_to_idx:
                idx = cls._symptom_to_idx[norm_symptom]
                input_vector[0, idx] = 1.0
            else:
                print(f"Warning: Symptom '{symptom}' not found in model features.")
                
        return input_vector
