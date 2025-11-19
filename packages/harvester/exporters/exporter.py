"""Data exporters for MCPS.

This module provides exporters for various formats including Parquet, JSONL, and binary vectors.
Implements Phase 4 of TASKS.md - Data Engineering (The Lake).

Exporters:
    - ParquetExporter: Exports servers and dependencies to Parquet format
    - JSONLExporter: Exports tools for LLM training to JSONL format
    - VectorExporter: Exports tool embeddings to binary format with metadata
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pyarrow as pa
import pyarrow.parquet as pq
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.harvester.models.models import (
    Dependency,
    Server,
    Tool,
    ToolEmbedding,
)


class ParquetExporter:
    """Exports MCPS data to Parquet format for data science workflows.

    Parquet provides efficient columnar storage with strong typing,
    ideal for analytical workloads and data lake architectures.
    """

    @staticmethod
    async def export_servers(output_path: Path, session: AsyncSession) -> None:
        """Export servers with analytics columns to Parquet format.

        Creates servers.parquet with comprehensive server metadata including:
        - Basic info (id, uuid, name, primary_url, host_type, description)
        - Metrics (stars, downloads, forks, open_issues)
        - Analysis (risk_level, health_score, verified_source)
        - Timestamps (created_at, updated_at, last_indexed_at)

        Args:
            output_path: Directory path for output files
            session: AsyncSession for database queries

        Raises:
            ValueError: If no servers found in database
            IOError: If file write fails
        """
        logger.info("Exporting servers to Parquet format...")

        # Query all servers
        stmt = select(Server)
        result = await session.execute(stmt)
        servers = result.scalars().all()

        if not servers:
            logger.warning("No servers found in database")
            raise ValueError("No servers to export")

        logger.info(f"Found {len(servers)} servers to export")

        # Prepare data as list of dicts for PyArrow
        data: List[Dict[str, Any]] = []

        for server in servers:
            data.append({
                "id": server.id,
                "uuid": str(server.uuid),
                "name": server.name,
                "primary_url": server.primary_url,
                "host_type": server.host_type.value,
                "description": server.description,
                "author_name": server.author_name,
                "homepage": server.homepage,
                "license": server.license,
                # Metrics
                "stars": server.stars,
                "downloads": server.downloads,
                "forks": server.forks,
                "open_issues": server.open_issues,
                # Analysis
                "risk_level": server.risk_level.value,
                "health_score": server.health_score,
                "verified_source": server.verified_source,
                # Timestamps
                "created_at": server.created_at,
                "updated_at": server.updated_at,
                "last_indexed_at": server.last_indexed_at,
            })

        # Define PyArrow schema with proper types
        schema = pa.schema([
            ("id", pa.int64()),
            ("uuid", pa.string()),
            ("name", pa.string()),
            ("primary_url", pa.string()),
            ("host_type", pa.string()),
            ("description", pa.string()),
            ("author_name", pa.string()),
            ("homepage", pa.string()),
            ("license", pa.string()),
            # Metrics
            ("stars", pa.int32()),
            ("downloads", pa.int32()),
            ("forks", pa.int32()),
            ("open_issues", pa.int32()),
            # Analysis
            ("risk_level", pa.string()),
            ("health_score", pa.int32()),
            ("verified_source", pa.bool_()),
            # Timestamps
            ("created_at", pa.timestamp("ms")),
            ("updated_at", pa.timestamp("ms")),
            ("last_indexed_at", pa.timestamp("ms")),
        ])

        # Convert to PyArrow table
        table = pa.Table.from_pylist(data, schema=schema)

        # Write to Parquet file
        output_file = output_path / "servers.parquet"
        pq.write_table(table, output_file, compression="snappy")

        logger.success(f"Exported {len(servers)} servers to {output_file}")
        logger.info(f"File size: {output_file.stat().st_size / 1024:.2f} KB")

    @staticmethod
    async def export_dependencies(output_path: Path, session: AsyncSession) -> None:
        """Export server dependencies as an edge list to Parquet format.

        Creates dependencies.parquet with exploded view of Server -> Dependency relationships.
        This format is ideal for graph analysis and dependency network visualization.

        Output columns:
            - server_id: Foreign key to server
            - server_name: Name of the server for convenience
            - library_name: Name of the dependency
            - version_constraint: Version specification (e.g., "^1.0.0")
            - ecosystem: Package ecosystem (npm, pypi, etc.)
            - type: Dependency type (runtime, dev, peer)

        Args:
            output_path: Directory path for output files
            session: AsyncSession for database queries

        Raises:
            ValueError: If no dependencies found in database
            IOError: If file write fails
        """
        logger.info("Exporting dependencies to Parquet format...")

        # Query all dependencies with server relationship
        stmt = select(Dependency).options(selectinload(Dependency.server))
        result = await session.execute(stmt)
        dependencies = result.scalars().all()

        if not dependencies:
            logger.warning("No dependencies found in database")
            raise ValueError("No dependencies to export")

        logger.info(f"Found {len(dependencies)} dependencies to export")

        # Prepare data as list of dicts for PyArrow
        data: List[Dict[str, Any]] = []

        for dep in dependencies:
            data.append({
                "server_id": dep.server_id,
                "server_name": dep.server.name if dep.server else None,
                "library_name": dep.library_name,
                "version_constraint": dep.version_constraint,
                "ecosystem": dep.ecosystem,
                "type": dep.type.value,
            })

        # Define PyArrow schema
        schema = pa.schema([
            ("server_id", pa.int64()),
            ("server_name", pa.string()),
            ("library_name", pa.string()),
            ("version_constraint", pa.string()),
            ("ecosystem", pa.string()),
            ("type", pa.string()),
        ])

        # Convert to PyArrow table
        table = pa.Table.from_pylist(data, schema=schema)

        # Write to Parquet file
        output_file = output_path / "dependencies.parquet"
        pq.write_table(table, output_file, compression="snappy")

        logger.success(f"Exported {len(dependencies)} dependencies to {output_file}")
        logger.info(f"File size: {output_file.stat().st_size / 1024:.2f} KB")


class JSONLExporter:
    """Exports MCPS data to JSONL format for LLM training.

    JSONL (JSON Lines) format is ideal for streaming and batch processing
    of training data for machine learning models.
    """

    @staticmethod
    async def export_tools_for_training(
        output_path: Path, session: AsyncSession
    ) -> None:
        """Export tools in training format for LLM fine-tuning.

        Generates tools.jsonl with conversational format suitable for fine-tuning:
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Create a tool for <description>"
                },
                {
                    "role": "assistant",
                    "content": "<JSON schema>"
                }
            ]
        }

        This format is compatible with OpenAI fine-tuning API and similar services.
        Only exports tools with valid JSON schemas.

        Args:
            output_path: Directory path for output files
            session: AsyncSession for database queries

        Raises:
            ValueError: If no tools found in database
            IOError: If file write fails
        """
        logger.info("Exporting tools for LLM training to JSONL format...")

        # Query all tools with server relationship for context
        stmt = select(Tool).options(selectinload(Tool.server))
        result = await session.execute(stmt)
        tools = result.scalars().all()

        if not tools:
            logger.warning("No tools found in database")
            raise ValueError("No tools to export")

        logger.info(f"Found {len(tools)} tools to export")

        output_file = output_path / "tools.jsonl"
        exported_count = 0
        skipped_count = 0

        with open(output_file, "w", encoding="utf-8") as f:
            for tool in tools:
                # Validate JSON schema before writing
                if not tool.input_schema or not isinstance(tool.input_schema, dict):
                    logger.warning(
                        f"Skipping tool {tool.name} (id={tool.id}): "
                        "Invalid or missing input_schema"
                    )
                    skipped_count += 1
                    continue

                # Validate that it's valid JSON
                try:
                    schema_str = json.dumps(tool.input_schema)
                    # Ensure it can be parsed back
                    json.loads(schema_str)
                except (TypeError, json.JSONDecodeError) as e:
                    logger.warning(
                        f"Skipping tool {tool.name} (id={tool.id}): "
                        f"Schema validation failed: {e}"
                    )
                    skipped_count += 1
                    continue

                # Generate user prompt based on tool description
                description = tool.description or tool.name
                server_context = (
                    f" from {tool.server.name}" if tool.server else ""
                )
                user_content = (
                    f"Create a tool for {description}{server_context}. "
                    f"The tool should be named '{tool.name}'."
                )

                # Format as training example
                training_example = {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_content,
                        },
                        {
                            "role": "assistant",
                            "content": schema_str,
                        },
                    ]
                }

                # Write as single line
                f.write(json.dumps(training_example) + "\n")
                exported_count += 1

        logger.success(
            f"Exported {exported_count} tools to {output_file} "
            f"(skipped {skipped_count} invalid)"
        )
        logger.info(f"File size: {output_file.stat().st_size / 1024:.2f} KB")


class VectorExporter:
    """Exports tool embeddings to binary format with metadata.

    Provides efficient storage of high-dimensional vectors for semantic search
    and similarity analysis workflows.
    """

    @staticmethod
    async def export_vectors(output_path: Path, session: AsyncSession) -> None:
        """Export tool embeddings to binary format with metadata file.

        Creates two files:
        1. vectors.bin: Raw binary dump of vectors (float32 format)
        2. vectors.json: Metadata file with tool_id mapping and dimensions

        The binary format allows for efficient loading into numpy/torch for
        offline analysis without database access.

        Metadata format:
        {
            "vector_count": int,
            "dimensions": int,
            "model_name": str,
            "exported_at": str (ISO timestamp),
            "mappings": [
                {"index": int, "tool_id": int, "tool_name": str},
                ...
            ]
        }

        Args:
            output_path: Directory path for output files
            session: AsyncSession for database queries

        Raises:
            ValueError: If no embeddings found in database
            IOError: If file write fails
        """
        logger.info("Exporting tool embeddings to binary format...")

        # Query all embeddings with tool relationship
        stmt = select(ToolEmbedding).options(selectinload(ToolEmbedding.tool))
        result = await session.execute(stmt)
        embeddings = result.scalars().all()

        if not embeddings:
            logger.warning("No embeddings found in database")
            raise ValueError("No embeddings to export")

        logger.info(f"Found {len(embeddings)} embeddings to export")

        # Prepare binary data and metadata
        import struct

        binary_file = output_path / "vectors.bin"
        metadata_file = output_path / "vectors.json"

        # Determine dimensions from first embedding
        dimensions = len(embeddings[0].vector) if embeddings else 0
        model_name = embeddings[0].model_name if embeddings else "unknown"

        logger.info(f"Vector dimensions: {dimensions}")
        logger.info(f"Model: {model_name}")

        # Write binary file
        mappings = []
        with open(binary_file, "wb") as f:
            for idx, embedding in enumerate(embeddings):
                # Validate vector dimensions
                if len(embedding.vector) != dimensions:
                    logger.warning(
                        f"Skipping embedding for tool_id={embedding.tool_id}: "
                        f"Dimension mismatch ({len(embedding.vector)} != {dimensions})"
                    )
                    continue

                # Write vector as float32
                for value in embedding.vector:
                    f.write(struct.pack("f", value))

                # Store mapping
                tool_name = embedding.tool.name if embedding.tool else "unknown"
                mappings.append({
                    "index": idx,
                    "tool_id": embedding.tool_id,
                    "tool_name": tool_name,
                })

        # Write metadata file
        metadata = {
            "vector_count": len(mappings),
            "dimensions": dimensions,
            "model_name": model_name,
            "exported_at": datetime.utcnow().isoformat(),
            "mappings": mappings,
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.success(
            f"Exported {len(mappings)} vectors to {binary_file} "
            f"with metadata in {metadata_file}"
        )
        logger.info(f"Binary size: {binary_file.stat().st_size / 1024:.2f} KB")
        logger.info(f"Metadata size: {metadata_file.stat().st_size / 1024:.2f} KB")
