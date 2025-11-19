"""Semantic indexing and embedding generation for tools.

This module provides functionality to generate and manage embeddings for
semantic search capabilities. It integrates with OpenAI's embedding API
and stores vectors in the database for efficient similarity search.
"""

import hashlib
import os
from typing import List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.harvester.models.models import Tool, ToolEmbedding


class EmbeddingService:
    """Service for generating and managing tool embeddings.

    Uses OpenAI's text-embedding-3-small model (1536 dimensions) to generate
    semantic embeddings for tool descriptions. Implements caching via hash
    to avoid re-embedding identical descriptions.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        """Initialize the embedding service.

        Args:
            api_key: OpenAI API key. If None, will try to read from OPENAI_API_KEY env var
            model: OpenAI embedding model to use (default: text-embedding-3-small)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.embedding_dim = 1536  # Dimension for text-embedding-3-small
        self._client: Optional[object] = None  # Type will be openai.AsyncOpenAI if available
        self._openai_available = False

        # Try to import OpenAI client
        try:
            from openai import AsyncOpenAI

            if self.api_key:
                self._client = AsyncOpenAI(api_key=self.api_key)
                self._openai_available = True
                logger.info(f"OpenAI embedding service initialized with model: {model}")
            else:
                logger.warning(
                    "OpenAI API key not provided. Embedding generation will be disabled. "
                    "Set OPENAI_API_KEY environment variable to enable embeddings."
                )
        except ImportError:
            logger.warning(
                "OpenAI package not installed. Embedding generation will be disabled. "
                "Install with: uv add openai"
            )

    @property
    def is_available(self) -> bool:
        """Check if embedding service is available and configured.

        Returns:
            True if OpenAI client is initialized and ready
        """
        return self._openai_available

    async def batch_embed(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Processes texts in batches to optimize API usage and respect rate limits.

        Args:
            texts: List of text strings to embed
            batch_size: Number of texts to process per API call (default: 50)

        Returns:
            List of embedding vectors (each vector is a list of floats)

        Raises:
            RuntimeError: If OpenAI client is not available
            Exception: If API call fails
        """
        if not self.is_available:
            raise RuntimeError(
                "OpenAI embedding service is not available. "
                "Ensure OPENAI_API_KEY is set and openai package is installed."
            )

        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.debug(f"Generating embeddings for batch {i // batch_size + 1} ({len(batch)} texts)")

            try:
                # Call OpenAI API
                response = await self._client.embeddings.create(  # type: ignore
                    model=self.model,
                    input=batch,
                    encoding_format="float",
                )

                # Extract embeddings from response
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Generated {len(batch_embeddings)} embeddings")

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch: {e}")
                raise

        logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
        return all_embeddings

    @staticmethod
    def hash_text(text: str) -> str:
        """Generate a hash for text to use as cache key.

        Args:
            text: Text to hash

        Returns:
            SHA256 hash of the text
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def get_or_create_embedding(
        self,
        tool_id: int,
        description: str,
        session: AsyncSession,
        force_regenerate: bool = False,
    ) -> Optional[ToolEmbedding]:
        """Get existing embedding or create a new one for a tool.

        Implements caching logic: if an embedding already exists for this tool
        and the description hasn't changed, returns the existing embedding.

        Args:
            tool_id: ID of the tool to embed
            description: Tool description text to embed
            session: Database session
            force_regenerate: If True, regenerate embedding even if one exists

        Returns:
            ToolEmbedding instance or None if service is not available
        """
        if not self.is_available:
            logger.warning(
                f"Skipping embedding generation for tool {tool_id} - service not available"
            )
            return None

        if not description or not description.strip():
            logger.warning(f"Skipping embedding for tool {tool_id} - empty description")
            return None

        # Check if embedding already exists
        if not force_regenerate:
            result = await session.execute(
                select(ToolEmbedding).where(ToolEmbedding.tool_id == tool_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.debug(f"Using existing embedding for tool {tool_id}")
                return existing

        # Generate new embedding
        try:
            embeddings = await self.batch_embed([description])

            if not embeddings:
                logger.error(f"Failed to generate embedding for tool {tool_id}")
                return None

            # Create or update ToolEmbedding
            result = await session.execute(
                select(ToolEmbedding).where(ToolEmbedding.tool_id == tool_id)
            )
            embedding_obj = result.scalar_one_or_none()

            if embedding_obj:
                # Update existing
                embedding_obj.vector = embeddings[0]
                embedding_obj.model_name = self.model
                logger.info(f"Updated embedding for tool {tool_id}")
            else:
                # Create new
                embedding_obj = ToolEmbedding(
                    tool_id=tool_id,
                    vector=embeddings[0],
                    model_name=self.model,
                )
                session.add(embedding_obj)
                logger.info(f"Created new embedding for tool {tool_id}")

            return embedding_obj

        except Exception as e:
            logger.error(f"Failed to generate/save embedding for tool {tool_id}: {e}")
            return None

    async def embed_tools_batch(
        self,
        tools: List[Tool],
        session: AsyncSession,
        skip_existing: bool = True,
    ) -> int:
        """Generate embeddings for a batch of tools.

        Args:
            tools: List of Tool instances to embed
            session: Database session
            skip_existing: If True, skip tools that already have embeddings

        Returns:
            Number of embeddings created
        """
        if not self.is_available:
            logger.warning("Embedding service not available - skipping batch embedding")
            return 0

        tools_to_embed = []
        descriptions = []

        for tool in tools:
            if not tool.description or not tool.description.strip():
                continue

            # Check if embedding exists
            if skip_existing:
                result = await session.execute(
                    select(ToolEmbedding).where(ToolEmbedding.tool_id == tool.id)
                )
                if result.scalar_one_or_none():
                    continue

            tools_to_embed.append(tool)
            descriptions.append(tool.description)

        if not descriptions:
            logger.info("No tools to embed (all have embeddings or empty descriptions)")
            return 0

        logger.info(f"Generating embeddings for {len(descriptions)} tools")

        try:
            # Generate all embeddings in batches
            embeddings = await self.batch_embed(descriptions)

            # Create ToolEmbedding records
            created_count = 0
            for tool, embedding in zip(tools_to_embed, embeddings):
                embedding_obj = ToolEmbedding(
                    tool_id=tool.id,
                    vector=embedding,
                    model_name=self.model,
                )
                session.add(embedding_obj)
                created_count += 1

            logger.info(f"Successfully created {created_count} tool embeddings")
            return created_count

        except Exception as e:
            logger.error(f"Failed to generate embeddings for tools batch: {e}")
            return 0


async def generate_embedding(text: str, api_key: Optional[str] = None) -> Optional[List[float]]:
    """Generate a single embedding for text (convenience function).

    Args:
        text: Text to embed
        api_key: OpenAI API key (optional, will use env var if not provided)

    Returns:
        Embedding vector or None if generation fails
    """
    service = EmbeddingService(api_key=api_key)

    if not service.is_available:
        return None

    try:
        embeddings = await service.batch_embed([text])
        return embeddings[0] if embeddings else None
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None
