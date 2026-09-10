"""
gradcam.py
==========
Grad-CAM (Gradient-weighted Class Activation Mapping) explainability module
for SafeSkin AI.

Generates a colour heat-map that highlights the image regions most influential
for the model's prediction, overlays it on the original image, and uploads the
result to Supabase Storage so the front-end can display it to the user.

References
----------
Selvaraju et al. (2017) "Grad-CAM: Visual Explanations from Deep Networks via
Gradient-based Localization". https://arxiv.org/abs/1610.02391
"""

import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports
# ---------------------------------------------------------------------------
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:  # pragma: no cover
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available – GradCAMGenerator will return None.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:  # pragma: no cover
    CV2_AVAILABLE = False

try:
    from supabase import create_client, Client as SupabaseClient  # type: ignore
    SUPABASE_AVAILABLE = True
except ImportError:  # pragma: no cover
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase client not installed – GradCAM upload will be skipped.")

# Supabase credentials read from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
GRADCAM_BUCKET = "gradcam-results"

IMG_SIZE = (224, 224)


class GradCAMGenerator:
    """
    Generates Grad-CAM visualisations for a given Keras model and image.

    Usage
    -----
        generator = GradCAMGenerator()
        path = generator.generate(
            model=my_model,
            image_path="/uploads/lesion.jpg",
            layer_name="top_conv",
            user_id="user-uuid",
            screening_id="screening-uuid",
        )
        # path → "gradcam-results/user-uuid/screening-uuid.png" (Supabase storage)
    """

    def generate(
        self,
        model: "tf.keras.Model",
        image_path: str,
        layer_name: str = "top_conv",
        user_id: str = "anonymous",
        screening_id: str = "screening",
        class_idx: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate a Grad-CAM heatmap, overlay it on the original image, and
        upload the result to Supabase Storage.

        Parameters
        ----------
        model : tf.keras.Model
            Trained Keras classification model.
        image_path : str
            Path to the input image.
        layer_name : str
            Name of the convolutional layer to target.
            EfficientNetB0's last conv layer is 'top_conv'.
        user_id : str
            Supabase user UUID (used to organise the storage path).
        screening_id : str
            Unique ID for this screening event.
        class_idx : int, optional
            Class index to explain. If None the predicted class is used.

        Returns
        -------
        str or None
            Supabase storage path on success, None on failure.
        """
        if not TF_AVAILABLE or not CV2_AVAILABLE:
            logger.error("Grad-CAM requires TensorFlow and OpenCV.")
            return None

        try:
            # 1. Load and preprocess image
            original_img, img_array = self._load_image(image_path)

            # 2. Determine class index
            if class_idx is None:
                preds = model.predict(img_array, verbose=0)
                class_idx = int(np.argmax(preds[0]))

            # 3. Compute Grad-CAM heatmap
            heatmap = self._compute_gradcam(model, img_array, class_idx, layer_name)

            # 4. Overlay heatmap on original image
            result_img = self._overlay_heatmap(heatmap, original_img)

            # 5. Save and upload
            storage_path = self._save_and_upload(result_img, user_id, screening_id)
            return storage_path

        except Exception as exc:
            logger.error("GradCAMGenerator.generate failed: %s", exc, exc_info=True)
            return None

    # ------------------------------------------------------------------
    #  Core Grad-CAM computation
    # ------------------------------------------------------------------

    def _compute_gradcam(
        self,
        model: "tf.keras.Model",
        img_array: np.ndarray,
        class_idx: int,
        layer_name: str = "top_conv",
    ) -> np.ndarray:
        """
        Compute the Grad-CAM heatmap for *class_idx* using *layer_name*.

        Algorithm:
          1. Build a sub-model that outputs both the target conv-layer
             activations and the final predictions simultaneously.
          2. Use GradientTape to record gradients of the target class score
             w.r.t. the conv-layer activations.
          3. Pool (mean) the gradients over the spatial dimensions → weights.
          4. Weighted sum of activation maps → raw heatmap.
          5. Apply ReLU and normalise to [0, 1].

        Parameters
        ----------
        model : tf.keras.Model
        img_array : np.ndarray
            Pre-processed image, shape (1, 224, 224, 3).
        class_idx : int
        layer_name : str

        Returns
        -------
        np.ndarray
            Normalised heatmap of shape (h, w) with values in [0, 1].
        """
        # Build gradient model
        grad_model = tf.keras.models.Model(
            inputs=model.inputs,
            outputs=[
                model.get_layer(layer_name).output,
                model.output,
            ],
        )

        with tf.GradientTape() as tape:
            inputs = tf.cast(img_array, tf.float32)
            conv_outputs, predictions = grad_model(inputs)
            # Score for the target class
            loss = predictions[:, class_idx]

        # Gradients of the class score w.r.t. conv-layer output
        grads = tape.gradient(loss, conv_outputs)               # (1, h, w, filters)

        # Global average pooling of gradients → per-filter importance weights
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))   # (filters,)

        # Weight each feature map by its importance
        conv_outputs = conv_outputs[0]                          # (h, w, filters)
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]  # (h, w, 1)
        heatmap = tf.squeeze(heatmap)                           # (h, w)

        # ReLU: keep only positive contributions
        heatmap = tf.maximum(heatmap, 0)

        # Normalise to [0, 1]
        heatmap_np = heatmap.numpy()
        max_val = heatmap_np.max()
        if max_val > 0:
            heatmap_np = heatmap_np / max_val

        return heatmap_np.astype(np.float32)

    # ------------------------------------------------------------------
    #  Overlay generation
    # ------------------------------------------------------------------

    def _overlay_heatmap(
        self,
        heatmap: np.ndarray,
        original_img: np.ndarray,
        alpha: float = 0.4,
        colormap: int = cv2.COLORMAP_JET if CV2_AVAILABLE else 2,
    ) -> np.ndarray:
        """
        Resize the heatmap to the original image size, apply a colour-map,
        and blend it with the original image.

        Blending formula:
            result = alpha * heatmap_coloured + (1 - alpha) * original

        Parameters
        ----------
        heatmap : np.ndarray
            Normalised heatmap (h, w), values in [0, 1].
        original_img : np.ndarray
            BGR image array (H, W, 3).
        alpha : float
            Heatmap opacity (default 0.4).
        colormap : int
            OpenCV colour-map constant (default COLORMAP_JET).

        Returns
        -------
        np.ndarray
            Blended BGR image of the same size as *original_img*.
        """
        h, w = original_img.shape[:2]

        # Scale heatmap to uint8 and resize to match the original image
        heatmap_uint8 = np.uint8(255 * heatmap)
        heatmap_resized = cv2.resize(heatmap_uint8, (w, h))

        # Apply colour map
        heatmap_coloured = cv2.applyColorMap(heatmap_resized, colormap)

        # Ensure original is uint8
        if original_img.dtype != np.uint8:
            original_uint8 = np.uint8(original_img)
        else:
            original_uint8 = original_img

        # Weighted blend
        result = cv2.addWeighted(heatmap_coloured, alpha, original_uint8, 1 - alpha, 0)
        return result

    # ------------------------------------------------------------------
    #  Persistence
    # ------------------------------------------------------------------

    def _save_and_upload(
        self,
        result_img: np.ndarray,
        user_id: str,
        screening_id: str,
    ) -> str:
        """
        Encode *result_img* as PNG, upload to Supabase Storage, and return
        the storage path.

        Storage path format:
            gradcam-results/{user_id}/{screening_id}.png

        If Supabase is unavailable the image is saved to the system temp
        directory and the local path is returned instead.

        Parameters
        ----------
        result_img : np.ndarray
            BGR image array to save.
        user_id : str
        screening_id : str

        Returns
        -------
        str
            Supabase storage path or local temp-file path.
        """
        storage_path = f"{user_id}/{screening_id}.png"

        # Encode image to PNG bytes in memory (no temp file needed for upload)
        success, buffer = cv2.imencode(".png", result_img)
        if not success:
            raise RuntimeError("cv2.imencode failed – could not encode Grad-CAM image.")

        png_bytes = buffer.tobytes()

        # ----------------------------------------------------------------
        # Upload to Supabase Storage
        # ----------------------------------------------------------------
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
            try:
                supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)
                supabase.storage.from_(GRADCAM_BUCKET).upload(
                    path=storage_path,
                    file=png_bytes,
                    file_options={"content-type": "image/png"},
                )
                full_path = f"{GRADCAM_BUCKET}/{storage_path}"
                logger.info("Grad-CAM uploaded to Supabase: %s", full_path)
                return full_path
            except Exception as exc:
                logger.error("Supabase upload failed: %s. Saving locally.", exc)

        # ----------------------------------------------------------------
        # Fallback: save to temp directory
        # ----------------------------------------------------------------
        tmp_dir = Path(tempfile.gettempdir()) / "safeskin_gradcam" / user_id
        tmp_dir.mkdir(parents=True, exist_ok=True)
        local_path = tmp_dir / f"{screening_id}.png"
        with open(local_path, "wb") as fh:
            fh.write(png_bytes)
        logger.info("Grad-CAM saved locally: %s", local_path)
        return str(local_path)

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    def _load_image(
        self, image_path: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load an image, return both the original BGR array and the
        pre-processed float32 array ready for model inference.

        Returns
        -------
        (original_bgr, preprocessed_batch)
        """
        img_bgr = cv2.imread(str(image_path))
        if img_bgr is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, IMG_SIZE)
        img_float = img_resized.astype(np.float32) / 255.0
        img_batch = np.expand_dims(img_float, axis=0)  # (1, 224, 224, 3)

        return img_bgr, img_batch
