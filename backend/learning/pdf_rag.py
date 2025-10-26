"""
PDF RAG (Retrieval-Augmented Generation) system
Learns from PDF documents and provides context for agent decisions
"""

import PyPDF2
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime


class PDFLearningSystem:
    """
    PDF ingestion and RAG system
    Uses PyPDF2 for extraction, embeddings for retrieval
    """

    def __init__(self, knowledge_dir: str = "./data/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Document store
        self.documents: List[Dict] = []

        # Embeddings (simplified - in production use OpenAI/Sentence-Transformers)
        self.embeddings = {}

        # Load existing knowledge base
        self._load_knowledge_base()

    def ingest_pdf(
        self,
        pdf_path: str,
        category: str = "general",
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Ingest PDF and extract text

        Args:
            pdf_path: Path to PDF file
            category: Category (e.g., 'technical_analysis', 'psychology')
            metadata: Additional metadata

        Returns:
            Number of chunks created
        """
        print(f"📖 Ingesting PDF: {pdf_path}")

        # Read PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            # Extract text from all pages
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                full_text += f"\n\n--- Page {page_num + 1} ---\n\n"
                full_text += text

        # Split into chunks
        chunks = self._split_text(full_text, chunk_size=1000, overlap=200)

        # Store documents
        pdf_name = Path(pdf_path).stem

        for i, chunk in enumerate(chunks):
            doc = {
                'id': f"{pdf_name}_chunk_{i}",
                'source': pdf_path,
                'category': category,
                'text': chunk,
                'metadata': metadata or {},
                'ingested_at': datetime.now().isoformat()
            }

            self.documents.append(doc)

            # Generate embedding (simplified - use real embeddings in production)
            self.embeddings[doc['id']] = self._simple_embedding(chunk)

        # Save knowledge base
        self._save_knowledge_base()

        print(f"✅ Ingested {len(chunks)} chunks from {pdf_name}")

        return len(chunks)

    def query(
        self,
        question: str,
        k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Query knowledge base

        Args:
            question: User question
            k: Number of results
            category: Filter by category

        Returns:
            List of relevant documents
        """
        # Generate query embedding
        query_emb = self._simple_embedding(question)

        # Filter by category
        if category:
            candidates = [doc for doc in self.documents if doc['category'] == category]
        else:
            candidates = self.documents

        # Compute similarity scores (cosine similarity)
        scores = []
        for doc in candidates:
            doc_emb = self.embeddings.get(doc['id'], [])
            if doc_emb:
                score = self._cosine_similarity(query_emb, doc_emb)
                scores.append((doc, score))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        results = [
            {
                **doc,
                'relevance_score': score
            }
            for doc, score in scores[:k]
        ]

        return results

    def get_context_for_decision(
        self,
        market_situation: str,
        indicators: Dict[str, float]
    ) -> str:
        """
        Get relevant context from knowledge base for trading decision

        Args:
            market_situation: Current market description
            indicators: Current indicator values

        Returns:
            Context string
        """
        # Construct query
        query = f"{market_situation}. Indicators: {', '.join([f'{k}={v:.2f}' for k, v in indicators.items()])}"

        # Query knowledge base
        results = self.query(query, k=3)

        if not results:
            return "No relevant knowledge found."

        # Format context
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"\n[Knowledge {i}] (Score: {result['relevance_score']:.2f})")
            context_parts.append(f"Category: {result['category']}")
            context_parts.append(f"{result['text'][:500]}...")

        return "\n".join(context_parts)

    def _split_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to end at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start += (chunk_size - overlap)

        return chunks

    def _simple_embedding(self, text: str) -> List[float]:
        """
        Simple embedding (TF-IDF-like)
        In production, use OpenAI embeddings or sentence-transformers
        """
        # Tokenize
        tokens = text.lower().split()

        # Simple vocabulary (top 1000 words)
        vocab = set([
            'buy', 'sell', 'price', 'trend', 'support', 'resistance',
            'bullish', 'bearish', 'volume', 'momentum', 'rsi', 'macd',
            'fibonacci', 'pattern', 'candle', 'market', 'breakout', 'reversal'
            # ... extend as needed
        ])

        # Count occurrences
        embedding = []
        for word in vocab:
            count = tokens.count(word)
            embedding.append(count / (len(tokens) + 1))  # Normalized frequency

        return embedding[:100]  # Fixed size

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity"""
        if len(a) != len(b):
            # Pad shorter vector
            max_len = max(len(a), len(b))
            a = a + [0] * (max_len - len(a))
            b = b + [0] * (max_len - len(b))

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _save_knowledge_base(self):
        """Save documents and embeddings"""
        kb_path = self.knowledge_dir / "knowledge_base.json"

        with open(kb_path, 'w') as f:
            json.dump({
                'documents': self.documents,
                'embeddings': self.embeddings
            }, f, indent=2)

    def _load_knowledge_base(self):
        """Load existing knowledge base"""
        kb_path = self.knowledge_dir / "knowledge_base.json"

        if kb_path.exists():
            with open(kb_path, 'r') as f:
                data = json.load(f)
                self.documents = data.get('documents', [])
                self.embeddings = data.get('embeddings', {})

            print(f"✅ Loaded {len(self.documents)} documents from knowledge base")

    def list_documents(self) -> List[Dict]:
        """List all ingested documents"""
        summary = {}
        for doc in self.documents:
            source = doc['source']
            category = doc['category']

            key = f"{Path(source).stem} ({category})"

            if key not in summary:
                summary[key] = {
                    'source': source,
                    'category': category,
                    'chunks': 0,
                    'ingested_at': doc['ingested_at']
                }

            summary[key]['chunks'] += 1

        return list(summary.values())
