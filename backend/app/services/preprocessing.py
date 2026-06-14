from pathlib import Path


class ImagePreprocessor:
    """Best-effort image cleanup before OCR.

    OpenCV is optional in minimal local environments. When present, this normalizes common
    label-photo problems without changing the original upload.
    """

    def preprocess(self, image_path: Path) -> Path:
        try:
            import cv2
            import numpy as np
        except Exception:
            return image_path

        image = cv2.imread(str(image_path))
        if image is None:
            return image_path

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Normalize broad lighting variation and modest glare before enhancing label text.
        illumination_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
        illumination = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, illumination_kernel)
        normalized = cv2.divide(gray, illumination, scale=255)
        denoised = cv2.fastNlMeansDenoising(normalized, h=10)
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )

        coords = np.column_stack(np.where(binary < 255))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            angle = -(90 + angle) if angle < -45 else -angle
            if abs(angle) > 0.5:
                h, w = binary.shape[:2]
                matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                binary = cv2.warpAffine(
                    binary,
                    matrix,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )

        processed_path = image_path.with_name(f"{image_path.stem}.processed.png")
        cv2.imwrite(str(processed_path), binary)
        return processed_path
