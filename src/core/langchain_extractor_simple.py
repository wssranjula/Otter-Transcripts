"""
Simplified LangChain Extractor - Focus on Strategic Business Information Only
Filters out casual conversation and personal topics
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


# ============================================
# SIMPLIFIED PYDANTIC MODELS
# ============================================

class PersonEntity(BaseModel):
    """Person mentioned in professional context"""
    name: str = Field(description="Full name")
    role: Optional[str] = Field(None, description="Professional role")
    organization: Optional[str] = Field(None, description="Organization")


class OrganizationEntity(BaseModel):
    """Organization mentioned"""
    name: str = Field(description="Organization name")
    type: Optional[str] = Field(None, description="NGO, Think_Tank, Government, Funder")


class CountryEntity(BaseModel):
    """Country discussed in strategic context"""
    name: str = Field(description="Country name")
    status: Optional[str] = Field(None, description="Current engagement status")


class TopicEntity(BaseModel):
    """Strategic topic discussed"""
    name: str = Field(description="Topic name")


class DecisionEntity(BaseModel):
    """Strategic decision made"""
    description: str = Field(description="What was decided")
    rationale: Optional[str] = Field(None, description="Why")


class ActionItemEntity(BaseModel):
    """Work item assigned"""
    task: str = Field(description="What needs to be done")
    owner: Optional[str] = Field(None, description="Who is responsible")


class SimplifiedEntities(BaseModel):
    """Core business entities only"""
    people: List[PersonEntity] = Field(default_factory=list)
    organizations: List[OrganizationEntity] = Field(default_factory=list)
    countries: List[CountryEntity] = Field(default_factory=list)
    topics: List[TopicEntity] = Field(default_factory=list)
    decisions: List[DecisionEntity] = Field(default_factory=list)
    action_items: List[ActionItemEntity] = Field(default_factory=list)


# ============================================
# SIMPLIFIED EXTRACTOR
# ============================================

class SimplifiedMistralExtractor:
    """Extract only strategic business information"""

    def __init__(self, api_key: str, model: str = "mistral-large-latest"):
        self.api_key = api_key
        self.model_name = model

        self.llm = ChatMistralAI(
            mistral_api_key=api_key,
            model=model,
            temperature=0.1,
            max_tokens=3000,
            timeout=120,  # 2 minute timeout
            max_retries=2
        )

        self.extraction_chain = self._create_extraction_chain()
        print(f"[OK] Simplified extractor initialized (model: {model})")

    def _create_extraction_chain(self):
        """Create simplified extraction chain"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting ONLY strategic business information from meeting transcripts.

IGNORE and DO NOT extract:
- Personal chitchat (weather, family, food preferences, hobbies)
- Small talk and ice breakers
- Social pleasantries
- Personal anecdotes unrelated to work
- Casual jokes or banter

ONLY extract:
- Work-related people and their professional roles
- Organizations relevant to the business
- Countries in strategic/policy context
- Strategic topics and initiatives
- Business decisions
- Work assignments and action items

Be selective and focused on business substance."""),
            ("user", """Extract ONLY strategic business information from this meeting transcript.

Meeting: {meeting_title}
Date: {meeting_date}

Transcript:
---
{transcript_chunk}
---

Extract these entities (business context only):

1. **People**: Names and roles of people discussed in professional capacity
2. **Organizations**: Companies, NGOs, think tanks, government agencies
3. **Countries**: Nations discussed in policy/strategy context
4. **Topics**: Strategic themes (NOT personal topics)
5. **Decisions**: Business decisions made
6. **Action Items**: Work tasks assigned

{format_instructions}

REMEMBER: Skip all personal/casual content. Focus on strategic business substance only.""")
        ])

        parser = JsonOutputParser(pydantic_object=SimplifiedEntities)
        chain = prompt | self.llm | parser

        return chain

    def extract_from_chunk(self, chunk: str, meeting_info: dict) -> dict:
        """Extract from a chunk"""
        try:
            parser = JsonOutputParser(pydantic_object=SimplifiedEntities)

            result = self.extraction_chain.invoke({
                "meeting_title": meeting_info.get("title", "Unknown"),
                "meeting_date": meeting_info.get("date", "Unknown"),
                "transcript_chunk": chunk,
                "format_instructions": parser.get_format_instructions()
            })

            return result

        except Exception as e:
            print(f"    [WARN] Extraction error: {e}")
            return self._empty_result()

    def extract_entities(self, transcript_text: str, meeting_info: dict) -> dict:
        """Extract all strategic entities"""

        print(f"  Extracting: {meeting_info.get('title', 'Unknown')}")

        # Filter out obvious casual content first
        filtered_text = self._filter_casual_content(transcript_text)

        # Split into chunks
        chunks = self._chunk_transcript(filtered_text)
        print(f"    Processing {len(chunks)} chunk(s)...")

        all_entities = self._empty_result()

        for i, chunk in enumerate(chunks, 1):
            print(f"    Chunk {i}/{len(chunks)}... ", end="", flush=True)
            chunk_entities = self.extract_from_chunk(chunk, meeting_info)

            # Merge
            for key in all_entities:
                if isinstance(all_entities[key], list):
                    all_entities[key].extend(chunk_entities.get(key, []))

            print("[OK]")

        # Deduplicate
        all_entities = self._deduplicate_entities(all_entities)

        # Filter low-value entities
        all_entities = self._filter_trivial_entities(all_entities)

        print(f"    [OK] {len(all_entities['people'])} people, "
              f"{len(all_entities['decisions'])} decisions, "
              f"{len(all_entities['action_items'])} actions")

        return all_entities

    def _filter_casual_content(self, text: str) -> str:
        """Remove obvious casual conversation sections"""
        import re

        # Keywords indicating personal/casual content
        casual_keywords = [
            r'\begg\b.*\bcook',
            r'\bweather\b',
            r'\bfamily\b.*\bvacation\b',
            r'\bhow.*weekend\b',
            r'\bbirthday\b',
            r'\bpersonal.*update\b'
        ]

        lines = text.split('\n')
        filtered_lines = []

        for line in lines:
            # Skip if line matches casual patterns
            is_casual = any(re.search(pattern, line, re.IGNORECASE) for pattern in casual_keywords)

            if not is_casual:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def _filter_trivial_entities(self, entities: dict) -> dict:
        """Remove low-value entities"""

        # Filter out generic topics
        trivial_topics = {'update', 'discussion', 'meeting', 'call', 'check-in', 'hello', 'introduction'}
        entities['topics'] = [t for t in entities['topics']
                             if t['name'].lower() not in trivial_topics]

        # Filter out very short action items (likely noise)
        entities['action_items'] = [a for a in entities['action_items']
                                    if len(a['task']) > 15]

        # Filter out very short decisions (likely noise)
        entities['decisions'] = [d for d in entities['decisions']
                                if len(d['description']) > 20]

        return entities

    def _chunk_transcript(self, text: str, max_chars: int = 12000) -> List[str]:
        """Split into chunks"""
        import re

        speaker_pattern = r'\n([A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+\d{1,2}:\d{2}'
        segments = re.split(f'({speaker_pattern})', text)

        chunks = []
        current_chunk = ""

        for segment in segments:
            if len(current_chunk) + len(segment) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = segment
            else:
                current_chunk += segment

        if current_chunk:
            chunks.append(current_chunk)

        if not chunks:
            for i in range(0, len(text), max_chars):
                chunks.append(text[i:i + max_chars])

        return chunks

    def _deduplicate_entities(self, entities: dict) -> dict:
        """Remove duplicates"""
        import json

        for key in entities:
            if isinstance(entities[key], list):
                seen = set()
                unique = []
                for item in entities[key]:
                    item_str = json.dumps(item, sort_keys=True)
                    if item_str not in seen:
                        seen.add(item_str)
                        unique.append(item)
                entities[key] = unique

        return entities

    def _empty_result(self) -> dict:
        """Empty result structure"""
        return {
            'people': [],
            'organizations': [],
            'countries': [],
            'topics': [],
            'decisions': [],
            'action_items': []
        }


# ============================================
# TEST
# ============================================

def test_extractor():
    """Test simplified extractor"""
    import os

    api_key = os.getenv("MISTRAL_API_KEY") or "YOUR_MISTRAL_API_KEY_HERE"

    # Sample with both business and casual content
    sample_text = """
Ben Margetts  00:01
Before we start, quick icebreaker - how do you like your eggs cooked?

Tom Pravda  00:10
Scrambled! Anyway, let's get to business. We need to decide on the Germany strategy.

Ben Margetts  00:20
Right. Tom, what's your assessment of engaging Germany right now?

Tom Pravda  00:25
Germany is too risky. They're too porous with anti-SRM NGOs. I recommend we wait.
Sue Biniaz agrees with this assessment.

Ben Margetts  00:45
Makes sense. Let's deprioritize Germany and focus on UK and Kenya instead.
Craig, can you follow up on the Texas proposal?

Craig Segall  01:00
Yes, I'll finalize the TCCRI white paper funding this week. Around $50k.
"""

    print("\n" + "="*70)
    print("TESTING SIMPLIFIED EXTRACTOR")
    print("="*70)

    extractor = SimplifiedMistralExtractor(api_key=api_key)

    meeting_info = {
        'title': 'Strategy Call',
        'date': '2024-10-01',
        'category': 'Strategy'
    }

    results = extractor.extract_entities(sample_text, meeting_info)

    import json
    print("\n" + "="*70)
    print("EXTRACTED (should skip egg discussion)")
    print("="*70)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    test_extractor()
