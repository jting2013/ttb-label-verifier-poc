import time
from pathlib import Path

from app.models.schemas import FormatObservations, OCRResult
from app.services.parser import parse_label_fields
from app.services.preprocessing import ImagePreprocessor


DEMO_OCR_BY_FILENAME = {
    "valid_old_tom": ("""OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Bottled by Old Tom Distillery Co., Louisville, KY
Country of Origin: United States
GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.""", True),
    "invalid_warning": ("""OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Bottled by Old Tom Distillery Co., Louisville, KY
Country of Origin: United States
Government warning: pregnancy risk. Do not drink and drive.""", False),
    "rotated_blurry": ("""OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Bottled by Old Tom Distillery Co., Louisville, KY
Country of Origin: United States
GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.""", True),
}


class OCRService:
    def __init__(self, engine: str = "tesseract") -> None:
        self.engine = engine
        self.preprocessor = ImagePreprocessor()
        self._reader = None

    def extract(self, image_path: Path) -> OCRResult:
        started = time.perf_counter()
        processed_path = self.preprocessor.preprocess(image_path)
        text, confidence, raw_blocks, engine_used, format_observations = self._run_ocr(processed_path)
        processing_ms = int((time.perf_counter() - started) * 1000)
        return OCRResult(
            text=text,
            confidence=confidence,
            engine=engine_used,
            processing_ms=processing_ms,
            fields=parse_label_fields(text),
            format_observations=format_observations,
            raw_blocks=raw_blocks,
        )

    def extract_fixture(
        self,
        image_path: Path,
        text: str,
        warning_prefix_bold: bool | None,
    ) -> OCRResult:
        started = time.perf_counter()
        self.preprocessor.preprocess(image_path)
        processing_ms = int((time.perf_counter() - started) * 1000)
        return OCRResult(
            text=text,
            confidence=0.93,
            engine="sample-fixture",
            processing_ms=processing_ms,
            fields=parse_label_fields(text),
            format_observations=FormatObservations(
                government_warning_prefix_bold=warning_prefix_bold,
                source="controlled_fixture_manifest",
            ),
            raw_blocks=[{"text": text, "confidence": 0.93}],
        )

    def _run_ocr(self, image_path: Path) -> tuple[str, float, list[dict], str, FormatObservations]:
        if self.engine.lower() == "sample-fixture":
            return self._demo(image_path, engine_label="sample-fixture")
        if self.engine.lower() == "reject-unrecognized-demo":
            return "", 0.0, [], "demo-unrecognized", FormatObservations(source="demo_no_fixture_match")
        if self.engine.lower() == "easyocr":
            try:
                return self._easyocr(image_path)
            except Exception:
                return self._demo(image_path, fallback=True)
        if self.engine.lower() == "tesseract":
            try:
                return self._tesseract(image_path)
            except Exception:
                return self._demo(image_path, fallback=True)
        return self._demo(image_path)

    def _easyocr(self, image_path: Path) -> tuple[str, float, list[dict], str, FormatObservations]:
        import easyocr

        if self._reader is None:
            self._reader = easyocr.Reader(["en"], gpu=False)
        results = self._reader.readtext(str(image_path), detail=1, paragraph=False)
        lines = [item[1] for item in results]
        confidences = [float(item[2]) for item in results] or [0.0]
        blocks = [{"text": item[1], "confidence": float(item[2]), "bbox": item[0]} for item in results]
        return "\n".join(lines), sum(confidences) / len(confidences), blocks, "easyocr", FormatObservations()

    def _tesseract(self, image_path: Path) -> tuple[str, float, list[dict], str, FormatObservations]:
        import pytesseract
        from PIL import Image

        text = pytesseract.image_to_string(Image.open(image_path))
        return text, 0.72, [{"text": text, "confidence": 0.72}], "tesseract", FormatObservations()

    def _demo(
        self,
        image_path: Path,
        fallback: bool = False,
        engine_label: str | None = None,
    ) -> tuple[str, float, list[dict], str, FormatObservations]:
        stem = image_path.stem.replace(".processed", "")
        fixture = next((value for key, value in DEMO_OCR_BY_FILENAME.items() if key in stem), None)
        if not fixture:
            return "", 0.0, [], "demo-unrecognized", FormatObservations(source="demo_no_fixture_match")
        text, warning_prefix_bold = fixture
        engine = engine_label or ("demo-fallback" if fallback else "demo")
        return (
            text,
            0.93 if not fallback else 0.68,
            [{"text": text, "confidence": 0.93}],
            engine,
            FormatObservations(
                government_warning_prefix_bold=warning_prefix_bold,
                source="bundled_fixture_metadata",
            ),
        )
