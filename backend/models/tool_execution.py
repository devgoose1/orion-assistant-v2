"""
ToolExecution model - audit log of tool executions
"""
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base
import uuid

class ToolExecution(Base):
    __tablename__ = 'tool_executions'
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    session_id = Column(String, ForeignKey('sessions.id'), nullable=True, index=True)
    device_id = Column(String, ForeignKey('devices.device_id'), nullable=False, index=True)
    
    # Tool information
    tool_name = Column(String, nullable=False, index=True)
    parameters = Column(JSON, nullable=False)
    
    # Execution result
    success = Column(Boolean, nullable=False, index=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    executed_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Context
    user_query = Column(Text, nullable=True)
    llm_reasoning = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'device_id': self.device_id,
            'tool_name': self.tool_name,
            'parameters': self.parameters,
            'success': self.success,
            'result': self.result,
            'error_message': self.error_message,
            'executed_at': self.executed_at.isoformat() if self.executed_at is not None else None,
            'duration_ms': self.duration_ms,
            'user_query': self.user_query,
            'llm_reasoning': self.llm_reasoning
        }
