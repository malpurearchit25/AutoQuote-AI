# Improvements from the original archive

- Consolidated duplicate FastAPI entry points and frontend copies into one application.
- Replaced absolute Mac paths with project-relative or environment-configured model paths.
- Removed automatic generic-model substitution and dummy detections from normal operation.
- Preserved the trained checkpoint locally and added an explicit model import helper.
- Removed bundled virtual environments, caches, redundant archives and historic uploaded images from the publishable project.
- Rebuilt the interface with responsive layout, labelled controls, clear error states and visible demo indicators.
- Implemented drag-and-drop, manufacturer/model selection, actual notes submission and report downloads.
- Redraws overlays on resize; clears stale results when image, vehicle or notes change.
- Prevents duplicate submissions and ignores stale responses after selection changes.
- Added bounded request handling, file-content validation, image pixel limits and orientation correction.
- Keeps predictions separate from notes and avoids using confidence as damage severity.
- Groups repeated labels and flags missing prices instead of assigning arbitrary fallbacks.
- Added dependency files, setup instructions, API documentation, regression tests and GitHub Actions.

The original archive is unchanged. Model accuracy and the market validity of the illustrative prices have not been established by these changes.
