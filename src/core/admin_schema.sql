-- Admin Panel Database Schema
-- Tables for admin authentication and WhatsApp whitelist management

-- ============================================================================
-- ADMIN USERS TABLE
-- ============================================================================
-- For future authentication implementation
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for admin_users
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_active ON admin_users(is_active);

-- ============================================================================
-- WHATSAPP WHITELIST TABLE
-- ============================================================================
-- Stores authorized WhatsApp numbers that can interact with the bot
CREATE TABLE IF NOT EXISTS whatsapp_whitelist (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    notes TEXT,
    added_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for whatsapp_whitelist
CREATE INDEX IF NOT EXISTS idx_whitelist_phone ON whatsapp_whitelist(phone_number);
CREATE INDEX IF NOT EXISTS idx_whitelist_active ON whatsapp_whitelist(is_active);
CREATE INDEX IF NOT EXISTS idx_whitelist_created ON whatsapp_whitelist(created_at DESC);

-- ============================================================================
-- ADMIN CHAT SESSIONS TABLE (Optional - for future chat history)
-- ============================================================================
-- Stores admin panel chat sessions with Sybil
CREATE TABLE IF NOT EXISTS admin_chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    admin_username VARCHAR(100),
    message_history JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_id ON admin_chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_admin ON admin_chat_sessions(admin_username);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE admin_users IS 'Admin users for panel authentication (future use)';
COMMENT ON TABLE whatsapp_whitelist IS 'Authorized WhatsApp numbers for bot interaction';
COMMENT ON TABLE admin_chat_sessions IS 'Admin panel chat history with Sybil (optional feature)';

COMMENT ON COLUMN whatsapp_whitelist.phone_number IS 'WhatsApp phone number in E.164 format (e.g., +1234567890)';
COMMENT ON COLUMN whatsapp_whitelist.is_active IS 'Whether this number is currently authorized';

