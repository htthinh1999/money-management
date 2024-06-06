docker build -t money-management .
docker compose down
docker image prune -f
docker compose up -d
