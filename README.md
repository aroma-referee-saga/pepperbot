# PepperBot - Docker Setup

A comprehensive shopping assistant with discount tracking, shopping lists, and Telegram bot integration.

## Features

- 🛒 **Discount Tracking**: Automatically scrape and track discounts from Pepper.ru
- 📱 **Web Interface**: Modern React frontend for managing shopping lists and discounts
- 🤖 **Telegram Bot**: Receive notifications and manage lists via Telegram
- 🔄 **Real-time Updates**: Get notified when discounts match your filters
- 🗄️ **SQLite Database**: Lightweight, file-based database with shared volumes
- 🐳 **Docker Ready**: Complete containerization for easy deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pepperbot
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Production Setup

1. **Configure production environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Start production environment**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. **Access the application**
   - Application: http://localhost
   - Backend API: http://localhost/api/

## Services

### Backend (FastAPI)
- **Port**: 8000
- **Health Check**: `/health`
- **API Docs**: `/docs`

### Frontend (React)
- **Port**: 3000 (dev) / 80 (prod)
- **Technology**: React + TypeScript + Vite

### Scraper
- **Function**: Periodic scraping of Pepper.ru
- **Schedule**: Every 30 minutes

### Telegram Bot
- **Function**: User notifications and list management
- **Commands**: /start, /login, /lists, /filters, etc.

### Database
- **Type**: SQLite (shared volume)
- **Location**: `/app/data/pepperbot.db`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./pepperbot.db` |
| `SECRET_KEY` | JWT secret key | Required |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Optional |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `REACT_APP_API_URL` | Frontend API URL | `http://localhost:8000` |

## Docker Commands

### Development
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up --build

# Start in background
docker-compose -f docker-compose.dev.yml up -d --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down

# Rebuild and restart
docker-compose -f docker-compose.dev.yml up --build --force-recreate
```

### Production
```bash
# Start production
docker-compose -f docker-compose.prod.yml up -d --build

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale scraper=2

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Update deployment
docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d
```

## Database Management

### SQLite Database
The SQLite database is stored in a Docker volume for persistence:

```bash
# View database volume
docker volume ls | grep sqlite_data

# Backup database
docker run --rm -v pepperbot_sqlite_data:/data -v $(pwd):/backup alpine tar czf /backup/database_backup.tar.gz -C /data .
```

### Database Initialization
The database is automatically initialized when the backend service starts for the first time.

## Monitoring and Health Checks

All services include health checks:

- **Backend**: `/health` endpoint
- **Frontend**: HTTP check on port 80
- **Database**: PostgreSQL health check
- **Nginx**: Basic HTTP check

```bash
# Check service health
docker-compose ps
docker-compose exec backend curl http://localhost:8000/health
```

## Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get the bot token
3. Set `TELEGRAM_BOT_TOKEN` in your `.env` file
4. Start the bot service
5. Send `/start` to your bot to begin

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using ports
   netstat -tulpn | grep :8000
   # Change ports in docker-compose files
   ```

2. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose logs db
   # Reset database volume
   docker-compose down -v && docker-compose up -d
   ```

3. **Permission issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Enter container for debugging
docker-compose exec backend bash
```

## Deployment

### Coolify Deployment

This setup is compatible with Coolify:

1. Connect your repository to Coolify
2. Use `docker-compose.prod.yml` as the compose file
3. Set environment variables in Coolify dashboard
4. Configure domains and SSL certificates

### Manual Server Deployment

```bash
# On your server
git clone <repository-url>
cd pepperbot
cp .env.example .env
# Edit .env with production values
docker-compose -f docker-compose.prod.yml up -d --build
```

## Development

### Adding New Features

1. **Backend**: Add endpoints in `backend/src/main.py`
2. **Frontend**: Add components in `frontend/src/components/`
3. **Database**: Update models in `backend/src/models.py`
4. **Bot**: Add commands in `backend/src/bot.py`

### Testing

```bash
# Run backend tests
docker-compose exec backend python -m pytest

# Run frontend tests
docker-compose exec frontend npm test
```

## Security Considerations

- Change default `SECRET_KEY` in production
- Use strong passwords for database
- Enable SSL/TLS in production
- Regularly update Docker images
- Monitor logs for security issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker setup
5. Submit a pull request

## License

This project is licensed under the MIT License.