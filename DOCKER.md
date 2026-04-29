# Docker Deployment Guide

Complete containerized deployment of SentryIQ with PostgreSQL, Redis, FastAPI backend, and React frontend.

## Prerequisites

- **Docker** 20.10+ — Download from [docker.com](https://www.docker.com/products/docker-desktop)
- **Docker Compose** 2.0+ — Included with Docker Desktop
- **NVIDIA NIM API Key** — Get for free at [build.nvidia.com](https://build.nvidia.com)

## Quick Start

```bash
# 1. Clone and prepare environment
git clone https://github.com/Archer7Mi/sentryiq.git
cd sentryiq
cp .env.example .env

# 2. Edit .env and add your NVIDIA API key
# NVIDIA_API_KEY=your-api-key-here

# 3. Build and start all services
docker compose up -d

# 4. Check service health
docker compose ps

# 5. View logs
docker compose logs -f api
```

Expected output after ~30 seconds:

```
CONTAINER ID   IMAGE                      STATUS                  PORTS
abc123         sentryiq-db               Up 30s (healthy)        5432/tcp
def456         sentryiq-cache            Up 30s (healthy)        6379/tcp
ghi789         sentryiq-api              Up 10s (health: starting) 0.0.0.0:8000->8000/tcp
jkl012         sentryiq-frontend         Up 5s (health: starting)  0.0.0.0:80->80/tcp
```

## Access Points

| Component | URL | Purpose |
|-----------|-----|---------|
| Frontend | http://localhost | React dashboard |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger UI (interactive) |
| Health Check | http://localhost:8000/health | Service status |
| Postgres | localhost:5432 | Database (internal) |
| Redis | localhost:6379 | Cache (internal) |

## Common Commands

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Stop services
docker compose stop

# Restart a specific service
docker compose restart api

# View logs
docker compose logs -f api          # Follow API logs
docker compose logs --tail 50 db    # Last 50 database logs

# Run commands in container
docker compose exec api python -m pytest  # Run tests
docker compose exec db psql -U sentryiq -d sentryiq  # Connect to database

# Remove everything (including data)
docker compose down -v
```

## Environment Variables

Edit `.env` to configure:

```bash
# Database
DB_USER=sentryiq          # PostgreSQL username
DB_PASSWORD=dev-password  # PostgreSQL password (change in production!)
DB_NAME=sentryiq          # Database name

# API
API_PORT=8000            # Port to expose API
ENVIRONMENT=development  # development or production
DEBUG=false               # Enable debug logging

# Frontend
FRONTEND_PORT=80         # Port to expose frontend

# AI Integration
NVIDIA_API_KEY=...       # Required for CVE synthesis and phishing simulation
```

## Troubleshooting

### Docker daemon not running
```
Error: Cannot connect to Docker daemon
Solution: Start Docker Desktop and wait for it to initialize
```

### Port already in use
```
Error: bind: address already in use
Solution: Change ports in .env (API_PORT=8001, FRONTEND_PORT=8080)
```

### Database connection refused
```
Error: could not translate host name "db" to address
Solution: Wait for PostgreSQL to be healthy (docker compose ps shows "healthy")
```

### API health check failing
```
Error: Health check for sentryiq-api is unhealthy
Solution: Check logs (docker compose logs api) for startup errors
Wait ~10 seconds for application initialization
```

### Out of disk space
```
Solution: Remove unused images and containers
docker system prune -a
docker volume prune
```

## Database Access

### Connect to PostgreSQL

```bash
docker compose exec db psql -U sentryiq -d sentryiq

# Within psql:
\dt                    # List tables
\l                     # List databases
SELECT * FROM cves;    # Query a table
\q                     # Quit
```

### Backup Database

```bash
docker compose exec db pg_dump -U sentryiq sentryiq > backup.sql
```

### Restore Database

```bash
cat backup.sql | docker compose exec -T db psql -U sentryiq sentryiq
```

## Redis Access

```bash
docker compose exec cache redis-cli

# Within redis-cli:
KEYS *              # List all keys
GET key_name        # Get value
DEL key_name        # Delete key
FLUSHALL            # Clear all data
EXIT                # Quit
```

## Performance Tuning

### Increase Resource Limits

Edit `docker-compose.yml` to add resource limits:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 1G
```

### Enable Caching Headers

Frontend Nginx caches static assets for 1 day by default. Adjust in `frontend/nginx.conf`:

```nginx
expires 7d;  # Cache for 7 days
add_header Cache-Control "public, immutable";
```

## Production Deployment

### 1. Update `.env` for Production

```bash
ENVIRONMENT=production
DEBUG=false
DB_PASSWORD=your-secure-password-here
NVIDIA_API_KEY=your-real-api-key
```

### 2. Security Considerations

- Change default database password
- Use HTTPS (deploy behind nginx/Traefik with SSL)
- Enable authentication on all API endpoints
- Restrict NVIDIA API key permissions
- Run containers as non-root user (add to Dockerfile)
- Enable resource limits
- Set up regular backups

### 3. Deploy with AWS/Azure/GCP

```bash
# Docker Swarm (simple)
docker swarm init
docker stack deploy -c docker-compose.yml sentryiq

# Kubernetes (advanced)
# See kubernetes/ directory for helm charts

# AWS ECS
aws ecs create-cluster --cluster-name sentryiq
# ... (follow AWS documentation for task definitions)
```

## Monitoring

### View Real-Time Stats

```bash
docker stats
```

### Health Check Endpoints

All services expose health checks:

```bash
# API
curl http://localhost:8000/health

# Frontend
curl http://localhost:80/health

# Database (from container)
docker compose exec db pg_isready

# Redis (from container)
docker compose exec cache redis-cli ping
```

### Logs and Debugging

```bash
# Show all logs with timestamps
docker compose logs --timestamps

# Follow specific service logs
docker compose logs -f api

# Show last 100 lines
docker compose logs --tail 100

# Combine with grep for errors
docker compose logs | grep ERROR
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Docker

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and test
        run: |
          docker compose build
          docker compose up -d
          docker compose exec -T api pytest
```

## Advanced: Custom Builds

### Build with Production Optimizations

```bash
# Set build arguments
docker compose build --build-arg PYTHON_OPTIMIZATION=2
```

### Use External Registry

```bash
# Build for registry push
docker compose -f docker-compose.prod.yml build
docker tag sentryiq-api:latest myregistry.azurecr.io/sentryiq-api:latest
docker push myregistry.azurecr.io/sentryiq-api:latest
```

## Support

- Issues: [github.com/Archer7Mi/sentryiq/issues](https://github.com/Archer7Mi/sentryiq/issues)
- Discussions: [github.com/Archer7Mi/sentryiq/discussions](https://github.com/Archer7Mi/sentryiq/discussions)
- Documentation: [sentryiq.dev](https://sentryiq.dev)
