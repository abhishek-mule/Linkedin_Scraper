#!/usr/bin/env python
"""
LinkedIn Profile Search Script

This script searches for specific LinkedIn profiles based on a name input.
It features improved error handling, CAPTCHA detection, and progress tracking.

Features:
- Detects and handles CAPTCHA challenges
- Saves search progress for resuming interrupted searches
- Robust error handling with detailed logging
- Rate limiting prevention with random delays
- Takes command line arguments for name search
"""

import os
import sys
import time
import json
import random
import logging
import argparse
from datetime import datetime
from pathlib import Path
import traceback

import pandas as pd
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
LINKEDIN_EMAIL = "your_email@example.com"  # Update with your LinkedIn email
LINKEDIN_PASSWORD = "your_password"         # Update with your LinkedIn password
MAX_WAIT_TIME = 20  # Maximum time to wait for elements to load (seconds)
BASE_SEARCH_URL = "https://www.linkedin.com/search/results/people/?keywords="
SEARCH_RESULTS_DIR = "linkedin_search_results"
SCREENSHOTS_DIR = os.path.join(SEARCH_RESULTS_DIR, "screenshots")
LOG_FILE = os.path.join(SEARCH_RESULTS_DIR, "search_log.txt")
MAX_PROFILES_PER_RUN = 3  # Limit to avoid timeouts and detection

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
    os.makedirs(SEARCH_RESULTS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def setup_webdriver():
    """Initialize and configure the Chrome WebDriver."""
    try:
        chrome_options = Options()
        # Uncomment the line below to run in headless mode
        # chrome_options.add_argument("--headless")
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

def handle_captcha(driver, search_timestamp):
    """Handle CAPTCHA detection by saving a screenshot and providing guidance."""
    logger.warning("CAPTCHA detected! Manual intervention required.")
    
    # Take a screenshot of the CAPTCHA
    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"captcha_{search_timestamp}.png")
    try:
        driver.save_screenshot(screenshot_path)
        logger.info(f"CAPTCHA screenshot saved to: {screenshot_path}")
    except Exception as e:
        logger.error(f"Failed to save CAPTCHA screenshot: {str(e)}")
    
    # Update search status
    status_data = {
        "status": "error",
        "message": "CAPTCHA detected. Manual intervention required.",
        "error": "LinkedIn security verification triggered",
        "error_screenshot": screenshot_path,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_search_status(search_timestamp, status_data)
    
    # This would normally wait for manual intervention, but for automation:
    logger.info("Please solve the CAPTCHA manually and then resume the script.")
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
    """Log in to LinkedIn with provided credentials."""
    try:
        logger.info("Logging in to LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        
        # Check for CAPTCHA before login
        if is_captcha_present(driver):
            logger.warning("CAPTCHA detected on login page")
            handle_captcha(driver, datetime.now().strftime("%Y%m%d%H%M%S"))
            return False
        
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
        random_delay(3, 5)
        
        # Verify login success
        try:
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
            )
            logger.info("Successfully logged in to LinkedIn")
            return True
        except TimeoutException:
            if "checkpoint" in driver.current_url or "challenge" in driver.current_url:
                logger.warning("LinkedIn security checkpoint detected")
                handle_captcha(driver, datetime.now().strftime("%Y%m%d%H%M%S"))
                return False
            else:
                logger.error("Login failed - Unable to verify successful login")
                return False
                
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return False

def search_linkedin_profiles(driver, name, search_timestamp):
    """Search for LinkedIn profiles using the given name."""
    try:
        logger.info(f"Searching for LinkedIn profiles with name: {name}")
        
        # Format the search query
        formatted_name = format_name_for_search(name)
        search_query = f"{formatted_name}"
        
        # Construct search URL
        search_url = f"{BASE_SEARCH_URL}{search_query.replace(' ', '%20')}"
        logger.info(f"Search URL: {search_url}")
        
        # Navigate to the search page
        driver.get(search_url)
        random_delay(2, 4)
        
        # Check for CAPTCHA
        if is_captcha_present(driver):
            logger.warning("CAPTCHA detected during search")
            return handle_captcha(driver, search_timestamp)
        
        # Wait for search results to load
        try:
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container"))
            )
        except TimeoutException:
            logger.warning("Search results container not found, attempting alternative method")
            try:
                WebDriverWait(driver, MAX_WAIT_TIME).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-result"))
                )
            except TimeoutException:
                logger.error("No search results elements found")
                
                # Take screenshot of the failed search
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"search_failed_{search_timestamp}.png")
                driver.save_screenshot(screenshot_path)
                
                status_data = {
                    "status": "not_found",
                    "message": f"No profiles found for '{name}'",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error_screenshot": screenshot_path
                }
                save_search_status(search_timestamp, status_data)
                return []
        
        # Extract profile links from search results
        profile_elements = driver.find_elements(By.CSS_SELECTOR, ".entity-result__title a.app-aware-link")
        profile_links = []
        
        for element in profile_elements[:MAX_PROFILES_PER_RUN]:  # Limit to avoid timeouts
            try:
                href = element.get_attribute("href")
                if href and "/in/" in href:
                    # Clean the LinkedIn URL to remove tracking parameters
                    base_url = href.split("?")[0]
                    profile_links.append(base_url)
            except StaleElementReferenceException:
                continue
        
        logger.info(f"Found {len(profile_links)} profile links")
        
        if not profile_links:
            logger.warning(f"No profile links found for search: {name}")
            
            # Update search status
            status_data = {
                "status": "not_found",
                "message": f"No profiles found for '{name}'",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_search_status(search_timestamp, status_data)
            
            return []
        
        return profile_links
        
    except Exception as e:
        logger.error(f"Error in search_linkedin_profiles: {str(e)}")
        traceback.print_exc()
        
        # Take screenshot of the error
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"search_error_{search_timestamp}.png")
        try:
            driver.save_screenshot(screenshot_path)
        except:
            pass
            
        # Update search status
        status_data = {
            "status": "error",
            "message": "Error occurred while searching profiles",
            "error": str(e),
            "error_screenshot": screenshot_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_search_status(search_timestamp, status_data)
        
        return []

def try_alternative_search(driver, name, search_timestamp):
    """Try alternative search approaches when standard search fails."""
    logger.info(f"Trying alternative search approaches for: {name}")
    
    alternative_methods = [
        # Method 1: Reverse name order
        lambda n: " ".join(n.split()[::-1]),
        
        # Method 2: Add "LinkedIn" to the search
        lambda n: f"{n} LinkedIn",
        
        # Method 3: First name only (if multiple names)
        lambda n: n.split()[0] if len(n.split()) > 1 else n,
        
        # Method 4: Last name only (if multiple names)
        lambda n: n.split()[-1] if len(n.split()) > 1 else n
    ]
    
    for i, method in enumerate(alternative_methods):
        try:
            alternative_name = method(name)
            logger.info(f"Alternative search {i+1}: '{alternative_name}'")
            
            # Skip if the alternative is the same as the original
            if alternative_name == name:
                continue
                
            profile_links = search_linkedin_profiles(driver, alternative_name, search_timestamp)
            
            if profile_links:
                logger.info(f"Alternative search {i+1} successful")
                return profile_links
                
            random_delay(2, 5)  # Delay between attempts
            
        except Exception as e:
            logger.error(f"Error in alternative search {i+1}: {str(e)}")
    
    logger.warning("All alternative search methods failed")
    return []

def extract_profile_data(driver, profile_url):
    """Extract key data from a LinkedIn profile page."""
    try:
        logger.info(f"Extracting data from profile: {profile_url}")
        driver.get(profile_url)
        random_delay(3, 5)
        
        # Check for CAPTCHA
        if is_captcha_present(driver):
            logger.warning("CAPTCHA detected while extracting profile data")
            handle_captcha(driver, datetime.now().strftime("%Y%m%d%H%M%S"))
            return None
        
        # Wait for profile page to load
        try:
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pv-top-card"))
            )
        except TimeoutException:
            logger.warning("Profile page did not load properly, using alternative selectors")
        
        # Initialize profile data dictionary
        profile_data = {
            "linkedin_url": profile_url,
            "name": "",
            "headline": "",
            "location": "",
            "about": "",
            "experience": [],
            "education": [],
            "skills": [],
            "image_url": ""
        }
        
        # Extract basic information
        try:
            profile_data["name"] = driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge").text.strip()
        except:
            try:
                profile_data["name"] = driver.find_element(By.CSS_SELECTOR, ".pv-top-card--list .text-heading-xlarge").text.strip()
            except:
                logger.warning("Could not extract name")
        
        try:
            profile_data["headline"] = driver.find_element(By.CSS_SELECTOR, ".pv-top-card .text-body-medium").text.strip()
        except:
            logger.warning("Could not extract headline")
        
        try:
            profile_data["location"] = driver.find_element(By.CSS_SELECTOR, ".pv-top-card .text-body-small:not(.break-words)").text.strip()
        except:
            logger.warning("Could not extract location")
        
        # Try to get profile image URL
        try:
            img_element = driver.find_element(By.CSS_SELECTOR, ".pv-top-card .pv-top-card__photo img")
            profile_data["image_url"] = img_element.get_attribute("src")
        except:
            logger.warning("Could not extract profile image")
        
        # Get about section (if available)
        try:
            about_section = driver.find_element(By.CSS_SELECTOR, "#about-section .pv-shared-text-with-see-more")
            driver.execute_script("arguments[0].scrollIntoView();", about_section)
            random_delay(1, 2)
            
            # Try to expand the about section if it's collapsed
            try:
                see_more_button = about_section.find_element(By.CSS_SELECTOR, ".inline-show-more-text__button")
                driver.execute_script("arguments[0].click();", see_more_button)
                random_delay(1, 2)
            except:
                pass
                
            profile_data["about"] = about_section.text.strip()
        except:
            logger.warning("Could not extract about section")
        
        # Extract simplified experience
        try:
            experience_section = driver.find_element(By.ID, "experience-section")
            driver.execute_script("arguments[0].scrollIntoView();", experience_section)
            random_delay(1, 2)
            
            experience_items = experience_section.find_elements(By.CSS_SELECTOR, ".pv-entity__position-group-pager, .pv-profile-section__list-item")
            
            for item in experience_items:
                try:
                    title_element = item.find_element(By.CSS_SELECTOR, ".pv-entity__summary-info h3, .pv-entity__summary-info-margin-top h3")
                    title = title_element.text.strip()
                    
                    company_element = item.find_element(By.CSS_SELECTOR, ".pv-entity__secondary-title, p.pv-entity__secondary-title")
                    company = company_element.text.strip()
                    
                    profile_data["experience"].append({
                        "title": title,
                        "company": company
                    })
                except:
                    continue
        except:
            logger.warning("Could not extract experience details")
        
        # Extract simplified education
        try:
            education_section = driver.find_element(By.ID, "education-section")
            driver.execute_script("arguments[0].scrollIntoView();", education_section)
            random_delay(1, 2)
            
            education_items = education_section.find_elements(By.CSS_SELECTOR, ".pv-profile-section__list-item")
            
            for item in education_items:
                try:
                    school_element = item.find_element(By.CSS_SELECTOR, "h3.pv-entity__school-name")
                    school = school_element.text.strip()
                    
                    degree_element = item.find_element(By.CSS_SELECTOR, ".pv-entity__degree-name .pv-entity__comma-item")
                    degree = degree_element.text.strip()
                    
                    profile_data["education"].append({
                        "school": school,
                        "degree": degree
                    })
                except:
                    try:
                        # Simplified approach
                        school = item.find_element(By.CSS_SELECTOR, "h3").text.strip()
                        profile_data["education"].append({
                            "school": school
                        })
                    except:
                        continue
        except:
            logger.warning("Could not extract education details")
        
        # Extract skills (basic approach)
        try:
            # Try to navigate to skills section
            skills_url = f"{profile_url}/details/skills/"
            driver.get(skills_url)
            random_delay(2, 3)
            
            skills_elements = driver.find_elements(By.CSS_SELECTOR, ".pv-skill-category-entity__name-text")
            skills = [skill.text.strip() for skill in skills_elements]
            profile_data["skills"] = skills
        except:
            logger.warning("Could not extract skills")
        
        return profile_data
    
    except Exception as e:
        logger.error(f"Error extracting profile data: {str(e)}")
        traceback.print_exc()
        return None

def save_results_to_json(profiles, search_timestamp):
    """Save profile data to a JSON file."""
    if not profiles:
        logger.warning("No profiles to save")
        return
    
    try:
        output_file = os.path.join(SEARCH_RESULTS_DIR, f"profiles_{search_timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Successfully saved {len(profiles)} profiles to {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error saving results to JSON: {str(e)}")
        return None

def save_search_status(search_timestamp, status_data):
    """Save the current status of the search to a file."""
    try:
        status_file = os.path.join(SEARCH_RESULTS_DIR, f"status_{search_timestamp}.json")
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Search status updated: {status_data['status']}")
        return status_file
    except Exception as e:
        logger.error(f"Error saving search status: {str(e)}")
        return None

def load_search_status(search_timestamp):
    """Load the current status of a search from a file."""
    try:
        status_file = os.path.join(SEARCH_RESULTS_DIR, f"status_{search_timestamp}.json")
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error loading search status: {str(e)}")
        return None

def random_delay(min_seconds=2, max_seconds=5):
    """Add a random delay to avoid rate limiting."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def main():
    """Main function to execute the LinkedIn profile search."""
    parser = argparse.ArgumentParser(description='Search for LinkedIn profiles by name')
    parser.add_argument('name', help='Name to search for on LinkedIn')
    parser.add_argument('--timestamp', help='Timestamp for this search process')
    args = parser.parse_args()
    
    search_name = args.name
    search_timestamp = args.timestamp or datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Set up necessary directories
    setup_directories()
    
    # Initialize search status
    status_data = {
        "status": "searching",
        "message": f"Searching for profiles matching '{search_name}'",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_search_status(search_timestamp, status_data)
    
    driver = None
    try:
        # Initialize WebDriver
        driver = setup_webdriver()
        
        # Login to LinkedIn
        login_success = login_to_linkedin(driver)
        if not login_success:
            logger.error("Failed to log in to LinkedIn. Exiting.")
            
            status_data = {
                "status": "error",
                "message": "Failed to log in to LinkedIn",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_search_status(search_timestamp, status_data)
            
            if driver:
                driver.quit()
            return
        
        # Search for profiles
        profile_links = search_linkedin_profiles(driver, search_name, search_timestamp)
        
        # If standard search fails, try alternative approaches
        if not profile_links:
            profile_links = try_alternative_search(driver, search_name, search_timestamp)
        
        if not profile_links:
            logger.warning(f"No profiles found for {search_name} after all search attempts")
            
            status_data = {
                "status": "not_found",
                "message": f"No profiles found for '{search_name}' after multiple search attempts",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_search_status(search_timestamp, status_data)
            
            if driver:
                driver.quit()
            return
        
        # Extract data from each profile
        profiles = []
        for url in profile_links:
            profile_data = extract_profile_data(driver, url)
            if profile_data:
                profiles.append(profile_data)
                logger.info(f"Successfully extracted data for profile: {profile_data['name']}")
            
            # Add a delay between profile visits
            random_delay(3, 7)
        
        # Save results
        if profiles:
            output_file = save_results_to_json(profiles, search_timestamp)
            
            status_data = {
                "status": "completed",
                "message": f"Found {len(profiles)} profiles for '{search_name}'",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "results_file": output_file,
                "profiles": profiles
            }
        else:
            status_data = {
                "status": "not_found",
                "message": f"No valid profiles data could be extracted for '{search_name}'",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        save_search_status(search_timestamp, status_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in main function: {str(e)}")
        traceback.print_exc()
        
        # Take screenshot of the error state
        if driver:
            try:
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"error_{search_timestamp}.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"Error screenshot saved to: {screenshot_path}")
            except:
                pass
        
        status_data = {
            "status": "error",
            "message": "An unexpected error occurred during the search process",
            "error": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_search_status(search_timestamp, status_data)
    
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    main() 