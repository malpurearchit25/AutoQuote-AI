# Validation record

Checked locally on Windows with Python 3.12 on 2026-10-28.

## Software checks

- 31 automated regression tests passed.
- Frontend JavaScript syntax check passed.
- Python source compilation passed.
- Installed dependency consistency check passed (`pip check`).
- Browser checks covered selecting a vehicle, choosing a photo, demo assessment, changing the vehicle after results, price updates, downloaded report content, and responsive layout.
- At a 390-pixel viewport, the page had no horizontal overflow and the annotation canvas matched the displayed image width. Desktop layout was checked at 1280 pixels.
- No browser warnings/errors were recorded during those interaction checks.
- The existing checkpoint loaded successfully and real-model `POST /predict` returned HTTP 200. A blank-image inference returned no detections.

The test runner emitted a deprecation notice about Starlette's current `httpx` test-client adapter. It did not affect the passing results.

## Model-quality limits

The supplied `car1.jpg` smoke-test image showed a front-light area. The checkpoint returned `taillight_damage` for that region (approximately 0.87 confidence). This demonstrates that a high-confidence prediction can be incorrect. The software does not hide or heuristically rewrite the model's label.

This is a single integration check, not a benchmark. No held-out dataset or reproducible training pipeline was included. Improving the classifier requires labelled data, training and evaluation; the application refactor does not establish model accuracy. The sample image remains local and is excluded from the source repository.

Automated GitHub Actions are configured but will run only after upload.
