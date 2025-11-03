"""
WhatsApp Chat Export Parser
Parses WhatsApp .txt exports and creates RAG-optimized chunks
"""

import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Optional embeddings support
try:
    from src.core.embeddings import MistralEmbedder
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    MistralEmbedder = None


@dataclass
class WhatsAppMessage:
    """Individual WhatsApp message"""
    timestamp: datetime
    sender: str
    text: str
    message_type: str  # "text" | "media" | "system" | "deleted"
    media_type: Optional[str] = None  # "image" | "video" | "document" | "voice" | "sticker"
    is_forwarded: bool = False
    sequence: int = 0


class WhatsAppParser:
    """Parse WhatsApp chat exports into RAG-friendly format"""

    # WhatsApp message patterns
    MESSAGE_PATTERNS = [
        # Pattern 1: DD/MM/YYYY, HH:MM - Sender: Message
        r'^(\d{1,2}/\d{1,2}/\d{4}),\s(\d{1,2}:\d{2})\s-\s([^:]+):\s(.+)$',
        # Pattern 2: [DD/MM/YYYY, HH:MM:SS] Sender: Message
        r'^\[(\d{1,2}/\d{1,2}/\d{4}),\s(\d{1,2}:\d{2}:\d{2})\]\s([^:]+):\s(.+)$',
        # Pattern 3: DD/MM/YY, HH:MM - Sender: Message
        r'^(\d{1,2}/\d{1,2}/\d{2}),\s(\d{1,2}:\d{2})\s-\s([^:]+):\s(.+)$',
        # Pattern 4: [M/D/YY, H:MM:SS AM/PM] Sender: Message (US format with 12-hour time)
        r'^\[(\d{1,2}/\d{1,2}/\d{2}),\s(\d{1,2}:\d{2}:\d{2}\s[AP]M)\]\s([^:]+):\s(.+)$',
    ]

    SYSTEM_MESSAGE_PATTERNS = [
        r'created group',
        r'added you',
        r'joined using this',
        r'left',
        r'removed',
        r'changed the subject',
        r'changed this group',
        r'security code changed',
        r'Messages and calls are end-to-end encrypted',
    ]

    MEDIA_INDICATORS = {
        '<Media omitted>': 'media',
        '‎image omitted': 'image',
        '‎video omitted': 'video',
        '‎audio omitted': 'voice',
        '‎document omitted': 'document',
        '‎sticker omitted': 'sticker',
        '‎GIF omitted': 'gif',
        '‎Contact card omitted': 'contact',
        '‎Location': 'location',
    }

    def __init__(self, mistral_api_key: str = None, generate_embeddings: bool = False):
        """
        Initialize WhatsApp parser

        Args:
            mistral_api_key: Optional API key for entity extraction and embeddings
            generate_embeddings: Whether to generate embeddings for chunks
        """
        self.mistral_api_key = mistral_api_key
        self.generate_embeddings = generate_embeddings
        
        # Initialize entity extractor
        self.extractor = None
        if mistral_api_key:
            try:
                from src.core.langchain_extractor_simple import SimplifiedMistralExtractor
                self.extractor = SimplifiedMistralExtractor(
                    api_key=mistral_api_key,
                    model="mistral-large-latest"
                )
            except Exception as e:
                print(f"[WARN] Could not initialize entity extractor: {e}")
        
        # Initialize embedder
        self.embedder = None
        if generate_embeddings and mistral_api_key:
            if EMBEDDINGS_AVAILABLE:
                self.embedder = MistralEmbedder(api_key=mistral_api_key)
                print("[OK] Embeddings enabled for WhatsApp parser")
            else:
                print("[WARN] Embeddings requested but module not available")

    def parse_chat_file(self, file_path: str) -> Dict:
        """
        Parse WhatsApp export file

        Returns:
            {
                'conversation': {...},
                'messages': [...],
                'chunks': [...],
                'participants': [...],
                'entities': [...]
            }
        """
        print(f"\n[LOG] Parsing WhatsApp chat: {Path(file_path).name}")

        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse messages
        messages = self._parse_messages(content)
        print(f"[OK] Parsed {len(messages)} messages")

        if not messages:
            print("[ERROR] No messages found in file")
            return None

        # Extract conversation metadata
        conversation = self._extract_conversation_metadata(file_path, messages)
        print(f"[OK] Conversation: {conversation['group_name']}")
        print(f"[OK] Date range: {conversation['date_range_start']} to {conversation['date_range_end']}")

        # Extract participants
        participants = self._extract_participants(messages)
        print(f"[OK] Found {len(participants)} participants")

        # Create chunks
        chunks = self._chunk_messages(messages, conversation)
        print(f"[OK] Created {len(chunks)} chunks")

        # Extract entities
        entities = []
        if self.extractor:
            print(f"[LOG] Extracting entities...")
            entities = self._extract_entities(chunks, conversation)
            print(f"[OK] Extracted {len(entities)} entities")

        # Link chunks to entities
        chunk_entity_links = self._link_chunks_to_entities(chunks, entities)
        print(f"[OK] Created {len(chunk_entity_links)} chunk-entity links")

        # Generate embeddings if enabled
        if self.embedder and chunks:
            print(f"[LOG] Generating embeddings for chunks...")
            self.embedder.embed_chunks(chunks)
            print(f"[OK] Embeddings generated")

        return {
            'conversation': conversation,
            'messages': [self._message_to_dict(m, conversation['id']) for m in messages],
            'chunks': chunks,
            'participants': participants,
            'entities': entities,
            'chunk_entity_links': chunk_entity_links
        }

    def _parse_messages(self, content: str) -> List[WhatsAppMessage]:
        """Parse all messages from chat content"""
        messages = []
        lines = content.split('\n')

        current_message = None
        sequence = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to parse as new message
            parsed = self._parse_message_line(line)

            if parsed:
                # Save previous message
                if current_message:
                    current_message.sequence = sequence
                    messages.append(current_message)
                    sequence += 1

                # Start new message
                timestamp, sender, text = parsed
                msg_type, media_type = self._detect_message_type(text)

                current_message = WhatsAppMessage(
                    timestamp=timestamp,
                    sender=sender,
                    text=text,
                    message_type=msg_type,
                    media_type=media_type,
                    is_forwarded=False
                )
            else:
                # Continuation of previous message (multi-line)
                if current_message:
                    current_message.text += "\n" + line

        # Add last message
        if current_message:
            current_message.sequence = sequence
            messages.append(current_message)

        return messages

    def _parse_message_line(self, line: str) -> Optional[Tuple[datetime, str, str]]:
        """
        Parse a single message line

        Returns: (timestamp, sender, text) or None
        """
        for pattern in self.MESSAGE_PATTERNS:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()

                # Extract date and time
                date_str = groups[0]
                time_str = groups[1]
                sender = groups[2].strip()
                text = groups[3]

                # Parse timestamp
                try:
                    timestamp = self._parse_timestamp(date_str, time_str)
                    return (timestamp, sender, text)
                except Exception as e:
                    print(f"[WARN] Could not parse timestamp: {date_str} {time_str} - {e}")
                    continue

        return None

    def _parse_timestamp(self, date_str: str, time_str: str) -> datetime:
        """Parse WhatsApp timestamp"""
        # Try different date formats
        date_formats = [
            '%d/%m/%Y',  # DD/MM/YYYY
            '%m/%d/%Y',  # MM/DD/YYYY
            '%d/%m/%y',  # DD/MM/YY 
            '%m/%d/%y',  # MM/DD/YY
        ]

        time_formats = [
            '%H:%M',          # HH:MM (24-hour)
            '%H:%M:%S',       # HH:MM:SS (24-hour)
            '%I:%M:%S %p',    # H:MM:SS AM/PM (12-hour)
            '%I:%M %p',       # H:MM AM/PM (12-hour)
        ]

        for date_fmt in date_formats:
            for time_fmt in time_formats:
                try:
                    dt_str = f"{date_str} {time_str}"
                    fmt = f"{date_fmt} {time_fmt}"
                    dt = datetime.strptime(dt_str, fmt)

                    # If year is 2-digit and parsed as 19xx, adjust to 20xx
                    if dt.year < 2000:
                        dt = dt.replace(year=dt.year + 100)

                    return dt
                except ValueError:
                    continue

        raise ValueError(f"Could not parse timestamp: {date_str} {time_str}")

    def _detect_message_type(self, text: str) -> Tuple[str, Optional[str]]:
        """
        Detect message type and media type

        Returns: (message_type, media_type)
        """
        # Check for media
        for indicator, media_type in self.MEDIA_INDICATORS.items():
            if indicator in text:
                return ("media", media_type)

        # Check for deleted message
        if "This message was deleted" in text or "You deleted this message" in text:
            return ("deleted", None)

        # Check for system message
        for pattern in self.SYSTEM_MESSAGE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ("system", None)

        return ("text", None)

    def _extract_conversation_metadata(self, file_path: str, messages: List[WhatsAppMessage]) -> Dict:
        """Extract conversation metadata"""
        file_path = Path(file_path)

        # Extract group name from filename
        filename = file_path.stem
        group_name = filename.replace('WhatsApp Chat with ', '').replace('_', ' ')

        # Date range
        date_range_start = min(m.timestamp for m in messages).isoformat()
        date_range_end = max(m.timestamp for m in messages).isoformat()

        # Count participants (excluding system messages)
        participants = set(m.sender for m in messages if m.message_type != "system")

        # Generate ID
        conversation_id = self._generate_id(f"{group_name}_{date_range_start}")

        return {
            'id': conversation_id,
            'group_name': group_name,
            'created_date': date_range_start,
            'export_date': datetime.now().isoformat(),
            'participant_count': len(participants),
            'message_count': len(messages),
            'date_range_start': date_range_start,
            'date_range_end': date_range_end,
            'source_file': str(file_path),
            'platform': 'WhatsApp',
            'conversation_type': 'group_chat' if len(participants) > 2 else 'direct_message'
        }

    def _extract_participants(self, messages: List[WhatsAppMessage]) -> List[Dict]:
        """Extract participant information"""
        participants = {}

        for msg in messages:
            if msg.message_type == "system":
                continue

            sender = msg.sender
            if sender not in participants:
                participants[sender] = {
                    'name': sender,
                    'message_count': 0,
                    'first_message_date': msg.timestamp.isoformat(),
                    'last_message_date': msg.timestamp.isoformat(),
                    'media_shared_count': 0
                }

            participants[sender]['message_count'] += 1
            participants[sender]['last_message_date'] = msg.timestamp.isoformat()

            if msg.message_type == "media":
                participants[sender]['media_shared_count'] += 1

        return list(participants.values())

    def _chunk_messages(self, messages: List[WhatsAppMessage], conversation: Dict) -> List[Dict]:
        """
        Group messages into chunks using intelligent strategy

        Strategy:
        - 15-minute time windows
        - Max 20 messages per chunk
        - Min 3 messages per chunk
        - Max 1500 characters
        """
        chunks = []
        current_chunk_messages = []

        TIME_WINDOW_MINUTES = 15
        MAX_MESSAGES = 20
        MIN_MESSAGES = 3
        MAX_CHARS = 1500

        for i, msg in enumerate(messages):
            # Skip system messages for chunking
            if msg.message_type == "system":
                continue

            current_chunk_messages.append(msg)

            # Check if we should close chunk
            should_close = False

            if len(current_chunk_messages) >= MAX_MESSAGES:
                should_close = True
            elif self._get_chunk_char_count(current_chunk_messages) >= MAX_CHARS:
                should_close = True
            elif i + 1 < len(messages):
                next_msg = messages[i + 1]
                time_gap = (next_msg.timestamp - msg.timestamp).total_seconds() / 60
                if time_gap > TIME_WINDOW_MINUTES:
                    should_close = True

            if should_close and len(current_chunk_messages) >= MIN_MESSAGES:
                chunk = self._create_chunk(current_chunk_messages, len(chunks), conversation)
                chunks.append(chunk)
                current_chunk_messages = []

        # Add remaining messages
        if len(current_chunk_messages) >= MIN_MESSAGES:
            chunk = self._create_chunk(current_chunk_messages, len(chunks), conversation)
            chunks.append(chunk)

        return chunks

    def _create_chunk(self, messages: List[WhatsAppMessage], sequence: int, conversation: Dict) -> Dict:
        """Create chunk from message list"""

        # Format chunk text
        chunk_text = self._format_chunk_text(messages)

        # Extract metadata
        participants = list(set(m.sender for m in messages))
        time_start = messages[0].timestamp
        time_end = messages[-1].timestamp
        duration_minutes = (time_end - time_start).total_seconds() / 60

        # Count media
        media_count = sum(1 for m in messages if m.message_type == "media")

        # Calculate importance score (simple heuristic)
        importance_score = self._calculate_importance(messages)

        chunk_id = self._generate_id(f"{conversation['id']}_{sequence}")

        return {
            'id': chunk_id,
            'text': chunk_text,
            'sequence_number': sequence,
            'importance_score': importance_score,

            # Source reference (universal)
            'source_id': conversation['id'],
            'source_title': conversation['group_name'],
            'source_date': conversation['date_range_start'],
            'source_type': 'whatsapp_chat',

            # WhatsApp-specific
            'participants': participants,
            'message_count': len(messages),
            'time_start': time_start.isoformat(),
            'time_end': time_end.isoformat(),
            'chunk_duration_minutes': round(duration_minutes, 2),
            'has_media': media_count > 0,
            'media_count': media_count,
        }

    def _format_chunk_text(self, messages: List[WhatsAppMessage]) -> str:
        """Format messages into readable chunk text"""
        lines = []

        # Header
        time_start = messages[0].timestamp.strftime('%Y-%m-%d %H:%M')
        time_end = messages[-1].timestamp.strftime('%H:%M')
        participants = list(set(m.sender for m in messages))

        lines.append(f"[WhatsApp Conversation: {time_start} to {time_end}]")
        lines.append(f"Participants: {', '.join(participants)}")
        lines.append(f"Messages: {len(messages)}")
        lines.append("")

        # Messages
        for msg in messages:
            time_str = msg.timestamp.strftime('%H:%M')

            if msg.message_type == "media":
                text = f"<{msg.media_type.upper() if msg.media_type else 'MEDIA'}>"
            elif msg.message_type == "deleted":
                text = "<Deleted message>"
            else:
                text = msg.text

            lines.append(f"{msg.sender} ({time_str}): {text}")

        return "\n".join(lines)

    def _get_chunk_char_count(self, messages: List[WhatsAppMessage]) -> int:
        """Get total character count for messages"""
        return sum(len(m.text) for m in messages)

    def _calculate_importance(self, messages: List[WhatsAppMessage]) -> float:
        """
        Calculate importance score for chunk

        Heuristics:
        - Longer messages = more important
        - More participants = more important
        - Media shared = slightly more important
        """
        # Base score
        score = 0.5

        # Message length factor
        avg_length = self._get_chunk_char_count(messages) / len(messages)
        if avg_length > 100:
            score += 0.2
        elif avg_length > 50:
            score += 0.1

        # Participant diversity
        participant_count = len(set(m.sender for m in messages))
        if participant_count > 3:
            score += 0.2
        elif participant_count > 2:
            score += 0.1

        # Media presence
        media_count = sum(1 for m in messages if m.message_type == "media")
        if media_count > 0:
            score += 0.1

        return min(score, 1.0)

    def _extract_entities(self, chunks: List[Dict], conversation: Dict) -> List[Dict]:
        """Extract entities from chunks using Mistral"""
        if not self.extractor:
            return []

        # Combine chunks into sample text (use first 5 chunks for performance)
        sample_chunks = chunks[:5]
        sample_text = "\n\n".join(c['text'] for c in sample_chunks)

        # Extract entities
        try:
            entities_data = self.extractor.extract_entities(sample_text, conversation)
            entities = self._process_entities(entities_data)
            return entities
        except Exception as e:
            print(f"[WARN] Entity extraction failed: {e}")
            return []

    def _process_entities(self, entities_data: Dict) -> List[Dict]:
        """Process extracted entities into unified format"""
        entities = []
        entity_cache = {}

        # People
        for person in entities_data.get('people', []):
            entity_id = self._generate_id(person['name'])
            if entity_id not in entity_cache:
                entities.append({
                    'id': entity_id,
                    'name': person['name'],
                    'type': 'Person',
                    'properties': {
                        'role': person.get('role'),
                        'organization': person.get('organization')
                    }
                })
                entity_cache[entity_id] = True

        # Organizations
        for org in entities_data.get('organizations', []):
            entity_id = self._generate_id(org['name'])
            if entity_id not in entity_cache:
                entities.append({
                    'id': entity_id,
                    'name': org['name'],
                    'type': 'Organization',
                    'properties': {
                        'org_type': org.get('type')
                    }
                })
                entity_cache[entity_id] = True

        # Topics
        for topic in entities_data.get('topics', []):
            entity_id = self._generate_id(topic['name'])
            if entity_id not in entity_cache:
                entities.append({
                    'id': entity_id,
                    'name': topic['name'],
                    'type': 'Topic',
                    'properties': {}
                })
                entity_cache[entity_id] = True

        return entities

    def _link_chunks_to_entities(self, chunks: List[Dict], entities: List[Dict]) -> List[Dict]:
        """Find which entities are mentioned in which chunks"""
        links = []

        for chunk_idx, chunk in enumerate(chunks):
            chunk_text_lower = chunk['text'].lower()

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

    def _message_to_dict(self, message: WhatsAppMessage, conversation_id: str) -> Dict:
        """Convert WhatsAppMessage to dict"""
        message_id = self._generate_id(f"{conversation_id}_{message.sequence}")

        return {
            'id': message_id,
            'text': message.text,
            'sender': message.sender,
            'timestamp': message.timestamp.isoformat(),
            'message_type': message.message_type,
            'media_type': message.media_type,
            'is_forwarded': message.is_forwarded,
            'sequence_in_conversation': message.sequence,
            'conversation_id': conversation_id
        }

    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()[:12]


def main():
    """Test WhatsApp parser"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python whatsapp_parser.py <whatsapp_export.txt>")
        sys.exit(1)

    file_path = sys.argv[1]

    parser = WhatsAppParser()
    result = parser.parse_chat_file(file_path)

    if result:
        print("\n" + "="*70)
        print("PARSING COMPLETE")
        print("="*70)
        print(f"Conversation: {result['conversation']['group_name']}")
        print(f"Messages: {len(result['messages'])}")
        print(f"Chunks: {len(result['chunks'])}")
        print(f"Participants: {len(result['participants'])}")
        print(f"Entities: {len(result['entities'])}")
        print("="*70)


if __name__ == "__main__":
    main()
