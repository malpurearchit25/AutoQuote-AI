import io
import logging
import warnings

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from .config import ROOT, Settings
from .detector import DamageDetector, DemoDetector, DetectorBusy, ModelUnavailable
from .pricing import VEHICLES, estimate

logger = logging.getLogger(__name__)


class UploadLimit:
    """Limit bytes as ASGI receives them, including chunked multipart requests."""

    def __init__(self, app, limit):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        # Bound the body before the multipart parser can spool an oversized file.
        # Pre-reading also avoids the parser converting our size exception to 400.
        chunks = []
        received = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            received += len(chunk)
            if received > self.limit:
                return await JSONResponse(
                    {"detail": "Upload is too large. Maximum image size is 10 MB."},
                    status_code=413)(scope, receive, send)
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        chunks.clear()
        delivered = False

        async def bounded_receive():
            nonlocal delivered, body
            if not delivered:
                delivered = True
                message = {"type": "http.request", "body": body, "more_body": False}
                body = b""
                return message
            return await receive()

        await self.app(scope, bounded_receive, send)


def decode_image(data: bytes, settings: Settings):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise HTTPException(415, "Use a JPEG, PNG or WebP image.")
                if source.width * source.height > settings.max_image_pixels:
                    raise HTTPException(413, "Image exceeds the 20 megapixel limit.")
                if getattr(source, "n_frames", 1) > 1:
                    raise HTTPException(415, "Use a still image, not an animation.")
                source.load()
                return ImageOps.exif_transpose(source).convert("RGB")
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise HTTPException(413, "Image dimensions are too large.") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "This file is not a readable image. Choose another image.") from exc


def create_app(settings: Settings | None = None, detector=None):
    settings = settings or Settings.from_env()
    app = FastAPI(title="AutoQuote AI", version="1.0.0",
                  description="Car damage detection with illustrative repair estimates in INR.")
    app.add_middleware(UploadLimit, limit=settings.max_upload_bytes + 64 * 1024)
    engine = detector if detector is not None else (
        DemoDetector() if settings.demo else DamageDetector(settings.model_path, settings.confidence))

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "demo" if settings.demo else "model",
                "model_status": engine.status}

    @app.get("/api/vehicles")
    def vehicles():
        return VEHICLES

    @app.post("/predict")
    async def predict(file: UploadFile = File(...), car_make: str = Form(..., max_length=60),
                      car_model: str = Form(..., max_length=60),
                      description: str = Form("", max_length=1000)):
        try:
            if car_make not in VEHICLES or car_model not in VEHICLES[car_make]:
                raise HTTPException(422, "Choose a supported manufacturer and model.")
            data = await file.read(settings.max_upload_bytes + 1)
            if len(data) > settings.max_upload_bytes:
                raise HTTPException(413, "Upload is too large. Maximum image size is 10 MB.")
            if not data:
                raise HTTPException(400, "The uploaded image is empty.")
            image = await run_in_threadpool(decode_image, data, settings)
            try:
                detections = await run_in_threadpool(engine.predict, image)
                return {"mode": "demo" if settings.demo else "model",
                        "detections": detections, "image": {"width": image.width, "height": image.height},
                        "car_info": {"make": car_make, "model": car_model},
                        "description": description.strip(),
                        **estimate(detections, car_make, car_model)}
            finally:
                image.close()
        except ModelUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        except DetectorBusy as exc:
            raise HTTPException(503, str(exc), headers={"Retry-After": "3"}) from exc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Image analysis failed")
            raise HTTPException(500, "Analysis failed. Please try again or check the server log.") from exc
        finally:
            await file.close()

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(ROOT / "frontend/index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")
    return app


app = create_app()
