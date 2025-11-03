-- Postgres Mirror Database Schema for Knowledge Graph
-- Supports: Meetings, Documents, WhatsApp Chats
-- Features: pgvector embeddings, raw JSON backup

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- SOURCES: All source documents (meetings, chats, PDFs)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'meeting', 'document', 'whatsapp_chat'
    date TIMESTAMP,
    
    -- Source-specific metadata
    category TEXT,              -- For meetings: 'All_Hands', 'Team_Meeting', etc.
    platform TEXT,              -- For chats: 'WhatsApp', 'Slack', etc.
    participant_count INTEGER,
    message_count INTEGER,
    
    -- File references
    source_file TEXT,
    transcript_file TEXT,
    
    -- Time ranges
    date_range_start TIMESTAMP,
    date_range_end TIMESTAMP,
    
    -- Raw backup (full parsed JSON)
    raw_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_date ON sources(date);
CREATE INDEX IF NOT EXISTS idx_sources_created ON sources(created_at);

-- ============================================================================
-- ENTITIES: People, Organizations, Topics, Countries
-- ============================================================================
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'Person', 'Organization', 'Topic', 'Country'
    
    -- Entity-specific properties
    role TEXT,
    organization TEXT,
    org_type TEXT,
    status TEXT,
    
    -- Additional metadata
    properties JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name_lower ON entities(LOWER(name));

-- ============================================================================
-- CHUNKS: Text chunks with embeddings (core of RAG)
-- ============================================================================
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    embedding vector(1024),  -- Mistral embeddings (1024 dimensions)
    
    -- Source reference
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    
    -- Chunk metadata
    importance_score FLOAT DEFAULT 0.5,
    chunk_type TEXT,  -- 'discussion', 'decision', 'action', etc.
    
    -- Meeting-specific
    speakers TEXT[],
    start_time TEXT,
    meeting_id TEXT,
    meeting_title TEXT,
    meeting_date TEXT,
    
    -- WhatsApp-specific
    participants TEXT[],
    message_count INTEGER,
    time_start TIMESTAMP,
    time_end TIMESTAMP,
    chunk_duration_minutes FLOAT,
    has_media BOOLEAN,
    media_count INTEGER,
    
    -- Universal fields
    source_title TEXT,
    source_date TEXT,
    source_type TEXT,
    
    -- Additional metadata
    chunk_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_chunks_sequence ON chunks(source_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_chunks_importance ON chunks(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type);
CREATE INDEX IF NOT EXISTS idx_chunks_source_type ON chunks(source_type);

-- pgvector similarity search index (cosine distance)
-- Note: This will be created after data is loaded for better performance
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks 
-- USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- CHUNK_MENTIONS: Which chunks mention which entities
-- ============================================================================
CREATE TABLE IF NOT EXISTS chunk_mentions (
    chunk_id TEXT REFERENCES chunks(id) ON DELETE CASCADE,
    entity_id TEXT REFERENCES entities(id) ON DELETE CASCADE,
    entity_name TEXT,  -- Denormalized for quick access
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (chunk_id, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_chunk_mentions_chunk ON chunk_mentions(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_mentions_entity ON chunk_mentions(entity_id);

-- ============================================================================
-- DECISIONS: Meeting decisions
-- ============================================================================
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    rationale TEXT,
    
    -- Source reference
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    meeting_id TEXT,  -- Denormalized for backwards compatibility
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_source ON decisions(source_id);

-- ============================================================================
-- ACTIONS: Action items from meetings
-- ============================================================================
CREATE TABLE IF NOT EXISTS actions (
    id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    owner TEXT,
    
    -- Source reference
    source_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    meeting_id TEXT,  -- Denormalized for backwards compatibility
    
    -- Status tracking
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed'
    due_date DATE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_actions_source ON actions(source_id);
CREATE INDEX IF NOT EXISTS idx_actions_owner ON actions(owner);
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status);

-- ============================================================================
-- CHUNK_OUTCOMES: Links chunks to decisions/actions they resulted in
-- ============================================================================
CREATE TABLE IF NOT EXISTS chunk_outcomes (
    chunk_id TEXT REFERENCES chunks(id) ON DELETE CASCADE,
    outcome_id TEXT NOT NULL,  -- Can reference decisions.id or actions.id
    outcome_type TEXT NOT NULL,  -- 'decision' or 'action'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (chunk_id, outcome_id)
);

CREATE INDEX IF NOT EXISTS idx_chunk_outcomes_chunk ON chunk_outcomes(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_outcomes_outcome ON chunk_outcomes(outcome_id);

-- ============================================================================
-- MESSAGES: Individual WhatsApp messages (fine-grained)
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    sender TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Message metadata
    message_type TEXT,  -- 'text', 'media', 'system', 'deleted'
    media_type TEXT,  -- 'image', 'video', 'document', 'voice', etc.
    is_forwarded BOOLEAN DEFAULT FALSE,
    
    -- References
    conversation_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    chunk_id TEXT REFERENCES chunks(id) ON DELETE SET NULL,
    
    -- Sequence
    sequence_in_conversation INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender);
CREATE INDEX IF NOT EXISTS idx_messages_sequence ON messages(conversation_id, sequence_in_conversation);

-- ============================================================================
-- PARTICIPANTS: Conversation participants (for WhatsApp)
-- ============================================================================
CREATE TABLE IF NOT EXISTS participants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    
    -- Conversation reference
    conversation_id TEXT REFERENCES sources(id) ON DELETE CASCADE,
    
    -- Participation stats
    message_count INTEGER DEFAULT 0,
    media_shared_count INTEGER DEFAULT 0,
    first_message_date TIMESTAMP,
    last_message_date TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (name, conversation_id)
);

CREATE INDEX IF NOT EXISTS idx_participants_conversation ON participants(conversation_id);
CREATE INDEX IF NOT EXISTS idx_participants_name ON participants(name);

-- ============================================================================
-- UTILITY VIEWS
-- ============================================================================

-- View: Chunks with entity mentions count
CREATE OR REPLACE VIEW chunks_with_entity_count AS
SELECT 
    c.id,
    c.text,
    c.source_id,
    c.source_type,
    c.importance_score,
    COUNT(cm.entity_id) as entity_count
FROM chunks c
LEFT JOIN chunk_mentions cm ON c.id = cm.chunk_id
GROUP BY c.id, c.text, c.source_id, c.source_type, c.importance_score;

-- View: Entity mention frequency
CREATE OR REPLACE VIEW entity_mention_frequency AS
SELECT 
    e.id,
    e.name,
    e.type,
    COUNT(cm.chunk_id) as mention_count,
    COUNT(DISTINCT c.source_id) as source_count
FROM entities e
LEFT JOIN chunk_mentions cm ON e.id = cm.entity_id
LEFT JOIN chunks c ON cm.chunk_id = c.id
GROUP BY e.id, e.name, e.type
ORDER BY mention_count DESC;

-- View: Source statistics
CREATE OR REPLACE VIEW source_statistics AS
SELECT 
    s.id,
    s.title,
    s.source_type,
    s.date,
    COUNT(DISTINCT c.id) as chunk_count,
    COUNT(DISTINCT cm.entity_id) as entity_count,
    COUNT(DISTINCT d.id) as decision_count,
    COUNT(DISTINCT a.id) as action_count
FROM sources s
LEFT JOIN chunks c ON s.id = c.source_id
LEFT JOIN chunk_mentions cm ON c.id = cm.chunk_id
LEFT JOIN decisions d ON s.id = d.source_id
LEFT JOIN actions a ON s.id = a.source_id
GROUP BY s.id, s.title, s.source_type, s.date;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Semantic similarity search
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(1024),
    limit_count INTEGER DEFAULT 10,
    min_similarity FLOAT DEFAULT 0.0
)
RETURNS TABLE (
    chunk_id TEXT,
    chunk_text TEXT,
    similarity FLOAT,
    source_title TEXT,
    source_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.text,
        1 - (c.embedding <=> query_embedding) as similarity,
        c.source_title,
        c.source_type
    FROM chunks c
    WHERE c.embedding IS NOT NULL
        AND (1 - (c.embedding <=> query_embedding)) >= min_similarity
    ORDER BY c.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE sources IS 'All source documents: meetings, WhatsApp chats, PDFs. Includes raw JSON backup.';
COMMENT ON TABLE chunks IS 'Text chunks with embeddings for RAG retrieval. Core table for semantic search.';
COMMENT ON TABLE entities IS 'Unified entities: People, Organizations, Topics, Countries';
COMMENT ON TABLE chunk_mentions IS 'Junction table linking chunks to entities they mention';
COMMENT ON TABLE decisions IS 'Decisions made in meetings';
COMMENT ON TABLE actions IS 'Action items from meetings';
COMMENT ON TABLE messages IS 'Individual WhatsApp messages (fine-grained chat data)';
COMMENT ON TABLE participants IS 'WhatsApp conversation participants';

COMMENT ON COLUMN chunks.embedding IS 'Mistral 1024-dimensional embedding vector for semantic search';
COMMENT ON COLUMN sources.raw_data IS 'Full parsed JSON for backup and recovery';

