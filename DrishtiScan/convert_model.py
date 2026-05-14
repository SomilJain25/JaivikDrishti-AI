import tensorflow as tf
from pathlib import Path

# Load the existing .keras model
keras_model_path = Path(__file__).parent / 'model' / 'drishtiscan_model.keras'
saved_model_dir = Path(__file__).parent / 'model' / 'drishtiscan_model_saved'

print(f"Loading model from: {keras_model_path}")

try:
    # Load the .keras model (TensorFlow 2.15 compatible)
    model = tf.keras.models.load_model(keras_model_path)
    print("✓ Model loaded successfully")
    
    # Save in SavedModel format
    model.save(saved_model_dir)
    print(f"✓ Model converted and saved to: {saved_model_dir}")
    print("\n✓ Conversion complete! The model is now in SavedModel format.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("Troubleshooting: Ensure the .keras file exists and is valid.")