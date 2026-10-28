import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    model_path: Path = ROOT / "models" / "damage.pt"
    demo: bool = False
    confidence: float = 0.40
    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 20_000_000

    @classmethod
    def from_env(cls):
        path = Path(os.getenv("AUTOQUOTE_MODEL_PATH", str(ROOT / "models/damage.pt")))
        if not path.is_absolute():
            path = ROOT / path
        return cls(model_path=path, demo=os.getenv("AUTOQUOTE_DEMO", "0") == "1")
