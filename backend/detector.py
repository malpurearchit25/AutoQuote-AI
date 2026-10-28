import threading
from pathlib import Path

from PIL import Image


class ModelUnavailable(RuntimeError):
    pass


class DetectorBusy(RuntimeError):
    pass


class DamageDetector:
    """Loads only the configured local checkpoint; serializes model access."""

    def __init__(self, path: Path, confidence: float):
        self.path = path
        self.confidence = confidence
        self._model = None
        self._lock = threading.Lock()

    @property
    def status(self):
        return "loaded" if self._model is not None else "available" if self.path.is_file() else "missing"

    def predict(self, image: Image.Image):
        if not self._lock.acquire(blocking=False):
            raise DetectorBusy("Another image is being analysed. Please try again shortly.")
        try:
            if self._model is None:
                if not self.path.is_file():
                    raise ModelUnavailable("Damage model is missing. Follow the model setup instructions in README.md.")
                try:
                    from ultralytics import YOLO
                    self._model = YOLO(str(self.path), task="detect")
                except Exception as exc:
                    raise ModelUnavailable("Could not load the damage model. Check the ML dependencies and checkpoint.") from exc
            result = self._model.predict(source=image, conf=self.confidence, imgsz=640,
                                         max_det=100, verbose=False, save=False)[0]
            return [{
                "class_name": str(result.names[int(box.cls[0])]),
                "confidence": round(float(box.conf[0]), 4),
                "bbox": [round(float(value), 2) for value in box.xyxy[0]],
            } for box in result.boxes]
        finally:
            self._lock.release()


class DemoDetector:
    """Fixed sample results for trying the UI; never presented as image analysis."""

    status = "demo"

    def predict(self, image: Image.Image):
        width, height = image.size
        return [{"class_name": "front_bumper_dent", "confidence": 0.87,
                 "bbox": [width * .15, height * .55, width * .8, height * .85]},
                {"class_name": "scratch", "confidence": .73,
                 "bbox": [width * .5, height * .3, width * .85, height * .5]}]
