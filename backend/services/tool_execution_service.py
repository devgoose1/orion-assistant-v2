"""
CRUD operations for ToolExecution model
"""
from sqlalchemy.orm import Session
from models.tool_execution import ToolExecution
from typing import Optional, List
from datetime import datetime, timedelta

def log_tool_execution(db: Session, execution_data: dict) -> ToolExecution:
    """Log a tool execution"""
    execution = ToolExecution(**execution_data)
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution

def get_tool_execution(db: Session, execution_id: str) -> Optional[ToolExecution]:
    """Get tool execution by id"""
    return db.query(ToolExecution).filter(ToolExecution.id == execution_id).first()

def get_device_executions(db: Session, device_id: str, limit: int = 100) -> List[ToolExecution]:
    """Get recent tool executions for a device"""
    return db.query(ToolExecution).filter(
        ToolExecution.device_id == device_id
    ).order_by(ToolExecution.executed_at.desc()).limit(limit).all()

def get_failed_executions(db: Session, device_id: Optional[str] = None, hours: int = 24) -> List[ToolExecution]:
    """Get failed executions in the last N hours"""
    since = datetime.now() - timedelta(hours=hours)
    query = db.query(ToolExecution).filter(
        ToolExecution.success.is_(False),
        ToolExecution.executed_at >= since
    )
    if device_id:
        query = query.filter(ToolExecution.device_id == device_id)
    return query.order_by(ToolExecution.executed_at.desc()).all()

def get_tool_statistics(db: Session, tool_name: str, days: int = 30) -> dict:
    """Get statistics for a specific tool"""
    since = datetime.now() - timedelta(days=days)
    executions = db.query(ToolExecution).filter(
        ToolExecution.tool_name == tool_name,
        ToolExecution.executed_at >= since
    ).all()
    
    total = len(executions)
    successful = sum(1 for e in executions if e.success is True)
    failed = total - successful
    
    durations = [e.duration_ms for e in executions if e.duration_ms is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        'tool_name': tool_name,
        'total_executions': total,
        'successful': successful,
        'failed': failed,
        'success_rate': successful / total if total > 0 else 0,
        'avg_duration_ms': avg_duration
    }
