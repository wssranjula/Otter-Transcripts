"""
Embedding Generation Module
Generates embeddings using Mistral API for semantic search
"""

import time
from typing import List, Optional

try:
    # New Mistral client (v1.0+)
    from mistralai import Mistral
    MISTRAL_NEW_API = True
except ImportError:
    try:
        # Old Mistral client (deprecated)
        from mistralai.client import MistralClient
        MISTRAL_NEW_API = False
    except ImportError:
        raise ImportError("Please install mistralai: pip install mistralai")


class MistralEmbedder:
    """Generate embeddings using Mistral API"""
    
    def __init__(self, api_key: str, model: str = "mistral-embed", batch_size: int = 50):
        """
        Initialize Mistral embedder
        
        Args:
            api_key: Mistral API key
            model: Embedding model (default: mistral-embed)
            batch_size: Number of texts to process per batch
        """
        if MISTRAL_NEW_API:
            # New API (v1.0+)
            self.client = Mistral(api_key=api_key)
        else:
            # Old API (deprecated, for backward compatibility)
            self.client = MistralClient(api_key=api_key)
        
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size
        self.dimensions = 1024  # Mistral embed produces 1024-dim vectors
        self.new_api = MISTRAL_NEW_API
        
        print(f"[OK] MistralEmbedder initialized (model: {model}, batch_size: {batch_size})")
    
    def embed_texts(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for list of texts
        
        Args:
            texts: List of text strings to embed
            show_progress: Show progress messages
            
        Returns:
            List of embedding vectors (each is List[float] of length 1024)
        """
        if not texts:
            return []
        
        embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            if show_progress:
                print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)...", end="")
            
            try:
                # Call Mistral API
                if self.new_api:
                    # New API (v1.0+)
                    response = self.client.embeddings.create(
                        model=self.model,
                        inputs=batch
                    )
                    # Extract embeddings from new API response
                    batch_embeddings = [item.embedding for item in response.data]
                else:
                    # Old API (deprecated)
                    response = self.client.embeddings(
                        model=self.model,
                        input=batch
                    )
                    # Extract embeddings from old API response
                    batch_embeddings = [item.embedding for item in response.data]
                
                embeddings.extend(batch_embeddings)
                
                if show_progress:
                    print(f" ✓")
                
                # Rate limiting (be nice to API)
                if i + self.batch_size < len(texts):
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f" ✗")
                print(f"  [ERROR] Embedding failed for batch {batch_num}: {e}")
                # Add zero vectors as fallback
                zero_vector = [0.0] * self.dimensions
                embeddings.extend([zero_vector] * len(batch))
        
        return embeddings
    
    def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector (List[float] of length 1024)
        """
        embeddings = self.embed_texts([text], show_progress=False)
        return embeddings[0] if embeddings else [0.0] * self.dimensions
    
    def embed_chunks(self, chunks: List[dict], text_field: str = 'text') -> List[dict]:
        """
        Add embeddings to chunk dictionaries
        
        Args:
            chunks: List of chunk dicts
            text_field: Field name containing text to embed
            
        Returns:
            Same chunks with 'embedding' field added
        """
        # Extract texts
        texts = [chunk[text_field] for chunk in chunks]
        
        print(f"\n[LOG] Generating embeddings for {len(texts)} chunks...")
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Add to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        print(f"[OK] Embeddings generated ({self.dimensions} dimensions)")
        
        return chunks


class CachedEmbedder:
    """Wrapper that caches embeddings to avoid re-computation"""
    
    def __init__(self, embedder: MistralEmbedder, cache_file: Optional[str] = None):
        """
        Initialize cached embedder
        
        Args:
            embedder: Base embedder to use
            cache_file: Optional file path to persist cache
        """
        self.embedder = embedder
        self.cache = {}
        self.cache_file = cache_file
        
        if cache_file:
            self._load_cache()
    
    def _load_cache(self):
        """Load cache from file"""
        import json
        from pathlib import Path
        
        if self.cache_file and Path(self.cache_file).exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"[OK] Loaded {len(self.cache)} cached embeddings")
            except Exception as e:
                print(f"[WARN] Could not load cache: {e}")
    
    def _save_cache(self):
        """Save cache to file"""
        import json
        
        if self.cache_file:
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.cache, f)
                print(f"[OK] Saved {len(self.cache)} embeddings to cache")
            except Exception as e:
                print(f"[WARN] Could not save cache: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def embed_texts(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """Generate embeddings with caching"""
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                embeddings.append(self.cache[cache_key])
            else:
                embeddings.append(None)
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        # Generate missing embeddings
        if texts_to_embed:
            if show_progress:
                print(f"  Cache hit: {len(texts) - len(texts_to_embed)}/{len(texts)}, generating {len(texts_to_embed)} new embeddings")
            
            new_embeddings = self.embedder.embed_texts(texts_to_embed, show_progress)
            
            # Update cache and results
            for idx, text, embedding in zip(indices_to_embed, texts_to_embed, new_embeddings):
                cache_key = self._get_cache_key(text)
                self.cache[cache_key] = embedding
                embeddings[idx] = embedding
            
            # Save cache periodically
            if len(texts_to_embed) > 0:
                self._save_cache()
        
        return embeddings
    
    def embed_chunks(self, chunks: List[dict], text_field: str = 'text') -> List[dict]:
        """Add embeddings to chunk dictionaries with caching"""
        texts = [chunk[text_field] for chunk in chunks]
        
        print(f"\n[LOG] Generating embeddings for {len(texts)} chunks (with cache)...")
        
        embeddings = self.embed_texts(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        print(f"[OK] Embeddings ready ({self.embedder.dimensions} dimensions)")
        
        return chunks


def main():
    """Test embedding generation"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python embeddings.py <mistral_api_key>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    # Test texts
    texts = [
        "Solar radiation management is a climate intervention technique.",
        "The UNEA conference will be held in Nairobi next year.",
        "We need to recruit a new policy analyst by next month.",
    ]
    
    print("Testing Mistral Embeddings...")
    print("="*70)
    
    embedder = MistralEmbedder(api_key=api_key)
    
    print(f"\nGenerating embeddings for {len(texts)} texts...")
    embeddings = embedder.embed_texts(texts)
    
    print("\nResults:")
    for i, (text, embedding) in enumerate(zip(texts, embeddings)):
        print(f"\nText {i+1}: {text[:50]}...")
        print(f"Embedding length: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    
    print("\n" + "="*70)
    print("[OK] Embedding generation test complete!")


if __name__ == "__main__":
    main()

