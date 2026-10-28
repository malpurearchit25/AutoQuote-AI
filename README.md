# AutoQuote AI

**Car damage detection with an itemised, illustrative repair estimate in INR.**

AutoQuote AI is an academic computer-vision project built with FastAPI, a custom-trained YOLOv8 checkpoint, and a lightweight HTML/CSS/JavaScript interface. Upload a vehicle photo, view damage markers, choose a vehicle, and download a readable assessment report.

## Features

- Responsive interface with drag-and-drop upload, image preview and numbered damage markers.
- Local YOLO inference with lazy loading and serialized model access.
- Vehicle-specific sample prices for Hyundai i20 and Maruti Swift, plus clearly labelled generic sample prices.
- Unknown prices flagged for inspection; repeated damage labels grouped into one provisional item.
- Image validation, 10 MB upload limit, 20 MP decoded-image limit and EXIF orientation correction.
- Clear loading, empty, failure and missing-model states; stale requests cannot overwrite a newer selection.
- Downloadable text report with vehicle details, notes, cost breakdown and estimate limitations.
- Explicit demo mode that works without model dependencies or weights.
- Backend regression tests and automated checks on Windows and Linux.

## Quick start: try the demo

Use **Python 3.11 or 3.12**. From the project root:

```sh
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```sh
# macOS / Linux
source .venv/bin/activate
```

Then run:

```sh
python -m pip install -r requirements.txt
python -m backend --demo
```

Open **http://127.0.0.1:8000**. Pick a manufacturer and model, add an image and choose **Show sample assessment**.

**Demo mode returns fixed sample detections. It does not analyse the content of the image.** The banner, results and downloaded report identify this mode explicitly. Without `--demo`, the application never substitutes dummy results for a missing model.

If PowerShell activation is unavailable, run `.venv\Scripts\python.exe` instead of `python` in the remaining commands; changing system execution policy is unnecessary.

## Run real image analysis

1. Install the ML dependencies:

   ```sh
   python -m pip install -r requirements-ml.txt
   ```

2. Place the trusted trained damage checkpoint at `models/damage.pt`. If you have the original project archive, use:

   ```sh
   python scripts/import_model.py "path/to/Complete ASEP.zip"
   ```

   This imports `Complete ASEP/asep/last.pt`. The prepared local project already has this file. It is excluded from Git and the source ZIP. A generic `yolov8n.pt` object detector is not a replacement for the damage-trained model.

3. Start the application:

   ```sh
   python -m backend
   ```

The first prediction loads the model and can take longer. The checkpoint was created with Ultralytics **8.3.240**, so the ML requirements retain that version. See [model notes](models/README.md) for provenance and limitations.

For a different checkpoint location, set `AUTOQUOTE_MODEL_PATH` in the environment. Relative paths resolve from the project root. `AUTOQUOTE_DEMO=1` also enables demo mode. `.env.example` documents the settings; `.env` is not automatically loaded.

## Pricing behaviour

Prices come from the original project's illustrative tables, **not live workshop data**. There is no validated severity model. Prediction confidence never increases or decreases the price. A text note is included in the report and never silently relabels model detections.

Multiple regions with the same damage label are billed once in this provisional estimate. This avoids simply charging for every bounding box, but separate damaged panels may need separate repairs. Unknown damage types receive `null` for their price and are excluded from the priced subtotal. No detections means no estimate is available, not a guarantee of no damage.

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The default suite uses explicit test detectors, needs no checkpoint and covers API behaviour, validation, image orientation, pricing, concurrency failure and model-unavailable responses. This is software regression coverage, not a measurement of model accuracy. GitHub Actions runs it across Python 3.11/3.12 on Windows/Linux and checks frontend JavaScript syntax. See [validation notes](docs/VALIDATION.md) for completed checks and an observed model misclassification.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Web interface |
| `GET /api/health` | Service mode and checkpoint state (`missing`, `available`, `loaded`, or `demo`) |
| `GET /api/vehicles` | Supported manufacturer/model choices |
| `POST /predict` | Multipart `file`, `car_make`, `car_model`, optional `description` |
| `GET /docs` | Interactive FastAPI API reference |

`available` means the checkpoint exists; the first inference verifies it can load. The response contains detections, oriented image dimensions, grouped price items, the priced subtotal, unpriced count, vehicle details, notes and a disclaimer.

## Structure

```text
backend/          API, validation, model adapter and pricing
frontend/         Browser interface (served by FastAPI)
models/           Model notes; local damage.pt is ignored by Git
scripts/          Import helper for the original checkpoint
tests/            API and pricing regression tests
docs/             Architecture and change notes
```

## Scope

This is a local academic prototype. The app does not retain submitted photos, although the request parser may temporarily spool data while processing. It has no user accounts, public-service rate limits or production deployment configuration. Run locally using the default loopback address. Model inference is single-request-at-a-time; another request receives a retry message.

The supplied archive does not include training data, reproducible training code or a held-out evaluation set. Detection accuracy and repair estimates have not been independently validated. Hidden damage, roadworthiness, taxes and extra labour are outside the assessment. Confirm findings and final prices with a workshop.

See [third-party notices](THIRD_PARTY_NOTICES.md) for dependency and checkpoint licensing information.
