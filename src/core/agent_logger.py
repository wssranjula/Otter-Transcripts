"""
Agent Monitoring and Logging System
Structured logging for tracking agent behavior, performance, and errors
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentMonitor:
    """Monitor and log agent behavior for analysis and improvement"""
    
    def __init__(self, log_file: str = "agent_monitoring.log"):
        """
        Initialize agent monitor
        
        Args:
            log_file: Path to monitoring log file
        """
        self.log_file = log_file
        self.current_session = None
        
        # Setup dedicated monitor logger
        self.monitor_logger = logging.getLogger("agent_monitor")
        self.monitor_logger.setLevel(logging.INFO)
        
        # Create file handler for monitoring
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # JSON formatter for easy parsing
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        # Remove existing handlers and add new one
        self.monitor_logger.handlers = []
        self.monitor_logger.addHandler(handler)
        self.monitor_logger.propagate = False
    
    def start_query_session(self, user_question: str, source: str = "unknown") -> str:
        """
        Start tracking a new query session
        
        Args:
            user_question: User's question
            source: Where the query came from (admin, whatsapp, etc)
        
        Returns:
            Session ID
        """
        session_id = f"{datetime.utcnow().timestamp()}"
        
        self.current_session = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": source,
            "user_question": user_question,
            "start_time": time.time(),
            "sub_agents_used": [],
            "tool_calls": [],
            "errors": [],
            "retries": 0,
            "status": "started"
        }
        
        self._log_event("session_start", self.current_session)
        return session_id
    
    def log_subagent_call(self, subagent_type: str, description: str):
        """
        Log when a sub-agent is called
        
        Args:
            subagent_type: Type of sub-agent (query-agent, analysis-agent)
            description: Task description
        """
        if not self.current_session:
            return
        
        call_data = {
            "subagent": subagent_type,
            "description": description,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "call_number": len(self.current_session["sub_agents_used"]) + 1
        }
        
        self.current_session["sub_agents_used"].append(call_data)
        self._log_event("subagent_call", call_data)
    
    def log_tool_call(self, tool_name: str, success: bool, duration: float, 
                      error: Optional[str] = None):
        """
        Log tool execution
        
        Args:
            tool_name: Name of the tool
            success: Whether tool succeeded
            duration: Execution time in seconds
            error: Error message if failed
        """
        if not self.current_session:
            return
        
        tool_data = {
            "tool": tool_name,
            "success": success,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error
        }
        
        self.current_session["tool_calls"].append(tool_data)
        
        if not success:
            self.current_session["retries"] += 1
        
        self._log_event("tool_call", tool_data)
    
    def log_query_attempt(self, cypher_query: str, success: bool, 
                          result_count: int = 0, error: Optional[str] = None,
                          retry_number: int = 1):
        """
        Log Cypher query attempt
        
        Args:
            cypher_query: The Cypher query executed
            success: Whether query succeeded
            result_count: Number of results returned
            error: Error message if failed
            retry_number: Which attempt this is
        """
        if not self.current_session:
            return
        
        query_data = {
            "cypher": cypher_query[:200] + "..." if len(cypher_query) > 200 else cypher_query,
            "success": success,
            "result_count": result_count,
            "error": error,
            "retry_number": retry_number,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if not success:
            self.current_session["errors"].append(query_data)
            self.current_session["retries"] += 1
        
        self._log_event("query_attempt", query_data)
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """
        Log an error
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        if not self.current_session:
            return
        
        error_data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.current_session["errors"].append(error_data)
        self._log_event("error", error_data)
    
    def end_query_session(self, success: bool, final_answer: str = None,
                          tokens_used: Optional[int] = None):
        """
        End query session and log summary
        
        Args:
            success: Whether query succeeded
            final_answer: Final answer provided (truncated for logging)
            tokens_used: Approximate tokens used
        """
        if not self.current_session:
            return
        
        duration = time.time() - self.current_session["start_time"]
        
        self.current_session.update({
            "status": "completed" if success else "failed",
            "duration_seconds": round(duration, 2),
            "total_retries": self.current_session["retries"],
            "total_subagent_calls": len(self.current_session["sub_agents_used"]),
            "total_tool_calls": len(self.current_session["tool_calls"]),
            "total_errors": len(self.current_session["errors"]),
            "final_answer_length": len(final_answer) if final_answer else 0,
            "tokens_used": tokens_used,
            "end_time": datetime.utcnow().isoformat() + "Z"
        })
        
        # Log summary
        self._log_event("session_end", self._create_summary())
        
        # Reset current session
        self.current_session = None
    
    def _create_summary(self) -> Dict[str, Any]:
        """Create session summary"""
        if not self.current_session:
            return {}
        
        return {
            "session_id": self.current_session["session_id"],
            "source": self.current_session["source"],
            "question_length": len(self.current_session["user_question"]),
            "duration_seconds": self.current_session.get("duration_seconds", 0),
            "status": self.current_session.get("status"),
            "subagent_calls": self.current_session.get("total_subagent_calls", 0),
            "tool_calls": self.current_session.get("total_tool_calls", 0),
            "retries": self.current_session.get("total_retries", 0),
            "errors": self.current_session.get("total_errors", 0),
            "answer_length": self.current_session.get("final_answer_length", 0),
            "timestamp": self.current_session["timestamp"]
        }
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """
        Log structured event
        
        Args:
            event_type: Type of event
            data: Event data
        """
        log_entry = {
            "event": event_type,
            "session_id": self.current_session["session_id"] if self.current_session else None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }
        
        self.monitor_logger.info(json.dumps(log_entry))
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get current session metrics"""
        if not self.current_session:
            return {}
        
        return {
            "session_id": self.current_session["session_id"],
            "elapsed_time": time.time() - self.current_session["start_time"],
            "subagent_calls": len(self.current_session["sub_agents_used"]),
            "tool_calls": len(self.current_session["tool_calls"]),
            "retries": self.current_session["retries"],
            "errors": len(self.current_session["errors"])
        }


# Global monitor instance
_global_monitor: Optional[AgentMonitor] = None


def get_monitor() -> AgentMonitor:
    """Get global monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = AgentMonitor()
    return _global_monitor


def log_agent_event(event_type: str, data: Dict[str, Any]):
    """Convenience function to log agent event"""
    monitor = get_monitor()
    if monitor.current_session:
        monitor._log_event(event_type, data)

