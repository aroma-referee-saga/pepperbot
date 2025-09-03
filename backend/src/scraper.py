import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime, timedelta
import asyncio
import httpx
from typing import List, Dict, Optional
import time
from urllib.parse import urljoin

from .database import get_db
from .models import Discount
from .schemas import DiscountCreate
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PepperScraper:
    def __init__(self, base_url: str = "https://pepper.ru"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _get_page(self, url: str) -> Optional[str]:
        """Fetch a page with error handling and rate limiting"""
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_discounts(self, html: str) -> List[Dict]:
        """Parse discount data from pepper.ru HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        discounts = []

        # Find discount items (adjust selectors based on actual pepper.ru structure)
        discount_items = soup.find_all('div', class_='thread-item')

        for item in discount_items:
            try:
                # Extract title
                title_elem = item.find('a', class_='thread-title')
                title = title_elem.text.strip() if title_elem else "Unknown Title"

                # Extract store
                store_elem = item.find('span', class_='store-name')
                store = store_elem.text.strip() if store_elem else "Unknown Store"

                # Extract prices
                price_elem = item.find('span', class_='price')
                original_price = None
                discount_price = None
                discount_percentage = None

                if price_elem:
                    price_text = price_elem.text.strip()
                    # Parse prices (this might need adjustment based on actual format)
                    if '→' in price_text:
                        parts = price_text.split('→')
                        if len(parts) == 2:
                            original_price = self._parse_price(parts[0].strip())
                            discount_price = self._parse_price(parts[1].strip())

                # Extract discount percentage
                discount_elem = item.find('span', class_='discount-percentage')
                if discount_elem:
                    discount_percentage = float(discount_elem.text.strip().replace('%', '').replace('-', ''))

                # Extract URL
                url = None
                if title_elem and title_elem.get('href'):
                    url = urljoin(self.base_url, title_elem['href'])

                # Extract description
                desc_elem = item.find('div', class_='thread-description')
                description = desc_elem.text.strip() if desc_elem else None

                # Extract image URL
                img_elem = item.find('img', class_='thread-image')
                image_url = img_elem.get('src') if img_elem else None
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)

                # Extract valid until date (if available)
                valid_until = None
                date_elem = item.find('span', class_='valid-until')
                if date_elem:
                    # Parse date (adjust format as needed)
                    try:
                        valid_until = datetime.strptime(date_elem.text.strip(), '%Y-%m-%d')
                    except ValueError:
                        pass

                discount_data = {
                    'title': title,
                    'description': description,
                    'store': store,
                    'original_price': original_price,
                    'discount_price': discount_price,
                    'discount_percentage': discount_percentage,
                    'url': url,
                    'image_url': image_url,
                    'valid_until': valid_until
                }

                # Only add if we have meaningful data
                if title and store:
                    discounts.append(discount_data)

            except Exception as e:
                logger.error(f"Error parsing discount item: {e}")
                continue

        return discounts

    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to float"""
        try:
            # Remove currency symbols and extra characters
            clean_price = price_str.replace('₽', '').replace('руб', '').replace(' ', '').strip()
            return float(clean_price)
        except (ValueError, AttributeError):
            return None

    async def scrape_and_store(self):
        """Main scraping function"""
        logger.info("Starting pepper.ru scraping...")

        try:
            # Scrape main page
            html = self._get_page(self.base_url)
            if not html:
                logger.error("Failed to fetch main page")
                return

            # Parse discounts
            discounts_data = self.parse_discounts(html)
            logger.info(f"Found {len(discounts_data)} discounts")

            # Store in database
            await self._store_discounts(discounts_data)

        except Exception as e:
            logger.error(f"Error during scraping: {e}")

    async def _store_discounts(self, discounts_data: List[Dict]):
        """Store parsed discounts in database"""
        db = next(get_db())

        try:
            for discount_data in discounts_data:
                # Check if discount already exists (by URL or title+store)
                existing = None
                if discount_data.get('url'):
                    existing = db.query(Discount).filter(Discount.url == discount_data['url']).first()
                else:
                    existing = db.query(Discount).filter(
                        Discount.title == discount_data['title'],
                        Discount.store == discount_data['store']
                    ).first()

                if existing:
                    # Update existing discount
                    for key, value in discount_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    logger.info(f"Updated discount: {discount_data['title']}")
                else:
                    # Create new discount
                    discount_create = DiscountCreate(**discount_data)
                    db_discount = Discount(**discount_create.dict())
                    db.add(db_discount)
                    logger.info(f"Created new discount: {discount_data['title']}")

            db.commit()

        except Exception as e:
            logger.error(f"Error storing discounts: {e}")
            db.rollback()
        finally:
            db.close()

# Global scraper instance
scraper = PepperScraper()

# Scheduler setup
scheduler = AsyncIOScheduler()

def start_scraper():
    """Start the periodic scraper"""
    # Add job to run every 30 minutes
    scheduler.add_job(
        scraper.scrape_and_store,
        trigger=IntervalTrigger(minutes=30),
        id='pepper_scraper',
        name='Pepper.ru Scraper',
        max_instances=1
    )

    # Start scheduler
    if not scheduler.running:
        scheduler.start()
        logger.info("Scraper scheduler started - will run every 30 minutes")

def stop_scraper():
    """Stop the scraper scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scraper scheduler stopped")

# Manual scraping function for testing
async def manual_scrape():
    """Manually trigger scraping"""
    await scraper.scrape_and_store()