from typing import Optional, Dict, List
import re
from app.core.config import get_config
from app.core.supabase import get_supabase_client


class StorageService:
    """Service handling Supabase Storage asset paths and operations for PIXEL-T.

    Enforces ownership-aware folder paths conforming to docs/DataModelSpecification.md:
        analysis/{user_id}/{analysis_id}/{category}/{filename}
    """

    ALLOWED_CATEGORIES = {'original', 'segmentation', 'gradcam'}

    def __init__(self, client=None, bucket_name: Optional[str] = None):
        """Initialize storage service with optional client and bucket name."""
        self._client = client
        config = get_config()
        self.bucket_name = bucket_name or getattr(config, 'SUPABASE_STORAGE_BUCKET', 'analysis-assets')

    def _get_client(self, use_service_role: bool = False):
        if self._client is not None:
            return self._client
        return get_supabase_client(use_service_role=use_service_role)

    # -------------------------------------------------------------------------
    # Path Generation & Ownership Security
    # -------------------------------------------------------------------------

    @staticmethod
    def sanitize_id(identifier: str) -> str:
        """Sanitize identifiers to prevent path traversal."""
        clean = str(identifier).strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", clean) or ".." in clean:
            raise ValueError(f"Invalid identifier for storage path: '{identifier}'")
        return clean

    def generate_asset_path(
        self, user_id: str, analysis_id: str, category: str, filename: str
    ) -> str:
        """Generate an ownership-isolated asset path.

        Format: analysis/{user_id}/{analysis_id}/{category}/{filename}
        """
        clean_user = self.sanitize_id(user_id)
        clean_analysis = self.sanitize_id(analysis_id)
        clean_file = filename.strip()

        if category not in self.ALLOWED_CATEGORIES:
            raise ValueError(
                f"Invalid asset category '{category}'. Must be one of {sorted(self.ALLOWED_CATEGORIES)}."
            )
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", clean_file) or ".." in clean_file:
            raise ValueError(f"Invalid asset filename: '{filename}'")

        return f"analysis/{clean_user}/{clean_analysis}/{category}/{clean_file}"

    def generate_original_image_path(
        self, user_id: str, analysis_id: str, extension: str = "jpg"
    ) -> str:
        """Generate standard storage path for the original uploaded image."""
        ext = extension.lstrip('.').lower() or "jpg"
        if ext not in {"jpg", "png"}:
            raise ValueError("Original image extension must be 'jpg' or 'png'.")
        return self.generate_asset_path(user_id, analysis_id, "original", f"input.{ext}")

    def generate_binary_mask_path(self, user_id: str, analysis_id: str) -> str:
        """Generate standard storage path for the binary segmentation mask."""
        return self.generate_asset_path(user_id, analysis_id, "segmentation", "mask.png")

    def generate_segmentation_overlay_path(self, user_id: str, analysis_id: str) -> str:
        """Generate standard storage path for the colored segmentation contour overlay."""
        return self.generate_asset_path(user_id, analysis_id, "segmentation", "overlay.png")

    def generate_gradcam_heatmap_path(self, user_id: str, analysis_id: str) -> str:
        """Generate standard storage path for the Grad-CAM jet heatmap."""
        return self.generate_asset_path(user_id, analysis_id, "gradcam", "heatmap.png")

    def generate_gradcam_overlay_path(self, user_id: str, analysis_id: str) -> str:
        """Generate standard storage path for the Grad-CAM heatmap blended overlay."""
        return self.generate_asset_path(user_id, analysis_id, "gradcam", "overlay.png")

    def get_analysis_asset_paths(
        self, user_id: str, analysis_id: str, original_extension: str = "jpg"
    ) -> Dict[str, str]:
        """Generate the complete set of standardized asset paths for an analysis session."""
        return {
            "original_image_path": self.generate_original_image_path(user_id, analysis_id, original_extension),
            "binary_mask_path": self.generate_binary_mask_path(user_id, analysis_id),
            "segmentation_overlay_path": self.generate_segmentation_overlay_path(user_id, analysis_id),
            "gradcam_heatmap_path": self.generate_gradcam_heatmap_path(user_id, analysis_id),
            "gradcam_overlay_path": self.generate_gradcam_overlay_path(user_id, analysis_id),
        }

    def validate_path_ownership(self, path: str, user_id: str) -> bool:
        """Verify that a storage path belongs strictly to the specified user.

        Prevents cross-user data tampering or unauthorized access.
        """
        clean_user = self.sanitize_id(user_id)
        segments = path.split("/")
        if len(segments) != 5 or segments[0] != "analysis" or segments[1] != clean_user:
            return False
        try:
            self.sanitize_id(segments[2])
            if segments[3] not in self.ALLOWED_CATEGORIES:
                return False
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", segments[4]) or ".." in segments[4]:
                return False
        except ValueError:
            return False
        return True

    # -------------------------------------------------------------------------
    # Storage Bucket Operations
    # -------------------------------------------------------------------------

    def upload_file(
        self,
        path: str,
        file_bytes: bytes,
        content_type: str,
        user_id: Optional[str] = None,
        use_service_role: bool = False,
    ) -> str:
        """Upload raw binary bytes to the private storage bucket."""
        if user_id and not self.validate_path_ownership(path, user_id):
            raise PermissionError("Storage path does not belong to the authenticated user.")

        client = self._get_client(use_service_role=use_service_role)
        client.storage.from_(self.bucket_name).upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return path

    def download_file(
        self, path: str, user_id: Optional[str] = None, use_service_role: bool = False
    ) -> bytes:
        """Download binary bytes from the private storage bucket."""
        if user_id and not self.validate_path_ownership(path, user_id):
            raise PermissionError("Storage path does not belong to the authenticated user.")

        client = self._get_client(use_service_role=use_service_role)
        return client.storage.from_(self.bucket_name).download(path)

    def create_signed_url(
        self,
        path: str,
        expires_in: int = 3600,
        user_id: Optional[str] = None,
        use_service_role: bool = False,
    ) -> str:
        """Generate a time-limited signed URL for private asset access."""
        if user_id and not self.validate_path_ownership(path, user_id):
            raise PermissionError("Storage path does not belong to the authenticated user.")

        client = self._get_client(use_service_role=use_service_role)
        res = client.storage.from_(self.bucket_name).create_signed_url(path, expires_in)
        return res.get("signedURL") or res.get("signedUrl") or ""

    def delete_file(
        self, path: str, user_id: Optional[str] = None, use_service_role: bool = False
    ) -> bool:
        """Delete an asset from the private storage bucket."""
        if user_id and not self.validate_path_ownership(path, user_id):
            raise PermissionError("Storage path does not belong to the authenticated user.")

        client = self._get_client(use_service_role=use_service_role)
        res = client.storage.from_(self.bucket_name).remove([path])
        return bool(res and len(res) > 0)

    def delete_analysis_files(
        self,
        paths: List[str],
        user_id: Optional[str] = None,
        use_service_role: bool = False,
    ) -> bool:
        """Delete multiple assets associated with an analysis session."""
        if user_id:
            for p in paths:
                if not self.validate_path_ownership(p, user_id):
                    raise PermissionError(f"Storage path '{p}' does not belong to the authenticated user.")

        client = self._get_client(use_service_role=use_service_role)
        res = client.storage.from_(self.bucket_name).remove(paths)
        return bool(res and len(res) > 0)
