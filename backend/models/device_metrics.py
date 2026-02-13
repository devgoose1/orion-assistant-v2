"""
Device metrics model - tracks CPU, memory, disk usage over time
"""
from sqlalchemy import Column, String, Float, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from database import Base
import uuid


class DeviceMetrics(Base):
    """Real-time and historical device metrics tracking.
    
    Stores CPU usage %, memory usage %, disk usage % at regular intervals.
    Used for dashboard visualization and performance monitoring.
    """
    __tablename__ = 'device_metrics'
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to device
    device_id = Column(String, ForeignKey('devices.device_id'), nullable=False, index=True)
    
    # Metrics (percentage values)
    cpu_percent = Column(Float, nullable=False)  # 0-100
    memory_percent = Column(Float, nullable=False)  # 0-100
    disk_percent = Column(Float, nullable=False)  # 0-100
    
    # Optional process/thread counts
    process_count = Column(Integer)
    thread_count = Column(Integer)
    
    # Timestamp when metrics were collected
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'disk_percent': self.disk_percent,
            'process_count': self.process_count,
            'thread_count': self.thread_count,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
