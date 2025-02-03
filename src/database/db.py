import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.config.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str):
        """
        Initialize the DatabaseSessionManager.

        Args:
            url (str): The database connection URL.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Provide a database session using a context manager.

        This method creates a new database session and ensures it is properly
        closed. If an error occurs during the transaction, the session is rolled back.

        Yields:
            session: An active database session object.

        Raises:
            SQLAlchemyError: If an error occurs during database operations.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise  # Re-raise the original error
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Provide a database session using the session manager.

    This function uses the DatabaseSessionManager to yield a session for
    interacting with the database.

    Yields:
        session: An active database session object.
    """
    async with sessionmanager.session() as session:
        yield session
