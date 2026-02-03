"""
Embedding Generator module - Convert text to vector representations.

Uses LlamaCloud's embedding service for generating embeddings.
Note: When using LlamaCloudIndex, embeddings are handled automatically.
This module is provided for standalone embedding needs.
"""

import logging
import os

from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from tenacity import retry, stop_after_attempt, wait_exponential

from compliance_auditor.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings using LlamaCloud-compatible embedding models.

    Note: When using LlamaCloudIndex for document storage and retrieval,
    embeddings are handled automatically. This class is for cases where
    you need standalone embeddings outside of the index workflow.
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize the embedding generator.

        Args:
            model_name: Embedding model to use (default: OpenAI's text-embedding-3-small)
        """
        settings = get_settings()

        # Ensure API key is set for LlamaCloud
        os.environ["LLAMA_CLOUD_API_KEY"] = settings.llama_cloud_api_key

        # Use OpenAI embeddings through LlamaCloud or configure alternative
        self.embed_model = OpenAIEmbedding(model=model_name)
        self.model_name = model_name

        logger.info(f"EmbeddingGenerator initialized with model: {model_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return self.embed_model.get_text_embedding(text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        return self.embed_model.get_query_embedding(query)

    def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.debug(f"Embedding batch {i // batch_size + 1}, size {len(batch)}")

            batch_embeddings = self._embed_batch_internal(batch)
            all_embeddings.extend(batch_embeddings)

        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _embed_batch_internal(self, texts: list[str]) -> list[list[float]]:
        """
        Internal method to embed a batch with retry logic.

        Args:
            texts: Batch of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embed_model.get_text_embedding_batch(texts)
