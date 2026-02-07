"""
Database models for pipeline run persistence.
Uses SQLAlchemy with PostgreSQL.
"""

import os
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

Base = declarative_base()


class PipelineRun(Base):
    """Model for storing pipeline run history."""
    
    __tablename__ = 'pipeline_runs'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Run metadata
    status = Column(String(20), default='running', nullable=False)  # running, complete, error
    source_files = Column(JSON, default=list)  # List of uploaded file names
    total_time_seconds = Column(Float, nullable=True)
    
    # Phase results (stored as JSON)
    extraction_result = Column(JSON, nullable=True)
    classification_result = Column(JSON, nullable=True)
    fol_result = Column(JSON, nullable=True)
    shacl_result = Column(JSON, nullable=True)
    validation_result = Column(JSON, nullable=True)
    
    # Full SHACL content (for "Show Full SHACL" feature)
    shacl_content = Column(Text, nullable=True)
    shacl_file_hash = Column(String(32), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'source_files': self.source_files,
            'total_time_seconds': self.total_time_seconds,
            'extraction_result': self.extraction_result,
            'classification_result': self.classification_result,
            'fol_result': self.fol_result,
            'shacl_result': self.shacl_result,
            'validation_result': self.validation_result,
            'shacl_file_hash': self.shacl_file_hash,
            'error_message': self.error_message
        }


# Database connection setup
_engine = None
_Session = None


def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv(
        'DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/policychecker'
    )


def init_db():
    """Initialize database connection and create tables."""
    global _engine, _Session
    
    database_url = get_database_url()
    print(f"[DB] Connecting to database...")
    
    _engine = create_engine(database_url, echo=False)
    _Session = sessionmaker(bind=_engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(_engine)
    print("[DB] Database initialized, tables created.")
    
    return _engine


def get_session():
    """Get a new database session."""
    global _Session
    if _Session is None:
        init_db()
    return _Session()


def save_run(run: PipelineRun):
    """Save or update a pipeline run."""
    session = get_session()
    try:
        session.merge(run)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DB] Error saving run: {e}")
        raise
    finally:
        session.close()


def get_run(run_id: str) -> Optional[PipelineRun]:
    """Get a pipeline run by ID."""
    session = get_session()
    try:
        return session.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    finally:
        session.close()


def get_all_runs(limit: int = 50) -> list:
    """Get all pipeline runs, sorted by created_at descending."""
    session = get_session()
    try:
        runs = session.query(PipelineRun)\
            .order_by(PipelineRun.created_at.desc())\
            .limit(limit)\
            .all()
        return [run.to_dict() for run in runs]
    finally:
        session.close()


def update_run_status(run_id: str, status: str, error: str = None):
    """Update the status of a run."""
    session = get_session()
    try:
        run = session.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if run:
            run.status = status
            if error:
                run.error_message = error
            if status in ('complete', 'error'):
                run.completed_at = datetime.utcnow()
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DB] Error updating run status: {e}")
    finally:
        session.close()


def update_run_phase(run_id: str, phase: str, result: dict, time_seconds: float = None):
    """Update a specific phase result for a run."""
    session = get_session()
    try:
        run = session.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if run:
            setattr(run, f"{phase}_result", result)
            if time_seconds is not None and run.total_time_seconds is not None:
                run.total_time_seconds += time_seconds
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DB] Error updating run phase: {e}")
    finally:
        session.close()
