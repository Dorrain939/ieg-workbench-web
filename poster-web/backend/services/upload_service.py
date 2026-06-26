from backend.core.paths import UPLOADS_DIR


class UploadService:
    @property
    def root(self):
        return UPLOADS_DIR
