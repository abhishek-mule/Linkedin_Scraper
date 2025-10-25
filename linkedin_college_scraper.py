import os
import time
import csv
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import base64
from linkedin_scraper import actions
from linkedin_scraper.person import Person

# Configuration
EMAIL = "cavad48528@cotigz.com"  # Replace with your LinkedIn email
PASSWORD = "Pass@cavad48528"  # Replace with your LinkedIn password
SEARCH_KEYWORDS = [
    "Priyadarshini Engineering College Higna Road",
    "PEC Higna Road Nagpur",
    "Priyadarshini College of Engineering Nagpur",
    "Priyadarshini Engineering College Faculty",
    "PEC Nagpur faculty",
    "PEC Nagpur alumni",
    "Priyadarshini Engineering College student"
]  # More specific search terms with location
OUTPUT_FOLDER = "students_data"
CSV_FILE = "students_data.csv"
MAX_PROFILES = 500  # Increased number of profiles to scrape
MAX_PAGES = 100  # Maximum number of pages to scan

# Create output folder if it doesn't exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Setup Chrome options
chrome_options = Options()
# Uncomment this line to run in non-headless mode so we can see what's happening
# chrome_options.add_argument("--headless")  # Uncomment to run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

# Initialize the WebDriver with a simpler approach
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
                return False
    except Exception as e:
        print(f"Error during login: {e}")
        # Add a pause here to allow for manual intervention if needed
        print("Pausing for 30 seconds to allow manual login if needed...")
        time.sleep(30)
        if "feed" in driver.current_url:
            print("Manual login successful")
            return True
        else:
        driver.quit()
        exit(1)

def search_for_profiles():
    """Search LinkedIn for profiles matching the search keyword"""
    print(f"Searching for: {SEARCH_KEYWORD}")
    
    # Try direct URL navigation to the people search results
    encoded_keyword = SEARCH_KEYWORD.replace(" ", "%20")
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_keyword}"
    driver.get(search_url)
    print(f"Navigating directly to people search: {search_url}")
    time.sleep(5)
    
    # Verify we're on a search results page
    if "search/results" not in driver.current_url:
        print(f"Failed to navigate to search results. Current URL: {driver.current_url}")
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
                                break
            
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

def download_profile_picture(profile_url, profile_id):
    """Download the profile picture for a given profile"""
    try:
        # The page should already be loaded by the calling function
        
        # Try multiple selectors for profile pictures
        img_selectors = [
            "img.pv-top-card-profile-picture__image",
            "img.profile-picture",
            "img.ember-view.profile-photo-edit__preview",
            "img.presence-entity__image", 
            "img[alt*='profile photo']",
            "img[alt*='profile picture']",
            "div.profile-photo-edit__preview img"
        ]
        
        img_url = None
        for selector in img_selectors:
            try:
                img_elem = driver.find_element(By.CSS_SELECTOR, selector)
            img_url = img_elem.get_attribute("src")
                if img_url:
                    print(f"Found profile picture using selector: {selector}")
                    break
            except:
                continue
        
        # If we couldn't find using selectors, try a more generic approach with BeautifulSoup
        if not img_url:
            print("Trying generic approach to find profile picture")
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Look for any image that might be a profile picture
            potential_img_elements = soup.find_all("img")
            for img in potential_img_elements:
                alt_text = img.get("alt", "").lower()
                if ("profile" in alt_text or "photo" in alt_text) and img.get("src"):
                    img_url = img.get("src")
                    print(f"Found profile picture using generic approach")
                    break
            
            if img_url:
                # Create a filename for the image
                img_filename = os.path.join(OUTPUT_FOLDER, f"{profile_id}_profile_pic.jpg")
                
            # Handle data URLs (base64 encoded images)
            if img_url.startswith('data:image'):
                try:
                    # Extract the base64 data
                    img_data = img_url.split(',')[1]
                    with open(img_filename, 'wb') as f:
                        f.write(base64.b64decode(img_data))
                    print(f"Saved base64 profile picture: {img_filename}")
                    return img_filename
                except Exception as e:
                    print(f"Error saving base64 image: {e}")
                    return None
            else:
                # Download the image from URL
                try:
                urllib.request.urlretrieve(img_url, img_filename)
                print(f"Downloaded profile picture: {img_filename}")
                return img_filename
                except Exception as e:
                    print(f"Error downloading image from URL: {e}")
                    return None
            else:
                print("No profile picture found")
            return None
            
    except Exception as e:
        print(f"Error in download_profile_picture: {e}")
        return None

def check_for_captcha_or_restriction():
    """Check if we've hit a captcha or been restricted, and wait for manual intervention if needed"""
    # Check for common captcha or restriction indicators in the URL or page content
    if "captcha" in driver.current_url.lower() or "challenge" in driver.current_url.lower():
        print("CAPTCHA detected! Please solve it manually...")
        # Wait for a longer time to allow the user to solve the captcha
        for i in range(60, 0, -1):
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
        "access to this page has been denied"
    ]
    
    for indicator in restriction_indicators:
        if indicator in page_source:
            print(f"Restriction detected: '{indicator}'")
            print("Please resolve the issue manually...")
            # Wait for a longer time to allow the user to resolve the issue
            for i in range(60, 0, -1):
                print(f"Waiting for manual intervention... {i} seconds remaining", end="\r")
                time.sleep(1)
            print("\nResuming scraping...")
            return True
    
    return False

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
        
        # Extract profile data directly from the page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Find name - usually in a heading element
        try:
            name_elem = soup.find("h1", class_=lambda c: c and "text-heading-xlarge" in c)
            if not name_elem:
                name_elem = soup.find("h1")  # fallback
            name = name_elem.get_text().strip() if name_elem else "Unknown Name"
        except:
            name = "Unknown Name"
            
        print(f"Found profile name: {name}")
        
        # Extract about/headline information
        try:
            about_elem = soup.find("div", class_=lambda c: c and "text-body-medium" in c)
            about = [about_elem.get_text().strip()] if about_elem else []
        except:
            about = []
            
        # Extract experience information
        experiences = []
        try:
            # Look for experience section
            exp_section = soup.find("section", {"id": "experience-section"}) or \
                         soup.find("section", {"aria-label": lambda l: l and "experience" in l.lower()}) or \
                         soup.find("div", {"id": lambda i: i and "experience" in i.lower()})
            
            if exp_section:
                # Look for experience items
                exp_items = exp_section.find_all("li") or exp_section.find_all("div", class_=lambda c: c and "pvs-entity" in c)
                
                for item in exp_items:
                    try:
                        # Try to extract details from each experience item
                        title_elem = item.find("h3") or item.find("span", class_=lambda c: c and "t-bold" in c)
                        company_elem = item.find("p", class_=lambda c: c and "pv-entity__secondary-title" in c) or \
                                      item.find("span", class_=lambda c: c and "t-normal" in c and "t-black" in c)
                        date_elem = item.find("h4", class_=lambda c: c and "pv-entity__date-range" in c) or \
                                   item.find("span", class_=lambda c: c and "t-normal" in c and "t-black--light" in c)
                        
                        title = title_elem.get_text().strip() if title_elem else ""
                        company = company_elem.get_text().strip() if company_elem else ""
                        date_range = date_elem.get_text().strip() if date_elem else ""
                        
                        # Parse date range if available
                        from_date = ""
                        to_date = ""
                        duration = ""
                        
                        if date_range:
                            if " - " in date_range:
                                dates = date_range.split(" - ")
                                from_date = dates[0].strip()
                                to_date = dates[1].strip()
                            if "· " in date_range:
                                parts = date_range.split("· ")
                                if len(parts) > 1:
                                    duration = parts[1].strip()
                        
                        # Add the experience
                        experiences.append({
                            "title": title,
                            "company": company,
                            "from_date": from_date,
                            "to_date": to_date,
                            "duration": duration,
                            "location": "",  # Location is harder to reliably extract
                            "description": "",  # Description is harder to reliably extract
                        })
                    except Exception as exp_err:
                        print(f"Error extracting experience item: {exp_err}")
        except Exception as e:
            print(f"Error extracting experiences: {e}")
        
        # Extract education information
        educations = []
        try:
            # Look for education section
            edu_section = soup.find("section", {"id": "education-section"}) or \
                         soup.find("section", {"aria-label": lambda l: l and "education" in l.lower()}) or \
                         soup.find("div", {"id": lambda i: i and "education" in i.lower()})
            
            if edu_section:
                # Look for education items
                edu_items = edu_section.find_all("li") or edu_section.find_all("div", class_=lambda c: c and "pvs-entity" in c)
                
                for item in edu_items:
                    try:
                        # Try to extract details from each education item
                        school_elem = item.find("h3") or item.find("span", class_=lambda c: c and "t-bold" in c)
                        degree_elem = item.find("p", class_=lambda c: c and "pv-entity__secondary-title" in c) or \
                                     item.find("span", class_=lambda c: c and "t-normal" in c and "t-black" in c)
                        date_elem = item.find("p", class_=lambda c: c and "pv-entity__dates" in c) or \
                                   item.find("span", class_=lambda c: c and "t-normal" in c and "t-black--light" in c)
                        
                        institution = school_elem.get_text().strip() if school_elem else ""
                        degree = degree_elem.get_text().strip() if degree_elem else ""
                        date_range = date_elem.get_text().strip() if date_elem else ""
                        
                        # Parse date range if available
                        from_date = ""
                        to_date = ""
                        
                        if date_range:
                            if " - " in date_range:
                                dates = date_range.split(" - ")
                                from_date = dates[0].strip()
                                to_date = dates[1].strip()
                        
                        # Add the education
                        educations.append({
                            "institution_name": institution,
                            "degree": degree,
                            "from_date": from_date,
                            "to_date": to_date,
                        })
                    except Exception as edu_err:
                        print(f"Error extracting education item: {edu_err}")
        except Exception as e:
            print(f"Error extracting educations: {e}")
        
        # Download profile picture
        profile_pic = download_profile_picture(profile_url, profile_id)
        
        # Compile profile data
        profile_data = {
            "id": profile_id,
            "name": name,
            "url": profile_url,
            "about": about,
            "experiences": experiences,
            "educations": educations,
            "profile_pic": profile_pic
        }
        
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
        except:
            print("Could not save debug HTML")
        return None

def save_to_csv(profiles_data):
    """Save all profiles data to a CSV file"""
    if not profiles_data:
        print("No data to save to CSV")
        return
    
    # Define CSV headers with more detailed information
    headers = [
        "ID", 
        "Name", 
        "Profile URL", 
        "About",
        "Current Company",
        "Current Position",
        "Current Location",
        "Current Duration",
        "All Experiences",
        "Current Education Institution",
        "Current Degree",
        "All Education Details",
        "Profile Picture Path"
    ]
    
    # Write to CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for data in profiles_data:
            if data:
                # Extract current experience if available
                current_exp = data["experiences"][0] if data["experiences"] else {
                    "company": "", 
                    "title": "",
                    "location": "",
                    "duration": ""
                }
                
                # Format all experiences as a single string
                all_experiences = " | ".join([
                    f"{exp.get('title', '')} at {exp.get('company', '')}, {exp.get('from_date', '')} to {exp.get('to_date', '')}"
                    for exp in data["experiences"]
                ]) if data["experiences"] else ""
                
                # Extract current education if available
                current_edu = data["educations"][0] if data["educations"] else {
                    "institution": "",
                    "degree": ""
                }
                
                # Format all education details as a single string
                all_education = " | ".join([
                    f"{edu.get('degree', '')} at {edu.get('institution', '')}, {edu.get('from_date', '')} to {edu.get('to_date', '')}"
                    for edu in data["educations"]
                ]) if data["educations"] else ""
                
                # Prepare row for CSV
                row = [
                    data["id"],
                    data["name"],
                    data["url"],
                    " ".join(data["about"]) if data["about"] else "",
                    current_exp.get("company", ""),
                    current_exp.get("title", ""),
                    current_exp.get("location", ""),
                    current_exp.get("duration", ""),
                    all_experiences,
                    current_edu.get("institution", ""),
                    current_edu.get("degree", ""),
                    all_education,
                    data["profile_pic"] if data["profile_pic"] else ""
                ]
                writer.writerow(row)
    
    print(f"Saved {len(profiles_data)} profiles to {CSV_FILE}")
    
    # Also create a backup copy with timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{CSV_FILE.split('.')[0]}_{timestamp}.csv"
    
    import shutil
    shutil.copy(CSV_FILE, backup_file)
    print(f"Created backup copy at {backup_file}")

def find_people_also_viewed(profile_url):
    """Find other profiles in the 'People Also Viewed' section"""
    try:
        # Navigate to the profile and scroll down to load "People Also Viewed"
        driver.get(profile_url)
        time.sleep(3)
        
        # Scroll to the bottom of the page slowly to load all content
        for i in range(5):
            driver.execute_script(f"window.scrollTo(0, {i*1000});")
            time.sleep(1)
        
        # Final scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Look for the "People Also Viewed" section
        soup = BeautifulSoup(driver.page_source, "html.parser")
        also_viewed_urls = []
        
        # Various selectors for the "People Also Viewed" section
        selectors = [
            "section.aside-similar-people",
            "div.aside-similar-people",
            "section[data-recommended-people]",
            "div[data-recommended-people]",
            "section.artdeco-card.pv-profile-card",
        ]
        
        section = None
        for selector in selectors:
            try:
                section = soup.select_one(selector)
                if section:
                    print(f"Found 'People Also Viewed' section using selector: {selector}")
                    break
            except:
                continue
        
        if not section:
            # Try a different approach - find any divs with profile links
            all_links = soup.find_all("a", href=True)
            for link in all_links:
                if "linkedin.com/in/" in link["href"] and profile_url not in link["href"]:
                    also_viewed_url = link["href"].split("?")[0]  # Remove query parameters
                    if also_viewed_url not in also_viewed_urls:
                        also_viewed_urls.append(also_viewed_url)
        else:
            # Extract profile links from the section
            links = section.find_all("a", href=True)
            for link in links:
                if "linkedin.com/in/" in link["href"]:
                    also_viewed_url = link["href"].split("?")[0]  # Remove query parameters
                    if also_viewed_url not in also_viewed_urls:
                        also_viewed_urls.append(also_viewed_url)
        
        print(f"Found {len(also_viewed_urls)} profiles in 'People Also Viewed' section")
        return also_viewed_urls
    except Exception as e:
        print(f"Error finding 'People Also Viewed' profiles: {e}")
        return []

def main():
    try:
        # Login to LinkedIn
        login_successful = login_to_linkedin()
        if not login_successful:
            print("Login failed. Exiting...")
            driver.quit()
            return
        
        all_profile_urls = []
        
        # Try each search keyword until we find enough profiles
        for keyword in SEARCH_KEYWORDS:
            print(f"\n--- Trying search keyword: {keyword} ---\n")
            
            # Update the global search keyword
            global SEARCH_KEYWORD
            SEARCH_KEYWORD = keyword
        
        # Search for profiles
        profile_urls = search_for_profiles()
            
            # Save the collected URLs to a file for backup/recovery
            urls_backup_file = os.path.join(OUTPUT_FOLDER, f"profile_urls_{keyword.replace(' ', '_')}.json")
            with open(urls_backup_file, "w", encoding="utf-8") as f:
                json.dump(profile_urls, f, indent=4)
            
            # Add new unique URLs to our main list
            for url in profile_urls:
                if url not in all_profile_urls:
                    all_profile_urls.append(url)
            
            print(f"Found {len(profile_urls)} profiles with keyword '{keyword}'. Total unique profiles: {len(all_profile_urls)}")
            
            # Stop if we've found enough profiles
            if len(all_profile_urls) >= MAX_PROFILES:
                print(f"Found enough profiles ({len(all_profile_urls)}). Stopping search.")
                break
        
        # If we found at least one profile, explore 'People Also Viewed' to find more profiles
        if len(all_profile_urls) > 0 and len(all_profile_urls) < MAX_PROFILES:
            print("\n--- Exploring 'People Also Viewed' sections to find more profiles ---\n")
            
            # Keep track of profiles we've already checked for 'People Also Viewed'
            checked_profiles = []
            
            # Use a queue to keep track of profiles to check
            profiles_to_check = all_profile_urls.copy()
            
            while profiles_to_check and len(all_profile_urls) < MAX_PROFILES:
                # Get the next profile to check
                profile_url = profiles_to_check.pop(0)
                
                # Skip if we've already checked this profile
                if profile_url in checked_profiles:
                    continue
                
                print(f"Looking for 'People Also Viewed' on profile: {profile_url}")
                
                # Find 'People Also Viewed' profiles
                also_viewed_urls = find_people_also_viewed(profile_url)
                
                # Add to checked profiles
                checked_profiles.append(profile_url)
                
                # Add new profiles to our lists
                for url in also_viewed_urls:
                    if url not in all_profile_urls:
                        all_profile_urls.append(url)
                        profiles_to_check.append(url)
                        print(f"Added new profile from 'People Also Viewed': {url}")
                        
                        if len(all_profile_urls) >= MAX_PROFILES:
                            print(f"Found enough profiles ({len(all_profile_urls)}). Stopping search.")
                            break
                
                # Wait a bit before checking the next profile
                time.sleep(5)
        
        # If we didn't find any profiles, exit
        if not all_profile_urls:
            print("No profiles found with any of the search keywords. Exiting...")
            driver.quit()
            return
        
        # Save all unique profile URLs
        urls_backup_file = os.path.join(OUTPUT_FOLDER, "all_profile_urls.json")
        with open(urls_backup_file, "w", encoding="utf-8") as f:
            json.dump(all_profile_urls, f, indent=4)
        print(f"Saved {len(all_profile_urls)} profile URLs to {urls_backup_file}")
        
        # Check if there's a progress file to resume from
        progress_file = os.path.join(OUTPUT_FOLDER, "scraping_progress.json")
        scraped_profiles = {}
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    scraped_profiles = json.load(f)
                print(f"Loaded {len(scraped_profiles)} previously scraped profiles from {progress_file}")
            except:
                print("Could not load progress file, starting from scratch")
        
        # Scrape data from each profile
        profiles_data = []
        for i, url in enumerate(all_profile_urls):
            profile_id = f"student_{i+1}"
            
            # Skip if already scraped
            if url in scraped_profiles:
                print(f"\nSkipping already scraped profile {i+1}/{len(all_profile_urls)}: {url}")
                profiles_data.append(scraped_profiles[url])
                continue
                
            print(f"\nScraping profile {i+1}/{len(all_profile_urls)}: {url}")
            try:
                profile_data = scrape_profile_data(url, profile_id)
            if profile_data:
                profiles_data.append(profile_data)
                    
                    # Save progress after each profile
                    scraped_profiles[url] = profile_data
                    with open(progress_file, "w", encoding="utf-8") as f:
                        json.dump(scraped_profiles, f, indent=2)
                
                # Save to CSV periodically (every 10 profiles)
                if (i+1) % 10 == 0 or (i+1) == len(all_profile_urls):
                    print(f"Saving intermediate results to CSV after {i+1} profiles...")
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
        
        # Save all data to CSV
        save_to_csv(profiles_data)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        driver.quit()
        print("Scraping completed")

if __name__ == "__main__":
    main() 