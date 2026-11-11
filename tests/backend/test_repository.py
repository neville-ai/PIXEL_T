import pytest
from unittest.mock import MagicMock
from src.repositories.analysis_repository import AnalysisRepository


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client for testing repository operations without live database."""
    client = MagicMock()
    return client


def test_status_validation():
    """Verify that only specified lifecycle statuses are allowed."""
    repo = AnalysisRepository()

    # Allowed statuses
    for s in ['processing', 'completed', 'failed']:
        repo.validate_lifecycle_status(s)

    # Disallowed / non-clinical statuses must raise ValueError
    for invalid in ['diagnosed', 'confirmed', 'malignant', 'benign', 'pending', 'started']:
        with pytest.raises(ValueError, match="Invalid analysis status"):
            repo.validate_lifecycle_status(invalid)


def test_segmentation_status_validation():
    """Verify that segmentation_status accepts strictly 'detected' or 'not_detected'."""
    repo = AnalysisRepository()

    repo.validate_segmentation_status(None)
    repo.validate_segmentation_status('detected')
    repo.validate_segmentation_status('not_detected')

    for invalid in ['segmented_region', 'no_segmented_region', 'unknown', 'positive', 'negative']:
        with pytest.raises(ValueError, match="Invalid segmentation status"):
            repo.validate_segmentation_status(invalid)


def test_create_analysis(mock_supabase):
    """Verify analysis creation properly scopes to user_id and inserts into analyses table."""
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "analysis-123",
        "user_id": "user-456",
        "status": "processing",
        "original_image_path": "analysis/user-456/analysis-123/original/input.jpg"
    }]

    repo = AnalysisRepository(client=mock_supabase)
    result = repo.create(
        user_id="user-456",
        data={
            "original_image_path": "analysis/user-456/analysis-123/original/input.jpg",
            "original_filename": "colonoscopy.jpg"
        }
    )

    assert result["id"] == "analysis-123"
    assert result["user_id"] == "user-456"
    assert result["status"] == "processing"

    mock_supabase.table.assert_called_with("analyses")
    mock_table.insert.assert_called_once()
    payload = mock_table.insert.call_args[0][0]
    assert payload["user_id"] == "user-456"
    assert payload["status"] == "processing"


def test_create_analysis_requires_user_id():
    """Creating an analysis without user_id must raise ValueError."""
    repo = AnalysisRepository()
    with pytest.raises(ValueError, match="user_id is required"):
        repo.create(user_id="", data={"original_image_path": "path"})


def test_get_by_id_enforces_user_ownership(mock_supabase):
    """Retrieving an analysis must filter by both analysis_id AND user_id."""
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "analysis-123",
        "user_id": "user-456",
        "status": "completed"
    }]

    repo = AnalysisRepository(client=mock_supabase)
    record = repo.get_by_id("analysis-123", "user-456")

    assert record is not None
    assert record["id"] == "analysis-123"

    # Verify query filtered by id and user_id
    mock_select.eq.assert_called_with("id", "analysis-123")
    mock_eq1.eq.assert_called_with("user_id", "user-456")


def test_update_analysis_prevents_user_id_mutation(mock_supabase):
    """Updating an analysis must not mutate id or user_id, and must enforce ownership."""
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "analysis-123",
        "user_id": "user-456",
        "status": "completed",
        "segmentation_status": "detected"
    }]

    repo = AnalysisRepository(client=mock_supabase)
    updated = repo.update(
        analysis_id="analysis-123",
        user_id="user-456",
        data={
            "id": "tampered-id",
            "user_id": "tampered-user",
            "status": "completed",
            "segmentation_status": "detected",
            "area_pixels": 5000
        }
    )

    assert updated is not None
    mock_table.update.assert_called_once()
    sent_payload = mock_table.update.call_args[0][0]
    # Ensure id and user_id were stripped from update payload
    assert "id" not in sent_payload
    assert "user_id" not in sent_payload
    assert sent_payload["status"] == "completed"
    assert sent_payload["segmentation_status"] == "detected"


def test_delete_analysis_scoped_to_user(mock_supabase):
    """Deleting an analysis must be scoped strictly to the authenticated user."""
    mock_table = MagicMock()
    mock_delete = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.delete.return_value = mock_delete
    mock_delete.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_execute
    mock_execute.data = [{"id": "analysis-123"}]

    repo = AnalysisRepository(client=mock_supabase)
    success = repo.delete("analysis-123", "user-456")

    assert success is True
    mock_delete.eq.assert_called_with("id", "analysis-123")
    mock_eq1.eq.assert_called_with("user_id", "user-456")


def test_list_by_user_scopes_to_user_with_order_and_range(mock_supabase):
    """Listing history must filter by user_id, order newest first, and page."""
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_order = MagicMock()
    mock_range = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.order.return_value = mock_order
    mock_order.range.return_value = mock_range
    mock_range.execute.return_value = mock_execute
    mock_execute.data = [{"id": "analysis-123", "user_id": "user-456"}]

    repo = AnalysisRepository(client=mock_supabase)
    records = repo.list_by_user("user-456", limit=20, offset=0)

    assert records == [{"id": "analysis-123", "user_id": "user-456"}]
    mock_supabase.table.assert_called_with("analyses")
    mock_select.eq.assert_called_with("user_id", "user-456")
    mock_eq.order.assert_called_with("created_at", desc=True)
    mock_order.range.assert_called_with(0, 19)


def test_list_by_user_requires_user_id():
    """Listing history without user_id must return an empty list."""
    repo = AnalysisRepository()
    assert repo.list_by_user("") == []
