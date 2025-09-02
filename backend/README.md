# PepperBot Backend API

A FastAPI-based backend for PepperBot with user authentication, shopping list management, discount tracking, and notification system.

## Features

- **User Authentication**: Cookie-based sessions with JWT tokens
- **Shopping Lists**: Full CRUD operations for shopping lists and items
- **Filters**: Custom notification filters for users
- **Discounts**: Store and retrieve discount information
- **Notifications**: User notification system
- **Telegram Integration**: Webhook endpoint for Telegram bot integration

## Tech Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Database (easily configurable for PostgreSQL/MySQL)
- **Pydantic**: Data validation and serialization
- **JWT**: JSON Web Tokens for authentication
- **Bcrypt**: Password hashing

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the database:**
   ```bash
   python init_db.py
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `GET /users/me` - Get current user info

### Shopping Lists
- `GET /lists` - Get all shopping lists
- `POST /lists` - Create a new shopping list
- `GET /lists/{id}` - Get a specific shopping list
- `PUT /lists/{id}` - Update a shopping list
- `DELETE /lists/{id}` - Delete a shopping list

### List Items
- `GET /lists/{list_id}/items` - Get items in a shopping list
- `POST /lists/{list_id}/items` - Add item to shopping list
- `PUT /lists/{list_id}/items/{item_id}` - Update list item
- `DELETE /lists/{list_id}/items/{item_id}` - Delete list item

### Filters
- `GET /filters` - Get user filters
- `POST /filters` - Create a new filter
- `PUT /filters/{id}` - Update a filter
- `DELETE /filters/{id}` - Delete a filter

### Discounts
- `GET /discounts` - Get all discounts (with optional store filter)
- `POST /discounts` - Create a new discount
- `GET /discounts/{id}` - Get a specific discount
- `PUT /discounts/{id}` - Update a discount
- `DELETE /discounts/{id}` - Delete a discount

### Notifications
- `GET /notifications` - Get user notifications
- `POST /notifications` - Create a new notification
- `GET /notifications/{id}` - Get a specific notification
- `PUT /notifications/{id}/read` - Mark notification as read
- `DELETE /notifications/{id}` - Delete a notification

### Telegram
- `POST /telegram/webhook` - Telegram webhook endpoint

## Configuration

Create a `.env` file in the backend directory:

```env
DATABASE_URL=sqlite:///./pepperbot.db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

## Development

The application uses automatic table creation on startup. For production, consider using Alembic for proper database migrations.

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation powered by Swagger UI.