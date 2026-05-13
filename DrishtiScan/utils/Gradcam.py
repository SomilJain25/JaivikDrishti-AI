"""
CropScan - Grad-CAM Visualization Utility
=============================================
Standalone module for generating Gradient-weighted Class Activation Maps.

Grad-CAM helps farmers and agronomists understand WHY the model made a
specific prediction by highlighting disease-relevant regions on the leaf.

Usage:
    from utils.gradcam import GradCAMVisualizer
    viz = GradCAMVisualizer(model)
    heatmap = viz.generate(image_array, class_index)
    viz.save_overlay("output.png", original_image, heatmap)
"""

import numpy as np
import tensorflow as tf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from PIL import Image
import io
import base64
import logging

logger = logging.getLogger(__name__)


class GradCAMVisualizer:
    """
    Generates Grad-CAM heatmaps for a given Keras model.

    Grad-CAM algorithm:
    1. Forward pass through model, capturing last conv layer output
    2. Compute gradient of predicted class score w.r.t. conv layer output
    3. Pool gradients spatially → importance weights per feature map
    4. Weighted sum of feature maps → raw heatmap
    5. Apply ReLU + normalize → final heatmap [0, 1]
    6. Resize to input image dimensions
    """

    def __init__(self, model: tf.keras.Model, last_conv_layer_name: str = "out_relu"):
        """
        Args:
            model: Trained Keras model
            last_conv_layer_name: Name of the last convolutional/activation layer
                                  For MobileNetV2 this is typically "out_relu"
        """
        self.model = model
        self.last_conv_layer_name = last_conv_layer_name
        self._build_grad_model()

    def _build_grad_model(self):
        """Build a sub-model that outputs both conv activations and predictions."""
        try:
            self.grad_model = tf.keras.models.Model(
                inputs=self.model.inputs,
                outputs=[
                    self.model.get_layer(self.last_conv_layer_name).output,
                    self.model.output
                ]
            )
            logger.info(f"Grad-CAM model built using layer: {self.last_conv_layer_name}")
        except ValueError as e:
            logger.error(f"Could not find layer '{self.last_conv_layer_name}': {e}")
            logger.info("Available layers:")
            for layer in self.model.layers[-10:]:
                logger.info(f"  {layer.name}")
            self.grad_model = None

    def generate(self, img_array: np.ndarray, class_index: int = None) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for a given image.

        Args:
            img_array: Preprocessed image array of shape (1, 224, 224, 3)
            class_index: Class index for which to generate Grad-CAM.
                         If None, uses the predicted class.

        Returns:
            Heatmap as numpy array of shape (224, 224), values in [0, 1]
        """
        if self.grad_model is None:
            logger.error("Grad model not initialized")
            return None

        try:
            img_tensor = tf.cast(img_array, tf.float32)

            with tf.GradientTape() as tape:
                # Forward pass — capture conv outputs and predictions
                conv_outputs, predictions = self.grad_model(img_tensor)

                # Use predicted class if not specified
                if class_index is None:
                    class_index = tf.argmax(predictions[0])

                # Class score for the target class
                class_score = predictions[:, class_index]

            # Compute gradients of class score w.r.t. conv layer output
            grads = tape.gradient(class_score, conv_outputs)

            # Global Average Pool the gradients: (batch, h, w, channels) → (channels,)
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

            # Weight conv outputs by pooled gradients
            # conv_outputs[0]: (h, w, channels)
            conv_outputs = conv_outputs[0]
            heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)  # (h, w)

            # Apply ReLU — only care about positive activations
            heatmap = tf.maximum(heatmap, 0)

            # Normalize to [0, 1]
            max_val = tf.reduce_max(heatmap)
            if max_val > 0:
                heatmap = heatmap / max_val

            heatmap = heatmap.numpy()

            # Resize from conv layer size (7x7) to input size (224x224)
            heatmap_img = Image.fromarray(np.uint8(heatmap * 255))
            heatmap_resized = heatmap_img.resize((224, 224), Image.LANCZOS)
            heatmap_resized = np.array(heatmap_resized) / 255.0

            return heatmap_resized

        except Exception as e:
            logger.error(f"Grad-CAM generation error: {e}", exc_info=True)
            return None

    def create_overlay(
        self,
        original_image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.4,
        colormap: str = "jet"
    ) -> np.ndarray:
        """
        Superimpose Grad-CAM heatmap on the original image.

        Args:
            original_image: Original image array (224, 224, 3), values in [0, 1]
            heatmap: Heatmap array (224, 224), values in [0, 1]
            alpha: Heatmap opacity (0=invisible, 1=fully opaque)
            colormap: Matplotlib colormap name ("jet", "hot", "viridis")

        Returns:
            Overlaid image array (224, 224, 3), values in [0, 1]
        """
        # Apply colormap to heatmap
        cmap = cm.get_cmap(colormap)
        heatmap_colored = cmap(heatmap)[:, :, :3]  # Drop alpha channel

        # Blend heatmap with original image
        overlay = heatmap_colored * alpha + original_image * (1 - alpha)
        overlay = np.clip(overlay, 0, 1)

        return overlay

    def to_base64(self, image_array: np.ndarray) -> str:
        """
        Convert image array to base64-encoded PNG string.
        Useful for embedding images directly in API JSON responses.

        Args:
            image_array: Image array (H, W, 3), values in [0, 1]

        Returns:
            Base64-encoded PNG string
        """
        buf = io.BytesIO()
        plt.imsave(buf, image_array, format="png")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()
        return encoded

    def save_comparison(
        self,
        save_path: str,
        original: np.ndarray,
        heatmap: np.ndarray,
        overlay: np.ndarray,
        disease_name: str,
        confidence: float
    ):
        """
        Save a side-by-side comparison: Original | Heatmap | Overlay.

        Useful for generating explainability reports for farmers or agronomists.

        Args:
            save_path: Where to save the PNG file
            original: Original image array
            heatmap: Raw heatmap array
            overlay: Overlaid image array
            disease_name: Predicted disease label
            confidence: Prediction confidence
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(
            f"CropScan — Grad-CAM Analysis\n"
            f"Disease: {disease_name} | Confidence: {confidence*100:.1f}%",
            fontsize=14, fontweight="bold"
        )

        axes[0].imshow(original)
        axes[0].set_title("Original Leaf Image", fontsize=12)
        axes[0].axis("off")

        axes[1].imshow(heatmap, cmap="jet")
        axes[1].set_title("Attention Heatmap\n(Red = High Focus)", fontsize=12)
        axes[1].axis("off")
        plt.colorbar(
            plt.cm.ScalarMappable(cmap="jet"),
            ax=axes[1], fraction=0.046, pad=0.04
        )

        axes[2].imshow(overlay)
        axes[2].set_title("Overlay\n(Disease Region Highlighted)", fontsize=12)
        axes[2].axis("off")

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Grad-CAM comparison saved to: {save_path}")