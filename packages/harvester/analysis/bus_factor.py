"""Bus factor analysis for MCP server maintainability assessment.

This module analyzes contributor distribution to determine the "bus factor" -
a metric indicating how many contributors would need to be unavailable before
a project becomes unmaintainable.
"""

from typing import List, Literal

from loguru import logger

from packages.harvester.models.models import Contributor


BusFactor = Literal["LOW", "MEDIUM", "HIGH"]


def calculate_bus_factor(contributors: List[Contributor]) -> BusFactor:
    """Calculate bus factor based on contributor distribution.

    The bus factor is a measure of project risk based on how work is distributed
    among contributors. A low bus factor indicates high risk (concentrated work),
    while a high bus factor indicates lower risk (distributed work).

    Algorithm:
    - LOW: Top contributor has >80% of commits (high risk - single point of failure)
    - MEDIUM: Top contributor has 50-80% of commits, or top 3 have >90%
    - HIGH: Work is well distributed among multiple contributors

    Args:
        contributors: List of Contributor objects with commit counts

    Returns:
        "LOW", "MEDIUM", or "HIGH" indicating the bus factor level
    """
    if not contributors:
        logger.warning("No contributors provided - defaulting to LOW bus factor")
        return "LOW"

    # Sort contributors by commit count (descending)
    sorted_contributors = sorted(contributors, key=lambda c: c.commits, reverse=True)

    total_commits = sum(c.commits for c in contributors)

    if total_commits == 0:
        logger.warning("Total commits is 0 - defaulting to LOW bus factor")
        return "LOW"

    # Calculate percentages for top contributors
    top_contributor_commits = sorted_contributors[0].commits
    top_contributor_percentage = (top_contributor_commits / total_commits) * 100

    logger.debug(
        f"Top contributor: {sorted_contributors[0].username} "
        f"({top_contributor_commits}/{total_commits} = {top_contributor_percentage:.1f}%)"
    )

    # LOW: Single point of failure (>80% of work by one person)
    if top_contributor_percentage > 80:
        logger.info(
            f"LOW bus factor: Top contributor has {top_contributor_percentage:.1f}% of commits "
            f"({sorted_contributors[0].username})"
        )
        return "LOW"

    # Calculate top 3 percentage if we have at least 3 contributors
    if len(sorted_contributors) >= 3:
        top_3_commits = sum(c.commits for c in sorted_contributors[:3])
        top_3_percentage = (top_3_commits / total_commits) * 100

        logger.debug(
            f"Top 3 contributors: {top_3_commits}/{total_commits} = {top_3_percentage:.1f}%"
        )

        # HIGH: Well distributed (top 3 have <75% or we have 5+ active contributors)
        if top_3_percentage < 75 or len([c for c in contributors if c.commits >= 5]) >= 5:
            logger.info(
                f"HIGH bus factor: Work well distributed "
                f"(top 3: {top_3_percentage:.1f}%, active contributors: "
                f"{len([c for c in contributors if c.commits >= 5])})"
            )
            return "HIGH"

        # Check for more even distribution among top 3
        # If top contributor has <60% and we have decent top-3 distribution
        if top_contributor_percentage < 60 and top_3_percentage < 90:
            logger.info(
                f"HIGH bus factor: Good distribution among top contributors "
                f"(top: {top_contributor_percentage:.1f}%, top 3: {top_3_percentage:.1f}%)"
            )
            return "HIGH"

        # MEDIUM: Moderate concentration
        logger.info(
            f"MEDIUM bus factor: Moderate concentration "
            f"(top: {top_contributor_percentage:.1f}%, top 3: {top_3_percentage:.1f}%)"
        )
        return "MEDIUM"

    # If we have only 1-2 contributors
    elif len(sorted_contributors) == 2:
        # If it's relatively balanced between the two
        second_contributor_percentage = (sorted_contributors[1].commits / total_commits) * 100

        if top_contributor_percentage < 70 and second_contributor_percentage > 25:
            logger.info(
                f"MEDIUM bus factor: Two contributors with reasonable distribution "
                f"({top_contributor_percentage:.1f}% / {second_contributor_percentage:.1f}%)"
            )
            return "MEDIUM"
        else:
            logger.info(
                f"LOW bus factor: Two contributors but unbalanced "
                f"({top_contributor_percentage:.1f}% / {second_contributor_percentage:.1f}%)"
            )
            return "LOW"

    else:
        # Single contributor
        logger.info("LOW bus factor: Single contributor")
        return "LOW"


def get_bus_factor_description(bus_factor: BusFactor) -> str:
    """Get a human-readable description of the bus factor level.

    Args:
        bus_factor: Bus factor level ("LOW", "MEDIUM", "HIGH")

    Returns:
        Description of what the bus factor means
    """
    descriptions = {
        "LOW": (
            "High risk: Project heavily depends on a single contributor. "
            "Significant knowledge concentration could impact maintainability."
        ),
        "MEDIUM": (
            "Moderate risk: Project has some contributor diversity but work is "
            "concentrated among a small group. Additional contributors would improve sustainability."
        ),
        "HIGH": (
            "Low risk: Work is well distributed among multiple active contributors. "
            "Project shows healthy collaborative development."
        ),
    }

    return descriptions.get(bus_factor, "Unknown bus factor level")


def analyze_contributor_health(contributors: List[Contributor]) -> dict:
    """Analyze contributor health metrics for a project.

    Provides a comprehensive view of contributor distribution and activity.

    Args:
        contributors: List of Contributor objects

    Returns:
        Dictionary containing:
        - bus_factor: "LOW", "MEDIUM", or "HIGH"
        - description: Human-readable description
        - total_contributors: Total number of contributors
        - active_contributors: Number of contributors with 5+ commits
        - top_contributor_percentage: Percentage of commits by top contributor
        - top_3_percentage: Percentage of commits by top 3 contributors
    """
    if not contributors:
        return {
            "bus_factor": "LOW",
            "description": get_bus_factor_description("LOW"),
            "total_contributors": 0,
            "active_contributors": 0,
            "top_contributor_percentage": 0.0,
            "top_3_percentage": 0.0,
        }

    bus_factor = calculate_bus_factor(contributors)
    sorted_contributors = sorted(contributors, key=lambda c: c.commits, reverse=True)
    total_commits = sum(c.commits for c in contributors)
    active_contributors = len([c for c in contributors if c.commits >= 5])

    top_contributor_percentage = (
        (sorted_contributors[0].commits / total_commits * 100) if total_commits > 0 else 0.0
    )

    top_3_percentage = 0.0
    if len(sorted_contributors) >= 3 and total_commits > 0:
        top_3_commits = sum(c.commits for c in sorted_contributors[:3])
        top_3_percentage = (top_3_commits / total_commits) * 100

    return {
        "bus_factor": bus_factor,
        "description": get_bus_factor_description(bus_factor),
        "total_contributors": len(contributors),
        "active_contributors": active_contributors,
        "top_contributor_percentage": round(top_contributor_percentage, 2),
        "top_3_percentage": round(top_3_percentage, 2),
        "top_contributor": sorted_contributors[0].username if sorted_contributors else None,
    }
