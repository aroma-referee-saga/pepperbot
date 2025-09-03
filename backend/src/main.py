from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List
import uvicorn
import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import settings

from . import models, schemas, auth, database, scraper, bot

from . import models, schemas, auth, database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
database.create_tables()
# Create database tables
database.create_tables()

# Start the scraper scheduler
scraper.start_scraper()

# Start the Telegram bot and notification worker
if settings.telegram_bot_token:
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start_bot())
    loop.create_task(bot.start_notification_worker())
    logger.info("Telegram bot and notification worker started")
else:
    logger.warning("Telegram bot token not configured")

app = FastAPI(title="PepperBot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}




@app.post("/auth/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/auth/login", response_model=schemas.Token)
async def login(response: Response, user_credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        expires=datetime.utcnow() + timedelta(seconds=settings.access_token_expire_minutes * 60),
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user


# Shopping List endpoints
@app.get("/lists", response_model=List[schemas.ShoppingList])
async def get_shopping_lists(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    lists = db.query(models.ShoppingList).filter(
        models.ShoppingList.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return lists


@app.post("/lists", response_model=schemas.ShoppingList)
async def create_shopping_list(
    shopping_list: schemas.ShoppingListCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_list = models.ShoppingList(**shopping_list.dict(), user_id=current_user.id)
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    return db_list


@app.get("/lists/{list_id}", response_model=schemas.ShoppingList)
async def get_shopping_list(
    list_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return db_list


@app.put("/lists/{list_id}", response_model=schemas.ShoppingList)
async def update_shopping_list(
    list_id: int,
    shopping_list_update: schemas.ShoppingListUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    update_data = shopping_list_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_list, field, value)

    db.commit()
    db.refresh(db_list)
    return db_list


@app.delete("/lists/{list_id}")
async def delete_shopping_list(
    list_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    db.delete(db_list)
    db.commit()
    return {"message": "Shopping list deleted successfully"}


# List Items endpoints
@app.get("/lists/{list_id}/items", response_model=List[schemas.ListItem])
async def get_list_items(
    list_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Verify list ownership
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    items = db.query(models.ListItem).filter(
        models.ListItem.shopping_list_id == list_id
    ).all()
    return items


@app.post("/lists/{list_id}/items", response_model=schemas.ListItem)
async def create_list_item(
    list_id: int,
    item: schemas.ListItemCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Verify list ownership
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    db_item = models.ListItem(**item.dict(), shopping_list_id=list_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.put("/lists/{list_id}/items/{item_id}", response_model=schemas.ListItem)
async def update_list_item(
    list_id: int,
    item_id: int,
    item_update: schemas.ListItemUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Verify list ownership
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    db_item = db.query(models.ListItem).filter(
        models.ListItem.id == item_id,
        models.ListItem.shopping_list_id == list_id
    ).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="List item not found")

    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/lists/{list_id}/items/{item_id}")
async def delete_list_item(
    list_id: int,
    item_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    # Verify list ownership
    db_list = db.query(models.ShoppingList).filter(
        models.ShoppingList.id == list_id,
        models.ShoppingList.user_id == current_user.id
    ).first()
    if db_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")

    db_item = db.query(models.ListItem).filter(
        models.ListItem.id == item_id,
        models.ListItem.shopping_list_id == list_id
    ).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="List item not found")

    db.delete(db_item)
    db.commit()
    return {"message": "List item deleted successfully"}


# Filter endpoints
@app.get("/filters", response_model=List[schemas.Filter])
async def get_filters(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    filters = db.query(models.Filter).filter(
        models.Filter.user_id == current_user.id
    ).all()
    return filters


@app.post("/filters", response_model=schemas.Filter)
async def create_filter(
    filter_data: schemas.FilterCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_filter = models.Filter(**filter_data.dict(), user_id=current_user.id)
    db.add(db_filter)
    db.commit()
    db.refresh(db_filter)
    return db_filter


@app.put("/filters/{filter_id}", response_model=schemas.Filter)
async def update_filter(
    filter_id: int,
    filter_update: schemas.FilterUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_filter = db.query(models.Filter).filter(
        models.Filter.id == filter_id,
        models.Filter.user_id == current_user.id
    ).first()
    if db_filter is None:
        raise HTTPException(status_code=404, detail="Filter not found")

    update_data = filter_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_filter, field, value)

    db.commit()
    db.refresh(db_filter)
    return db_filter


@app.delete("/filters/{filter_id}")
async def delete_filter(
    filter_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_filter = db.query(models.Filter).filter(
        models.Filter.id == filter_id,
        models.Filter.user_id == current_user.id
    ).first()
    if db_filter is None:
        raise HTTPException(status_code=404, detail="Filter not found")

    db.delete(db_filter)
    db.commit()
    return {"message": "Filter deleted successfully"}


# Discount endpoints
@app.get("/discounts", response_model=List[schemas.Discount])
async def get_discounts(
    skip: int = 0,
    limit: int = 100,
    store: str = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Discount)
    if store:
        query = query.filter(models.Discount.store.ilike(f"%{store}%"))
    discounts = query.offset(skip).limit(limit).all()
    return discounts


@app.post("/discounts", response_model=schemas.Discount)
async def create_discount(
    discount: schemas.DiscountCreate,
    db: Session = Depends(database.get_db)
):
    db_discount = models.Discount(**discount.dict())
    db.add(db_discount)
    db.commit()
    db.refresh(db_discount)
    return db_discount


@app.get("/discounts/{discount_id}", response_model=schemas.Discount)
async def get_discount(
    discount_id: int,
    db: Session = Depends(database.get_db)
):
    db_discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if db_discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")
    return db_discount


@app.put("/discounts/{discount_id}", response_model=schemas.Discount)
async def update_discount(
    discount_id: int,
    discount_update: schemas.DiscountUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if db_discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")

    update_data = discount_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_discount, field, value)

    db.commit()
    db.refresh(db_discount)
    return db_discount


@app.delete("/discounts/{discount_id}")
async def delete_discount(
    discount_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if db_discount is None:
        raise HTTPException(status_code=404, detail="Discount not found")

    db.delete(db_discount)
    db.commit()
    return {"message": "Discount deleted successfully"}


# Notification endpoints
@app.get("/notifications", response_model=List[schemas.Notification])
async def get_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    notifications = query.offset(skip).limit(limit).all()
    return notifications


@app.post("/notifications", response_model=schemas.Notification)
async def create_notification(
    notification: schemas.NotificationCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_notification = models.Notification(**notification.dict(), user_id=current_user.id)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


@app.get("/notifications/{notification_id}", response_model=schemas.Notification)
async def get_notification(
    notification_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification


@app.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    db_notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}


@app.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    db_notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(db_notification)
    db.commit()
    return {"message": "Notification deleted successfully"}


# Telegram webhook endpoint
@app.post("/telegram/webhook")
async def telegram_webhook(update: schemas.TelegramUpdate):
    """
    Handle incoming Telegram updates.
    This is a basic implementation - you would need to add proper Telegram bot logic here.
    """
    if update.message:
        # Handle incoming message
        chat_id = update.message.get("chat", {}).get("id")
        text = update.message.get("text", "")

        # Here you would process the message and potentially create notifications
        # or interact with shopping lists based on the message content

        return {"status": "ok", "message": "Update received"}


# Telegram user management endpoints
@app.post("/telegram/link", response_model=schemas.TelegramUser)
async def link_telegram_user(
    link_data: schemas.TelegramUserLink,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """Link Telegram chat ID to current user"""
    # This would typically be called from the bot when user provides credentials
    # For now, we'll create the link directly
    telegram_user = models.TelegramUser(
        telegram_chat_id=str(link_data.username),  # Using username as placeholder for chat_id
        user_id=current_user.id
    )
    db.add(telegram_user)
    db.commit()
    db.refresh(telegram_user)
    return telegram_user


@app.get("/telegram/users", response_model=List[schemas.TelegramUser])
async def get_telegram_users(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """Get linked Telegram users for current user"""
    telegram_users = db.query(models.TelegramUser).filter(
        models.TelegramUser.user_id == current_user.id
    ).all()
    return telegram_users


@app.delete("/telegram/users/{telegram_user_id}")
async def unlink_telegram_user(
    telegram_user_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db)
):
    """Unlink Telegram user"""
    telegram_user = db.query(models.TelegramUser).filter(
        models.TelegramUser.id == telegram_user_id,
        models.TelegramUser.user_id == current_user.id
    ).first()

    if not telegram_user:
        raise HTTPException(status_code=404, detail="Telegram user link not found")

    db.delete(telegram_user)
    db.commit()
    return {"message": "Telegram user unlinked successfully"}
# Scraper endpoints
@app.post("/scraper/trigger")
async def trigger_scraper():
    """Manually trigger the scraper"""
    try:
        await scraper.manual_scrape()
        return {"message": "Scraper triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering scraper: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger scraper")


@app.get("/scraper/status")
async def get_scraper_status():
    """Get scraper status"""
    return {
        "scheduler_running": scraper.scheduler.running if hasattr(scraper, 'scheduler') else False,
        "last_run": getattr(scraper, 'last_run', None)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)