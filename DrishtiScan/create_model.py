"""
Create a TensorFlow 2.15 compatible model for CropScan.

This script builds a MobileNetV2-based model with custom head
for 15 crop disease classes. Model is saved in both .keras and SavedModel formats.
"""

import tensorflow as tf
from tensorflow import keras
from pathlib import Path
import json
import sys

print("TensorFlow version:", tf.__version__)

# Configuration
IMAGE_SIZE = 224
NUM_CLASSES = 15

# Class labels mapping
CLASS_LABELS = {
    "0": "Apple___Apple_scab",
    "1": "Apple___Black_rot",
    "2": "Apple___Cedar_apple_rust",
    "3": "Apple___healthy",
    "4": "Blueberry___healthy",
    "5": "Cherry_(including_sour)___Powdery_mildew",
    "6": "Cherry_(including_sour)___healthy",
    "7": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "8": "Corn_(maize)___Common_rust_",
    "9": "Corn_(maize)___Northern_Leaf_Blight",
    "10": "Corn_(maize)___healthy",
    "11": "Grape___Black_rot",
    "12": "Grape___Esca_(Black_Measles)",
    "13": "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "14": "Grape___healthy",
}

def build_model():
    """
    Build MobileNetV2-based model with custom head.
    
    Architecture:
    - MobileNetV2 base (frozen early layers)
    - Global Average Pooling (1280 dims)
    - Dense(256, relu)
    - Dropout(0.5)
    - Dense(NUM_CLASSES, softmax)
    """
    print("\nBuilding model architecture...")
    
    # Input layer with proper shape (no deprecated batch_shape)
    inputs = keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3), dtype='float32')
    
    # Load MobileNetV2 base model (pre-trained on ImageNet)
    base_model = keras.applications.MobileNetV2(
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze early layers (keep ImageNet features)
    for layer in base_model.layers[:-30]:
        layer.trainable = False
    
    print(f"  Base Model: MobileNetV2 (frozen {len(base_model.layers)-30} early layers)")
    
    # Build custom head
    x = inputs
    x = base_model(x, training=False)
    print(f"  After MobileNetV2: {x.shape}")
    
    x = keras.layers.GlobalAveragePooling2D()(x)
    print(f"  After GlobalAveragePooling2D: {x.shape}")
    
    x = keras.layers.Dense(256, activation='relu', name='dense_1')(x)
    print(f"  After Dense(256, relu): {x.shape}")
    
    x = keras.layers.Dropout(0.5, name='dropout_1')(x)
    
    outputs = keras.layers.Dense(NUM_CLASSES, activation='softmax', name='predictions')(x)
    print(f"  After Dense({NUM_CLASSES}, softmax): {x.shape}")
    
    # Create functional model
    model = keras.Model(inputs=inputs, outputs=outputs, name='DrishtiScan_MobileNetV2')
    
    print(f"\nModel created successfully!")
    print(f"  Input shape: {model.input_shape}")
    print(f"  Output shape: {model.output_shape}")
    print(f"  Total parameters: {model.count_params():,}")
    
    return model, base_model

def main():
    try:
        # Create model directory
        model_dir = Path(__file__).parent / 'model'
        model_dir.mkdir(exist_ok=True)
        
        # Build model
        model, base_model = build_model()
        
        # Save class labels
        labels_json = model_dir / 'class_labels.json'
        with open(labels_json, 'w') as f:
            json.dump({
                'index_to_class': CLASS_LABELS,
                'num_classes': NUM_CLASSES,
                'input_size': IMAGE_SIZE
            }, f, indent=2)
        print(f"\nSaved class labels: {labels_json}")
        
        # Save to .keras format (native TensorFlow 2.15 format)
        keras_path = model_dir / 'drishtiscan_model.keras'
        print(f"\nSaving to .keras format: {keras_path}")
        model.save(keras_path, save_format='keras')
        print(f"✓ Saved: {keras_path} ({keras_path.stat().st_size / 1024 / 1024:.1f} MB)")
        
        # Save to SavedModel format (for production serving)
        saved_model_dir = model_dir / 'drishtiscan_model_saved'
        print(f"\nSaving to SavedModel format: {saved_model_dir}")
        model.save(saved_model_dir, save_format='tf')
        print(f"✓ Saved: {saved_model_dir}")
        
        print("\n" + "="*60)
        print("MODEL CREATION COMPLETE!")
        print("="*60)
        print(f"Models saved to: {model_dir}")
        print(f"  - .keras format: drishtiscan_model.keras")
        print(f"  - SavedModel format: drishtiscan_model_saved/")
        print(f"  - Class labels: class_labels.json")
        print(f"\nReady for API testing with predict.py")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
