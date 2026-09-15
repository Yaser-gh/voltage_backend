"""Re-export of the DB session dependency for convenient importing."""
from app.database.session import get_db_session

__all__ = ["get_db_session"]
