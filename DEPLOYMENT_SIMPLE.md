# Simplified Deployment Guide

This guide provides a streamlined path to deploying the Warehouse Operational Assistant in a production-like environment using Docker Compose.

## Prerequisites

- **Docker Desktop** (or Docker Engine + Compose plugin) installed and running.
- **NVIDIA API Key** (for AI services).

## 1. Environment Setup

### Step 1: Get an NVIDIA API Key
1. Go to [build.nvidia.com](https://build.nvidia.com/).
2. Create an account or log in.
3. Click on your profile icon and select **Get API Key**.
4. Generate a new key and copy it (starts with `nvapi-`).

### Step 2: Configure Environment Variables
1. Navigate to the `deploy/compose` directory:
   ```bash
   cd deploy/compose
   ```
2. Copy the example environment file:
   ```bash
   cp ../../.env.example .env
   ```
   *(On Windows PowerShell, use `copy ..\..\.env.example .env`)*

3. Open `.env` in a text editor and update the following **critical** variables:

   ```ini
   # --- AI Services ---
   NVIDIA_API_KEY=nvapi-your-key-here
   
   # --- Security ---
   # Generate a strong random string (e.g. `openssl rand -hex 32`)
   JWT_SECRET_KEY=your-super-secret-key-minimum-32-chars
   POSTGRES_PASSWORD=secure-db-password
   DEFAULT_ADMIN_PASSWORD=secure-admin-password
   
   # --- Ports (Optional) ---
   # Change these if ports are occupied (e.g. if 3000 is used)
   FRONTEND_PORT=3000
   API_PORT=8001
   DB_PORT=5435
   ```

## 2. Deploy

Run the following command from the `deploy/compose` directory to build and start all services (Frontend, Backend, Database, Vector DB, Redis):

```bash
docker compose -f docker-compose.prod.yaml up --build -d
```

- `-d`: Runs containers in the background (detached mode).
- `--build`: Forces a rebuild of the images (important for first run).

## 3. Verify Deployment

Wait a few minutes for the services to initialize (especially the database and API).

### Check Status
```bash
docker compose -f docker-compose.prod.yaml ps
```
All services (`warehouse-api-prod`, `warehouse-frontend-prod`, etc.) should be `Up (healthy)` or `Up`.

### Access the Application
- **Frontend**: [http://localhost:3000](http://localhost:3000) (or the port defined in `FRONTEND_PORT`)
  - Login: `admin` / `secure-admin-password` (from your .env)
- **API Health Check**: [http://localhost:8001/api/v1/health](http://localhost:8001/api/v1/health) (or the port defined in `API_PORT`)

## Troubleshooting

**Port Conflicts (e.g., Port 3000 already in use):**
If `docker compose` fails with "Bind for 0.0.0.0:3000 failed: port is already allocated":
1. Open `.env`.
2. Change `FRONTEND_PORT=3000` to `FRONTEND_PORT=3002` (or another free port).
3. Restart: `docker compose -f docker-compose.prod.yaml up -d`

**Database Connection Errors:**
Ensure `POSTGRES_PASSWORD` in `.env` matches the password used by the database container. If you changed the password *after* the first run volume creation, you must remove the volume to reset it:
```bash
docker compose -f docker-compose.prod.yaml down -v
docker compose -f docker-compose.prod.yaml up -d
```

**View Logs:**
```bash
# View backend logs
docker compose -f docker-compose.prod.yaml logs -f chain_server

# View frontend logs
docker compose -f docker-compose.prod.yaml logs -f frontend
```
