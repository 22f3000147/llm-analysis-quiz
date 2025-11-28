"""Headless browser helper using Playwright."""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging
from config import Config

logger = logging.getLogger(__name__)

class BrowserHelper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        if Config.BROWSER_TYPE == 'firefox':
            self.browser = self.playwright.firefox.launch(headless=Config.HEADLESS)
        elif Config.BROWSER_TYPE == 'webkit':
            self.browser = self.playwright.webkit.launch(headless=Config.HEADLESS)
        else:
            self.browser = self.playwright.chromium.launch(headless=Config.HEADLESS)
        
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def get_rendered_content(self, url, wait_time=5000):
        try:
            page = self.context.new_page()
            logger.info(f"Navigating to: {url}")
            page.goto(url, wait_until='networkidle', timeout=Config.REQUEST_TIMEOUT * 1000)
            page.wait_for_timeout(wait_time)
            
            html_content = page.content()
            text_content = page.inner_text('body')
            
            result_div = page.query_selector('#result')
            if result_div:
                text_content = result_div.inner_text()
            
            logger.info(f"Successfully rendered page: {len(html_content)} chars")
            page.close()
            
            return {'html': html_content, 'text': text_content, 'url': url}
        except Exception as e:
            logger.error(f"Error rendering page {url}: {str(e)}")
            raise
