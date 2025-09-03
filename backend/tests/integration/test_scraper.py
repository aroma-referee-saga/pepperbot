import pytest
from unittest.mock import MagicMock, patch, mock_open
from bs4 import BeautifulSoup

from src.scraper import PepperScraper


class TestPepperScraper:
    """Test cases for PepperScraper class."""

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = PepperScraper()

        assert scraper.base_url == "https://pepper.ru"
        assert scraper.session is not None
        assert scraper.min_request_interval == 1

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        scraper = PepperScraper()
        scraper.min_request_interval = 0.1  # Fast for testing

        import time
        start_time = time.time()
        scraper._rate_limit()
        scraper._rate_limit()
        end_time = time.time()

        # Should have waited at least the minimum interval
        assert end_time - start_time >= scraper.min_request_interval

    @patch('src.scraper.requests.Session.get')
    def test_get_page_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        scraper = PepperScraper()
        result = scraper._get_page("https://example.com")

        assert result == "<html><body>Test content</body></html>"
        mock_get.assert_called_once()

    @patch('src.scraper.requests.Session.get')
    def test_get_page_failure(self, mock_get):
        """Test page fetching failure."""
        mock_get.side_effect = Exception("Network error")

        scraper = PepperScraper()
        result = scraper._get_page("https://example.com")

        assert result is None

    def test_parse_discounts_empty_html(self):
        """Test parsing discounts from empty HTML."""
        scraper = PepperScraper()
        html = "<html><body></body></html>"

        discounts = scraper.parse_discounts(html)

        assert discounts == []

    def test_parse_discounts_with_data(self):
        """Test parsing discounts from HTML with discount data."""
        html = """
        <html>
        <body>
            <div class="thread-item">
                <a href="/deal/123" class="thread-title">Test Deal</a>
                <span class="store-name">Test Store</span>
                <span class="price">1000 → 800 ₽</span>
                <span class="discount-percentage">-20%</span>
                <div class="thread-description">Great deal on test item</div>
                <img src="/images/deal.jpg" class="thread-image" />
            </div>
        </body>
        </html>
        """

        scraper = PepperScraper()
        discounts = scraper.parse_discounts(html)

        assert len(discounts) == 1
        discount = discounts[0]
        assert discount['title'] == "Test Deal"
        assert discount['store'] == "Test Store"
        assert discount['original_price'] == 1000.0
        assert discount['discount_price'] == 800.0
        assert discount['discount_percentage'] == 20.0
        assert discount['url'] == "https://pepper.ru/deal/123"
        assert discount['description'] == "Great deal on test item"
        assert "/images/deal.jpg" in discount['image_url']

    def test_parse_discounts_multiple_items(self):
        """Test parsing multiple discount items."""
        html = """
        <html>
        <body>
            <div class="thread-item">
                <a class="thread-title">Deal 1</a>
                <span class="store-name">Store 1</span>
            </div>
            <div class="thread-item">
                <a class="thread-title">Deal 2</a>
                <span class="store-name">Store 2</span>
            </div>
        </body>
        </html>
        """

        scraper = PepperScraper()
        discounts = scraper.parse_discounts(html)

        assert len(discounts) == 2
        assert discounts[0]['title'] == "Deal 1"
        assert discounts[1]['title'] == "Deal 2"

    def test_parse_discounts_missing_elements(self):
        """Test parsing discounts with missing HTML elements."""
        html = """
        <html>
        <body>
            <div class="thread-item">
                <a class="thread-title">Test Deal</a>
                <!-- Missing store name and other elements -->
            </div>
        </body>
        </html>
        """

        scraper = PepperScraper()
        discounts = scraper.parse_discounts(html)

        assert len(discounts) == 1
        discount = discounts[0]
        assert discount['title'] == "Test Deal"
        assert discount['store'] == "Unknown Store"
        assert discount['original_price'] is None

    def test_parse_price_various_formats(self):
        """Test price parsing with various formats."""
        scraper = PepperScraper()

        # Test with currency symbols
        assert scraper._parse_price("1000 ₽") == 1000.0
        assert scraper._parse_price("500руб") == 500.0

        # Test with spaces
        assert scraper._parse_price("1 500") == 1500.0

        # Test invalid formats
        assert scraper._parse_price("invalid") is None
        assert scraper._parse_price("") is None

    @patch('src.scraper.PepperScraper._get_page')
    @patch('src.scraper.PepperScraper._store_discounts')
    @pytest.mark.asyncio
    async def test_scrape_and_store_success(self, mock_store, mock_get_page):
        """Test successful scraping and storing."""
        mock_get_page.return_value = "<html><body>Test</body></html>"

        scraper = PepperScraper()
        scraper.parse_discounts = MagicMock(return_value=[
            {
                'title': 'Test Deal',
                'store': 'Test Store',
                'original_price': 100.0,
                'discount_price': 80.0
            }
        ])

        await scraper.scrape_and_store()

        mock_get_page.assert_called_once_with("https://pepper.ru")
        scraper.parse_discounts.assert_called_once()
        mock_store.assert_called_once()

    @patch('src.scraper.PepperScraper._get_page')
    @pytest.mark.asyncio
    async def test_scrape_and_store_page_fetch_failure(self, mock_get_page):
        """Test scraping when page fetch fails."""
        mock_get_page.return_value = None

        scraper = PepperScraper()
        await scraper.scrape_and_store()

        # Should not crash, just log error
        mock_get_page.assert_called_once()

    @patch('src.database.get_db')
    @pytest.mark.asyncio
    async def test_store_discounts_success(self, mock_get_db, db_session):
        """Test successful discount storage."""
        mock_get_db.return_value = db_session

        discounts_data = [
            {
                'title': 'New Deal',
                'store': 'Test Store',
                'original_price': 100.0,
                'discount_price': 80.0,
                'url': 'https://example.com/deal'
            }
        ]

        scraper = PepperScraper()
        await scraper._store_discounts(discounts_data)

        # Check if discount was created
        from src.models import Discount
        discount = db_session.query(Discount).filter(Discount.title == 'New Deal').first()
        assert discount is not None
        assert discount.store == 'Test Store'
        assert discount.original_price == 100.0

    @patch('src.database.get_db')
    @pytest.mark.asyncio
    async def test_store_discounts_duplicate_handling(self, mock_get_db, db_session, sample_discount):
        """Test handling of duplicate discounts."""
        mock_get_db.return_value = db_session

        # Try to store the same discount again
        discounts_data = [
            {
                'title': sample_discount.title,
                'store': sample_discount.store,
                'original_price': 200.0,  # Different price
                'discount_price': 150.0,
                'url': sample_discount.url
            }
        ]

        scraper = PepperScraper()
        await scraper._store_discounts(discounts_data)

        # Check if discount was updated
        from src.models import Discount
        discount = db_session.query(Discount).filter(Discount.id == sample_discount.id).first()
        assert discount.original_price == 200.0  # Should be updated

    @patch('src.database.get_db')
    @pytest.mark.asyncio
    async def test_store_discounts_error_handling(self, mock_get_db, db_session):
        """Test error handling during discount storage."""
        mock_get_db.return_value = db_session

        # Force a database error
        db_session.commit = MagicMock(side_effect=Exception("DB Error"))

        discounts_data = [
            {
                'title': 'Test Deal',
                'store': 'Test Store'
            }
        ]

        scraper = PepperScraper()
        await scraper._store_discounts(discounts_data)

        # Should not crash, should rollback
        db_session.rollback.assert_called_once()


class TestScraperIntegration:
    """Integration tests for scraper functionality."""

    @patch('src.scraper.PepperScraper._get_page')
    @patch('src.scraper.PepperScraper._store_discounts')
    @pytest.mark.asyncio
    async def test_manual_scrape_function(self, mock_store, mock_get_page):
        """Test the manual scrape function."""
        mock_get_page.return_value = "<html><body>Test</body></html>"

        from src.scraper import manual_scrape
        await manual_scrape()

        mock_get_page.assert_called_once()
        mock_store.assert_called_once()

    @patch('src.scraper.AsyncIOScheduler')
    def test_start_scraper_scheduler(self, mock_scheduler):
        """Test starting the scraper scheduler."""
        from src.scraper import start_scraper

        mock_scheduler_instance = MagicMock()
        mock_scheduler.return_value = mock_scheduler_instance

        start_scraper()

        mock_scheduler_instance.add_job.assert_called_once()
        mock_scheduler_instance.start.assert_called_once()

    @patch('src.scraper.AsyncIOScheduler')
    def test_stop_scraper_scheduler(self, mock_scheduler):
        """Test stopping the scraper scheduler."""
        from src.scraper import stop_scraper

        mock_scheduler_instance = MagicMock()
        mock_scheduler_instance.running = True
        mock_scheduler.return_value = mock_scheduler_instance

        stop_scraper()

        mock_scheduler_instance.shutdown.assert_called_once()