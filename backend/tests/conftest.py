import os
import sys
from unittest.mock import MagicMock

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("PINECONE_API_KEY", "test-key")
os.environ.setdefault("PINECONE_INDEX", "test-index")

# Mock ingestion.embedder before it's imported
sys.modules["ingestion.embedder"] = MagicMock()
