#!/usr/bin/env python3
"""
Database initialization script for PepperBot.
This script creates the database and tables.
"""

from src.database import engine, Base
from src.models import User, ShoppingList, ListItem, Filter, Discount, Notification

def init_database():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()