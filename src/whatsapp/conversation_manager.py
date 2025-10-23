"""
Conversation History Manager
Stores and retrieves conversation history for multi-turn WhatsApp conversations
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation history for WhatsApp users"""

    def __init__(self, postgres_connection_string: Optional[str] = None, 
                 max_history: int = 10):
        """
        Initialize conversation manager

        Args:
            postgres_connection_string: PostgreSQL connection string (optional)
            max_history: Maximum number of messages to keep per user
        """
        self.max_history = max_history
        self.lock = Lock()
        self.postgres_connection = None
        self.postgres_connection_string = postgres_connection_string
        self.conversations = {}  # Always initialize for fallback
        
        # Try PostgreSQL first, fallback to in-memory
        if postgres_connection_string:
            try:
                import psycopg2
                self.postgres_connection = psycopg2.connect(postgres_connection_string)
                self._init_postgres_schema()
                logger.info("Using PostgreSQL for conversation history")
            except Exception as e:
                logger.warning(f"Failed to connect to PostgreSQL: {e}. Using in-memory storage.")
        else:
            logger.info("Using in-memory storage for conversation history")

    def _init_postgres_schema(self):
        """Initialize PostgreSQL schema for conversation history"""
        try:
            with self.postgres_connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS whatsapp_conversations (
                        user_phone VARCHAR(50) PRIMARY KEY,
                        group_id VARCHAR(100),
                        message_history JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_whatsapp_user_phone 
                    ON whatsapp_conversations(user_phone)
                """)
                
                self.postgres_connection.commit()
                logger.info("PostgreSQL schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            raise

    def add_message(self, user_phone: str, role: str, content: str, 
                    group_id: Optional[str] = None):
        """
        Add a message to user's conversation history

        Args:
            user_phone: User's phone number (WhatsApp ID)
            role: Message role ('user' or 'assistant')
            content: Message content
            group_id: Optional WhatsApp group ID
        """
        with self.lock:
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            }

            if self.postgres_connection:
                self._add_message_postgres(user_phone, message, group_id)
            else:
                self._add_message_memory(user_phone, message, group_id)

    def _ensure_postgres_connection(self):
        """Ensure PostgreSQL connection is alive, reconnect if needed"""
        try:
            if self.postgres_connection and self.postgres_connection.closed == 0:
                # Connection exists and is open, test it
                cursor = self.postgres_connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
        except Exception:
            pass
        
        # Connection is closed or broken, try to reconnect
        try:
            import psycopg2
            if self.postgres_connection:
                try:
                    self.postgres_connection.close()
                except Exception:
                    pass
            
            self.postgres_connection = psycopg2.connect(self.postgres_connection_string)
            logger.info("Reconnected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to reconnect to PostgreSQL: {e}")
            self.postgres_connection = None
            return False

    def _add_message_postgres(self, user_phone: str, message: dict, 
                              group_id: Optional[str]):
        """Add message to PostgreSQL"""
        try:
            # Ensure connection is alive
            if not self._ensure_postgres_connection():
                logger.warning("PostgreSQL unavailable, falling back to in-memory storage")
                self._add_message_memory(user_phone, message, group_id)
                return
            
            with self.postgres_connection.cursor() as cursor:
                # Get existing history
                cursor.execute(
                    "SELECT message_history FROM whatsapp_conversations WHERE user_phone = %s",
                    (user_phone,)
                )
                result = cursor.fetchone()

                if result:
                    # Update existing conversation
                    history = result[0] or []
                    history.append(message)
                    
                    # Keep only last N messages
                    history = history[-self.max_history:]
                    
                    cursor.execute(
                        """UPDATE whatsapp_conversations 
                           SET message_history = %s, updated_at = %s 
                           WHERE user_phone = %s""",
                        (json.dumps(history), datetime.now(), user_phone)
                    )
                else:
                    # Insert new conversation
                    cursor.execute(
                        """INSERT INTO whatsapp_conversations 
                           (user_phone, group_id, message_history) 
                           VALUES (%s, %s, %s)""",
                        (user_phone, group_id, json.dumps([message]))
                    )
                
                self.postgres_connection.commit()
                
        except Exception as e:
            logger.error(f"Failed to add message to PostgreSQL: {e}. Falling back to in-memory.")
            try:
                self.postgres_connection.rollback()
            except Exception:
                pass
            # Fallback to in-memory storage
            self._add_message_memory(user_phone, message, group_id)

    def _add_message_memory(self, user_phone: str, message: dict, 
                           group_id: Optional[str]):
        """Add message to in-memory storage"""
        if user_phone not in self.conversations:
            self.conversations[user_phone] = {
                'group_id': group_id,
                'history': []
            }
        
        self.conversations[user_phone]['history'].append(message)
        
        # Keep only last N messages
        self.conversations[user_phone]['history'] = \
            self.conversations[user_phone]['history'][-self.max_history:]

    def get_history(self, user_phone: str) -> List[Dict]:
        """
        Get conversation history for a user

        Args:
            user_phone: User's phone number

        Returns:
            List of message dictionaries
        """
        with self.lock:
            if self.postgres_connection:
                return self._get_history_postgres(user_phone)
            else:
                return self._get_history_memory(user_phone)

    def _get_history_postgres(self, user_phone: str) -> List[Dict]:
        """Get history from PostgreSQL"""
        try:
            # Ensure connection is alive
            if not self._ensure_postgres_connection():
                logger.warning("PostgreSQL unavailable, using in-memory storage")
                return self._get_history_memory(user_phone)
            
            with self.postgres_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT message_history FROM whatsapp_conversations WHERE user_phone = %s",
                    (user_phone,)
                )
                result = cursor.fetchone()
                
                if result and result[0]:
                    return result[0]
                return []
                
        except Exception as e:
            logger.error(f"Failed to get history from PostgreSQL: {e}. Using in-memory fallback.")
            return self._get_history_memory(user_phone)

    def _get_history_memory(self, user_phone: str) -> List[Dict]:
        """Get history from in-memory storage"""
        if user_phone in self.conversations:
            return self.conversations[user_phone]['history']
        return []

    def clear_history(self, user_phone: str):
        """
        Clear conversation history for a user

        Args:
            user_phone: User's phone number
        """
        with self.lock:
            if self.postgres_connection:
                try:
                    if self._ensure_postgres_connection():
                        with self.postgres_connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM whatsapp_conversations WHERE user_phone = %s",
                                (user_phone,)
                            )
                            self.postgres_connection.commit()
                            logger.info(f"Cleared history for {user_phone}")
                except Exception as e:
                    logger.error(f"Failed to clear history: {e}")
                    try:
                        self.postgres_connection.rollback()
                    except Exception:
                        pass
            
            # Also clear from in-memory (fallback)
            if user_phone in self.conversations:
                del self.conversations[user_phone]
                logger.info(f"Cleared in-memory history for {user_phone}")

    def format_history_for_context(self, user_phone: str) -> str:
        """
        Format conversation history as context string for RAG

        Args:
            user_phone: User's phone number

        Returns:
            Formatted conversation history
        """
        history = self.get_history(user_phone)
        
        if not history:
            return ""
        
        context_lines = ["Previous conversation:"]
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)

    def get_stats(self) -> Dict:
        """
        Get conversation statistics

        Returns:
            Dictionary with statistics
        """
        if self.postgres_connection:
            try:
                with self.postgres_connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM whatsapp_conversations")
                    total_users = cursor.fetchone()[0]
                    return {
                        'total_users': total_users,
                        'storage': 'PostgreSQL'
                    }
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                return {'error': str(e)}
        else:
            return {
                'total_users': len(self.conversations),
                'storage': 'In-Memory'
            }

    def close(self):
        """Close database connection"""
        if self.postgres_connection:
            self.postgres_connection.close()
            logger.info("PostgreSQL connection closed")

