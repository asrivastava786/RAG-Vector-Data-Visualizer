from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings


class ObjectStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.minio_bucket
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as exc:
            raise RuntimeError("Object storage is unavailable.") from exc

    def put_bytes(self, key: str, payload: bytes, content_type: str) -> None:
        self.ensure_bucket()
        self.client.put_object(
            self.bucket,
            key,
            BytesIO(payload),
            length=len(payload),
            content_type=content_type,
        )

    def get_bytes(self, key: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as exc:
            raise RuntimeError("Unable to read document from object storage.") from exc

    def delete(self, key: str) -> None:
        try:
            self.client.remove_object(self.bucket, key)
        except S3Error:
            # Database deletion is source of truth for access; object cleanup is best effort.
            return


def get_object_storage() -> ObjectStorage:
    return ObjectStorage()
