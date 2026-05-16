import tensorflow as tf
from pathlib import Path
import os

model_dir = Path(__file__).parent / 'model'
keras_model_path = model_dir / 'drishtiscan_model.keras'
h5_model_path = model_dir / 'drishtiscan_model.h5'
saved_model_dir = model_dir / 'drishtiscan_model_saved'

print("Starting model conversion...")
print(f"Model directory: {model_dir}")

model = None

# Try loading .keras first with safe_mode
if keras_model_path.exists():
    print(f"\nAttempt 1: Loading {keras_model_path.name} with safe_mode=True...")
    try:
        model = tf.keras.models.load_model(keras_model_path, compile=False, safe_mode=True)
        print("SUCCESS: .keras model loaded with safe_mode=True")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)[:200]}")
        model = None

# If that failed, try without safe_mode
if model is None and keras_model_path.exists():
    print(f"\nAttempt 2: Loading {keras_model_path.name} without safe_mode...")
    try:
        model = tf.keras.models.load_model(keras_model_path, compile=False)
        print("SUCCESS: .keras model loaded without safe_mode")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)[:200]}")
        model = None

# Try loading .h5 model as fallback
if model is None and h5_model_path.exists():
    print(f"\nAttempt 3: Loading {h5_model_path.name} as fallback...")
    try:
        model = tf.keras.models.load_model(h5_model_path, compile=False, safe_mode=True)
        print("SUCCESS: .h5 model loaded (will save as .keras and SavedModel)")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)[:200]}")
        model = None

# If we successfully loaded a model, save it
if model is not None:
    try:
        print(f"\nModel loaded successfully! Architecture:")
        print(f"  Input shape: {model.input_shape}")
        print(f"  Output shape: {model.output_shape}")
        
        # Save to SavedModel format
        print(f"\nSaving to SavedModel format: {saved_model_dir}")
        model.save(saved_model_dir)
        print("SUCCESS: Model saved to SavedModel directory")
        
        # Also re-save .keras format
        print(f"\nRe-saving to .keras format: {keras_model_path}")
        model.save(keras_model_path)
        print("SUCCESS: Model saved to .keras format")
        
        print("\n" + "="*50)
        print("CONVERSION COMPLETE!")
        print("="*50)
        print(f"SavedModel: {saved_model_dir}")
        print(f".keras model: {keras_model_path}")
        
    except Exception as e:
        print(f"ERROR during save: {type(e).__name__}: {e}")
else:
    print("\nERROR: Could not load any model file!")
    print("Available files:")
    for f in model_dir.glob("*"):
        print(f"  - {f.name}")