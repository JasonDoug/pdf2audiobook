up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

backend-logs:
	docker-compose logs -f backend

frontend-logs:
	docker-compose logs -f frontend

worker-logs:
	docker-compose logs -f worker

lint:
	black . && isort .

migrate:
	docker-compose run --rm backend alembic upgrade head

migration:
	docker-compose run --rm backend alembic revision --autogenerate -m "New migration"
