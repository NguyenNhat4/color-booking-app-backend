# Color Swap Backend API

A FastAPI-based backend service for the Color Swap application that provides image processing and color replacement functionality.

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- Git (for cloning the repository)

### Running the Backend Container

1. **Clone and navigate to the backend directory:**
   ```bash
   git clone <your-repo-url>
   cd Backend
   ```

2. **Create environment configuration:**
   ```bash
   # Copy the example environment file (if it exists) or create a new one
   cp .env.example .env  # or create .env manually
   ```

3. **Configure environment variables (optional):**
   
   Create a `.env` file in the Backend directory with the following variables:
   ```env
   # Database Configuration
   POSTGRES_USER=colorswapuser_backend
   POSTGRES_PASSWORD=colorswappass_backend
   POSTGRES_DB=colorswapdb_backend
   POSTGRES_EXPOSED_PORT_BACKEND=5433
   
   # API Configuration
   API_PORT_BACKEND=8001
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```
   
   > **Note:** If you don't create a `.env` file, the system will use the default values specified in `docker-compose.yml`.

4. **Start the backend services:**
   ```bash
   docker-compose up -d
   ```
   
   This command will:
   - Start a PostgreSQL database container
   - Build and start the FastAPI application container
   - Set up networking between containers
   - Expose the API on port 8001 (or your configured port)

5. **Verify the services are running:**
   ```bash
   docker-compose ps
   ```
   
   You should see both `color_swap_db_backend` and `color_swap_api_backend` containers running.

6. **Access the API:**
   - **API Documentation (Swagger UI):** http://localhost:8001/docs
   - **Alternative Documentation (ReDoc):** http://localhost:8001/redoc
   - **Health Check:** http://localhost:8001/health (if implemented)

## 🔧 Development Commands

### Container Management

```bash
# Start services in foreground (see logs)
docker-compose up

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Stop services and remove volumes (⚠️ This will delete database data)
docker-compose down -v

# Rebuild containers (after code changes)
docker-compose up --build

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs api
docker-compose logs db
```

### Executing Commands Inside Containers

```bash
# Access the API container shell
docker-compose exec api bash

# Run database migrations (if implemented)
docker-compose exec api python -m alembic upgrade head

# Run tests inside the container
docker-compose exec api python -m pytest

# Check Python packages
docker-compose exec api pip list

# Access PostgreSQL directly
docker-compose exec db psql -U colorswapuser_backend -d colorswapdb_backend
```

### Database Operations

```bash
# Create database backup
docker-compose exec db pg_dump -U colorswapuser_backend colorswapdb_backend > backup.sql

# Restore database from backup
docker-compose exec -T db psql -U colorswapuser_backend colorswapdb_backend < backup.sql

# Reset database (⚠️ This will delete all data)
docker-compose down -v
docker-compose up -d
```

## 📁 Project Structure

```
Backend/
├── api/                    # API route handlers
├── models/                 # Database models
├── schemas/                # Pydantic schemas
├── services/               # Business logic
├── scripts/                # Utility scripts
├── storage/                # File storage directory
├── tests/                  # Test files
├── config.py               # Configuration settings
├── database.py             # Database connection
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build instructions
├── docker-compose.yml      # Multi-container orchestration
└── .env                    # Environment variables (create this)
```

## 🌐 API Endpoints

Once the backend is running, you can explore all available endpoints using the interactive API documentation:

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use:**
   ```bash
   # Error: Port 8001 is already allocated
   # Solution: Change the port in .env file
   API_PORT_BACKEND=8002
   ```

2. **Database Connection Issues:**
   ```bash
   # Check if database is ready
   docker-compose logs db
   
   # Wait for database to be ready before starting API
   docker-compose up db
   # Wait for healthy status, then:
   docker-compose up api
   ```

3. **Permission Issues with Storage:**
   ```bash
   # Ensure storage directory has proper permissions
   chmod 755 storage/
   ```

4. **Container Build Failures:**
   ```bash
   # Clean build with no cache
   docker-compose build --no-cache
   
   # Remove old containers and rebuild
   docker-compose down
   docker system prune -f
   docker-compose up --build
   ```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f db

# Last 50 lines
docker-compose logs --tail=50 api
```

### Health Checks

```bash
# Check container status
docker-compose ps

# Check container resource usage
docker stats

# Inspect container details
docker-compose inspect api
```

## 🧪 Testing

Run the test suite inside the container:

```bash
# Run all tests
docker-compose exec api python -m pytest

# Run tests with coverage
docker-compose exec api python -m pytest --cov=.

# Run specific test file
docker-compose exec api python -m pytest tests/test_auth.py

# Run tests with verbose output
docker-compose exec api python -m pytest -v
```

## 📦 Dependencies

The main dependencies are listed in `requirements.txt`:
- FastAPI - Web framework
- SQLAlchemy - Database ORM
- PostgreSQL - Database
- Pillow - Image processing
- And more...

## 🔒 Security Notes

- Always use strong passwords for production databases
- Keep your `.env` file secure and never commit it to version control
- Regularly update dependencies for security patches
- Use HTTPS in production environments

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `colorswapuser_backend` | Database username |
| `POSTGRES_PASSWORD` | `colorswappass_backend` | Database password |
| `POSTGRES_DB` | `colorswapdb_backend` | Database name |
| `POSTGRES_EXPOSED_PORT_BACKEND` | `5433` | Host port for database |
| `API_PORT_BACKEND` | `8001` | Host port for API |
| `SECRET_KEY` | Required | JWT secret key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `docker-compose exec api python -m pytest`
4. Submit a pull request

## 📄 License

[Add your license information here] 