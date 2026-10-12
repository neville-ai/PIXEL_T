from typing import Optional, List, Dict, Any
from app.core.supabase import get_supabase_client


class AnalysisRepository:
    """Repository handling CRUD and persistence operations for the 'analyses' table.

    Enforces user ownership, lifecycle status constraints, and model metadata persistence
    conforming strictly to docs/DataModelSpecification.md.
    """

    ALLOWED_STATUSES = {'processing', 'completed', 'failed'}
    ALLOWED_SEGMENTATION_STATUSES = {'detected', 'not_detected'}

    def __init__(self, client=None):
        """Initialize repository with optional Supabase client (useful for dependency injection in tests)."""
        self._client = client

    def _get_client(self, use_service_role: bool = False):
        if self._client is not None:
            return self._client
        return get_supabase_client(use_service_role=use_service_role)

    def validate_lifecycle_status(self, status: str) -> None:
        """Ensure status matches the defined lifecycle state."""
        if status not in self.ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid analysis status '{status}'. Must be one of {sorted(self.ALLOWED_STATUSES)}."
            )

    def validate_segmentation_status(self, status: Optional[str]) -> None:
        """Ensure segmentation_status matches the model-derived specification."""
        if status is not None and status not in self.ALLOWED_SEGMENTATION_STATUSES:
            raise ValueError(
                f"Invalid segmentation status '{status}'. Must be one of {sorted(self.ALLOWED_SEGMENTATION_STATUSES)}."
            )

    def create(self, user_id: str, data: Dict[str, Any], use_service_role: bool = False) -> Dict[str, Any]:
        """Create a new analysis record scoped to the authenticated user.

        Args:
            user_id: Supabase Auth UUID of the owner.
            data: Analysis metadata payload.
            use_service_role: Whether to use service-role client for background operations.

        Returns:
            Dict: The inserted analysis record.
        """
        if not user_id:
            raise ValueError("user_id is required to create an analysis record.")

        record = dict(data)
        record["user_id"] = str(user_id)

        # Enforce lifecycle status default and validation
        status = record.get("status", "processing")
        self.validate_lifecycle_status(status)
        record["status"] = status

        # Enforce segmentation status validation if provided
        if "segmentation_status" in record and record["segmentation_status"] is not None:
            self.validate_segmentation_status(record["segmentation_status"])

        client = self._get_client(use_service_role=use_service_role)
        response = client.table("analyses").insert(record).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return record

    def get_by_id(
        self, analysis_id: str, user_id: str, use_service_role: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Retrieve an analysis record by ID, strictly verifying user ownership.

        Args:
            analysis_id: UUID of the analysis.
            user_id: Supabase Auth UUID of the requesting user.
            use_service_role: Whether to use service-role client.

        Returns:
            Optional[Dict]: The analysis record if found and owned by user, else None.
        """
        if not analysis_id or not user_id:
            return None

        client = self._get_client(use_service_role=use_service_role)
        response = (
            client.table("analyses")
            .select("*")
            .eq("id", str(analysis_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    def list_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        use_service_role: bool = False,
    ) -> List[Dict[str, Any]]:
        """List historical analyses belonging to a specific user, ordered newest first.

        Args:
            user_id: Supabase Auth UUID of the user.
            limit: Maximum records to return.
            offset: Pagination offset.
            use_service_role: Whether to use service-role client.

        Returns:
            List[Dict]: List of analysis records.
        """
        if not user_id:
            return []

        client = self._get_client(use_service_role=use_service_role)
        response = (
            client.table("analyses")
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return response.data or []

    def update(
        self,
        analysis_id: str,
        user_id: str,
        data: Dict[str, Any],
        use_service_role: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Update an analysis record, strictly verifying user ownership.

        Prevents modifying identity (id, user_id).
        Validates status transitions and segmentation values.
        """
        if not analysis_id or not user_id:
            return None

        updates = dict(data)
        # Prevent mutating identity or ownership
        updates.pop("id", None)
        updates.pop("user_id", None)

        if "status" in updates:
            self.validate_lifecycle_status(updates["status"])

        if "segmentation_status" in updates and updates["segmentation_status"] is not None:
            self.validate_segmentation_status(updates["segmentation_status"])

        client = self._get_client(use_service_role=use_service_role)
        response = (
            client.table("analyses")
            .update(updates)
            .eq("id", str(analysis_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    def delete(
        self, analysis_id: str, user_id: str, use_service_role: bool = False
    ) -> bool:
        """Delete an analysis record belonging to the authenticated user.

        Args:
            analysis_id: UUID of the analysis.
            user_id: Supabase Auth UUID of the requesting user.

        Returns:
            bool: True if operation completed successfully.
        """
        if not analysis_id or not user_id:
            return False

        client = self._get_client(use_service_role=use_service_role)
        response = (
            client.table("analyses")
            .delete()
            .eq("id", str(analysis_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        return bool(response.data and len(response.data) > 0)
