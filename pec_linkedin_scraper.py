#!/usr/bin/env python
"""
LinkedIn Profile Scraper for Priyadarshini Engineering College, Higna Road
--------------------------------------------------------------------------
This script scrapes LinkedIn profiles of students and faculty from 
Priyadarshini Engineering College, Higna Road, and saves the data to CSV.
"""

import os
import time
import csv
import json
import urllib.request
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configuration
EMAIL = "cavad48528@cotigz.com"  # Replace with your LinkedIn email
PASSWORD = "Pass@cavad48528"  # Replace with your LinkedIn password
PRIMARY_KEYWORD = "Priyadarshini Engineering College, Higna Road"  # The main keyword to search
OUTPUT_FOLDER = "pec_profiles"
CSV_FILE = "pec_profiles.csv"
MAX_PROFILES = 500  # Maximum number of profiles to scrape
MAX_PAGES = 100  # Maximum number of pages to scan

# List of potential job titles and departments to search specifically
JOB_TITLES = [
    "Professor", 
    "Assistant Professor", 
    "Associate Professor", 
    "Lecturer", 
    "HOD", 
    "Department Head",
    "Principal", 
    "Dean", 
    "Student", 
    "Alumni",
    "Engineer"
]

# List of departments to search
DEPARTMENTS = [
    "Computer Science", 
    "Information Technology", 
    "Mechanical Engineering", 
    "Civil Engineering",
    "Electronics Engineering", 
    "Electrical Engineering", 
    "Computer Engineering"
]

# Create output folder if it doesn't exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Setup Chrome options for faster loading
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment to run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-notifications")
# chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Commenting out - enable images for CAPTCHA

# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)

def login_to_linkedin():
    """Login to LinkedIn with provided credentials"""
    try:
        driver.get("https://www.linkedin.com/login")
        print("Navigated to LinkedIn login page")
        time.sleep(3)  # Wait for login page to load
        
        # Find and fill email field
        email_elem = driver.find_element(By.ID, "username")
        email_elem.send_keys(EMAIL)
        
        # Find and fill password field
        password_elem = driver.find_element(By.ID, "password")
        password_elem.send_keys(PASSWORD)
        
        # Submit login form
        password_elem.submit()
        print("Submitted login credentials")
        
        # Wait for login to complete
        print("Waiting for login to complete...")
        time.sleep(10)
        
        # Check if login was successful
        if "feed" in driver.current_url or "checkpoint" in driver.current_url:
            print("Successfully logged in to LinkedIn")
            return True
        else:
            print(f"Login might have failed, current URL: {driver.current_url}")
            # Add a pause here to allow for manual intervention if needed
            print("Pausing for 30 seconds to allow manual login if needed...")
            time.sleep(30)
            if "feed" in driver.current_url:
                print("Manual login successful")
                return True
            else:
                print("Login failed even after manual intervention")
                return handle_manual_login()  # Try the manual login process
    except Exception as e:
        print(f"Error during login: {e}")
        # Add a pause here to allow for manual intervention if needed
        print("Pausing for 30 seconds to allow manual login if needed...")
        time.sleep(30)
        if "feed" in driver.current_url:
            print("Manual login successful")
            return True
        else:
            return handle_manual_login()  # Try the manual login process

def handle_manual_login():
    """Provide guidance for manual login when automation fails"""
    print("\n" + "="*60)
    print("MANUAL LOGIN REQUIRED")
    print("="*60)
    print("The automated login process has failed, likely due to CAPTCHA or security measures.")
    print("Please follow these steps in the browser window that has opened:")
    print("1. Make sure you can see the LinkedIn login page in the browser")
    print("2. If you see a CAPTCHA, solve it manually")
    print("3. If CAPTCHA is not visible/loading, try refreshing the page")
    print("4. Enter your LinkedIn credentials manually:")
    print(f"   Email: {EMAIL}")
    print(f"   Password: {PASSWORD}")
    print("5. Click Sign In")
    print("\nYou have 2 minutes to complete this process before the script continues")
    
    # Navigate to login page if we're not already there
    if "login" not in driver.current_url:
        driver.get("https://www.linkedin.com/login")
        print("Navigated to LinkedIn login page")
    
    # Wait for manual login
    for i in range(120, 0, -1):
        print(f"Waiting for manual login... {i} seconds remaining", end="\r")
        time.sleep(1)
        # Check if login successful
        if "feed" in driver.current_url or "/in/" in driver.current_url:
            print("\nManual login successful!")
            return True
    
    print("\nTime expired. Checking if login was successful...")
    if "feed" in driver.current_url or "/in/" in driver.current_url:
        print("Login successful!")
        return True
    else:
        print("Manual login failed. LinkedIn scraper cannot continue without authentication.")
        return False

def check_for_captcha_or_restriction():
    """Check if we've hit a captcha or been restricted, and wait for manual intervention if needed"""
    # Check for common captcha or restriction indicators in the URL or page content
    if "captcha" in driver.current_url.lower() or "challenge" in driver.current_url.lower():
        print("\n===============================================================")
        print("CAPTCHA detected! Please solve it manually in the browser window.")
        print("===============================================================")
        print("If the CAPTCHA is not loading, try these steps:")
        print("1. Click the refresh button in the browser")
        print("2. Try clicking on any visible CAPTCHA elements")
        print("3. If still not working, log in manually in the browser window")
        
        # Wait for a longer time to allow the user to solve the captcha
        for i in range(120, 0, -1):  # Increased from 60 to 120 seconds
            print(f"Waiting for captcha solution... {i} seconds remaining", end="\r")
            time.sleep(1)
        print("\nResuming scraping...")
        return True
    
    # Check for text indicating restrictions
    page_source = driver.page_source.lower()
    restriction_indicators = [
        "you've reached the limit", 
        "please verify you're a person",
        "unusual activity",
        "security verification",
        "we've detected unusual activity",
        "sign in to continue",
        "please log in",
        "access to this page has been denied",
        "captcha",  # Also check for "captcha" in the page source
        "verification"
    ]
    
    for indicator in restriction_indicators:
        if indicator in page_source:
            print("\n===============================================================")
            print(f"Restriction detected: '{indicator}'")
            print("Please resolve the issue manually in the browser window.")
            print("===============================================================")
            print("If the CAPTCHA is not loading, try these steps:")
            print("1. Click the refresh button in the browser")
            print("2. Try manually navigating to https://www.linkedin.com/feed/")
            print("3. Log in manually if prompted")
            
            # Wait for a longer time to allow the user to resolve the issue
            for i in range(120, 0, -1):  # Increased from 60 to 120 seconds
                print(f"Waiting for manual intervention... {i} seconds remaining", end="\r")
                time.sleep(1)
            print("\nResuming scraping...")
            return True
    
    return False

def search_for_profiles(search_keyword):
    """Search LinkedIn for profiles matching the search keyword"""
    print(f"Searching for: {search_keyword}")
    
    # Try direct URL navigation to the people search results
    encoded_keyword = search_keyword.replace(" ", "%20")
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_keyword}"
    driver.get(search_url)
    print(f"Navigating directly to people search: {search_url}")
    time.sleep(5)
    
    # Verify we're on a search results page
    if "search/results" not in driver.current_url:
        print(f"Failed to navigate to search results. Current URL: {driver.current_url}")
        print("Attempting alternative search method...")
        
        # Try an alternative approach - navigate to LinkedIn homepage first
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        
        # Check for login issues
        if "login" in driver.current_url or "checkpoint" in driver.current_url:
            print("Login issue detected. Attempting to re-authenticate...")
            login_successful = login_to_linkedin()
            if not login_successful:
                print("Re-authentication failed. Cannot continue search.")
                return []
        
        # Try to find and use the search bar
        try:
            # Wait for the search box to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search' i]"))
            )
            
            # Find the search box
            search_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search' i]")
            search_input.clear()
            search_input.send_keys(search_keyword)
            search_input.send_keys(Keys.RETURN)
            print("Executed search using search bar")
            time.sleep(5)
            
            # Try to navigate to People tab if not already there
            try:
                people_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'People') or contains(@aria-label, 'People')]"))
                )
                people_tab.click()
                print("Clicked on People tab")
                time.sleep(3)
            except Exception as e:
                print(f"Could not find or click People tab: {e}")
                # Check if we're already on the people search results
                if "search/results/people" not in driver.current_url:
                    print("Not on people search results page, attempting direct navigation again")
                    driver.get(search_url)
                    time.sleep(5)
        except Exception as e:
            print(f"Error using search bar: {e}")
            # Try direct URL navigation again as a last resort
            driver.get(search_url)
            time.sleep(5)
    
    # Now we should be on the search results page
    print(f"Current URL after search attempts: {driver.current_url}")
    
    # Handle possible CAPTCHA or restrictions
    if check_for_captcha_or_restriction():
        print("Handled CAPTCHA/restriction, continuing...")
    
    # Additional check - if we're still not on a search results page, give up
    if "search/results" not in driver.current_url:
        print("All search attempts failed. Cannot continue search.")
        return []
    
    print(f"Successfully navigated to search results page: {driver.current_url}")
    
    # Collect profile URLs from search results
    profile_urls = []
    page_num = 1
    
    while len(profile_urls) < MAX_PROFILES and page_num <= MAX_PAGES:
        print(f"Scanning page {page_num} of search results...")
        
        # Add a debug screenshot
        debug_screenshot = os.path.join(OUTPUT_FOLDER, f"search_page_{page_num}.png")
        try:
            driver.save_screenshot(debug_screenshot)
            print(f"Saved debug screenshot to {debug_screenshot}")
        except Exception as e:
            print(f"Could not save debug screenshot: {e}")
        
        try:
            # Check for captcha or restrictions
            if check_for_captcha_or_restriction():
                print("Continuing after captcha/restriction check...")
            
            # Generic approach - find all links on the page that look like LinkedIn profile URLs
            soup = BeautifulSoup(driver.page_source, "html.parser")
            links = soup.find_all("a", href=True)
            profile_links = [link for link in links if "linkedin.com/in/" in link["href"]]
            
            print(f"Found {len(profile_links)} potential profile links on the page")
            for link in profile_links:
                profile_url = link["href"].split("?")[0]  # Remove query parameters
                if profile_url not in profile_urls:
                    profile_urls.append(profile_url)
                    print(f"Found profile: {profile_url}")
                    
                    if len(profile_urls) >= MAX_PROFILES:
                        print(f"Reached maximum number of profiles ({MAX_PROFILES})")
                        break
            
            # If we didn't find any profiles on this page, it might be empty or we might be blocked
            if len(profile_links) == 0 and page_num == 1:
                print("No profiles found on the first page. LinkedIn might be blocking the search.")
                print("Saving page HTML for debugging...")
                with open(os.path.join(OUTPUT_FOLDER, "search_page_debug.html"), "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                
                # For the fallback search, make an extra effort - try scrolling down to load more content
                if search_keyword == "Priyadarshini Engineering College, Higna Road":
                    print("This is the fallback search. Trying additional techniques to find profiles...")
                    
                    # Scroll down a few times to load more content
                    for _ in range(5):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                    
                    # Try again after scrolling
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    links = soup.find_all("a", href=True)
                    profile_links = [link for link in links if "linkedin.com/in/" in link["href"]]
                    
                    print(f"After scrolling, found {len(profile_links)} potential profile links")
                    for link in profile_links:
                        profile_url = link["href"].split("?")[0]  # Remove query parameters
                        if profile_url not in profile_urls:
                            profile_urls.append(profile_url)
                            print(f"Found profile: {profile_url}")
                            
                            if len(profile_urls) >= MAX_PROFILES:
                                print(f"Reached maximum number of profiles ({MAX_PROFILES})")
                                break
                
                if len(profile_links) == 0:
                    break  # Still no profiles, exit the loop
            
            # Check if there's a next page button and click it
            try:
                next_button = driver.find_element(By.XPATH, "//button[@aria-label='Next']")
                if "disabled" in next_button.get_attribute("class"):
                    print("Reached the last page of search results")
                    break
                next_button.click()
                page_num += 1
                print(f"Navigating to page {page_num}")
                time.sleep(5)  # Wait longer for next page to load
            except Exception as e:
                print(f"Could not find or click next page button: {e}")
                print("No more pages available")
                break
            
        except Exception as e:
            print(f"Error scanning page {page_num}: {e}")
            time.sleep(5)
            try:
                driver.refresh()
                time.sleep(5)
                continue
            except Exception as refresh_error:
                print(f"Error refreshing page: {refresh_error}")
                break
    
    print(f"Found {len(profile_urls)} profile URLs across {page_num} pages")
    return profile_urls

def get_profile_picture_url(soup):
    """Extract the profile picture URL without downloading it"""
    try:
        # Look for image elements with profile picture-related attributes
        img_selectors = [
            "img.pv-top-card-profile-picture__image",
            "img.profile-picture",
            "img.ember-view.profile-photo-edit__preview",
            "img.presence-entity__image", 
            "img[alt*='profile photo']",
            "img[alt*='profile picture']",
            "div.profile-photo-edit__preview img"
        ]
        
        # Try each selector
        for selector in img_selectors:
            img_elements = soup.select(selector)
            if img_elements:
                for img in img_elements:
                    if img.has_attr('src'):
                        img_url = img['src']
                        # Skip data URLs as they are base64 encoded and very long
                        if not img_url.startswith('data:'):
                            print(f"Found profile picture URL using selector: {selector}")
                            return img_url
        
        # Generic approach - look for any image that might be a profile picture
        potential_img_elements = soup.find_all("img")
        for img in potential_img_elements:
            alt_text = img.get("alt", "").lower()
            if ("profile" in alt_text or "photo" in alt_text or "picture" in alt_text) and img.get("src"):
                img_url = img.get("src")
                if not img_url.startswith('data:'):
                    print(f"Found profile picture URL using generic approach")
                    return img_url
                    
        print("No profile picture URL found")
        return ""
            
    except Exception as e:
        print(f"Error extracting profile picture URL: {e}")
        return ""

def extract_profile_data(soup, profile_url, profile_id):
    """Extract profile data from BeautifulSoup object"""
    # Check if we have limited access
    has_limited_access = check_for_limited_access()
    
    # Find name - usually in a heading element
    try:
        name_elem = soup.find("h1", class_=lambda c: c and "text-heading-xlarge" in c)
        if not name_elem:
            name_elem = soup.find("h1")  # fallback
        name = name_elem.get_text().strip() if name_elem else "Unknown Name"
    except Exception as e:
        print(f"Error extracting name: {e}")
        name = "Unknown Name"
    
    print(f"Found profile name: {name}")
    
    # Extract about/headline information
    try:
        about_elem = soup.find("div", class_=lambda c: c and "text-body-medium" in c)
        about = about_elem.get_text().strip() if about_elem else ""
    except Exception as e:
        print(f"Error extracting about: {e}")
        about = ""
    
    # Extract location
    try:
        location_elem = soup.find("span", class_=lambda c: c and "text-body-small" in c and "inline" in c)
        location = location_elem.get_text().strip() if location_elem else ""
    except Exception as e:
        print(f"Error extracting location: {e}")
        location = ""
    
    # Check if this person is from Priyadarshini Engineering College
    is_from_pec = False
    pec_indicators = [
        "priyadarshini engineering college", 
        "pec higna road", 
        "priyadarshini college of engineering",
        "priyadarshini engineering", 
        "pec nagpur"
    ]
    
    # Extract education information
    educations = []
    try:
        education_section = soup.find("section", {"id": "education-section"}) or \
                          soup.find("section", {"aria-label": lambda l: l and "education" in l.lower()})
        
        if education_section:
            edu_items = education_section.find_all("li") or education_section.find_all("div", class_=lambda c: c and "pvs-entity" in c)
            
            for item in edu_items:
                try:
                    institution_elem = item.find("h3") or item.find("span", class_=lambda c: c and "t-bold" in c)
                    degree_elem = item.find("p", class_=lambda c: c and "pv-entity__secondary-title" in c) or \
                                item.find("span", class_=lambda c: c and "t-normal" in c)
                    date_elem = item.find("p", class_=lambda c: c and "pv-entity__dates" in c) or \
                              item.find("span", class_=lambda c: c and "t-normal" in c and "t-black--light" in c)
                    
                    institution = institution_elem.get_text().strip() if institution_elem else ""
                    degree = degree_elem.get_text().strip() if degree_elem else ""
                    date_range = date_elem.get_text().strip() if date_elem else ""
                    
                    # Check if this education is from PEC
                    if any(pec_ind in institution.lower() for pec_ind in pec_indicators):
                        is_from_pec = True
                        print(f"Found PEC education: {institution}")
                    
                    educations.append({
                        "institution": institution,
                        "degree": degree,
                        "date_range": date_range
                    })
                except Exception as e:
                    print(f"Error extracting education item: {e}")
        
    except Exception as e:
        print(f"Error extracting education: {e}")
    
    # Also check about text and experience for PEC mentions
    if not is_from_pec:
        if any(pec_ind in about.lower() for pec_ind in pec_indicators):
            is_from_pec = True
            print(f"Found PEC mention in about section")
    
    # Determine if the person is faculty or student based on their profile content
    is_faculty = False
    faculty_indicators = ["professor", "faculty", "teacher", "lecturer", "instructor", "hod", "head of department", "principal", "dean"]
    
    # Check name and about text for faculty indicators
    combined_text = (name + " " + about).lower()
    for indicator in faculty_indicators:
        if indicator in combined_text:
            is_faculty = True
            break
    
    # Extract current position and company
    current_position = ""
    current_company = ""
    try:
        position_elem = soup.find("div", class_=lambda c: c and "pv-text-details__left-panel" in c)
        if position_elem:
            title_elem = position_elem.find("h2", class_=lambda c: c and "mt1" in c)
            if title_elem:
                current_position = title_elem.get_text().strip()
            
            company_elem = position_elem.find("div", class_=lambda c: c and "pv-entity__secondary-title" in c)
            if company_elem:
                current_company = company_elem.get_text().strip()
                
                # Check if current company matches PEC
                if any(pec_ind in current_company.lower() for pec_ind in pec_indicators):
                    is_from_pec = True
                    print(f"Found PEC mention in current company: {current_company}")
    except Exception as e:
        print(f"Error extracting position/company: {e}")
    
    # If we couldn't get position/company from the specific elements, try a more generic approach
    if not current_position or not current_company:
        try:
            experience_section = soup.find("section", {"id": "experience-section"}) or \
                                soup.find("section", {"aria-label": lambda l: l and "experience" in l.lower()})
            
            if experience_section:
                exp_item = experience_section.find("li")
                if exp_item:
                    title_elem = exp_item.find("h3") or exp_item.find("span", class_=lambda c: c and "t-bold" in c)
                    if title_elem:
                        current_position = title_elem.get_text().strip()
                    
                    company_elem = exp_item.find("p", class_=lambda c: c and "pv-entity__secondary-title" in c) or \
                                 exp_item.find("span", class_=lambda c: c and "t-normal" in c and "t-black" in c)
                    if company_elem:
                        current_company = company_elem.get_text().strip()
                        
                        # Check if current company matches PEC
                        if any(pec_ind in current_company.lower() for pec_ind in pec_indicators):
                            is_from_pec = True
                            print(f"Found PEC mention in current company (alt method): {current_company}")
        except Exception as e:
            print(f"Error extracting position/company (alternative method): {e}")
    
    # Extract experience information to check for PEC mentions
    all_experiences = []
    try:
        experience_section = soup.find("section", {"id": "experience-section"}) or \
                            soup.find("section", {"aria-label": lambda l: l and "experience" in l.lower()})
        
        if experience_section:
            exp_items = experience_section.find_all("li") or experience_section.find_all("div", class_=lambda c: c and "pvs-entity" in c)
            
            for item in exp_items:
                try:
                    title_elem = item.find("h3") or item.find("span", class_=lambda c: c and "t-bold" in c)
                    company_elem = item.find("p", class_=lambda c: c and "pv-entity__secondary-title" in c) or \
                                 item.find("span", class_=lambda c: c and "t-normal" in c and "t-black" in c)
                    
                    title = title_elem.get_text().strip() if title_elem else ""
                    company = company_elem.get_text().strip() if company_elem else ""
                    
                    # Check if any experience is at PEC
                    if any(pec_ind in company.lower() for pec_ind in pec_indicators):
                        is_from_pec = True
                        print(f"Found PEC mention in experience: {company}")
                    
                    all_experiences.append({
                        "title": title,
                        "company": company
                    })
                except Exception as e:
                    print(f"Error extracting experience item: {e}")
    except Exception as e:
        print(f"Error extracting all experiences: {e}")
    
    # Extract contact info only if we have full access
    email = ""
    phone = ""
    website = ""
    
    if not has_limited_access:
        try:
            # Look for contact info in the page
            contact_section = soup.find("section", {"id": "contact-info"})
            if contact_section:
                email_elem = contact_section.find("a", {"href": lambda h: h and "mailto:" in h})
                if email_elem:
                    email = email_elem.get_text().strip()
                
                phone_elem = contact_section.find("a", {"href": lambda h: h and "tel:" in h})
                if phone_elem:
                    phone = phone_elem.get_text().strip()
                
                website_elem = contact_section.find("a", {"href": lambda h: h and "://" in h and "linkedin.com" not in h})
                if website_elem:
                    website = website_elem.get_text().strip()
        except Exception as e:
            print(f"Error extracting contact info: {e}")
    
    # Extract skills list
    skills = []
    try:
        skills_section = soup.find("section", {"id": "skills-section"}) or \
                        soup.find("section", {"aria-label": lambda l: l and "skill" in l.lower()})
        
        if skills_section:
            skill_items = skills_section.find_all("li") or skills_section.find_all("div", class_=lambda c: c and "pvs-entity" in c)
            
            for item in skill_items:
                try:
                    skill_name = item.find("span", class_=lambda c: c and "t-bold" in c)
                    if skill_name:
                        skills.append(skill_name.get_text().strip())
                except Exception:
                    pass
    except Exception as e:
        print(f"Error extracting skills: {e}")
    
    # Get profile picture URL
    profile_pic_url = get_profile_picture_url(soup)
    
    # Compile profile data
    return {
        "id": profile_id,
        "name": name,
        "profile_url": profile_url,
        "about": about,
        "is_faculty": is_faculty,
        "is_from_pec": is_from_pec,  # New flag indicating if this profile is from PEC
        "current_position": current_position,
        "current_company": current_company,
        "location": location,
        "email": email,
        "phone": phone,
        "website": website,
        "educations": educations,
        "experiences": all_experiences,
        "skills": skills,
        "skills_text": ", ".join(skills),
        "education_text": " | ".join([f"{edu['degree']} at {edu['institution']}, {edu['date_range']}" for edu in educations]),
        "experience_text": " | ".join([f"{exp['title']} at {exp['company']}" for exp in all_experiences]),
        "profile_pic_url": profile_pic_url,
        "has_limited_access": has_limited_access  # Add a flag to indicate limited access
    }

def scrape_profile_data(profile_url, profile_id):
    """Scrape detailed information from a LinkedIn profile"""
    try:
        # Navigate to the profile URL
        driver.get(profile_url)
        time.sleep(5)  # Increase wait time for profile to load
        
        # Check for captcha or restrictions
        if check_for_captcha_or_restriction():
            print("Continuing after captcha/restriction check...")
        
        # Take a screenshot for debugging
        debug_screenshot = os.path.join(OUTPUT_FOLDER, f"{profile_id}_profile_debug.png")
        try:
            driver.save_screenshot(debug_screenshot)
            print(f"Saved profile debug screenshot to {debug_screenshot}")
        except:
            print("Could not save debug screenshot")
        
        # Check if we have access to this profile
        if check_for_limited_access():
            print(f"Limited access to profile {profile_url}. Extracting available data only.")
            # We'll continue and extract whatever data we can access
        
        # Extract profile data directly from the page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        profile_data = extract_profile_data(soup, profile_url, profile_id)
        
        # Save profile data to a JSON file
        json_filename = os.path.join(OUTPUT_FOLDER, f"{profile_id}_data.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4, ensure_ascii=False)
        
        print(f"Saved profile data to {json_filename}")
        return profile_data
        
    except Exception as e:
        print(f"Error scraping profile {profile_url}: {e}")
        # Save the page source for debugging
        debug_html = os.path.join(OUTPUT_FOLDER, f"{profile_id}_error_debug.html")
        try:
            with open(debug_html, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Saved error debug HTML to {debug_html}")
        except Exception as file_error:
            print(f"Could not save debug HTML: {file_error}")
        return None

def check_for_limited_access():
    """Check if we have limited access to this profile due to network restrictions"""
    limited_access_indicators = [
        "outside your network",
        "limited visibility",
        "continue to grow your network",
        "you don't have access to this profile",
        "to see their full profile",
        "isn't available to you",
        "this profile isn't fully visible",
        "full profile is unavailable"
    ]
    
    page_source = driver.page_source.lower()
    
    for indicator in limited_access_indicators:
        if indicator in page_source:
            print(f"Limited access detected: '{indicator}'")
            return True
            
    return False

def save_to_csv(profiles_data):
    """Save profiles data to a CSV file, filtering for only PEC students/faculty"""
    if not profiles_data:
        print("No data to save to CSV")
        return
    
    # Filter profiles to include only those from PEC
    pec_profiles = [profile for profile in profiles_data if profile.get("is_from_pec", False)]
    
    print(f"Found {len(pec_profiles)} profiles from Priyadarshini Engineering College out of {len(profiles_data)} total profiles")
    
    if not pec_profiles:
        print("No profiles from Priyadarshini Engineering College to save")
        return
    
    # Define CSV headers with detailed information
    headers = [
        "ID", 
        "Name", 
        "Profile URL", 
        "About",
        "Role Type",  # Faculty or Student
        "Current Position",
        "Current Company",
        "Location",
        "Email",
        "Phone",
        "Website",
        "All Education Details",
        "Skills",
        "All Experience Details",
        "Profile Picture Path",
        "Has Limited Access"
    ]
    
    # Write to CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for profile in pec_profiles:
            # Prepare role type
            role_type = "Faculty" if profile.get("is_faculty", False) else "Student"
            
            # Prepare row for CSV
            row = [
                profile.get("id", ""),
                profile.get("name", ""),
                profile.get("profile_url", ""),
                profile.get("about", ""),
                role_type,
                profile.get("current_position", ""),
                profile.get("current_company", ""),
                profile.get("location", ""),
                profile.get("email", ""),
                profile.get("phone", ""),
                profile.get("website", ""),
                profile.get("education_text", ""),
                profile.get("skills_text", ""),
                profile.get("experience_text", ""),
                profile.get("profile_pic_url", ""),
                "Yes" if profile.get("has_limited_access", False) else "No"
            ]
            writer.writerow(row)
    
    print(f"Saved {len(pec_profiles)} PEC profiles to {CSV_FILE}")
    
    # Also create a backup copy with timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{CSV_FILE.split('.')[0]}_{timestamp}.csv"
    
    import shutil
    shutil.copy(CSV_FILE, backup_file)
    print(f"Created backup copy at {backup_file}")
    
    # Create separate CSVs for students and faculty
    students = [p for p in pec_profiles if not p.get("is_faculty", False)]
    faculty = [p for p in pec_profiles if p.get("is_faculty", False)]
    
    # Save students CSV
    if students:
        students_file = "pec_students.csv"
        with open(students_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for profile in students:
                row = [
                    profile.get("id", ""),
                    profile.get("name", ""),
                    profile.get("profile_url", ""),
                    profile.get("about", ""),
                    "Student",
                    profile.get("current_position", ""),
                    profile.get("current_company", ""),
                    profile.get("location", ""),
                    profile.get("email", ""),
                    profile.get("phone", ""),
                    profile.get("website", ""),
                    profile.get("education_text", ""),
                    profile.get("skills_text", ""),
                    profile.get("experience_text", ""),
                    profile.get("profile_pic_url", ""),
                    "Yes" if profile.get("has_limited_access", False) else "No"
                ]
                writer.writerow(row)
        print(f"Saved {len(students)} PEC student profiles to {students_file}")
    
    # Save faculty CSV
    if faculty:
        faculty_file = "pec_faculty.csv"
        with open(faculty_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for profile in faculty:
                row = [
                    profile.get("id", ""),
                    profile.get("name", ""),
                    profile.get("profile_url", ""),
                    profile.get("about", ""),
                    "Faculty",
                    profile.get("current_position", ""),
                    profile.get("current_company", ""),
                    profile.get("location", ""),
                    profile.get("email", ""),
                    profile.get("phone", ""),
                    profile.get("website", ""),
                    profile.get("education_text", ""),
                    profile.get("skills_text", ""),
                    profile.get("experience_text", ""),
                    profile.get("profile_pic_url", ""),
                    "Yes" if profile.get("has_limited_access", False) else "No"
                ]
                writer.writerow(row)
        print(f"Saved {len(faculty)} PEC faculty profiles to {faculty_file}")

def send_connection_request(profile_url):
    """Attempts to send a connection request to the profile"""
    try:
        # Navigate to the profile
        driver.get(profile_url)
        time.sleep(3)
        
        # Look for connection request buttons using various potential selectors
        connect_button_selectors = [
            "button.pv-s-profile-actions--connect",
            "button[aria-label*='Connect']",
            "button[aria-label*='connect']",
            "button.artdeco-button--primary",
            "button.artdeco-button[aria-label*='Invite']",
            "button.pvs-profile-actions__action[aria-label*='Connect']"
        ]
        
        for selector in connect_button_selectors:
            try:
                connect_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in connect_buttons:
                    if "connect" in button.text.lower() or "invite" in button.text.lower():
                        print(f"Found connect button: {button.text}")
                        
                        # Before clicking, make sure it's visible and clickable
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(1)
                            
                            # Click the connect button
                            button.click()
                            print("Clicked connect button")
                            time.sleep(2)
                            
                            # Look for the send button in the connection modal
                            send_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Send']")
                            for send_button in send_buttons:
                                if "send" in send_button.text.lower():
                                    send_button.click()
                                    print("Sent connection request!")
                                    time.sleep(1)
                                    return True
                        except Exception as click_error:
                            print(f"Failed to click button: {click_error}")
            except Exception:
                continue
                
        # If we got here, we couldn't find a way to connect
        print("Could not find a way to send connection request")
        return False
    
    except Exception as e:
        print(f"Error sending connection request: {e}")
        return False

def main():
    try:
        # Login to LinkedIn
        login_successful = login_to_linkedin()
        if not login_successful:
            print("Login failed. Exiting...")
            driver.quit()
            return
        
        all_profile_urls = []
        profiles_data = []
        limited_access_profiles = []  # Track profiles with limited access
        
        # Check if there's a progress file to resume from
        progress_file = os.path.join(OUTPUT_FOLDER, "scraping_progress.json")
        scraped_profiles = {}
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    scraped_profiles = json.load(f)
                print(f"Loaded {len(scraped_profiles)} previously scraped profile URLs from {progress_file}")
                
                # Load the previously scraped profile data
                for url, profile_id in scraped_profiles.items():
                    json_file = os.path.join(OUTPUT_FOLDER, f"{profile_id}_data.json")
                    if os.path.exists(json_file):
                        with open(json_file, "r", encoding="utf-8") as f:
                            profile_data = json.load(f)
                            profiles_data.append(profile_data)
                            all_profile_urls.append(url)
            except Exception as e:
                print(f"Could not load progress file, starting from scratch: {e}")
        
        print("\n" + "="*60)
        print("STARTING ONE-BY-ONE SEARCHES FOR PEOPLE FROM PRIYADARSHINI ENGINEERING COLLEGE")
        print("="*60 + "\n")
        
        # First, search with the primary keyword alone
        print(f"\n--- Searching with primary keyword: '{PRIMARY_KEYWORD}' ---\n")
        primary_profile_urls = search_for_profiles(PRIMARY_KEYWORD)
        
        # Add to our list, avoiding duplicates
        for url in primary_profile_urls:
            if url not in all_profile_urls:
                all_profile_urls.append(url)
        
        print(f"Found {len(primary_profile_urls)} profiles with primary keyword. Total profiles: {len(all_profile_urls)}")
        
        # Then do a more targeted search combining the institution with specific job titles
        for title in JOB_TITLES:
            search_term = f"{title} at {PRIMARY_KEYWORD}"
            print(f"\n--- Searching for: '{search_term}' ---\n")
            
            # Skip if we've reached the maximum number of profiles
            if len(all_profile_urls) >= MAX_PROFILES:
                print(f"Reached maximum number of profiles ({MAX_PROFILES}). Stopping search.")
                break
                
            # Search for profiles with this job title at the institution
            title_profile_urls = search_for_profiles(search_term)
            
            # Add to our list, avoiding duplicates
            for url in title_profile_urls:
                if url not in all_profile_urls:
                    all_profile_urls.append(url)
            
            print(f"Found {len(title_profile_urls)} profiles with '{search_term}'. Total profiles: {len(all_profile_urls)}")
            
            # Save progress after each search term
            urls_backup_file = os.path.join(OUTPUT_FOLDER, f"profile_urls_{title.replace(' ', '_')}.json")
            with open(urls_backup_file, "w", encoding="utf-8") as f:
                json.dump(title_profile_urls, f, indent=4)
            
            # Wait a bit between searches to avoid rate limiting
            wait_time = 3 + (2 * (JOB_TITLES.index(title) % 3))
            print(f"Waiting {wait_time} seconds before next search...")
            time.sleep(wait_time)
        
        # Then search by department
        for dept in DEPARTMENTS:
            search_term = f"{dept} {PRIMARY_KEYWORD}"
            print(f"\n--- Searching for: '{search_term}' ---\n")
            
            # Skip if we've reached the maximum number of profiles
            if len(all_profile_urls) >= MAX_PROFILES:
                print(f"Reached maximum number of profiles ({MAX_PROFILES}). Stopping search.")
                break
                
            # Search for profiles in this department at the institution
            dept_profile_urls = search_for_profiles(search_term)
            
            # Add to our list, avoiding duplicates
            for url in dept_profile_urls:
                if url not in all_profile_urls:
                    all_profile_urls.append(url)
            
            print(f"Found {len(dept_profile_urls)} profiles with '{search_term}'. Total profiles: {len(all_profile_urls)}")
            
            # Save progress after each search term
            urls_backup_file = os.path.join(OUTPUT_FOLDER, f"profile_urls_{dept.replace(' ', '_')}.json")
            with open(urls_backup_file, "w", encoding="utf-8") as f:
                json.dump(dept_profile_urls, f, indent=4)
            
            # Wait a bit between searches to avoid rate limiting
            wait_time = 3 + (2 * (DEPARTMENTS.index(dept) % 3))
            print(f"Waiting {wait_time} seconds before next search...")
            time.sleep(wait_time)
        
        # If we didn't find any profiles, exit
        if not all_profile_urls:
            print("No profiles found with any search terms. Exiting...")
            driver.quit()
            return
        
        # Save all unique profile URLs
        urls_backup_file = os.path.join(OUTPUT_FOLDER, "all_profile_urls.json")
        with open(urls_backup_file, "w", encoding="utf-8") as f:
            json.dump(all_profile_urls, f, indent=4)
        print(f"Saved {len(all_profile_urls)} profile URLs to {urls_backup_file}")
        
        # Now scrape each profile one by one
        print("\n" + "="*60)
        print("STARTING ONE-BY-ONE PROFILE DATA EXTRACTION")
        print("="*60 + "\n")
        
        # Track connection requests to limit how many we send per session
        connection_requests_sent = 0
        max_connection_requests = 15  # LinkedIn typically limits to around 100 per week
        
        # Scrape data from each profile
        for i, url in enumerate(all_profile_urls):
            profile_id = f"profile_{i+1}"
            
            # Skip if already scraped
            if url in scraped_profiles:
                print(f"\nSkipping already scraped profile {i+1}/{len(all_profile_urls)}: {url}")
                continue
                
            print(f"\nScraping profile {i+1}/{len(all_profile_urls)}: {url}")
            try:
                profile_data = scrape_profile_data(url, profile_id)
                if profile_data:
                    profiles_data.append(profile_data)
                    
                    # Check if this was a limited access profile
                    if profile_data.get("has_limited_access", False):
                        limited_access_profiles.append(url)
                        print(f"Adding to limited access profiles list: {url}")
                        
                        # Send connection request if we haven't hit our limit
                        if connection_requests_sent < max_connection_requests:
                            print(f"Attempting to send connection request to {url}")
                            if send_connection_request(url):
                                connection_requests_sent += 1
                                # Wait longer after sending a connection request
                                time.sleep(10)
                                print(f"Connection requests sent this session: {connection_requests_sent}/{max_connection_requests}")
                    
                    # Save progress after each profile
                    scraped_profiles[url] = profile_id
                    with open(progress_file, "w", encoding="utf-8") as f:
                        json.dump(scraped_profiles, f, indent=2)
                    
                    # Save each profile individually to CSV as soon as it's scraped
                    # This ensures we capture data even if the script is interrupted
                    print(f"Saving data for profile {profile_id} to CSV...")
                    save_to_csv(profiles_data)
                
                # Wait between profile scraping to avoid rate limiting
                wait_time = 5 + (3 * (i % 5))  # Varied wait time to avoid detection
                print(f"Waiting {wait_time} seconds before next profile...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"Error scraping profile {url}: {e}")
                # Still save progress even if this profile failed
                with open(progress_file, "w", encoding="utf-8") as f:
                    json.dump(scraped_profiles, f, indent=2)
                # Wait a bit longer after an error
                time.sleep(10)
        
        # Save all data to CSV one final time
        save_to_csv(profiles_data)
        
        # Save the list of limited access profiles for future reference
        limited_file = os.path.join(OUTPUT_FOLDER, "limited_access_profiles.json")
        with open(limited_file, "w", encoding="utf-8") as f:
            json.dump(limited_access_profiles, f, indent=2)
        print(f"Saved {len(limited_access_profiles)} limited access profiles to {limited_file}")
        
        print("\nAll profiles have been processed and saved to CSV successfully!")
        print(f"Total connection requests sent: {connection_requests_sent}")
        print(f"Profiles with limited access: {len(limited_access_profiles)}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        driver.quit()
        print("Scraping completed")

if __name__ == "__main__":
    main() 