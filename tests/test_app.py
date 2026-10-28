import asyncio
import io
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.config import Settings
from backend.detector import DamageDetector, DetectorBusy
from backend.main import UploadLimit, create_app
from backend.pricing import estimate


def picture(fmt="PNG", size=(100, 60), orientation=None):
    stream = io.BytesIO()
    image = Image.new("RGB", size, "#dde4da")
    kwargs = {}
    if orientation:
        exif = Image.Exif()
        exif[274] = orientation
        kwargs["exif"] = exif
    image.save(stream, format=fmt, **kwargs)
    return stream.getvalue()


@pytest.fixture
def client():
    with TestClient(create_app(Settings(demo=True))) as client:
        yield client


def upload(client, data=None, make="Hyundai", model="i20", description="", filename="car.png"):
    return client.post("/predict", data={"car_make": make, "car_model": model, "description": description},
                       files={"file": (filename, picture() if data is None else data, "image/png")})


def test_home_and_assets(client):
    assert "AutoQuote" in client.get("/").text
    for asset in ["app.js", "style.css"]:
        assert client.get(f"/static/{asset}").status_code == 200


def test_vehicle_list_and_demo_status(client):
    assert "Swift" in client.get("/api/vehicles").json()["Maruti"]
    assert client.get("/api/health").json()["mode"] == "demo"


def test_estimate_uses_vehicle_and_notes(client):
    response = upload(client, description="Headlight looks damaged")
    assert response.status_code == 200
    body = response.json()
    assert body["total_cost"] == 5000
    assert body["mode"] == "demo"
    assert body["image"] == {"width": 100, "height": 60}
    assert body["description"] == "Headlight looks damaged"
    assert body["detections"][0]["class_name"] == "front_bumper_dent"  # Notes never rewrite labels.


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_supported_images(client, fmt):
    assert upload(client, picture(fmt)).status_code == 200


@pytest.mark.parametrize("data,code", [(b"", 400), (b"not an image", 400), (picture("GIF"), 415)])
def test_invalid_images(client, data, code):
    assert upload(client, data).status_code == code


def test_corrupt_image(client):
    assert upload(client, picture()[:25]).status_code == 400


def test_animated_image(client):
    stream = io.BytesIO()
    Image.new("RGB", (5, 5), "red").save(stream, format="PNG", save_all=True,
        append_images=[Image.new("RGB", (5, 5), "blue")], duration=100, loop=0)
    assert upload(client, stream.getvalue()).status_code == 415


def test_exif_orientation(client):
    body = upload(client, picture("JPEG", (80, 40), orientation=6)).json()
    assert body["image"] == {"width": 40, "height": 80}


@pytest.mark.parametrize("make,model", [("Fake", "i20"), ("Honda", "i20"), ("", "")])
def test_invalid_vehicle(client, make, model):
    assert upload(client, make=make, model=model).status_code == 422


def test_missing_file(client):
    assert client.post("/predict", data={"car_make": "Hyundai", "car_model": "i20"}).status_code == 422


def test_notes_limit(client):
    assert upload(client, description="x" * 1001).status_code == 422


def test_pixel_limit():
    with TestClient(create_app(replace(Settings(demo=True), max_image_pixels=100))) as client:
        assert upload(client).status_code == 413


def test_file_size_limit():
    with TestClient(create_app(replace(Settings(demo=True), max_upload_bytes=100))) as client:
        assert upload(client, b"x" * 101).status_code == 413


def test_request_size_limit():
    with TestClient(create_app(replace(Settings(demo=True), max_upload_bytes=100))) as client:
        assert upload(client, b"x" * 70_000).status_code == 413


def test_chunked_request_limit():
    called = False
    messages = []
    chunks = iter([{"type": "http.request", "body": b"abcd", "more_body": True},
                   {"type": "http.request", "body": b"efgh", "more_body": False}])
    async def downstream(scope, receive, send):
        nonlocal called
        while True:
            message = await receive()
            if not message.get("more_body"):
                called = True
                break
    async def receive():
        return next(chunks)
    async def send(message):
        messages.append(message)
    asyncio.run(UploadLimit(downstream, limit=6)({"type": "http"}, receive, send))
    assert not called
    assert messages[0]["status"] == 413


def test_model_missing_does_not_return_fake_results(tmp_path):
    with TestClient(create_app(Settings(model_path=tmp_path / "absent.pt"))) as client:
        assert client.get("/api/health").json()["model_status"] == "missing"
        assert upload(client).status_code == 503


def test_busy_model_retries():
    class Busy:
        status = "loaded"
        def predict(self, image):
            raise DetectorBusy("Try again shortly")
    with TestClient(create_app(detector=Busy())) as client:
        response = upload(client)
        assert response.status_code == 503
        assert response.headers["retry-after"] == "3"


def test_model_errors_do_not_expose_paths():
    class Broken:
        status = "loaded"
        def predict(self, image):
            raise RuntimeError("private path or internal traceback")
    with TestClient(create_app(detector=Broken())) as client:
        response = upload(client)
        assert response.status_code == 500
        assert "private path" not in response.text


def test_no_detections():
    class Empty:
        status = "loaded"
        def predict(self, image):
            return []
    with TestClient(create_app(detector=Empty())) as client:
        body = upload(client).json()
        assert body["detections"] == []
        assert body["items"] == []
        assert body["total_cost"] == 0


def test_filename_is_never_used_as_storage_path(client, tmp_path):
    filename = str(tmp_path / "injected.png")
    assert upload(client, filename=filename).status_code == 200
    assert not (tmp_path / "injected.png").exists()


def test_confidence_does_not_change_prices():
    low = estimate([{"class_name": "scratch", "confidence": .4}], "Maruti", "Swift")
    high = estimate([{"class_name": "scratch", "confidence": .99}], "Maruti", "Swift")
    assert low["total_cost"] == high["total_cost"] == 1200


def test_repeated_labels_are_grouped():
    result = estimate([{"class_name": "scratch"}] * 3, "Hyundai", "i20")
    assert result["total_cost"] == 1500
    assert result["items"][0]["detection_count"] == 3


def test_unknown_prices_are_not_invented():
    result = estimate([{"class_name": "roof_dent"}], "Honda", "City")
    assert result["total_cost"] == 0
    assert result["unpriced_count"] == 1
    assert result["items"][0]["estimated_cost"] is None


def test_generic_price_is_marked():
    result = estimate([{"class_name": "scratch"}], "Honda", "City")
    assert result["items"][0]["price_basis"] == "generic sample"


def test_model_lock_returns_busy(tmp_path):
    detector = DamageDetector(tmp_path / "absent.pt", .4)
    detector._lock.acquire()
    try:
        with pytest.raises(DetectorBusy):
            detector.predict(Image.new("RGB", (5, 5)))
    finally:
        detector._lock.release()
