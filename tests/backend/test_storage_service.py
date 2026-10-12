import pytest
from unittest.mock import MagicMock
from app.services.storage_service import StorageService


def test_generate_asset_path_valid():
    """Verify ownership-aware asset path structure matches DataModelSpecification."""
    service = StorageService()

    path = service.generate_asset_path(
        user_id="user-123",
        analysis_id="analysis-456",
        category="original",
        filename="input.jpg"
    )
    assert path == "analysis/user-123/analysis-456/original/input.jpg"

    mask_path = service.generate_binary_mask_path("user-123", "analysis-456")
    assert mask_path == "analysis/user-123/analysis-456/segmentation/mask.png"

    overlay_path = service.generate_segmentation_overlay_path("user-123", "analysis-456")
    assert overlay_path == "analysis/user-123/analysis-456/segmentation/overlay.png"

    heatmap_path = service.generate_gradcam_heatmap_path("user-123", "analysis-456")
    assert heatmap_path == "analysis/user-123/analysis-456/gradcam/heatmap.png"

    gradcam_overlay = service.generate_gradcam_overlay_path("user-123", "analysis-456")
    assert gradcam_overlay == "analysis/user-123/analysis-456/gradcam/overlay.png"


def test_get_analysis_asset_paths_completeness():
    """Verify that all 5 required asset paths are returned with consistent structure."""
    service = StorageService()
    paths = service.get_analysis_asset_paths("usr-1", "anl-2", original_extension="png")

    assert set(paths.keys()) == {
        "original_image_path",
        "binary_mask_path",
        "segmentation_overlay_path",
        "gradcam_heatmap_path",
        "gradcam_overlay_path",
    }
    assert paths["original_image_path"] == "analysis/usr-1/anl-2/original/input.png"
    assert paths["binary_mask_path"] == "analysis/usr-1/anl-2/segmentation/mask.png"
    assert paths["segmentation_overlay_path"] == "analysis/usr-1/anl-2/segmentation/overlay.png"
    assert paths["gradcam_heatmap_path"] == "analysis/usr-1/anl-2/gradcam/heatmap.png"
    assert paths["gradcam_overlay_path"] == "analysis/usr-1/anl-2/gradcam/overlay.png"


def test_sanitize_id_prevents_path_traversal():
    """Verify that path traversal characters in user_id or analysis_id are rejected."""
    service = StorageService()

    for invalid in ['../user', 'user/sub', '..\\admin', ' ']:
        with pytest.raises(ValueError, match="Invalid identifier"):
            service.sanitize_id(invalid)


def test_validate_path_ownership():
    """Verify validate_path_ownership enforces strict user isolation."""
    service = StorageService()

    valid_path = "analysis/user-123/analysis-456/original/input.jpg"
    assert service.validate_path_ownership(valid_path, "user-123") is True
    assert service.validate_path_ownership(valid_path, "user-999") is False

    # Path traversal attack attempt
    tampered_path = "analysis/user-999/analysis-456/original/input.jpg"
    assert service.validate_path_ownership(tampered_path, "user-123") is False


def test_upload_file_enforces_ownership():
    """Uploading a file to a path belonging to another user must raise PermissionError."""
    service = StorageService()

    tampered_path = "analysis/victim-user/analysis-456/original/input.jpg"

    with pytest.raises(PermissionError, match="does not belong to the authenticated user"):
        service.upload_file(
            path=tampered_path,
            file_bytes=b"fake-bytes",
            content_type="image/jpeg",
            user_id="attacker-user"
        )


def test_create_signed_url_success():
    """Verify signed URL creation delegates to Supabase Storage client."""
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_bucket = MagicMock()

    mock_client.storage = mock_storage
    mock_storage.from_.return_value = mock_bucket
    mock_bucket.create_signed_url.return_value = {
        "signedURL": "https://supabase.co/storage/v1/object/sign/analysis-assets/analysis/usr/anl/img.jpg?token=abc"
    }

    service = StorageService(client=mock_client, bucket_name="analysis-assets")
    path = "analysis/usr-1/anl-1/original/input.jpg"

    signed_url = service.create_signed_url(path, expires_in=1800, user_id="usr-1")

    assert "https://supabase.co/storage" in signed_url
    mock_storage.from_.assert_called_with("analysis-assets")
    mock_bucket.create_signed_url.assert_called_with(path, 1800)


def test_delete_analysis_files_rejects_foreign_paths():
    """Batch deletion must refuse to remove assets owned by another user."""
    service = StorageService()

    with pytest.raises(PermissionError, match="does not belong to the authenticated user"):
        service.delete_analysis_files(
            paths=[
                "analysis/user-a/a-1/original/input.jpg",
                "analysis/user-b/b-9/original/input.jpg",
            ],
            user_id="user-a",
        )


def test_delete_analysis_files_removes_all_owned_paths():
    """Batch deletion must remove every owned path in a single call."""
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_bucket = MagicMock()

    mock_client.storage = mock_storage
    mock_storage.from_.return_value = mock_bucket
    mock_bucket.remove.return_value = ["removed-1", "removed-2"]

    service = StorageService(client=mock_client, bucket_name="analysis-assets")
    paths = [
        "analysis/usr-1/anl-1/original/input.jpg",
        "analysis/usr-1/anl-1/segmentation/mask.png",
    ]

    assert service.delete_analysis_files(paths, user_id="usr-1") is True
    mock_storage.from_.assert_called_with("analysis-assets")
    mock_bucket.remove.assert_called_once_with(paths)
