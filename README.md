Download the repository:

##To start container
docker-compose up -d

##To start with DB
alembic upgrade head

##tests
poetry run pytest --cov=src tests/
