#!/usr/bin/env python
"""
Batch LinkedIn Profile Scraper
------------------------------
This script reads a CSV file of student names, searches for their LinkedIn profiles,
and extracts detailed information into a consolidated CSV file.

Features:
- Reads student names from a CSV file
- Searches for LinkedIn profiles matching those names
- Extracts comprehensive profile information
- Handles rate limiting and CAPTCHA detection
- Implements robust error handling and recovery
- Tracks progress to allow resuming interrupted runs
- Saves all data to a single CSV file without storing profile images
"""

import os
import csv
import time
import json
import random
import logging
import argparse
from datetime import datetime
import traceback
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, ElementNotInteractableException,
    StaleElementReferenceException
)
from bs4 import BeautifulSoup

# Configuration
LINKEDIN_EMAIL = "your_email@example.com"    # Update with your LinkedIn email
LINKEDIN_PASSWORD = "your_password"           # Update with your LinkedIn password
MAX_WAIT_TIME = 15                            # Maximum time to wait for elements to load (seconds)
BASE_SEARCH_URL = "https://www.linkedin.com/search/results/people/?keywords="
OUTPUT_DIR = "linkedin_batch_results"
SCREENSHOTS_DIR = os.path.join(OUTPUT_DIR, "screenshots")
LOG_FILE = os.path.join(OUTPUT_DIR, "batch_scraping_log.txt")
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "progress.json")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "students_linkedin_data.csv")
INPUT_CSV = "students_data.csv"
MAX_PROFILES_PER_RUN = 25                    # Limit profiles per session to avoid timeouts
NAME_COLUMN = "Full Name"                     # Column name in CSV containing student names
MIN_DELAY = 10                                # Minimum delay between profile visits (seconds)
MAX_DELAY = 20                                # Maximum delay between profile visits (seconds)
MAX_SEARCH_ATTEMPTS = 3                       # Maximum search attempts per name
BATCH_SAVE_COUNT = 5                          # Save to CSV after this many profiles

# CSV column headers for output file
CSV_HEADERS = [
    "Name", "Profile URL", "About", "Role Type", "Current Position", 
    "Current Company", "Location", "Email", "Phone", "Website", 
    "All Education Details", "Skills", "All Experience Details",
    "Search Status", "Last Updated"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def setup_webdriver(headless=False):
    """Initialize and configure the Chrome WebDriver.
    
    Args:
        headless (bool): Whether to run browser in headless mode
        
    Returns:
        WebDriver: Configured Chrome WebDriver instance
    """
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # User agent to look more like a real browser
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except WebDriverException as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise

def is_captcha_present(driver):
    """Detect if a CAPTCHA challenge is present."""
    try:
        # Check for common CAPTCHA indicators
        captcha_indicators = [
            "//div[contains(text(), 'CAPTCHA')]",
            "//div[contains(text(), 'Security Verification')]",
            "//div[contains(text(), 'Verify you')]",
            "//iframe[contains(@src, 'captcha')]",
            "//div[contains(@class, 'captcha')]"
        ]
        
        for indicator in captcha_indicators:
            elements = driver.find_elements(By.XPATH, indicator)
            if elements:
                return True
                
        # Also check page title
        if "Security Verification" in driver.title or "CAPTCHA" in driver.title:
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Error checking for CAPTCHA: {str(e)}")
        return False

def handle_captcha(driver, student_name):
    """Handle CAPTCHA detection with user guidance."""
    logger.warning(f"CAPTCHA detected during search for {student_name}! Manual intervention required.")
    
    # Take a screenshot of the CAPTCHA
    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"captcha_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
    try:
        driver.save_screenshot(screenshot_path)
        logger.info(f"CAPTCHA screenshot saved to: {screenshot_path}")
    except Exception as e:
        logger.error(f"Failed to save CAPTCHA screenshot: {str(e)}")
    
    print("\n" + "="*60)
    print(f"CAPTCHA DETECTED while searching for {student_name}")
    print("="*60)
    print("Please solve the CAPTCHA in the browser window.")
    print(f"Screenshot saved to: {screenshot_path}")
    print("The script will wait for 2 minutes before continuing.")
    print("If you need more time, you can press Ctrl+C to stop the script")
    print("and resume later with the --resume flag.")
    print("="*60 + "\n")
    
    # Wait for user to handle the CAPTCHA
    try:
        time.sleep(120)  # Wait 2 minutes for manual intervention
        logger.info("Resuming after CAPTCHA wait period")
        return True
    except KeyboardInterrupt:
        logger.info("Script interrupted during CAPTCHA handling")
        return False 

def format_name_for_search(name):
    """Format a name for LinkedIn search to maximize results."""
    # Normalize whitespace and handle special characters
    name = name.strip()
    name = " ".join(name.split())  # Normalize whitespace
    
    # Replace special characters
    name = name.replace(".", " ").replace("-", " ").replace("_", " ")
    
    return name

def login_to_linkedin(driver):
    """Log in to LinkedIn with provided credentials.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        logger.info("Logging in to LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        
        # Check for CAPTCHA before login
        if is_captcha_present(driver):
            logger.warning("CAPTCHA detected on login page")
            handle_captcha(driver, "LOGIN")
        
        # Enter email/username
        username_input = WebDriverWait(driver, MAX_WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_input.clear()
        username_input.send_keys(LINKEDIN_EMAIL)
        
        # Enter password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(LINKEDIN_PASSWORD)
        
        # Submit the form
        password_input.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        time.sleep(3)
        
        # Verify login success by checking for feed or security checkpoint
        try:
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "global-nav")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
                )
            )
            logger.info("Successfully logged in to LinkedIn")
            return True
        except TimeoutException:
            if "checkpoint" in driver.current_url or "challenge" in driver.current_url:
                logger.warning("LinkedIn security checkpoint detected - manual intervention required")
                if handle_captcha(driver, "LOGIN_CHECKPOINT"):
                    # Try to verify login again after CAPTCHA
                    try:
                        WebDriverWait(driver, MAX_WAIT_TIME).until(
                            EC.any_of(
                                EC.presence_of_element_located((By.ID, "global-nav")),
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
                            )
                        )
                        logger.info("Successfully logged in after security checkpoint")
                        return True
                    except TimeoutException:
                        logger.error("Failed to verify login after security checkpoint")
                        return False
                return False
            else:
                logger.error("Login failed - Unable to verify successful login")
                return False
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        traceback.print_exc()
        return False

def search_linkedin_profile(driver, student_name):
    """Search for a LinkedIn profile using the student's name.
    
    Args:
        driver: Selenium WebDriver instance
        student_name: Name of the student to search for
        
    Returns:
        str or None: URL of the best matching profile, or None if not found
    """
    logger.info(f"Searching for LinkedIn profile: {student_name}")
    
    # Format the name for searching
    formatted_name = format_name_for_search(student_name)
    search_url = f"{BASE_SEARCH_URL}{formatted_name.replace(' ', '%20')}"
    
    # Try different search strategies
    search_strategies = [
        {"name": formatted_name, "desc": "standard"},
        {"name": f"{formatted_name} student", "desc": "with 'student'"},
        {"name": " ".join(formatted_name.split()[::-1]), "desc": "reversed"},  # Last name first
        {"name": formatted_name.split()[0] if len(formatted_name.split()) > 1 else formatted_name, "desc": "first name only"}
    ]
    
    for attempt, strategy in enumerate(search_strategies):
        if attempt >= MAX_SEARCH_ATTEMPTS:
            logger.info(f"Reached maximum search attempts ({MAX_SEARCH_ATTEMPTS}) for {student_name}")
            break
            
        current_name = strategy["name"]
        search_url = f"{BASE_SEARCH_URL}{current_name.replace(' ', '%20')}"
        logger.info(f"Search attempt {attempt+1}/{len(search_strategies)}: {strategy['desc']} strategy")
        
        try:
            # Navigate to search URL
            driver.get(search_url)
            time.sleep(random.uniform(2, 5))  # Random delay
            
            # Check for CAPTCHA
            if is_captcha_present(driver):
                logger.warning(f"CAPTCHA detected during search for {student_name}")
                if not handle_captcha(driver, student_name):
                    return None
                continue  # Try the same strategy again after CAPTCHA
            
            # Wait for search results to load
            try:
                WebDriverWait(driver, MAX_WAIT_TIME).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".search-result")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".reusable-search__result-container"))
                    )
                )
            except TimeoutException:
                logger.warning(f"Search results did not load for {current_name} (strategy: {strategy['desc']})")
                continue
            
            # Extract profile links from search results
            profile_selectors = [
                ".entity-result__title a.app-aware-link",  # Current LinkedIn format
                ".search-result__result-link",  # Older LinkedIn format
                ".reusable-search__result-container a.app-aware-link",  # Another possible format
                ".actor-name a"  # Yet another format
            ]
            
            profile_links = []
            
            # Try each selector
            for selector in profile_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        try:
                            href = element.get_attribute("href")
                            if href and "/in/" in href:
                                # Clean the LinkedIn URL
                                base_url = href.split("?")[0]
                                if base_url not in profile_links:
                                    profile_links.append(base_url)
                        except StaleElementReferenceException:
                            continue
            
            if profile_links:
                logger.info(f"Found {len(profile_links)} potential profile(s) for {student_name}")
                # Return the first profile link for now - in a real scenario, you might
                # want to implement additional verification to ensure it's the right person
                return profile_links[0]
        
        except Exception as e:
            logger.error(f"Error searching for {student_name} (attempt {attempt+1}): {str(e)}")
            
            # Take a screenshot for debugging
            screenshot_path = os.path.join(
                SCREENSHOTS_DIR, 
                f"search_error_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            )
            try:
                driver.save_screenshot(screenshot_path)
                logger.info(f"Error screenshot saved to: {screenshot_path}")
            except:
                pass
    
    logger.warning(f"No profile found for {student_name} after {MAX_SEARCH_ATTEMPTS} attempts")
    return None

def add_random_delay():
    """Add a random delay between requests to avoid rate limiting."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    logger.info(f"Waiting {delay:.2f} seconds...")
    time.sleep(delay)

def load_students_from_csv():
    """Load student names from the input CSV file.
    
    Returns:
        list: List of dictionaries with student information
    """
    students = []
    try:
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if NAME_COLUMN in row and row[NAME_COLUMN].strip():
                    students.append({
                        'name': row[NAME_COLUMN].strip(),
                        'processed': False,
                        'profile_url': None,
                        'status': 'pending'
                    })
    except Exception as e:
        logger.error(f"Error loading students from CSV: {str(e)}")
        raise
    
    logger.info(f"Loaded {len(students)} students from {INPUT_CSV}")
    return students

def load_progress():
    """Load progress from the progress file if it exists."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                logger.info(f"Loaded progress for {len(progress['students'])} students")
                return progress
        except Exception as e:
            logger.error(f"Error loading progress: {str(e)}")
    
    # Initialize new progress
    students = load_students_from_csv()
    progress = {
        'students': students,
        'last_processed_index': -1,
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'profiles_found': 0,
        'profiles_not_found': 0
    }
    return progress

def save_progress(progress):
    """Save current progress to the progress file."""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=4, ensure_ascii=False)
        logger.info("Progress saved successfully")
    except Exception as e:
        logger.error(f"Error saving progress: {str(e)}") 