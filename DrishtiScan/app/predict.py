"""
CropScan - JaivikDrishti AI Module
======================================
Prediction System with Grad-CAM Visualization

Loads a trained model and predicts:
- Disease name
- Confidence score
- Treatment recommendation
- (Optional) Grad-CAM heatmap for explainability

Usage:
    from predict import CropScanPredictor
    predictor = CropScanPredictor()
    result = predictor.predict("path/to/leaf.jpg")
"""

import os
import json
import logging
import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from typing import Optional
import io

os.makedirs("logs", exist_ok=True)
# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/predictions.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── Treatment Database ───────────────────────────────────────────────────────
# Maps disease names → recommended treatments
# Expand this dictionary as more diseases are added
TREATMENT_DATABASE = {
    # ── Tomato Diseases ──────────────────────────────────────────────────────
    "Tomato___Bacterial_spot": (
        "Apply copper-based bactericides (copper hydroxide or copper sulfate). "
        "Remove and destroy infected plant material. Avoid overhead irrigation. "
        "Use disease-resistant tomato varieties. Rotate crops annually."
    ),
    "Tomato___Early_blight": (
        "Apply fungicides containing chlorothalonil, mancozeb, or azoxystrobin. "
        "Remove lower infected leaves. Ensure adequate plant spacing for airflow. "
        "Mulch around plants to prevent soil splash. Water at the base."
    ),
    "Tomato___Late_blight": (
        "Apply fungicides like metalaxyl or chlorothalonil immediately. "
        "Remove and destroy all infected plant parts (do not compost). "
        "Avoid wet foliage — water in the morning. Use resistant varieties like 'Mountain Magic'."
    ),
    "Tomato___Leaf_Mold": (
        "Improve greenhouse ventilation to reduce humidity below 85%. "
        "Apply fungicides containing chlorothalonil or copper-based products. "
        "Prune lower leaves to improve airflow. Avoid wetting foliage."
    ),
    "Tomato___Septoria_leaf_spot": (
        "Apply fungicides with chlorothalonil or mancozeb at first signs. "
        "Remove and dispose of infected lower leaves. "
        "Avoid overhead watering. Rotate crops for 2–3 years."
    ),
    "Tomato___Spider_mites Two-spotted_spider_mite": (
        "Apply miticides or insecticidal soap. Introduce predatory mites (Phytoseiulus persimilis). "
        "Spray plants with water to knock off mites. Maintain proper humidity. "
        "Avoid dusty conditions that favor mite populations."
    ),
    "Tomato___Target_Spot": (
        "Apply fungicides (azoxystrobin, boscalid) preventively. "
        "Ensure good air circulation. Remove infected debris. "
        "Avoid excessive nitrogen fertilization."
    ),
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": (
        "No cure exists — remove and destroy infected plants immediately. "
        "Control whitefly vectors using yellow sticky traps and insecticides. "
        "Use virus-resistant varieties. Apply reflective mulch to deter whiteflies."
    ),
    "Tomato___Tomato_mosaic_virus": (
        "No chemical cure. Remove infected plants. Disinfect tools with bleach solution (10%). "
        "Control aphid vectors. Do not smoke near plants (tobacco mosaic virus link). "
        "Use certified virus-free seeds."
    ),
    "Tomato___healthy": (
        "✅ Plant is healthy! Maintain good practices: "
        "Regular watering at the base, balanced fertilization (NPK 10-10-10), "
        "periodic inspection for early signs of disease."
    ),

    # ── Potato Diseases ──────────────────────────────────────────────────────
    "Potato___Early_blight": (
        "Apply fungicides (chlorothalonil, mancozeb) starting when plants reach 12 inches tall. "
        "Ensure adequate potassium nutrition. Remove infected lower leaves. "
        "Avoid overhead irrigation. Use certified disease-free seed potatoes."
    ),
    "Potato___Late_blight": (
        "Apply fungicides (metalaxyl + mancozeb) preventively during cool, wet conditions. "
        "Destroy all infected plant material (don't compost). "
        "Hill up potatoes to protect tubers. Harvest when vines are completely dead."
    ),
    "Potato___healthy": (
        "✅ Plant is healthy! Maintain soil pH 5.8–6.5. "
        "Ensure consistent moisture. Apply balanced fertilizer. "
        "Monitor for Colorado potato beetle and aphids."
    ),

    # ── Apple Diseases ───────────────────────────────────────────────────────
    "Apple___Apple_scab": (
        "Apply fungicides (captan, myclobutanil) from green tip through petal fall. "
        "Rake and destroy fallen leaves. Prune for better air circulation. "
        "Plant scab-resistant varieties like Liberty or Freedom."
    ),
    "Apple___Black_rot": (
        "Prune out infected wood (cankers) during dormant season. "
        "Apply fungicides (captan, thiophanate-methyl). "
        "Remove mummified fruits and dead wood. Improve orchard sanitation."
    ),
    "Apple___Cedar_apple_rust": (
        "Apply fungicides (myclobutanil, propiconazole) from pink stage through petal fall. "
        "Remove nearby eastern red cedar trees if possible. "
        "Plant rust-resistant apple varieties."
    ),
    "Apple___healthy": (
        "✅ Apple tree is healthy! Maintain annual pruning for airflow, "
        "proper irrigation, and balanced fertilization. "
        "Apply dormant oil spray in early spring to prevent scale insects."
    ),

    # ── Corn / Maize Diseases ────────────────────────────────────────────────
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": (
        "Apply fungicides (strobilurin + triazole mixture) at VT to R1 growth stage. "
        "Plant resistant hybrids. Rotate crops with non-host crops. "
        "Till crop residue to reduce inoculum."
    ),
    "Corn_(maize)___Common_rust_": (
        "Plant rust-resistant corn hybrids. Apply fungicides (propiconazole, azoxystrobin) "
        "if rust appears before silking on susceptible varieties. "
        "Monitor weather — rust is worst in cool, humid conditions."
    ),
    "Corn_(maize)___Northern_Leaf_Blight": (
        "Plant resistant hybrids (Ht1, Ht2 resistance genes). "
        "Apply fungicides (azoxystrobin, propiconazole) if disease is detected early. "
        "Rotate crops and till residue. Avoid excessive nitrogen."
    ),
    "Corn_(maize)___healthy": (
        "✅ Corn plant is healthy! Ensure proper spacing (30cm between plants), "
        "adequate nitrogen fertilization, and consistent irrigation. "
        "Scout weekly for pests like fall armyworm."
    ),

    # ── Grape Diseases ───────────────────────────────────────────────────────
    "Grape___Black_rot": (
        "Apply fungicides (myclobutanil, mancozeb) from bud break through 4–6 weeks after bloom. "
        "Remove mummified berries and infected leaves. "
        "Improve air circulation through proper training and pruning."
    ),
    "Grape___Esca_(Black_Measles)": (
        "No reliable chemical cure. Prune infected wood 30cm below symptoms in winter. "
        "Disinfect pruning tools with 70% ethanol. "
        "Protect pruning wounds with fungicidal paste. Remove heavily infected vines."
    ),
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": (
        "Apply copper-based fungicides or mancozeb. "
        "Remove infected leaves and debris. "
        "Ensure good canopy management for air circulation."
    ),
    "Grape___healthy": (
        "✅ Grape vine is healthy! Maintain proper trellising, "
        "regular pruning, and balanced fertilization. "
        "Monitor for grapevine leafroller and phylloxera."
    ),

    # ── Other Crops ──────────────────────────────────────────────────────────
    "Cherry_(including_sour)___Powdery_mildew": (
        "Apply sulfur-based fungicides or potassium bicarbonate. "
        "Prune to improve air circulation. Avoid excessive nitrogen. "
        "Apply neem oil as an organic option."
    ),
    "Cherry_(including_sour)___healthy": (
        "✅ Cherry tree is healthy! Ensure proper sunlight and drainage. "
        "Apply dormant copper spray in early spring."
    ),
    "Peach___Bacterial_spot": (
        "Apply copper-based bactericides in spring. "
        "Plant resistant varieties. Avoid overhead irrigation. "
        "Prune to improve air circulation."
    ),
    "Peach___healthy": (
        "✅ Peach tree is healthy! Maintain proper thinning of fruits, "
        "annual pruning, and balanced fertilization."
    ),
    "Pepper,_bell___Bacterial_spot": (
        "Apply copper hydroxide sprays. Use disease-free transplants. "
        "Rotate crops. Avoid working in fields when plants are wet."
    ),
    "Pepper,_bell___healthy": (
        "✅ Bell pepper plant is healthy! Ensure consistent moisture "
        "and calcium-rich fertilization to prevent blossom end rot."
    ),
    "Strawberry___Leaf_scorch": (
        "Apply fungicides (myclobutanil, captan) in early spring. "
        "Remove and destroy infected leaves. Plant resistant varieties. "
        "Ensure good drainage and air circulation."
    ),
    "Strawberry___healthy": (
        "✅ Strawberry plant is healthy! Maintain proper row spacing "
        "and replace plants every 2–3 years."
    ),
    "Soybean___healthy": (
        "✅ Soybean plant is healthy! Monitor for soybean aphid, "
        "spider mites, and sudden death syndrome. Maintain proper inoculation."
    ),
    "Squash___Powdery_mildew": (
        "Apply sulfur or potassium bicarbonate fungicides. "
        "Plant resistant varieties. Ensure adequate spacing. "
        "Apply neem oil as preventive spray."
    ),
    "Raspberry___healthy": (
        "✅ Raspberry plant is healthy! Prune old canes after harvest "
        "and ensure trellising for support."
    ),
    "Orange___Haunglongbing_(Citrus_greening)": (
        "⚠️ SEVERE — No cure exists. Remove and destroy infected trees immediately. "
        "Control Asian citrus psyllid vectors with insecticides. "
        "Use certified disease-free nursery stock. Report to local agricultural authorities."
    ),
    "Blueberry___healthy": (
        "✅ Blueberry plant is healthy! Maintain soil pH 4.5–5.5, "
        "ensure good drainage, and apply acid fertilizer."
    ),
    "Background_without_leaves": (
        "⚠️ No plant detected in image. Please upload a clear photo of a plant leaf "
        "for accurate disease detection."
    ),
}

# Default treatment when disease is not in database
DEFAULT_TREATMENT = (
    "Consult your local agricultural extension officer (KVK) for tailored advice. "
    "General recommendations: Remove and destroy infected plant material, "
    "apply broad-spectrum fungicide/bactericide as appropriate, "
    "and ensure proper crop hygiene."
)

# ─── Constants ────────────────────────────────────────────────────────────────
IMAGE_SIZE = (224, 224)
MODEL_PATH = "model/drishtiscan_model.tflite"
CLASS_LABELS_PATH = "model/class_labels.json"
CONFIDENCE_THRESHOLD = 0.4  # Below this, result is flagged as uncertain


class CropScanPredictor:
    """
    Main prediction engine for CropScan.
    
    Handles:
    - Model loading and caching
    - Image preprocessing
    - Disease prediction
    - Treatment lookup
    - Grad-CAM visualization
    """

    def __init__(self, model_path: str = MODEL_PATH, labels_path: str = CLASS_LABELS_PATH):
        """
        Initialize predictor by loading model and class labels.
        
        Args:
            model_path: Path to the saved .tflite or Keras model
            labels_path: Path to the class_labels.json file
        """
        os.makedirs("logs", exist_ok=True)
        self.model = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.model_type = None
        self.class_labels = {}
        self.num_classes = 0

        # Optimize for CPU inference (before model loads)
        try:
            tf.config.threading.set_intra_op_parallelism_threads(4)
            tf.config.threading.set_inter_op_parallelism_threads(4)
        except RuntimeError as e:
            logger.warning(f"Could not configure threading after initialization: {e}")

        self._load_model(model_path)
        self._load_class_labels(labels_path)

        logger.info("CropScanPredictor initialized successfully")

    def _load_model(self, model_path: str):
        """Load the trained model from the given path.

        Supports TFLite models for mobile-friendly deployment.
        """
        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}. Please convert the model to TFLite first.")
            return

        logger.info(f"Loading model from: {model_path}")
        try:
            if model_path.lower().endswith(".tflite"):
                self.interpreter = tf.lite.Interpreter(model_path=model_path)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                self.model_type = "tflite"
                logger.info("TFLite model loaded successfully")
            else:
                self.model = tf.keras.models.load_model(model_path, compile=False, safe_mode=True)
                self.model_type = "keras"
                logger.info("Keras model loaded successfully")
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            self.model = None
            self.interpreter = None
            self.model_type = None

    def _load_class_labels(self, labels_path: str):
        """Load class label mapping from JSON file."""
        if not os.path.exists(labels_path):
            logger.warning(f"Class labels not found at {labels_path}")
            return

        with open(labels_path, "r") as f:
            data = json.load(f)

        self.class_labels = data.get("index_to_class", {})
        self.num_classes = data.get("num_classes", 0)
        logger.info(f"Loaded {self.num_classes} class labels")

    def preprocess_image(self, image_input) -> np.ndarray:
        """
        Preprocess image for model input.
        
        Accepts file path (str), bytes, or PIL Image.
        
        Returns:
            Normalized numpy array of shape (1, 224, 224, 3)
        
        Raises:
            ValueError: If image cannot be processed
        """
        try:
            # Handle different input types
            if isinstance(image_input, str):
                # File path
                img = Image.open(image_input)
            elif isinstance(image_input, bytes):
                # Raw bytes (from API upload)
                img = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                raise ValueError(f"Unsupported image input type: {type(image_input)}")

            # Convert to RGB (handles PNG with alpha channel, grayscale, etc.)
            img = img.convert("RGB")

            # Resize to model's expected input size
            img = img.resize(IMAGE_SIZE, Image.LANCZOS)

            # Convert to numpy array and normalize to [0, 1]
            img_array = np.array(img, dtype=np.float32) / 255.0

            # Add batch dimension: (224, 224, 3) → (1, 224, 224, 3)
            img_array = np.expand_dims(img_array, axis=0)

            return img_array

        except UnidentifiedImageError:
            raise ValueError("Invalid image file — cannot be opened or identified")
        except Exception as e:
            raise ValueError(f"Image preprocessing failed: {str(e)}")

    def get_treatment(self, disease_name: str) -> str:
        """
        Look up treatment recommendation for a given disease.
        
        Args:
            disease_name: Predicted disease class name
        
        Returns:
            Treatment string
        """
        return TREATMENT_DATABASE.get(disease_name, DEFAULT_TREATMENT)

    def predict_with_model(self, model, image_input, return_top_k: int = 3) -> dict:
        """
        Run prediction with a registry-provided model wrapper.

        The current registry stores CropScanPredictor instances so versioning can
        be added without duplicating the prediction logic.
        """
        if isinstance(model, CropScanPredictor):
            return model.predict(image_input, return_top_k=return_top_k)

        logger.warning("Unsupported registry model type: %s", type(model).__name__)
        return {
            "status": "error",
            "error": "Unsupported registry model type.",
            "disease": None,
            "confidence": 0.0,
            "treatment": None,
        }

    def predict(self, image_input, return_top_k: int = 3) -> dict:
        """
        Run full prediction pipeline on an image.
        
        Args:
            image_input: Image as file path, bytes, or PIL Image
            return_top_k: Number of top predictions to return
        
        Returns:
            Dictionary with:
                - disease: Predicted disease name
                - confidence: Confidence score (0–1)
                - treatment: Recommended treatment
                - is_uncertain: True if confidence below threshold
                - top_predictions: List of top-k predictions
                - status: "success" or "error"
        """
        # Guard: model not loaded
        if self.interpreter is None and self.model is None:
            logger.error("Model not loaded. Cannot make prediction.")
            return {
                "status": "error",
                "error": "Model not loaded.",
                "disease": None,
                "confidence": 0.0,
                "treatment": None
            }

        try:
            # ── Step 1: Preprocess Image ────────────────────────────────────
            img_array = self.preprocess_image(image_input)

            # ── Step 2: Run Model Inference ─────────────────────────────────
            if self.model_type == "tflite":
                input_index = self.input_details[0]["index"]
                output_index = self.output_details[0]["index"]

                input_dtype = self.input_details[0]["dtype"]

                # Prepare input tensor
                if input_dtype == np.float32:
                    input_data = img_array.astype(np.float32)
                else:
                    input_scale, input_zero_point = self.input_details[0]["quantization"]

                    if input_scale == 0:
                        input_data = (img_array * 255).astype(input_dtype)
                    else:
                        input_data = (
                            img_array / input_scale + input_zero_point
                        ).astype(input_dtype)

                # Run inference
                self.interpreter.set_tensor(input_index, input_data)
                self.interpreter.invoke()

                output_data = self.interpreter.get_tensor(output_index)

                # Dequantize output if necessary
                output_dtype = self.output_details[0]["dtype"]

                if output_dtype in [np.uint8, np.int8]:
                    output_scale, output_zero_point = self.output_details[0]["quantization"]
                    probabilities = (
                        output_scale
                        * (output_data.astype(np.float32) - output_zero_point)
                    )
                else:
                    probabilities = output_data.astype(np.float32)

                probabilities = np.squeeze(probabilities)

            else:
                predictions = self.model.predict(img_array, verbose=0)
                probabilities = predictions[0]
            
            # ── Step 3: Get Top-K Predictions ───────────────────────────────
            top_k_indices = np.argsort(probabilities)[::-1][:return_top_k]
            top_predictions = [
                {
                    "disease": self.class_labels.get(str(idx), f"Class_{idx}"),
                    "confidence": float(probabilities[idx])
                }
                for idx in top_k_indices
            ]

            # ── Step 4: Extract Best Prediction ─────────────────────────────
            best_idx = top_k_indices[0]
            disease_name = self.class_labels.get(str(best_idx), f"Unknown_Class_{best_idx}")
            confidence = float(probabilities[best_idx])

            # ── Step 5: Get Treatment ────────────────────────────────────────
            treatment = self.get_treatment(disease_name)

            # ── Step 6: Log Prediction ───────────────────────────────────────
            is_uncertain = confidence < CONFIDENCE_THRESHOLD
            logger.info(
                f"Prediction: {disease_name} | "
                f"Confidence: {confidence:.4f} | "
                f"Uncertain: {is_uncertain}"
            )

            return {
                "status": "success",
                "disease": disease_name,
                "confidence": round(confidence, 4),
                "confidence_percent": f"{confidence * 100:.1f}%",
                "treatment": treatment,
                "is_uncertain": is_uncertain,
                "uncertainty_warning": (
                    "Low confidence prediction. Please provide a clearer image."
                    if is_uncertain else None
                ),
                "top_predictions": top_predictions
            }

        except ValueError as e:
            logger.error(f"Image error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "disease": None,
                "confidence": 0.0,
                "treatment": None
            }
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": f"Prediction failed: {str(e)}",
                "disease": None,
                "confidence": 0.0,
                "treatment": None
            }

    def generate_gradcam(self, image_input, last_conv_layer_name: str = "out_relu") -> Optional[np.ndarray]:
        """
        Generate Grad-CAM heatmap for model explainability.
        
        Grad-CAM highlights which parts of the image the model focused on 
        when making its prediction — crucial for agricultural use to verify
        the model is looking at actual lesions/symptoms.
        
        Args:
            image_input: Image as file path, bytes, or PIL Image
            last_conv_layer_name: Name of the last convolutional layer
        
        Returns:
            Heatmap as numpy array (224, 224), or None on failure
        """
        if self.model is None or self.model_type != "keras":
            logger.warning("Grad-CAM is only available for Keras model deployments.")
            return None

        try:
            img_array = self.preprocess_image(image_input)

            # Build Grad-CAM model: outputs both predictions and last conv layer activations
            grad_model = tf.keras.models.Model(
                inputs=self.model.inputs,
                outputs=[
                    self.model.get_layer(last_conv_layer_name).output,
                    self.model.output
                ]
            )

            # Compute gradients with respect to the predicted class
            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(img_array)
                pred_index = tf.argmax(predictions[0])
                class_channel = predictions[:, pred_index]

            # Gradients of the class score w.r.t. conv layer output
            grads = tape.gradient(class_channel, conv_outputs)

            # Pool gradients over spatial dimensions
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

            # Weight conv outputs by pooled gradients
            conv_outputs = conv_outputs[0]
            heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)

            # Normalize heatmap to [0, 1]
            heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
            heatmap = heatmap.numpy()

            # Resize to original image size
            from PIL import Image as PILImage
            heatmap_img = PILImage.fromarray(np.uint8(heatmap * 255))
            heatmap_resized = np.array(heatmap_img.resize(IMAGE_SIZE, PILImage.LANCZOS)) / 255.0

            logger.info("Grad-CAM heatmap generated successfully")
            return heatmap_resized

        except Exception as e:
            logger.error(f"Grad-CAM generation failed: {e}")
            return None

    def predict_with_gradcam(self, image_input) -> dict:
        """
        Run prediction and generate Grad-CAM heatmap in one call.
        
        Returns prediction result with base64-encoded heatmap overlay.
        """
        import base64

        result = self.predict(image_input)

        if result["status"] == "success":
            heatmap = self.generate_gradcam(image_input)
            if heatmap is not None:
                # Convert heatmap to base64 PNG for API response
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import matplotlib.cm as cm

                # Apply colormap (jet: blue=low attention, red=high attention)
                heatmap_colored = cm.jet(heatmap)[:, :, :3]  # RGB only

                # Superimpose on original image
                img_array = self.preprocess_image(image_input)[0]
                superimposed = heatmap_colored * 0.4 + img_array * 0.6
                superimposed = np.clip(superimposed, 0, 1)

                # Encode as base64
                buf = io.BytesIO()
                plt.imsave(buf, superimposed, format="png")
                buf.seek(0)
                result["gradcam_image"] = base64.b64encode(buf.read()).decode("utf-8")
                buf.close()

        return result


# ─── Demo Usage ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python predict.py <image_path>")
        print("Example: python predict.py sample_leaf.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    predictor = CropScanPredictor()
    result = predictor.predict(image_path)

    print("\n" + "=" * 60)
    print("CropScan - Disease Detection Result")
    print("=" * 60)
    print(f"Status     : {result['status']}")
    if result["status"] == "success":
        print(f"Disease    : {result['disease']}")
        print(f"Confidence : {result['confidence_percent']}")
        print(f"Uncertain  : {result['is_uncertain']}")
        print(f"\nTreatment  :\n{result['treatment']}")
        print("\nTop Predictions:")
        for i, pred in enumerate(result["top_predictions"]):
            print(f"  {i+1}. {pred['disease']}: {pred['confidence']*100:.1f}%")
    else:
        print(f"Error: {result['error']}")
    print("=" * 60)
