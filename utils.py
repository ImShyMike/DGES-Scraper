"""Utility functions for web scraping and data processing."""

import logging
import sys
import time

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, PageElement, Tag


def get_soup(url, timeout=3, attempts=5):
    """Get the BeautifulSoup object of a webpage."""
    for attempt in range(attempts):
        logging.debug("Attempt %d to fetch URL: %s", attempt + 1, url)
        if attempt > 0:
            time.sleep(1)
            logging.warning("Retrying...")
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            logging.info("Successfully fetched URL: %s", url)
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logging.error("Request failed for URL %s: %s", url, e)
            if attempt == 2:
                logging.error("Failed to fetch URL after 3 attempts: %s", url)
                return None


def get_next(
    bs4_obj: NavigableString | Tag | PageElement | None,
) -> NavigableString | Tag | PageElement:
    """Get the next element in the BeautifulSoup object."""
    if not bs4_obj:
        logging.warning("No next element found. (%s)", bs4_obj)
        sys.exit(1)
    next_obj = bs4_obj.next
    if not next_obj:
        logging.warning("No next element found. (%s)", bs4_obj)
        sys.exit(1)
    return next_obj
