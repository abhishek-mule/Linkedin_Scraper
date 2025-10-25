# Priyadarshini Engineering College LinkedIn Scraper

This tool scrapes LinkedIn profiles of students, alumni, and faculty from Priyadarshini Engineering College, Higna Road, Nagpur.

## Features

- Specifically targets PEC Higna Road profiles (students, faculty, and alumni)
- Identifies whether a profile is faculty or student based on profile content
- Extracts comprehensive data including:
  - Basic profile information (name, about, location)
  - Current position and company
  - Contact information (email, phone, website) when available
  - Education history
  - Skills
  - Profile pictures
- Saves data in both CSV and JSON formats
- Includes built-in error handling and recovery
- Creates backup files to prevent data loss

## Requirements

- Python 3.6+
- Selenium WebDriver
- ChromeDriver (matching your Chrome version)
- BeautifulSoup4
- A valid LinkedIn account

## Installation

1. Install required Python packages:

```bash
pip install selenium beautifulsoup4 pillow
```

2. Download ChromeDriver from https://sites.google.com/a/chromium.org/chromedriver/downloads
   - Make sure to download the version that matches your Chrome browser version
   - Place the ChromeDriver executable in your PATH or in the same directory as the script

3. Update the LinkedIn credentials in the script:
   - Open `pec_linkedin_scraper.py`
   - Update the `EMAIL` and `PASSWORD` variables with your LinkedIn credentials

## Usage

Run the script with:

```bash
python pec_linkedin_scraper.py
```

The script will:
1. Log in to LinkedIn using your credentials
2. Search for profiles related to Priyadarshini Engineering College, Higna Road
3. Visit each profile and extract relevant information
4. Save the data to `pec_profiles.csv` and individual JSON files for each profile
5. Create backup files with timestamps

## Output

- `pec_profiles.csv`: Contains all scraped profiles with key information
- `pec_profiles/`: Directory containing:
  - JSON files for each profile with detailed information
  - Profile pictures
  - Debug screenshots
  - Backup files

## CSV Structure

The CSV file includes the following columns:
- ID: Unique identifier
- Name: Profile name
- Profile URL: LinkedIn URL
- About: Profile headline or summary
- Role Type: Faculty or Student (determined automatically)
- Current Position
- Current Company
- Location
- Email (if available)
- Phone (if available)
- Website (if available)
- All Education Details
- Skills
- Profile Picture Path

## Notes

- LinkedIn may limit the rate at which you can view profiles
- The tool includes built-in waiting periods to avoid detection
- If you encounter CAPTCHA challenges, the script will pause to allow you to solve them manually
- Login issues may require manual intervention, which the script will prompt for

## Web Application Integration

To view the scraped profiles in the web application:
1. Run the scraper to collect data
2. Ensure the web app is configured to read from `pec_profiles.csv`
3. Start the web application with `python run_web_app.py`

## Legal Considerations

This tool is provided for educational purposes only. Please use responsibly and in accordance with:
- LinkedIn's Terms of Service
- Privacy regulations and laws
- Ethical web scraping practices

Always respect the data privacy of individuals whose profiles you are scraping. 