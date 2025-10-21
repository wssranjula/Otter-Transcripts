"""
RAG-Optimized Transcript Parser
Creates chunks with entity mentions for retrieval-augmented generation
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.core.chunking_logic import TranscriptChunker
from src.core.langchain_extractor_simple import SimplifiedMistralExtractor

try:
    from src.core.embeddings import MistralEmbedder
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class RAGTranscriptParser:
    """Parse transcripts optimized for RAG retrieval"""

    def __init__(self, transcript_dir: str, mistral_api_key: str, model: str = "mistral-large-latest", 
                 generate_embeddings: bool = False):
        self.transcript_dir = Path(transcript_dir)
        self.mistral_api_key = mistral_api_key
        self.generate_embeddings = generate_embeddings

        # Initialize components
        self.chunker = TranscriptChunker(min_chunk_size=300, max_chunk_size=1500)
        self.extractor = SimplifiedMistralExtractor(api_key=mistral_api_key, model=model)

        # Initialize embedder if requested
        self.embedder = None
        if generate_embeddings:
            if EMBEDDINGS_AVAILABLE:
                self.embedder = MistralEmbedder(api_key=mistral_api_key)
                print("[OK] Embeddings enabled (Mistral 1024-dim)")
            else:
                print("[WARN] Embeddings requested but module not available. Install: pip install mistralai")

        # Caches
        self.entity_cache = {}  # Unified entity cache

    def parse_all_transcripts(self) -> List[Dict]:
        """Parse all transcripts for RAG"""

        print("\n" + "="*70)
        print("RAG-OPTIMIZED TRANSCRIPT PARSING")
        print("Creating: Chunks + Entities + Relationships")
        print("="*70)

        transcript_files = list(self.transcript_dir.rglob('*.txt'))
        transcript_files = [f for f in transcript_files
                           if not f.name.upper().startswith(('PARSED_', 'README', 'SETUP', 'NEO4J', 'QUICK'))
                           and f.name.lower() not in ('requirements.txt', 'license.txt', 'readme.txt')]

        print(f"\nFound {len(transcript_files)} transcripts\n")

        results = []
        for i, file_path in enumerate(transcript_files, 1):
            try:
                print(f"[{i}/{len(transcript_files)}] {file_path.name}")
                result = self.parse_transcript(file_path)
                results.append(result)
                print()
            except Exception as e:
                print(f"  [ERROR] Error: {e}\n")

        return results

    def parse_transcript(self, file_path: Path) -> Dict:
        """Parse single transcript"""

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract meeting metadata
        meeting_info = self._extract_meeting_info(file_path, content)

        print(f"  Step 1: Chunking...")
        # Create chunks
        chunks = self.chunker.chunk_transcript(content, meeting_info)
        print(f"    [OK] Created {len(chunks)} chunks")

        print(f"  Step 2: Extracting entities...")
        # Extract entities from full transcript
        entities_data = self.extractor.extract_entities(content, meeting_info)

        # Process entities (unified)
        entities = self._process_entities(entities_data)
        print(f"    [OK] Found {len(entities)} entities")

        print(f"  Step 3: Linking chunks to entities...")
        # Link chunks to entities they mention
        chunk_entity_links = self._link_chunks_to_entities(chunks, entities)
        print(f"    [OK] Created {len(chunk_entity_links)} chunk-entity links")

        print(f"  Step 4: Extracting outcomes...")
        # Extract decisions and actions
        decisions = self._process_decisions(entities_data, chunks)
        actions = self._process_actions(entities_data, chunks)
        print(f"    [OK] {len(decisions)} decisions, {len(actions)} actions")

        # Convert chunks to dicts
        chunk_dicts = [self._chunk_to_dict(c, meeting_info, i) for i, c in enumerate(chunks)]

        # Generate embeddings if enabled
        if self.embedder:
            print(f"  Step 5: Generating embeddings...")
            self.embedder.embed_chunks(chunk_dicts)
            print(f"    [OK] Embeddings generated")

        return {
            'meeting': meeting_info,
            'chunks': chunk_dicts,
            'entities': entities,
            'chunk_entity_links': chunk_entity_links,
            'decisions': decisions,
            'actions': actions
        }

    def _extract_meeting_info(self, file_path: Path, content: str) -> Dict:
        """Extract meeting metadata"""
        import re

        filename = file_path.stem
        parent_dir = file_path.parent.name

        # Extract date
        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?', filename, re.IGNORECASE)
        if not date_match:
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', filename)

        date_str = None
        if date_match:
            date_str = self._parse_date(date_match.group())

        # Category
        categories = {
            'All Hands': 'All_Hands',
            'Outlier': 'Funder_Call',
            'Principals': 'Principals_Call',
            'HAC Team': 'Team_Meeting'
        }

        category = 'General'
        for key, value in categories.items():
            if key.lower() in parent_dir.lower() or key.lower() in filename.lower():
                category = value
                break

        meeting_id = self._generate_id(f"{filename}_{date_str}")

        # Extract participants from content
        participants = self._extract_participants(content)

        return {
            'id': meeting_id,
            'title': filename,
            'date': date_str,
            'category': category,
            'participants': participants,
            'transcript_file': str(file_path.relative_to(self.transcript_dir))
        }

    def _extract_participants(self, content: str) -> List[str]:
        """Extract participant names from transcript"""
        import re
        pattern = r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+\d{1,2}:\d{2}'
        matches = re.findall(pattern, content, re.MULTILINE)
        return list(set(matches))

    def _process_entities(self, entities_data: Dict) -> List[Dict]:
        """Process all entities into unified format"""
        entities = []

        # People
        for person in entities_data.get('people', []):
            entity_id = self._generate_id(person['name'])
            entities.append({
                'id': entity_id,
                'name': person['name'],
                'type': 'Person',
                'properties': {
                    'role': person.get('role'),
                    'organization': person.get('organization')
                }
            })
            self.entity_cache[person['name']] = entity_id

        # Organizations
        for org in entities_data.get('organizations', []):
            entity_id = self._generate_id(org['name'])
            entities.append({
                'id': entity_id,
                'name': org['name'],
                'type': 'Organization',
                'properties': {
                    'org_type': org.get('type')
                }
            })
            self.entity_cache[org['name']] = entity_id

        # Countries
        for country in entities_data.get('countries', []):
            entity_id = self._generate_id(country['name'])
            entities.append({
                'id': entity_id,
                'name': country['name'],
                'type': 'Country',
                'properties': {
                    'status': country.get('status')
                }
            })
            self.entity_cache[country['name']] = entity_id

        # Topics
        for topic in entities_data.get('topics', []):
            entity_id = self._generate_id(topic['name'])
            entities.append({
                'id': entity_id,
                'name': topic['name'],
                'type': 'Topic',
                'properties': {}
            })
            self.entity_cache[topic['name']] = entity_id

        return entities

    def _link_chunks_to_entities(self, chunks, entities) -> List[Dict]:
        """Find which entities are mentioned in which chunks"""
        links = []

        for chunk_idx, chunk in enumerate(chunks):
            chunk_text_lower = chunk.text.lower()

            for entity in entities:
                entity_name_lower = entity['name'].lower()

                # Check if entity is mentioned in chunk
                if entity_name_lower in chunk_text_lower:
                    links.append({
                        'chunk_sequence': chunk_idx,
                        'entity_id': entity['id'],
                        'entity_name': entity['name']
                    })

        return links

    def _process_decisions(self, entities_data: Dict, chunks) -> List[Dict]:
        """Process decisions and link to source chunks"""
        decisions = []

        for decision in entities_data.get('decisions', []):
            decision_id = self._generate_id(decision['description'][:50])

            # Find source chunk (chunk with highest similarity to decision text)
            source_chunks = self._find_source_chunks(decision['description'], chunks)

            decisions.append({
                'id': decision_id,
                'description': decision['description'],
                'rationale': decision.get('rationale', ''),
                'source_chunk_sequences': source_chunks
            })

        return decisions

    def _process_actions(self, entities_data: Dict, chunks) -> List[Dict]:
        """Process actions and link to source chunks"""
        actions = []

        for action in entities_data.get('action_items', []):
            action_id = self._generate_id(action['task'][:50])

            # Find source chunk
            source_chunks = self._find_source_chunks(action['task'], chunks)

            actions.append({
                'id': action_id,
                'task': action['task'],
                'owner': action.get('owner', 'Unknown'),
                'source_chunk_sequences': source_chunks
            })

        return actions

    def _find_source_chunks(self, text: str, chunks, top_n: int = 2) -> List[int]:
        """Find chunks most likely to contain this text"""
        text_lower = text.lower()
        text_words = set(text_lower.split())

        scores = []
        for i, chunk in enumerate(chunks):
            chunk_words = set(chunk.text.lower().split())
            overlap = len(text_words & chunk_words)
            scores.append((i, overlap))

        # Return top N chunks
        scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, score in scores[:top_n] if score > 0]

    def _chunk_to_dict(self, chunk, meeting_info: Dict, sequence: int) -> Dict:
        """Convert chunk object to dict"""
        return {
            'id': self._generate_id(f"{meeting_info['id']}_{sequence}"),
            'text': chunk.text,
            'sequence_number': sequence,
            'speakers': chunk.speakers,
            'start_time': chunk.start_time,
            'chunk_type': chunk.chunk_type,
            'importance_score': chunk.importance_score,
            'meeting_id': meeting_info['id'],
            'meeting_title': meeting_info['title'],
            'meeting_date': meeting_info['date']
        }

    def _parse_date(self, date_str: str) -> str:
        """Parse date to ISO"""
        try:
            formats = ['%b %d, %Y', '%B %d, %Y', '%Y-%m-%d', '%b %d', '%B %d']
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if dt.year == 1900:
                        dt = dt.replace(year=datetime.now().year)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except:
            pass
        return None

    def _generate_id(self, text: str) -> str:
        """Generate ID"""
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def export_to_json(self, output_file: str):
        """Export to JSON"""

        print("\nStarting RAG extraction...")
        transcripts = self.parse_all_transcripts()

        # Aggregate statistics
        total_chunks = sum(len(t['chunks']) for t in transcripts)
        total_entities = len(self.entity_cache)
        total_links = sum(len(t['chunk_entity_links']) for t in transcripts)

        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'transcript_count': len(transcripts),
                'total_chunks': total_chunks,
                'total_entities': total_entities,
                'total_chunk_entity_links': total_links,
                'extraction_method': 'RAG-Optimized (Chunks + Entities)',
                'model': self.extractor.model_name
            },
            'transcripts': transcripts,
            'entity_index': self.entity_cache
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print("\n" + "="*70)
        print("RAG EXTRACTION COMPLETE")
        print("="*70)
        print(f"Output: {output_file}")
        print(f"\nStatistics:")
        print(f"  Transcripts: {len(transcripts)}")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Avg chunks/transcript: {total_chunks/len(transcripts):.1f}")
        print(f"  Total entities: {total_entities}")
        print(f"  Chunk-entity links: {total_links}")
        print("\n[OK] Ready for RAG-optimized Neo4j loading!")


def main():
    """Main execution"""

    TRANSCRIPT_DIR = r"C:\Users\Admin\Desktop\Suresh\Otter Transcripts\transcripts"
    OUTPUT_FILE = r"C:\Users\Admin\Desktop\Suresh\Otter Transcripts\knowledge_graph_rag.json"
    MISTRAL_API_KEY = 'xELPoQf6Msav4CZ7fPEAfcKnJTa4UOxn'
    MODEL = "mistral-large-latest"

    print("="*70)
    print("RAG-OPTIMIZED KNOWLEDGE GRAPH BUILDER")
    print("="*70)
    print(f"Directory: {TRANSCRIPT_DIR}")
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_FILE}")
    print("\nFeatures: Intelligent chunking + Entity linking + Context preservation")
    print("="*70)

    parser = RAGTranscriptParser(
        transcript_dir=TRANSCRIPT_DIR,
        mistral_api_key=MISTRAL_API_KEY,
        model=MODEL
    )

    parser.export_to_json(OUTPUT_FILE)


if __name__ == "__main__":
    main()
