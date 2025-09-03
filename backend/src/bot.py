import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.orm import Session

from config.settings import settings
from . import models, schemas, auth, database
from .database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
if settings.telegram_bot_token:
    bot = Bot(token=settings.telegram_bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Only define bot handlers if dp is available
    class BotStates(StatesGroup):
        waiting_for_login = State()
        waiting_for_password = State()
        waiting_for_filter_name = State()
        waiting_for_filter_criteria = State()
        waiting_for_list_name = State()
        waiting_for_item_name = State()

    def get_user_by_chat_id(db: Session, chat_id: str) -> Optional[models.User]:
        """Get user by Telegram chat ID"""
        telegram_user = db.query(models.TelegramUser).filter(
            models.TelegramUser.telegram_chat_id == str(chat_id),
            models.TelegramUser.is_active == True
        ).first()

        if telegram_user:
            return telegram_user.user
        return None

    def link_telegram_user(db: Session, chat_id: str, user: models.User) -> models.TelegramUser:
        """Link Telegram chat ID to user"""
        # Check if already linked
        existing = db.query(models.TelegramUser).filter(
            models.TelegramUser.telegram_chat_id == str(chat_id)
        ).first()

        if existing:
            existing.user_id = user.id
            existing.is_active = True
            db.commit()
            return existing

        # Create new link
        telegram_user = models.TelegramUser(
            telegram_chat_id=str(chat_id),
            user_id=user.id
        )
        db.add(telegram_user)
        db.commit()
        db.refresh(telegram_user)
        return telegram_user

    def check_discount_matches_filter(discount: models.Discount, filter_criteria: str) -> bool:
        """Check if discount matches filter criteria"""
        try:
            criteria = json.loads(filter_criteria)
            # Simple matching logic - can be extended
            if 'store' in criteria and criteria['store'].lower() not in discount.store.lower():
                return False
            if 'min_discount' in criteria and discount.discount_percentage:
                if discount.discount_percentage < criteria['min_discount']:
                    return False
            if 'keywords' in criteria:
                keywords = [k.lower() for k in criteria['keywords']]
                title_lower = discount.title.lower()
                if not any(keyword in title_lower for keyword in keywords):
                    return False
            return True
        except (json.JSONDecodeError, KeyError):
            return False

    async def send_discount_notification(chat_id: str, discount: models.Discount):
        """Send discount notification to user"""
        if not bot:
            return

        message = f"🛒 *{discount.title}*\n"
        message += f"🏪 Store: {discount.store}\n"

        if discount.discount_price and discount.original_price:
            message += f"💰 Price: {discount.discount_price} (was {discount.original_price})\n"
        elif discount.discount_percentage:
            message += f"📉 Discount: {discount.discount_percentage}%\n"

        if discount.description:
            message += f"📝 {discount.description}\n"

        if discount.url:
            message += f"🔗 [View Deal]({discount.url})"

        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Failed to send notification to {chat_id}: {e}")

    async def send_shopping_list_suggestion(chat_id: str, discount: models.Discount, user: models.User, db: Session):
        """Send shopping list suggestion for discounted item"""
        if not bot:
            return

        # Check if item is already in any of user's shopping lists
        existing_items = db.query(models.ListItem).join(models.ShoppingList).filter(
            models.ShoppingList.user_id == user.id,
            models.ListItem.name.ilike(f"%{discount.title}%"),
            models.ListItem.is_completed == False
        ).all()

        if existing_items:
            return  # Already in shopping list

        # Find active shopping lists
        active_lists = db.query(models.ShoppingList).filter(
            models.ShoppingList.user_id == user.id
        ).all()

        if not active_lists:
            return

        keyboard = []
        for shopping_list in active_lists:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=f"Add to {shopping_list.title}",
                    callback_data=f"add_to_list:{shopping_list.id}:{discount.id}"
                )
            ])

        markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

        message = f"🛒 Found discount on *{discount.title}*!\n"
        message += f"Would you like to add this to your shopping list?"

        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Failed to send suggestion to {chat_id}: {e}")

    async def process_discount_notifications(db: Session):
        """Process and send discount notifications to users"""
        if not bot:
            return

        # Get all active discounts
        discounts = db.query(models.Discount).filter(
            models.Discount.valid_until.is_(None) |
            (models.Discount.valid_until > datetime.utcnow())
        ).all()

        # Get all active filters with linked Telegram users
        filters = db.query(models.Filter).join(models.User).join(models.TelegramUser).filter(
            models.Filter.is_active == True,
            models.TelegramUser.is_active == True
        ).all()

        for discount in discounts:
            for filter_obj in filters:
                if check_discount_matches_filter(discount, filter_obj.criteria):
                    # Check if notification already sent
                    existing_notification = db.query(models.Notification).filter(
                        models.Notification.user_id == filter_obj.user_id,
                        models.Notification.discount_id == discount.id
                    ).first()

                    if not existing_notification:
                        # Create notification in database
                        notification = models.Notification(
                            title=f"Discount Match: {discount.title}",
                            message=f"Found a discount matching your '{filter_obj.name}' filter",
                            type="discount",
                            user_id=filter_obj.user_id,
                            discount_id=discount.id
                        )
                        db.add(notification)
                        db.commit()

                        # Send Telegram notification
                        telegram_user = db.query(models.TelegramUser).filter(
                            models.TelegramUser.user_id == filter_obj.user_id,
                            models.TelegramUser.is_active == True
                        ).first()

                        if telegram_user:
                            await send_discount_notification(telegram_user.telegram_chat_id, discount)
                            await send_shopping_list_suggestion(
                                telegram_user.telegram_chat_id, discount, filter_obj.user, db
                            )

    # Command handlers
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        """Handle /start command"""
        await state.clear()

        welcome_text = """
🤖 Welcome to PepperBot!

I help you find the best discounts and manage your shopping lists.

Commands:
/login - Link your account
/filters - Manage discount filters
/lists - View shopping lists
/help - Show this help

First, please /login to link your account.
"""

        await message.reply(welcome_text)

    @dp.message(Command("login"))
    async def cmd_login(message: types.Message, state: FSMContext):
        """Handle /login command"""
        await state.clear()

        # Check if already logged in
        async with database.get_db() as db:
            user = get_user_by_chat_id(db, message.chat.id)
            if user:
                await message.reply(f"✅ Already logged in as {user.username}")
                return

        await state.set_state(BotStates.waiting_for_login)
        await message.reply("Please enter your username:")

    @dp.message(BotStates.waiting_for_login)
    async def process_username(message: types.Message, state: FSMContext):
        """Process username input"""
        username = message.text.strip()

        await state.update_data(username=username)
        await state.set_state(BotStates.waiting_for_password)
        await message.reply("Please enter your password:")

    @dp.message(BotStates.waiting_for_password)
    async def process_password(message: types.Message, state: FSMContext):
        """Process password input"""
        password = message.text.strip()
        data = await state.get_data()

        async with database.get_db() as db:
            user = auth.authenticate_user(db, data['username'], password)
            if user:
                link_telegram_user(db, message.chat.id, user)
                await state.clear()
                await message.reply(f"✅ Successfully logged in as {user.username}!")
            else:
                await message.reply("❌ Invalid username or password. Please try again with /login")

    @dp.message(Command("filters"))
    async def cmd_filters(message: types.Message):
        """Handle /filters command"""
        async with database.get_db() as db:
            user = get_user_by_chat_id(db, message.chat.id)
            if not user:
                await message.reply("❌ Please /login first")
                return

            filters = db.query(models.Filter).filter(
                models.Filter.user_id == user.id
            ).all()

            if not filters:
                text = "📋 You have no filters yet.\n\nUse /addfilter to create one."
            else:
                text = "📋 Your filters:\n\n"
                for f in filters:
                    status = "✅" if f.is_active else "❌"
                    text += f"{status} {f.name}\n"

                text += "\nUse /addfilter to create a new filter."

            keyboard = []
            for f in filters:
                keyboard.append([
                    types.InlineKeyboardButton(
                        text=f"{'Disable' if f.is_active else 'Enable'} {f.name}",
                        callback_data=f"toggle_filter:{f.id}"
                    )
                ])

            if keyboard:
                markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
                await message.reply(text, reply_markup=markup)
            else:
                await message.reply(text)

    @dp.message(Command("addfilter"))
    async def cmd_addfilter(message: types.Message, state: FSMContext):
        """Handle /addfilter command"""
        async with database.get_db() as db:
            user = get_user_by_chat_id(db, message.chat.id)
            if not user:
                await message.reply("❌ Please /login first")
                return

        await state.set_state(BotStates.waiting_for_filter_name)
        await message.reply("Please enter a name for your new filter:")

    @dp.message(BotStates.waiting_for_filter_name)
    async def process_filter_name(message: types.Message, state: FSMContext):
        """Process filter name input"""
        filter_name = message.text.strip()

        await state.update_data(filter_name=filter_name)
        await state.set_state(BotStates.waiting_for_filter_criteria)

        example_criteria = """
Please enter filter criteria as JSON. Examples:

For store-specific discounts:
{"store": "Amazon"}

For minimum discount percentage:
{"min_discount": 20}

For keyword matching:
{"keywords": ["laptop", "computer"]}

Combined criteria:
{"store": "Walmart", "min_discount": 15, "keywords": ["electronics"]}
"""

        await message.reply(example_criteria)

    @dp.message(BotStates.waiting_for_filter_criteria)
    async def process_filter_criteria(message: types.Message, state: FSMContext):
        """Process filter criteria input"""
        criteria_text = message.text.strip()
        data = await state.get_data()

        try:
            # Validate JSON
            json.loads(criteria_text)

            async with database.get_db() as db:
                user = get_user_by_chat_id(db, message.chat.id)
                if user:
                    new_filter = models.Filter(
                        name=data['filter_name'],
                        criteria=criteria_text,
                        user_id=user.id
                    )
                    db.add(new_filter)
                    db.commit()

                    await message.reply(f"✅ Filter '{data['filter_name']}' created successfully!")
                else:
                    await message.reply("❌ Session expired. Please /login again")

        except json.JSONDecodeError:
            await message.reply("❌ Invalid JSON format. Please try again or use /addfilter to start over")
            return

        await state.clear()

    @dp.message(Command("lists"))
    async def cmd_lists(message: types.Message):
        """Handle /lists command"""
        async with database.get_db() as db:
            user = get_user_by_chat_id(db, message.chat.id)
            if not user:
                await message.reply("❌ Please /login first")
                return

            shopping_lists = db.query(models.ShoppingList).filter(
                models.ShoppingList.user_id == user.id
            ).all()

            if not shopping_lists:
                text = "📝 You have no shopping lists yet.\n\nUse /createlist to create one."
            else:
                text = "📝 Your shopping lists:\n\n"
                for sl in shopping_lists:
                    item_count = db.query(models.ListItem).filter(
                        models.ListItem.shopping_list_id == sl.id
                    ).count()
                    completed_count = db.query(models.ListItem).filter(
                        models.ListItem.shopping_list_id == sl.id,
                        models.ListItem.is_completed == True
                    ).count()

                    text += f"🛒 {sl.title} ({completed_count}/{item_count} completed)\n"

                text += "\nUse /createlist to create a new list."

            keyboard = []
            for sl in shopping_lists:
                keyboard.append([
                    types.InlineKeyboardButton(
                        text=f"View {sl.title}",
                        callback_data=f"view_list:{sl.id}"
                    )
                ])

            if keyboard:
                markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
                await message.reply(text, reply_markup=markup)
            else:
                await message.reply(text)

    @dp.message(Command("createlist"))
    async def cmd_createlist(message: types.Message, state: FSMContext):
        """Handle /createlist command"""
        async with database.get_db() as db:
            user = get_user_by_chat_id(db, message.chat.id)
            if not user:
                await message.reply("❌ Please /login first")
                return

        await state.set_state(BotStates.waiting_for_list_name)
        await message.reply("Please enter a name for your new shopping list:")

    @dp.message(BotStates.waiting_for_list_name)
    async def process_list_name(message: types.Message, state: FSMContext):
        """Process shopping list name input"""
        list_name = message.text.strip()

        async with database.get_db() as db:
            user = get_user_by_chat_id(db, message.chat.id)
            if user:
                new_list = models.ShoppingList(
                    title=list_name,
                    user_id=user.id
                )
                db.add(new_list)
                db.commit()

                await message.reply(f"✅ Shopping list '{list_name}' created successfully!")
            else:
                await message.reply("❌ Session expired. Please /login again")

        await state.clear()

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        """Handle /help command"""
        help_text = """
🤖 PepperBot Help

Commands:
/start - Start the bot and get welcome message
/login - Link your PepperBot account
/filters - View and manage discount filters
/addfilter - Create a new discount filter
/lists - View your shopping lists
/createlist - Create a new shopping list
/help - Show this help message

Features:
• Get notified when discounts match your filters
• Add discounted items to shopping lists
• Manage your shopping lists directly from Telegram

For support, contact the administrators.
"""

        await message.reply(help_text)

    # Callback query handlers
    @dp.callback_query(lambda c: c.data.startswith("toggle_filter:"))
    async def toggle_filter(callback_query: types.CallbackQuery):
        """Handle filter toggle"""
        filter_id = int(callback_query.data.split(":")[1])

        async with database.get_db() as db:
            user = get_user_by_chat_id(db, callback_query.message.chat.id)
            if not user:
                await callback_query.answer("Please login first")
                return

            filter_obj = db.query(models.Filter).filter(
                models.Filter.id == filter_id,
                models.Filter.user_id == user.id
            ).first()

            if filter_obj:
                filter_obj.is_active = not filter_obj.is_active
                db.commit()

                status = "enabled" if filter_obj.is_active else "disabled"
                await callback_query.answer(f"Filter {status}")
                await callback_query.message.edit_text(
                    f"Filter '{filter_obj.name}' has been {status}"
                )
            else:
                await callback_query.answer("Filter not found")

    @dp.callback_query(lambda c: c.data.startswith("view_list:"))
    async def view_list(callback_query: types.CallbackQuery):
        """Handle view shopping list"""
        list_id = int(callback_query.data.split(":")[1])

        async with database.get_db() as db:
            user = get_user_by_chat_id(db, callback_query.message.chat.id)
            if not user:
                await callback_query.answer("Please login first")
                return

            shopping_list = db.query(models.ShoppingList).filter(
                models.ShoppingList.id == list_id,
                models.ShoppingList.user_id == user.id
            ).first()

            if not shopping_list:
                await callback_query.answer("List not found")
                return

            items = db.query(models.ListItem).filter(
                models.ListItem.shopping_list_id == list_id
            ).all()

            text = f"🛒 {shopping_list.title}\n\n"
            if not items:
                text += "No items in this list yet."
            else:
                for item in items:
                    status = "✅" if item.is_completed else "⬜"
                    text += f"{status} {item.name}"
                    if item.quantity != 1.0:
                        text += f" ({item.quantity}"
                        if item.unit:
                            text += f" {item.unit}"
                        text += ")"
                    text += "\n"

            keyboard = []
            for item in items:
                if not item.is_completed:
                    keyboard.append([
                        types.InlineKeyboardButton(
                            text=f"Mark complete: {item.name}",
                            callback_data=f"complete_item:{item.id}"
                        )
                    ])

            if keyboard:
                markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
                await callback_query.message.edit_text(text, reply_markup=markup)
            else:
                await callback_query.message.edit_text(text)

    @dp.callback_query(lambda c: c.data.startswith("complete_item:"))
    async def complete_item(callback_query: types.CallbackQuery):
        """Handle item completion"""
        item_id = int(callback_query.data.split(":")[1])

        async with database.get_db() as db:
            user = get_user_by_chat_id(db, callback_query.message.chat.id)
            if not user:
                await callback_query.answer("Please login first")
                return

            item = db.query(models.ListItem).join(models.ShoppingList).filter(
                models.ListItem.id == item_id,
                models.ShoppingList.user_id == user.id
            ).first()

            if item:
                item.is_completed = True
                db.commit()
                await callback_query.answer("Item marked as complete")
                await callback_query.message.edit_text("✅ Item marked as complete!")
            else:
                await callback_query.answer("Item not found")

    @dp.callback_query(lambda c: c.data.startswith("add_to_list:"))
    async def add_to_list(callback_query: types.CallbackQuery):
        """Handle adding discounted item to shopping list"""
        parts = callback_query.data.split(":")
        list_id = int(parts[1])
        discount_id = int(parts[2])

        async with database.get_db() as db:
            user = get_user_by_chat_id(db, callback_query.message.chat.id)
            if not user:
                await callback_query.answer("Please login first")
                return

            # Verify ownership
            shopping_list = db.query(models.ShoppingList).filter(
                models.ShoppingList.id == list_id,
                models.ShoppingList.user_id == user.id
            ).first()

            discount = db.query(models.Discount).filter(
                models.Discount.id == discount_id
            ).first()

            if shopping_list and discount:
                # Check if item already exists
                existing_item = db.query(models.ListItem).filter(
                    models.ListItem.shopping_list_id == list_id,
                    models.ListItem.name.ilike(f"%{discount.title}%")
                ).first()

                if not existing_item:
                    new_item = models.ListItem(
                        name=discount.title,
                        shopping_list_id=list_id
                    )
                    db.add(new_item)
                    db.commit()
                    await callback_query.answer("Item added to shopping list!")
                    await callback_query.message.edit_text("✅ Item added to your shopping list!")
                else:
                    await callback_query.answer("Item already in shopping list")
            else:
                await callback_query.answer("List or discount not found")

    # Error handler
    @dp.errors()
    async def handle_error(update: types.Update, exception: Exception):
        """Handle errors"""
        logger.error(f"Update {update} caused error: {exception}")
        return True

else:
    bot = None
    dp = None
    logger.warning("Telegram bot token not configured")


async def start_bot():
    """Start the Telegram bot"""
    if not bot or not dp:
        logger.warning("Bot not configured, skipping start")
        return

    logger.info("Starting Telegram bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")


async def stop_bot():
    """Stop the Telegram bot"""
    if bot:
        await bot.session.close()


# Background task for processing notifications
async def notification_worker():
    """Background worker for processing discount notifications"""
    while True:
        try:
            async with database.get_db() as db:
                if bot:  # Only process if bot is configured
                    await process_discount_notifications(db)
            await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Error in notification worker: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying


async def start_notification_worker():
    """Start the notification worker"""
    asyncio.create_task(notification_worker())


# Export functions for use in main application
__all__ = ['start_bot', 'stop_bot', 'start_notification_worker']