import tensorflow as tf
import os

MODEL_PATH = "model/drishtiscan_model.keras"
OUTPUT_PATH = "model/drishtiscan_model.tflite"

print("Checking model path...")

if not os.path.exists(MODEL_PATH):
    print(f"❌ Model not found: {MODEL_PATH}")
    exit()

print("✅ Model found")

try:
    print("Loading model...")
    model = tf.keras.models.load_model(MODEL_PATH)
    print("✅ Model loaded")

    print("Converting to TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Optional optimization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    tflite_model = converter.convert()

    print("Saving model...")
    with open(OUTPUT_PATH, "wb") as f:
        f.write(tflite_model)

    print(f"✅ Saved successfully at: {OUTPUT_PATH}")

except Exception as e:
    print("❌ Error:")
    print(e)