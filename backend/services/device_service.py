"""
CRUD operations for Device model
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.device import Device
from datetime import datetime
from typing import Optional, List

def create_device(db: Session, device_data: dict) -> Device:
    """Create a new device"""
    device = Device(**device_data)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

def get_device(db: Session, device_id: str) -> Optional[Device]:
    """Get device by device_id"""
    return db.query(Device).filter(Device.device_id == device_id).first()

def get_all_devices(db: Session) -> List[Device]:
    """Get all devices"""
    return db.query(Device).all()

def get_online_devices(db: Session) -> List[Device]:
    """Get all online devices"""
    return db.query(Device).filter(Device.status == 'online').all()

def update_device(db: Session, device_id: str, update_data: dict) -> Optional[Device]:
    """Update device"""
    device = get_device(db, device_id)
    if device:
        for key, value in update_data.items():
            setattr(device, key, value)

        db.commit()
        db.refresh(device)
    return device

def update_heartbeat(db: Session, device_id: str) -> Optional[Device]:
    """Update device heartbeat"""
    device = get_device(db, device_id)
    if device:
        setattr(device, 'last_heartbeat', datetime.now())
        setattr(device, 'status', 'online')
        db.commit()
        db.refresh(device)
    return device

def delete_device(db: Session, device_id: str) -> bool:
    """Delete device"""
    device = get_device(db, device_id)
    if device:
        db.delete(device)
        db.commit()
        return True
    return False

def check_device_permission(db: Session, device_id: str, tool_name: str, permission_type: str = "tool") -> bool:
    """Check if device has permission for tool or app"""
    device = get_device(db, device_id)
    if not device:
        return False
    
    if permission_type == "tool":
        return tool_name in device.allowed_tools
    elif permission_type == "app":
        allowed_apps = device.allowed_apps if isinstance(device.allowed_apps, list) else []
        return tool_name in allowed_apps
    
    return False

def check_path_allowed(db: Session, device_id: str, path: str) -> bool:
    """Check if path is allowed for device"""
    device = get_device(db, device_id)
    if not device:
        return False
    
    # Get allowed paths from device
    allowed_paths = device.allowed_paths if isinstance(device.allowed_paths, list) else []
    
    # Check if path starts with any allowed path
    for allowed_path in allowed_paths:
        if path.startswith(str(allowed_path)):
            return True
    return False
