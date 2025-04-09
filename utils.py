"""Utility functions for web scraping and data processing."""

import logging
import time

import requests
from bs4 import BeautifulSoup


# Function to get the BeautifulSoup object of a webpage
def get_soup(url):
    """Get the BeautifulSoup object of a webpage."""
    for attempt in range(3):
        logging.debug("Attempt %d to fetch URL: %s", attempt + 1, url)
        if attempt > 0:
            time.sleep(1)
            logging.warning("Retrying...")
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            logging.info("Successfully fetched URL: %s", url)
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logging.error("Request failed for URL %s: %s", url, e)
            if attempt == 2:
                logging.error("Failed to fetch URL after 3 attempts: %s", url)
                return None
