"""
Admin Database Operations
PostgreSQL helper functions for admin panel (whitelist management, user management)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class AdminDatabase:
    """Database operations for admin panel"""
    
    def __init__(self, connection_string: str):
        """
        Initialize admin database
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            logger.info("Admin database connected")
        except Exception as e:
            logger.error(f"Failed to connect to admin database: {e}")
            raise
    
    def _ensure_connection(self):
        """Ensure database connection is alive"""
        try:
            if self.conn is None or self.conn.closed:
                self._connect()
            else:
                # Test connection
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
        except Exception:
            logger.warning("Connection lost, reconnecting...")
            self._connect()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Admin database connection closed")
    
    # ========================================
    # Whitelist Operations
    # ========================================
    
    def get_all_whitelist(self, include_inactive: bool = False) -> List[Dict]:
        """
        Get all whitelist entries
        
        Args:
            include_inactive: Include inactive entries
        
        Returns:
            List of whitelist entries
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            if include_inactive:
                cursor.execute("""
                    SELECT id, phone_number, name, notes, added_by, is_active, 
                           created_at, updated_at
                    FROM whatsapp_whitelist
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT id, phone_number, name, notes, added_by, is_active, 
                           created_at, updated_at
                    FROM whatsapp_whitelist
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """)
            
            results = cursor.fetchall()
            cursor.close()
            
            # Convert to list of dicts with datetime serialization
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get whitelist: {e}")
            raise
    
    def get_whitelist_entry(self, entry_id: int) -> Optional[Dict]:
        """
        Get single whitelist entry by ID
        
        Args:
            entry_id: Whitelist entry ID
        
        Returns:
            Whitelist entry or None
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, phone_number, name, notes, added_by, is_active, 
                       created_at, updated_at
                FROM whatsapp_whitelist
                WHERE id = %s
            """, (entry_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get whitelist entry: {e}")
            raise
    
    def check_phone_whitelisted(self, phone_number: str) -> bool:
        """
        Check if phone number is whitelisted and active
        
        Args:
            phone_number: Phone number to check
        
        Returns:
            True if whitelisted and active
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM whatsapp_whitelist
                WHERE phone_number = %s AND is_active = TRUE
            """, (phone_number,))
            
            count = cursor.fetchone()[0]
            cursor.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check phone whitelist: {e}")
            return False
    
    def add_to_whitelist(
        self, 
        phone_number: str, 
        name: Optional[str] = None,
        notes: Optional[str] = None,
        added_by: Optional[str] = None
    ) -> Dict:
        """
        Add phone number to whitelist
        
        Args:
            phone_number: Phone number in E.164 format
            name: Contact name (optional)
            notes: Additional notes (optional)
            added_by: Username who added this entry (optional)
        
        Returns:
            Created whitelist entry
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO whatsapp_whitelist 
                (phone_number, name, notes, added_by, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, TRUE, NOW(), NOW())
                RETURNING id, phone_number, name, notes, added_by, is_active, 
                          created_at, updated_at
            """, (phone_number, name, notes, added_by))
            
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Added to whitelist: {phone_number}")
            return dict(result)
            
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Phone number already exists in whitelist: {phone_number}")
            raise ValueError(f"Phone number {phone_number} already exists in whitelist")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to add to whitelist: {e}")
            raise
    
    def update_whitelist(
        self,
        entry_id: int,
        phone_number: Optional[str] = None,
        name: Optional[str] = None,
        notes: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict:
        """
        Update whitelist entry
        
        Args:
            entry_id: Whitelist entry ID
            phone_number: New phone number (optional)
            name: New name (optional)
            notes: New notes (optional)
            is_active: Active status (optional)
        
        Returns:
            Updated whitelist entry
        """
        self._ensure_connection()
        
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            
            if phone_number is not None:
                update_fields.append("phone_number = %s")
                params.append(phone_number)
            if name is not None:
                update_fields.append("name = %s")
                params.append(name)
            if notes is not None:
                update_fields.append("notes = %s")
                params.append(notes)
            if is_active is not None:
                update_fields.append("is_active = %s")
                params.append(is_active)
            
            if not update_fields:
                raise ValueError("No fields to update")
            
            update_fields.append("updated_at = NOW()")
            params.append(entry_id)
            
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(f"""
                UPDATE whatsapp_whitelist
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, phone_number, name, notes, added_by, is_active, 
                          created_at, updated_at
            """, params)
            
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            
            if result:
                logger.info(f"Updated whitelist entry: {entry_id}")
                return dict(result)
            else:
                raise ValueError(f"Whitelist entry {entry_id} not found")
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update whitelist: {e}")
            raise
    
    def delete_from_whitelist(self, entry_id: int) -> bool:
        """
        Delete whitelist entry (soft delete - sets is_active to False)
        
        Args:
            entry_id: Whitelist entry ID
        
        Returns:
            True if deleted successfully
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE whatsapp_whitelist
                SET is_active = FALSE, updated_at = NOW()
                WHERE id = %s
            """, (entry_id,))
            
            rows_affected = cursor.rowcount
            self.conn.commit()
            cursor.close()
            
            if rows_affected > 0:
                logger.info(f"Deleted whitelist entry: {entry_id}")
                return True
            else:
                logger.warning(f"Whitelist entry not found: {entry_id}")
                return False
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete from whitelist: {e}")
            raise
    
    def toggle_whitelist_status(self, entry_id: int) -> Dict:
        """
        Toggle active/inactive status of a whitelist entry
        
        Args:
            entry_id: Whitelist entry ID
        
        Returns:
            Updated whitelist entry
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Toggle the is_active status
            cursor.execute("""
                UPDATE whatsapp_whitelist
                SET is_active = NOT is_active, updated_at = NOW()
                WHERE id = %s
                RETURNING id, phone_number, name, notes, added_by, is_active, 
                          created_at, updated_at
            """, (entry_id,))
            
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                raise ValueError(f"Whitelist entry {entry_id} not found")
            
            self.conn.commit()
            cursor.close()
            
            status = "activated" if result['is_active'] else "deactivated"
            logger.info(f"Whitelist entry {entry_id} {status}: {result['phone_number']}")
            
            return dict(result)
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to toggle whitelist status: {e}")
            raise
    
    def hard_delete_from_whitelist(self, entry_id: int) -> bool:
        """
        Permanently delete whitelist entry from database
        
        Args:
            entry_id: Whitelist entry ID
        
        Returns:
            True if deleted successfully
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM whatsapp_whitelist
                WHERE id = %s
            """, (entry_id,))
            
            rows_affected = cursor.rowcount
            self.conn.commit()
            cursor.close()
            
            if rows_affected > 0:
                logger.info(f"Hard deleted whitelist entry: {entry_id}")
                return True
            else:
                logger.warning(f"Whitelist entry not found: {entry_id}")
                return False
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to hard delete from whitelist: {e}")
            raise
    
    def get_whitelist_stats(self) -> Dict:
        """
        Get whitelist statistics
        
        Returns:
            Statistics dictionary
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM whatsapp_whitelist")
            total = cursor.fetchone()[0]
            
            # Active entries
            cursor.execute("SELECT COUNT(*) FROM whatsapp_whitelist WHERE is_active = TRUE")
            active = cursor.fetchone()[0]
            
            # Inactive entries
            cursor.execute("SELECT COUNT(*) FROM whatsapp_whitelist WHERE is_active = FALSE")
            inactive = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'total': total,
                'active': active,
                'inactive': inactive
            }
            
        except Exception as e:
            logger.error(f"Failed to get whitelist stats: {e}")
            return {'total': 0, 'active': 0, 'inactive': 0}
    
    # ========================================
    # Admin User Operations (for future auth)
    # ========================================
    
    def create_admin_user(
        self,
        username: str,
        password_hash: str,
        email: Optional[str] = None,
        role: str = 'admin'
    ) -> Dict:
        """
        Create admin user
        
        Args:
            username: Username
            password_hash: Hashed password
            email: Email address (optional)
            role: User role (default: 'admin')
        
        Returns:
            Created user (without password_hash)
        """
        self._ensure_connection()
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO admin_users 
                (username, password_hash, email, role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, TRUE, NOW(), NOW())
                RETURNING id, username, email, role, is_active, created_at, updated_at
            """, (username, password_hash, email, role))
            
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Created admin user: {username}")
            return dict(result)
            
        except psycopg2.IntegrityError:
            self.conn.rollback()
            logger.error(f"Username already exists: {username}")
            raise ValueError(f"Username {username} already exists")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create admin user: {e}")
            raise

