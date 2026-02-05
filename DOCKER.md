# Docker Deployment Guide for MD2DB

This guide covers building, deploying, and running MD2DB using Docker containers.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Building Images](#building-images)
- [Running with Docker Compose](#running-with-docker-compose)
- [Environment Configuration](#environment-configuration)
- [Multi-Architecture Support](#multi-architecture-support)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- At least 2GB of available RAM
- 5GB of free disk space

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository and navigate to the project:**
   ```bash
   cd /path/to/md2db
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env to customize settings
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Check service status:**
   ```bash
   docker-compose ps
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f md2db
   ```

The API will be available at `http://localhost:8080`

### Using Docker Run

1. **Build the image:**
   ```bash
   docker build -t md2db:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name md2db \
     -p 8080:8080 \
     -e RUST_LOG=info \
     md2db:latest
   ```

## Building Images

### Standard Build (Current Architecture)

```bash
docker build -t md2db:latest .
```

### Multi-Architecture Build

Build for both ARM64 and AMD64 platforms:

```bash
# Using buildx (recommended)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t md2db:latest .

# Build and push to registry
docker buildx build --platform linux/amd64,linux/arm64 -t your-registry/md2db:latest --push .
```

### Build Options

```bash
# Build with custom Rust version
docker build --build-arg RUST_VERSION=1.75 -t md2db:latest .

# Build with debug symbols (not recommended for production)
docker build --target builder -t md2db:debug .
```

## Running with Docker Compose

### Basic Services

Start the application with PostgreSQL:

```bash
docker-compose up -d
```

### With Admin Tools

Include pgAdmin and Mongo Express for database management:

```bash
docker-compose --profile admin up -d
```

### Individual Services

Start specific services:

```bash
# Only MD2DB (external database required)
docker-compose up -d md2db

# Only PostgreSQL
docker-compose up -d postgres

# Only MongoDB
docker-compose up -d mongodb
```

### Service Management

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Restart services
docker-compose restart md2db

# View logs
docker-compose logs -f md2db

# Execute commands in container
docker-compose exec md2db /bin/sh
```

## Environment Configuration

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | API server port | `8080` |
| `HOST` | Bind address | `0.0.0.0` |
| `RUST_LOG` | Log level | `info` |

### Database Configuration

#### PostgreSQL

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_ENABLED` | Enable PostgreSQL | `true` |
| `POSTGRES_DB` | Database name | `md2db` |
| `POSTGRES_USER` | Database user | `md2db` |
| `POSTGRES_PASSWORD` | Database password | `md2db_password` |
| `DATABASE_URL` | Full connection string | Auto-generated |

#### MongoDB

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_ENABLED` | Enable MongoDB | `false` |
| `MONGO_DB` | Database name | `md2db` |
| `MONGO_USER` | Database user | `md2db` |
| `MONGO_PASSWORD` | Database password | `md2db_password` |
| `MONGODB_URI` | Full connection string | Auto-generated |

### Admin Tools

| Variable | Description | Default |
|----------|-------------|---------|
| `PGADMIN_EMAIL` | pgAdmin login email | `admin@md2db.local` |
| `PGADMIN_PASSWORD` | pgAdmin password | `admin` |
| `PGADMIN_PORT` | pgAdmin web port | `5050` |
| `MONGO_EXPRESS_USER` | Mongo Express user | `admin` |
| `MONGO_EXPRESS_PASSWORD` | Mongo Express password | `admin` |
| `MONGO_EXPRESS_PORT` | Mongo Express port | `8081` |

## Multi-Architecture Support

The Dockerfile is designed to support multiple architectures:

### Supported Platforms

- `linux/amd64` (x86_64) - Intel/AMD processors
- `linux/arm64` (aarch64) - Apple Silicon, ARM servers

### Building for Specific Architecture

```bash
# Build for AMD64
docker buildx build --platform linux/amd64 -t md2db:amd64 .

# Build for ARM64
docker buildx build --platform linux/arm64 -t md2db:arm64 .

# Build for both (multi-arch image)
docker buildx build --platform linux/amd64,linux/arm64 -t md2db:latest .
```

### Platform-Specific Optimization

The Dockerfile uses:
- Multi-stage builds to minimize image size
- Architecture-agnostic base images
- Cached dependency layers for faster rebuilds

Final image size: ~80-100 MB (depending on architecture)

## Production Deployment

### Security Best Practices

1. **Change default passwords:**
   ```bash
   # Edit .env and set strong passwords
   POSTGRES_PASSWORD=$(openssl rand -base64 32)
   MONGO_PASSWORD=$(openssl rand -base64 32)
   ```

2. **Use secrets management:**
   ```bash
   # Using Docker Secrets (Swarm mode)
   echo "your_password" | docker secret create postgres_password -
   ```

3. **Run as non-root user:**
   The Dockerfile already creates a non-root user (`md2db`).

4. **Enable TLS:**
   Use a reverse proxy (nginx, traefik) for HTTPS termination.

### Resource Limits

Configure resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
    reservations:
      memory: 256M
      cpus: '0.5'
```

### Health Checks

The container includes built-in health checks:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' md2db-app
```

### Volume Management

Persistent data is stored in named volumes:

```bash
# List volumes
docker volume ls | grep md2db

# Backup PostgreSQL data
docker run --rm \
  -v md2db-postgres-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore PostgreSQL data
docker run --rm \
  -v md2db-postgres-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

### Scaling

```bash
# Scale MD2DB instances (requires external database)
docker-compose up -d --scale md2db=3

# Use load balancer (nginx example)
upstream md2db {
    server md2db_1:8080;
    server md2db_2:8080;
    server md2db_3:8080;
}
```

## Troubleshooting

### Container Won't Start

**Problem:** Container exits immediately

**Solutions:**
```bash
# Check logs
docker-compose logs md2db

# Common issues:
# 1. Port already in use - Change PORT in .env
# 2. Database connection failed - Check DATABASE_URL
# 3. Missing environment variables - Verify .env file
```

### Database Connection Issues

**Problem:** Cannot connect to PostgreSQL/MongoDB

**Solutions:**
```bash
# Check if database is running
docker-compose ps

# Verify network connectivity
docker-compose exec md2db ping postgres

# Check database logs
docker-compose logs postgres
docker-compose logs mongodb
```

### High Memory Usage

**Problem:** Container using too much memory

**Solutions:**
```bash
# Check resource usage
docker stats

# Reduce memory limit in docker-compose.yml
# Or increase system swap space
```

### Build Failures

**Problem:** Docker build fails

**Solutions:**
```bash
# Clean build cache
docker builder prune -a

# Build without cache
docker build --no-cache -t md2db:latest .

# Check for dependency issues
docker-compose run --rm md2db cargo check
```

### Architecture Mismatches

**Problem:** Image doesn't run on target platform

**Solutions:**
```bash
# Check current architecture
uname -m
docker buildx ls

# Rebuild for correct platform
docker buildx build --platform linux/amd64 -t md2db:latest .
```

## Advanced Usage

### Custom Entry Point

```bash
docker run -d \
  --name md2db \
  -p 8080:8080 \
  --entrypoint /bin/sh \
  md2db:latest \
  -c "while true; do sleep 30; done"
```

### Development Mode

Mount source code for live reloading:

```yaml
# Override in docker-compose.override.yml
services:
  md2db:
    volumes:
      - ./src:/usr/src/app/src
      - ./Cargo.toml:/usr/src/app/Cargo.toml
```

### Monitoring

```bash
# Live container metrics
docker stats md2db-app

# Detailed inspection
docker inspect md2db-app

# Resource usage history
docker system df
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Rust Docker Best Practices](https://github.com/rust-lang/docker-rust)
- [PostgreSQL Docker Images](https://hub.docker.com/_/postgres)
- [MongoDB Docker Images](https://hub.docker.com/_/mongo)
