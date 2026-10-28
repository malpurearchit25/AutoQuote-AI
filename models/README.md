# Trained damage model

The original archive includes `asep/last.pt`, a YOLOv8s damage checkpoint. The application expects it at `models/damage.pt`; a copy is present in the prepared local project. Model binaries are excluded from Git and the source ZIP. The lightweight demo runs without them.

Import from the original archive with `python scripts/import_model.py "path/to/Complete ASEP.zip"`, or copy a trusted checkpoint manually. Do not substitute the archive's generic `yolov8n.pt`, which detects common objects rather than the custom damage classes.

Metadata in the supplied checkpoint records:

- Date: 2025-12-19.
- Ultralytics version: 8.3.240.
- Base model name: `yolov8s.pt`.
- Embedded license marker: `AGPL-3.0 (https://ultralytics.com/license)`.
- 15 classes: scratch, front/rear bumper dent, quarter-panel dent, outer-door dent, headlight damage, running-board damage, taillight damage, fender dent, bonnet dent, boot dent, side-mirror damage, front/rear windscreen damage and roof dent.

The archive contains no dataset, model card with evaluation metrics, or training script. The project therefore makes no accuracy claims. Loading and executing the checkpoint verifies integration only.

Only load checkpoints you trust: `.pt` model files may contain serialized Python objects. No model is accepted through the image-upload API, and missing weights never trigger a download of an unrelated detector.
