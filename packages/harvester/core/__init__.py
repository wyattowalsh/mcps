"""Core - Abstract Base Classes & Interfaces.

This package contains abstract base classes and interfaces that define
the structure of adapters and processors.
"""

from .models import (
    BaseEntity,
    Capability,
    DependencyType,
    HostType,
    RiskLevel,
)

# BaseHarvester and HarvesterError should be imported directly from base_harvester
# to avoid circular import issues, since base_harvester imports from models
# from .base_harvester import BaseHarvester, HarvesterError

__all__ = [
    "BaseEntity",
    "HostType",
    "RiskLevel",
    "DependencyType",
    "Capability",
    # "BaseHarvester",  # Import from .base_harvester directly
    # "HarvesterError",  # Import from .base_harvester directly
]
