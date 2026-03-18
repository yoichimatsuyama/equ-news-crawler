import logging
from datetime import timedelta

LOG_LEVEL = logging.INFO
REQUEST_TIMEOUT = 30_000  # milliseconds for Playwright
MIN_REQUEST_INTERVAL = timedelta(seconds=5)
