"""
Confidentiality and Status Detection for RAG Pipeline
Automatically detects confidentiality levels and document status from metadata
"""

import re
from typing import Dict, List


class ConfidentialityDetector:
    """Detect confidentiality levels and document status from meeting metadata"""
    
    def __init__(self):
        """Initialize detection rules"""
        
        # Filename/title patterns for confidentiality
        self.confidential_patterns = [
            r'confidential',
            r'sensitive',
            r'restricted',
            r'classified',
            r'private',
            r'internal only',
            r'executive',
            r'board',
            r'principals',
            r'leadership'
        ]
        
        # Filename/title patterns for draft status
        self.draft_patterns = [
            r'draft',
            r'wip',
            r'work in progress',
            r'preliminary',
            r'rough',
            r'v0\.',
            r'working copy',
            r'temp',
            r'scratch'
        ]
        
        # Category-based confidentiality
        self.category_confidentiality = {
            'Principals_Call': 'CONFIDENTIAL',
            'Leadership_Call': 'CONFIDENTIAL',
            'Board_Meeting': 'CONFIDENTIAL',
            'Executive_Session': 'CONFIDENTIAL',
            'Funder_Call': 'CONFIDENTIAL',
            'Legal_Review': 'RESTRICTED',
            'HR_Meeting': 'RESTRICTED',
            'Team_Meeting': 'INTERNAL',
            'All_Hands': 'INTERNAL',
            'Field_Coordination': 'INTERNAL',
            'Public_Event': 'PUBLIC'
        }
        
        # Participant-based detection
        self.restricted_participant_keywords = [
            'lawyer',
            'attorney',
            'counsel',
            'hr director',
            'general counsel'
        ]
    
    def detect_confidentiality(self, meeting: Dict) -> str:
        """
        Detect confidentiality level from meeting metadata
        
        Args:
            meeting: Meeting dictionary with title, category, participants, etc.
            
        Returns:
            Confidentiality level: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
        """
        title = meeting.get('title', '').lower()
        category = meeting.get('category', '')
        participants = [p.lower() for p in meeting.get('participants', [])]
        filename = meeting.get('transcript_file', '').lower()
        
        # Check for RESTRICTED (highest priority)
        for keyword in self.restricted_participant_keywords:
            if any(keyword in p for p in participants):
                return 'RESTRICTED'
        
        if any(re.search(pattern, title) for pattern in ['legal', 'hr ', 'personnel']):
            return 'RESTRICTED'
        
        # Check for CONFIDENTIAL
        # 1. Category-based
        if category in self.category_confidentiality:
            level = self.category_confidentiality[category]
            if level in ['CONFIDENTIAL', 'RESTRICTED']:
                return level
        
        # 2. Title/filename-based
        if any(re.search(pattern, title) for pattern in self.confidential_patterns):
            return 'CONFIDENTIAL'
        
        if any(re.search(pattern, filename) for pattern in self.confidential_patterns):
            return 'CONFIDENTIAL'
        
        # Default to INTERNAL for most organizational content
        return 'INTERNAL'
    
    def detect_status(self, meeting: Dict) -> str:
        """
        Detect document status from meeting metadata
        
        Args:
            meeting: Meeting dictionary with title, category, etc.
            
        Returns:
            Document status: FINAL (always - no drafts in this workflow)
        """
        # SIMPLIFIED for workflows with only completed documents
        # All documents are FINAL - no draft detection needed
        return 'FINAL'
    
    def detect_tags(self, meeting: Dict) -> List[str]:
        """
        Generate tags from meeting metadata
        
        Args:
            meeting: Meeting dictionary
            
        Returns:
            List of tags
        """
        tags = []
        title = meeting.get('title', '').lower()
        category = meeting.get('category', '')
        
        # Add category as tag
        if category:
            tags.append(category.lower().replace('_', '-'))
        
        # Topic-based tags
        topic_keywords = {
            'unea': ['unea', 'environment assembly'],
            'funding': ['funding', 'fundraising', 'grant', 'proposal'],
            'strategy': ['strategy', 'strategic', 'planning'],
            'media': ['media', 'press', 'communications', 'pr'],
            'international': ['international', 'country', 'diplomatic'],
            'research': ['research', 'science', 'scientific'],
            'policy': ['policy', 'legislation', 'regulatory'],
            'srm': ['srm', 'solar radiation', 'geoengineering']
        }
        
        for tag, keywords in topic_keywords.items():
            if any(keyword in title for keyword in keywords):
                tags.append(tag)
        
        # Priority indicators
        if any(word in title for word in ['urgent', 'priority', 'critical']):
            tags.append('priority')
        
        if any(word in title for word in ['decision', 'vote']):
            tags.append('decision-making')
        
        return tags
    
    def enrich_meeting(self, meeting: Dict) -> Dict:
        """
        Enrich meeting with detected confidentiality, status, and tags
        
        Args:
            meeting: Original meeting dictionary
            
        Returns:
            Meeting dictionary with added fields
        """
        enriched = meeting.copy()
        
        enriched['confidentiality_level'] = self.detect_confidentiality(meeting)
        enriched['document_status'] = self.detect_status(meeting)
        enriched['tags'] = self.detect_tags(meeting)
        
        return enriched


# Example usage
if __name__ == "__main__":
    detector = ConfidentialityDetector()
    
    # Test cases
    test_meetings = [
        {
            'title': 'Principals Call - October Strategy',
            'category': 'Principals_Call',
            'participants': ['Chris', 'Ben', 'Sarah'],
            'transcript_file': 'principals_oct_2024.txt'
        },
        {
            'title': 'DRAFT - UNEA 7 Strategy Document',
            'category': 'Team_Meeting',
            'participants': ['Tom', 'Sue'],
            'transcript_file': 'draft_unea_strategy.txt'
        },
        {
            'title': 'All Hands Meeting - October',
            'category': 'All_Hands',
            'participants': ['Everyone'],
            'transcript_file': 'all_hands_oct.txt'
        }
    ]
    
    print("Testing Confidentiality Detection:")
    print("=" * 70)
    
    for meeting in test_meetings:
        enriched = detector.enrich_meeting(meeting)
        print(f"\nTitle: {meeting['title']}")
        print(f"Category: {meeting['category']}")
        print(f"→ Confidentiality: {enriched['confidentiality_level']}")
        print(f"→ Status: {enriched['document_status']}")
        print(f"→ Tags: {enriched['tags']}")

