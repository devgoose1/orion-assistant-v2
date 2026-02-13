"""
Dashboard service - provides monitoring and metrics data
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models.device import Device
from models.device_metrics import DeviceMetrics
from models.tool_execution import ToolExecution
from models.session import Session as SessionModel
from config import MAX_METRICS_HISTORY, MAX_EXECUTION_HISTORY, METRICS_RETENTION_DAYS


def get_dashboard_overview(db: Session) -> Dict[str, Any]:
    """Get overview of all devices and system status.
    
    Returns:
        Dict with:
        - total_devices: int
        - online_devices: int
        - offline_devices: int
        - recent_executions: int (last 24h)
        - devices: list of device summaries
    """
    all_devices = db.query(Device).all()
    online = sum(1 for d in all_devices if d.status == 'online')
    
    # Count recent executions (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_executions = db.query(ToolExecution).filter(
        ToolExecution.created_at >= yesterday
    ).count()
    
    devices_summary = []
    for device in all_devices:
        # Get latest metrics for this device
        latest_metrics = db.query(DeviceMetrics).filter(
            DeviceMetrics.device_id == device.device_id
        ).order_by(desc(DeviceMetrics.timestamp)).first()
        
        devices_summary.append({
            'device_id': device.device_id,
            'hostname': device.hostname,
            'os_type': device.os_type,
            'status': device.status,
            'last_heartbeat': device.last_heartbeat.isoformat() if device.last_heartbeat else None,
            'metrics': latest_metrics.to_dict() if latest_metrics else None
        })
    
    return {
        'total_devices': len(all_devices),
        'online_devices': online,
        'offline_devices': len(all_devices) - online,
        'recent_executions': recent_executions,
        'timestamp': datetime.utcnow().isoformat(),
        'devices': devices_summary
    }


def get_device_details(device_id: str, db: Session) -> Dict[str, Any]:
    """Get detailed information about a specific device.
    
    Returns:
        Dict with:
        - device info
        - current metrics
        - recent execution history
        - conversation sessions
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return None
    
    # Get latest metrics
    latest_metrics = db.query(DeviceMetrics).filter(
        DeviceMetrics.device_id == device_id
    ).order_by(desc(DeviceMetrics.timestamp)).first()
    
    # Get recent executions
    recent_executions = db.query(ToolExecution).filter(
        ToolExecution.device_id == device_id
    ).order_by(desc(ToolExecution.created_at)).limit(MAX_EXECUTION_HISTORY).all()
    
    # Get active sessions
    sessions = db.query(SessionModel).filter(
        SessionModel.device_id == device_id
    ).all()
    
    return {
        'device': device.to_dict(),
        'current_metrics': latest_metrics.to_dict() if latest_metrics else None,
        'recent_executions': [
            {
                'tool_name': ex.tool_name,
                'success': ex.success,
                'result': ex.result,
                'created_at': ex.created_at.isoformat() if ex.created_at else None
            }
            for ex in recent_executions
        ],
        'active_sessions': len(sessions),
        'timestamp': datetime.utcnow().isoformat()
    }


def get_device_metrics_history(
    device_id: str, 
    db: Session, 
    limit: int = MAX_METRICS_HISTORY
) -> List[Dict[str, Any]]:
    """Get historical metrics for a device.
    
    Args:
        device_id: Device to get metrics for
        db: Database session
        limit: Max number of entries to return
    
    Returns:
        List of metric entries, most recent first
    """
    metrics = db.query(DeviceMetrics).filter(
        DeviceMetrics.device_id == device_id
    ).order_by(desc(DeviceMetrics.timestamp)).limit(limit).all()
    
    return [m.to_dict() for m in metrics]


def record_device_metrics(
    device_id: str,
    cpu_percent: float,
    memory_percent: float,
    disk_percent: float,
    process_count: Optional[int] = None,
    thread_count: Optional[int] = None,
    db: Optional[Session] = None
) -> bool:
    """Record device metrics snapshot.
    
    Args:
        device_id: Device to record metrics for
        cpu_percent: CPU usage percentage (0-100)
        memory_percent: Memory usage percentage (0-100)
        disk_percent: Disk usage percentage (0-100)
        process_count: Number of processes (optional)
        thread_count: Number of threads (optional)
        db: Database session (required)
    
    Returns:
        True if successfully recorded, False otherwise
    """
    if not db:
        return False
    
    try:
        metrics = DeviceMetrics(
            device_id=device_id,
            cpu_percent=max(0, min(100, cpu_percent)),  # Clamp 0-100
            memory_percent=max(0, min(100, memory_percent)),
            disk_percent=max(0, min(100, disk_percent)),
            process_count=process_count,
            thread_count=thread_count
        )
        db.add(metrics)
        db.commit()
        return True
    except Exception as e:
        print(f"Error recording metrics for {device_id}: {e}")
        return False


def cleanup_old_metrics(db: Session, days: int = METRICS_RETENTION_DAYS) -> int:
    """Delete metrics older than specified days.
    
    Args:
        db: Database session
        days: Keep metrics newer than this many days
    
    Returns:
        Number of records deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(DeviceMetrics).filter(
        DeviceMetrics.timestamp < cutoff_date
    ).delete()
    db.commit()
    return deleted
