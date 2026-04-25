.PHONY: dev

dev:
	@trap 'kill 0' INT; \
	(cd backend && uv run fastapi dev) & \
	(cd frontend && npm run dev) & \
	wait
