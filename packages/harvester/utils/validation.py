"""Validation utilities for update operations.

This module provides validation functions for server updates, ensuring data
integrity and preventing invalid operations.
"""

from typing import Any, Dict, List, Set

from loguru import logger

from packages.harvester.core.models import HostType, RiskLevel

# Define allowed update fields
ALLOWED_SERVER_FIELDS: Set[str] = {
    "name",
    "description",
    "author_name",
    "homepage",
    "license",
    "readme_content",
    "keywords",
    "categories",
    "stars",
    "downloads",
    "forks",
    "open_issues",
    "risk_level",
    "verified_source",
    "health_score",
    "host_type",
}

# Fields that should not be directly updated (system-managed)
PROTECTED_FIELDS: Set[str] = {
    "id",
    "uuid",
    "primary_url",  # URL is the canonical identifier, shouldn't change
    "created_at",
    "updated_at",
    "last_indexed_at",
}


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_server_update(updates: Dict[str, Any]) -> None:
    """Validate server update payload.

    Args:
        updates: Dictionary of field names and values to update

    Raises:
        ValidationError: If validation fails
    """
    if not updates:
        raise ValidationError("Update dictionary cannot be empty")

    # Check for protected fields
    protected_found = set(updates.keys()) & PROTECTED_FIELDS
    if protected_found:
        raise ValidationError(f"Cannot update protected fields: {', '.join(protected_found)}")

    # Check for unknown fields
    unknown_fields = set(updates.keys()) - ALLOWED_SERVER_FIELDS
    if unknown_fields:
        logger.warning(f"Unknown fields will be ignored: {', '.join(unknown_fields)}")

    # Validate specific field types and values
    for field, value in updates.items():
        if field not in ALLOWED_SERVER_FIELDS:
            continue

        # Validate field-specific rules
        if field == "risk_level":
            validate_risk_level(value)
        elif field == "host_type":
            validate_host_type(value)
        elif field == "health_score":
            validate_health_score(value)
        elif field == "verified_source":
            validate_boolean(field, value)
        elif field in ["stars", "downloads", "forks", "open_issues"]:
            validate_non_negative_int(field, value)
        elif field in ["keywords", "categories"]:
            validate_list_of_strings(field, value)
        elif field in ["name", "description", "author_name", "homepage", "license"]:
            validate_string(field, value)


def validate_risk_level(value: Any) -> None:
    """Validate risk level value.

    Args:
        value: Value to validate

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (str, RiskLevel)):
        raise ValidationError(f"risk_level must be a string or RiskLevel enum")

    valid_values = [level.value for level in RiskLevel]
    if isinstance(value, str) and value not in valid_values:
        raise ValidationError(
            f"Invalid risk_level: {value}. Must be one of: {', '.join(valid_values)}"
        )


def validate_host_type(value: Any) -> None:
    """Validate host type value.

    Args:
        value: Value to validate

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (str, HostType)):
        raise ValidationError(f"host_type must be a string or HostType enum")

    valid_values = [host.value for host in HostType]
    if isinstance(value, str) and value not in valid_values:
        raise ValidationError(
            f"Invalid host_type: {value}. Must be one of: {', '.join(valid_values)}"
        )


def validate_health_score(value: Any) -> None:
    """Validate health score value.

    Args:
        value: Value to validate

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, int):
        raise ValidationError(f"health_score must be an integer")

    if value < 0 or value > 100:
        raise ValidationError(f"health_score must be between 0 and 100")


def validate_boolean(field: str, value: Any) -> None:
    """Validate boolean value.

    Args:
        field: Field name
        value: Value to validate

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be a boolean")


def validate_non_negative_int(field: str, value: Any) -> None:
    """Validate non-negative integer value.

    Args:
        field: Field name
        value: Value to validate

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, int):
        raise ValidationError(f"{field} must be an integer")

    if value < 0:
        raise ValidationError(f"{field} must be non-negative")


def validate_list_of_strings(field: str, value: Any) -> None:
    """Validate list of strings.

    Args:
        field: Field name
        value: Value to validate

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be a list")

    if not all(isinstance(item, str) for item in value):
        raise ValidationError(f"{field} must be a list of strings")


def validate_string(field: str, value: Any) -> None:
    """Validate string value.

    Args:
        field: Field name
        value: Value to validate

    Raises:
        ValidationError: If validation fails
    """
    if value is not None and not isinstance(value, str):
        raise ValidationError(f"{field} must be a string or None")


def check_update_conflicts(
    server_id: int, updates: Dict[str, Any], existing_servers: List[Any]
) -> None:
    """Check for conflicts with existing servers.

    This function ensures that updates don't create duplicate entries or
    violate unique constraints.

    Args:
        server_id: ID of the server being updated
        updates: Dictionary of updates
        existing_servers: List of existing servers

    Raises:
        ValidationError: If conflicts are detected
    """
    # Currently, the main unique constraint is primary_url
    # Since we don't allow updating primary_url, we don't need to check for conflicts
    # This function is a placeholder for future conflict detection logic
    pass


def validate_bulk_filters(filters: Dict[str, Any]) -> None:
    """Validate bulk update filters.

    Args:
        filters: Dictionary of filter conditions

    Raises:
        ValidationError: If validation fails
    """
    if not filters:
        raise ValidationError("Filter dictionary cannot be empty")

    # Validate filter fields are valid Server fields
    allowed_filter_fields = ALLOWED_SERVER_FIELDS | {"id", "uuid"}

    unknown_fields = set(filters.keys()) - allowed_filter_fields
    if unknown_fields:
        raise ValidationError(f"Unknown filter fields: {', '.join(unknown_fields)}")


def validate_prune_days(days: int) -> None:
    """Validate days parameter for pruning.

    Args:
        days: Number of days

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(days, int):
        raise ValidationError("days must be an integer")

    if days < 1:
        raise ValidationError("days must be at least 1")

    if days < 30:
        logger.warning(
            f"Pruning servers inactive for only {days} days is aggressive. "
            "Consider using a longer period (e.g., 90-180 days)."
        )
