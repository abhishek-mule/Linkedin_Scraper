#!/usr/bin/env python
"""
Run PEC LinkedIn Scraper
------------------------
This script runs the Priyadarshini Engineering College LinkedIn scraper.
"""

import os
import subprocess
import sys
import time

def main():
    print("\n" + "="*60)
    print(" Priyadarshini Engineering College LinkedIn Scraper")
    print("="*60 + "\n")
    
    # Check if the pec_profiles directory exists, create if not
    if not os.path.exists("pec_profiles"):
        os.makedirs("pec_profiles")
        print("Created 'pec_profiles' directory")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 6):
        print("Error: This script requires Python 3.6 or higher")
        return
    
    # Check requirements
    try:
        import selenium
        import bs4
        print("Required packages found")
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Run the scraper
    print("\nStarting the LinkedIn scraper...")
    print("Note: This process may take several hours depending on the number of profiles.\n")
    print("The scraper will save data to 'pec_profiles.csv' and the 'pec_profiles' directory.\n")
    print("Press Ctrl+C at any time to stop the scraper (data already collected will be saved).\n")
    
    # CAPTCHA handling information
    print("\n" + "="*60)
    print(" IMPORTANT: CAPTCHA HANDLING ")
    print("="*60)
    print("LinkedIn frequently shows CAPTCHAs to prevent scraping.")
    print("If you encounter CAPTCHA issues during execution:")
    print("1. The scraper will pause automatically when it detects a CAPTCHA")
    print("2. If the CAPTCHA is not loading correctly:")
    print("   - Click the refresh button in the browser")
    print("   - Try manually navigating to https://www.linkedin.com/feed/")
    print("   - Log in manually if prompted")
    print("3. The scraper will wait 2 minutes for you to solve any CAPTCHA issues")
    print("4. After solving, the scraper will automatically continue\n")
    
    # Network access information
    print("\n" + "="*60)
    print(" LIMITED PROFILE ACCESS HANDLING ")
    print("="*60)
    print("LinkedIn restricts access to profiles outside of your network.")
    print("When the scraper encounters a profile with limited access:")
    print("1. It will still extract all available data")
    print("2. The profile will be flagged with 'limited access' in the data")
    print("3. The scraper will automatically attempt to send connection requests")
    print("   to profiles with limited access (up to 15 per session)")
    print("4. This helps grow your network for future scraping sessions")
    print("5. Limited access profiles are saved to 'limited_access_profiles.json'")
    print("   for follow-up in future runs\n")
    
    # Fallback search information
    print("\n" + "="*60)
    print(" SEARCH FALLBACK MECHANISM ")
    print("="*60)
    print("The scraper will try multiple search keywords to find profiles.")
    print("If all search attempts fail or no profiles are found:")
    print("1. The scraper will automatically use a fallback search keyword:")
    print("   'Priyadarshini Engineering College, Higna Road'")
    print("2. Additional search techniques will be applied for this fallback")
    print("3. This ensures maximum chances of finding relevant profiles\n")
    
    time.sleep(7)  # Give user more time to read the instructions
    
    try:
        subprocess.check_call([sys.executable, "pec_linkedin_scraper.py"])
        print("\nScraping completed successfully!")
        print("Data has been saved to 'pec_profiles.csv' and the 'pec_profiles' directory.")
        print("\nTo view the data in the web application, run:")
        print("  python run_web_app.py")
    except subprocess.CalledProcessError:
        print("\nScraping stopped or encountered an error.")
        print("Check the 'pec_profiles' directory for any collected data.")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        print("Data collected so far has been saved.")

if __name__ == "__main__":
    main() 