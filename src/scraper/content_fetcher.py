from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging

logger = logging.getLogger(__name__)


def fetch_article_html(url: str, headless: bool = True, timeout: int = 30000) -> str:
    """Fetch fully-rendered HTML for a given URL using Playwright (synchronous).

    Returns the page HTML as a string. Raises RuntimeError on failure.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            logger.info("Navigating to %s", url)
            page.goto(url, timeout=timeout)
            # small wait to let SPA render JS-driven content (adjust as needed)
            page.wait_for_timeout(1000)
            html = page.content()
            browser.close()
            return html
    except PlaywrightTimeout as e:
        logger.exception("Playwright timeout when fetching %s", url)
        raise RuntimeError("Timeout fetching page") from e
    except Exception:
        logger.exception("Error fetching %s", url)
        raise
