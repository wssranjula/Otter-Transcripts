"""
Intelligent Chunking Logic for RAG
Splits transcripts into meaningful conversation segments
"""

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class ConversationChunk:
    """Represents a chunk of conversation"""
    text: str
    speakers: List[str]
    start_time: str
    sequence_number: int
    topic_hint: str = None
    chunk_type: str = "discussion"  # discussion, decision, action_assignment, assessment, question
    importance_score: float = 0.5


class TranscriptChunker:
    """Intelligently chunk transcripts for RAG"""

    def __init__(self, min_chunk_size: int = 300, max_chunk_size: int = 1500):
        """
        Initialize chunker

        Args:
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # Patterns for identifying chunk boundaries
        self.topic_change_patterns = [
            r'\b(okay|alright|so|now|next|moving on)\b.*\b(let\'s|we should|need to)\b',
            r'\b(another|different|next)\s+(topic|item|thing|point)\b',
            r'\b(shifting|moving|turning)\s+to\b'
        ]

        # Patterns for identifying chunk types
        self.decision_patterns = [
            r'\b(decided|decision|agreed|conclude|let\'s go with)\b',
            r'\b(we\'re going to|we will|we should)\b'
        ]

        self.action_patterns = [
            r'\b(will|should|need to|have to)\s+\w+\s+(do|follow up|reach out|finalize|schedule)\b',
            r'\b(action item|to do|task)\b',
            r'\b([A-Z][a-z]+)\s+(will|should|to)\s+\w+'  # "Craig will do X"
        ]

        self.question_patterns = [
            r'\?$',
            r'\b(what|why|how|when|where|who)\b.*\?',
            r'\b(question|wondering|curious)\b'
        ]

        self.assessment_patterns = [
            r'\b(assessment|evaluation|view|opinion|think|believe)\b',
            r'\b(too risky|opportunity|challenge|concern)\b',
            r'\b(strengths?|weaknesses?|pros?|cons?)\b'
        ]

    def chunk_transcript(self, transcript_text: str, meeting_info: Dict) -> List[ConversationChunk]:
        """
        Chunk transcript into conversation segments

        Args:
            transcript_text: Full transcript text
            meeting_info: Meeting metadata

        Returns:
            List of ConversationChunk objects
        """
        # Parse into speaker turns
        turns = self._parse_speaker_turns(transcript_text)

        if not turns:
            # Fallback: simple chunking
            return self._simple_chunk(transcript_text)

        # Group turns into chunks
        chunks = self._group_turns_into_chunks(turns)

        # Classify each chunk
        classified_chunks = []
        for i, chunk in enumerate(chunks):
            classified = self._classify_chunk(chunk, i)
            classified_chunks.append(classified)

        return classified_chunks

    def _parse_speaker_turns(self, text: str) -> List[Dict]:
        """Parse transcript into speaker turns"""
        # Pattern: Speaker Name  timestamp
        pattern = r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+(\d{1,2}:\d{2})\s*$'

        turns = []
        current_speaker = None
        current_time = None
        current_text = []

        lines = text.split('\n')

        for line in lines:
            # Check if this is a speaker line
            match = re.match(pattern, line.strip())

            if match:
                # Save previous turn
                if current_speaker and current_text:
                    turns.append({
                        'speaker': current_speaker,
                        'time': current_time,
                        'text': '\n'.join(current_text).strip()
                    })

                # Start new turn
                current_speaker = match.group(1)
                current_time = match.group(2)
                current_text = []
            else:
                # Continue current turn
                if line.strip():
                    current_text.append(line.strip())

        # Save last turn
        if current_speaker and current_text:
            turns.append({
                'speaker': current_speaker,
                'time': current_time,
                'text': '\n'.join(current_text).strip()
            })

        return turns

    def _group_turns_into_chunks(self, turns: List[Dict]) -> List[Dict]:
        """Group speaker turns into coherent chunks"""
        chunks = []
        current_chunk = {
            'text': [],
            'speakers': [],
            'start_time': None,
            'turn_count': 0
        }

        for turn in turns:
            turn_text = f"{turn['speaker']}: {turn['text']}"
            turn_length = len(turn_text)

            # Start new chunk if:
            # 1. Current chunk too large
            # 2. Topic change detected
            # 3. Natural break (empty turn, etc.)

            current_size = sum(len(t) for t in current_chunk['text'])

            should_break = False

            # Check if adding this turn exceeds max size
            if current_size + turn_length > self.max_chunk_size and current_size > self.min_chunk_size:
                should_break = True

            # Check for topic change indicators
            if self._is_topic_change(turn['text']):
                if current_size > self.min_chunk_size:
                    should_break = True

            if should_break and current_chunk['text']:
                # Save current chunk
                chunks.append({
                    'text': '\n'.join(current_chunk['text']),
                    'speakers': list(set(current_chunk['speakers'])),
                    'start_time': current_chunk['start_time'],
                    'turn_count': current_chunk['turn_count']
                })

                # Start new chunk
                current_chunk = {
                    'text': [],
                    'speakers': [],
                    'start_time': turn['time'],
                    'turn_count': 0
                }

            # Add turn to current chunk
            if not current_chunk['start_time']:
                current_chunk['start_time'] = turn['time']

            current_chunk['text'].append(turn_text)
            current_chunk['speakers'].append(turn['speaker'])
            current_chunk['turn_count'] += 1

        # Save last chunk
        if current_chunk['text']:
            chunks.append({
                'text': '\n'.join(current_chunk['text']),
                'speakers': list(set(current_chunk['speakers'])),
                'start_time': current_chunk['start_time'],
                'turn_count': current_chunk['turn_count']
            })

        return chunks

    def _is_topic_change(self, text: str) -> bool:
        """Detect if this turn indicates a topic change"""
        text_lower = text.lower()

        for pattern in self.topic_change_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _classify_chunk(self, chunk: Dict, sequence: int) -> ConversationChunk:
        """Classify chunk type and calculate importance"""
        text = chunk['text']
        text_lower = text.lower()

        # Determine chunk type
        chunk_type = "discussion"  # Default
        importance = 0.5

        # Check for decision
        if any(re.search(pattern, text_lower) for pattern in self.decision_patterns):
            chunk_type = "decision"
            importance = 0.9

        # Check for action assignment
        elif any(re.search(pattern, text_lower) for pattern in self.action_patterns):
            chunk_type = "action_assignment"
            importance = 0.8

        # Check for assessment
        elif any(re.search(pattern, text_lower) for pattern in self.assessment_patterns):
            chunk_type = "assessment"
            importance = 0.7

        # Check for question
        elif any(re.search(pattern, text_lower) for pattern in self.question_patterns):
            chunk_type = "question"
            importance = 0.6

        # Adjust importance based on length (longer = more substantive)
        length_factor = min(len(text) / 1000, 1.0)  # Normalize to 0-1
        importance = (importance + length_factor) / 2

        # Adjust importance based on speaker diversity (more speakers = more important)
        speaker_factor = min(len(chunk['speakers']) / 3, 1.0)
        importance = (importance + speaker_factor) / 2

        return ConversationChunk(
            text=text,
            speakers=chunk['speakers'],
            start_time=chunk['start_time'],
            sequence_number=sequence,
            chunk_type=chunk_type,
            importance_score=round(importance, 2)
        )

    def _simple_chunk(self, text: str) -> List[ConversationChunk]:
        """Fallback: simple size-based chunking"""
        chunks = []
        chunk_size = self.max_chunk_size

        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i + chunk_size]

            chunks.append(ConversationChunk(
                text=chunk_text,
                speakers=["Unknown"],
                start_time="00:00",
                sequence_number=i // chunk_size,
                chunk_type="discussion",
                importance_score=0.5
            ))

        return chunks


def test_chunker():
    """Test the chunker"""

    sample_transcript = """
Ben Margetts  00:01
We need to decide on the Germany strategy. Tom, what's your assessment?

Tom Pravda  00:15
Germany is too risky right now. They're too porous with anti-SRM NGOs like Heinrich Böll Foundation.
If we engage now, there's a high likelihood of leaks. I recommend we wait until the field
is more mature. Sue Biniaz agrees with this assessment.

Ben Margetts  00:45
Makes sense. Let's deprioritize Germany and focus on UK and Kenya instead. Craig, can you
follow up on the Texas Republican think tank proposal?

Craig Segall  01:00
Yes, I'll finalize the TCCRI white paper funding this week. Should be around $50k.

Ben Margetts  01:15
Great. Moving on to the next topic - let's talk about climate week planning.

Tom Pravda  01:20
We have three events scheduled. Should we coordinate with FAS on their briefing?
"""

    print("="*70)
    print("TESTING TRANSCRIPT CHUNKER")
    print("="*70)

    chunker = TranscriptChunker(min_chunk_size=200, max_chunk_size=800)

    meeting_info = {
        'title': 'Strategy Call',
        'date': '2024-10-01'
    }

    chunks = chunker.chunk_transcript(sample_transcript, meeting_info)

    print(f"\nGenerated {len(chunks)} chunks:\n")

    for i, chunk in enumerate(chunks, 1):
        print(f"--- CHUNK {i} ---")
        print(f"Type: {chunk.chunk_type}")
        print(f"Speakers: {', '.join(chunk.speakers)}")
        print(f"Importance: {chunk.importance_score}")
        print(f"Start time: {chunk.start_time}")
        print(f"\nText ({len(chunk.text)} chars):")
        print(chunk.text[:300] + "..." if len(chunk.text) > 300 else chunk.text)
        print()


if __name__ == "__main__":
    test_chunker()
