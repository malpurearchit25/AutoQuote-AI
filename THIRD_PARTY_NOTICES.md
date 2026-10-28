# Third-party notices

The optional inference integration uses [Ultralytics](https://github.com/ultralytics/ultralytics). Its package and the supplied checkpoint carry an AGPL-3.0 license marker; Ultralytics also describes other licensing options on its [official licensing page](https://www.ultralytics.com/license).

The checkpoint is retained locally and is not redistributed in this source repository. Its training-data provenance and any associated terms were not supplied in the archive. No new license is assigned to the original project's code or trained weights by this cleanup.

Other dependencies retain their own licenses, including FastAPI, Starlette, Pydantic, Uvicorn, Python Multipart, Pillow, PyTorch and the packages used for tests. Refer to each installed distribution's license files.

Implementation references:

- [FastAPI file uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Ultralytics image prediction](https://docs.ultralytics.com/modes/predict/)
- [Pillow EXIF orientation support](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.exif_transpose)
