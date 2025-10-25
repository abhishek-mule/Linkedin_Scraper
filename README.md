🚀 LinkedIn College Student Scraper

A Python-based automation tool that searches LinkedIn for students from Priyadarshini Engineering College, Hingna Road and extracts detailed profile information — including education, experience, and profile photos — for educational or research purposes.



🧩 *Features*

🔍 Automated LinkedIn Search
Searches for profiles matching:
"Priyadarshini Engineering College, Hingna Road"

📋 Comprehensive Profile Extraction
Extracts structured data including:

Name, headline, and “About” section

Education and experience details

Profile photo (if available)

💾 ****Data Storage Options****

Saves individual profiles as JSON files

Generates a summary CSV containing all basic info


⚙️ Setup Instructions
1. Clone the Repository
git clone https://github.com/abhishek-mule/Linkedin_Scraper.git
cd Linkedin_Scraper

2. Install Dependencies
pip install -r requirements.txt

3. Configure Your Credentials

Open linkedin_college_scraper.py and edit:

EMAIL = "your_linkedin_email@example.com"
PASSWORD = "your_linkedin_password"


Optional configuration parameters:

SEARCH_KEYWORD = "Priyadarshini Engineering College, Hingna Road"
OUTPUT_FOLDER = "students_data"
CSV_FILE = "students_data.csv"
MAX_PROFILES = 50

4. Chrome & WebDriver Setup

Install Google Chrome

Ensure ChromeDriver matches your Chrome version
(automatically managed if you use webdriver_manager)



▶️ Usage

Run the script:

python linkedin_college_scraper.py


The script will:

Log in to LinkedIn

Search for profiles using the keyword

Collect profile URLs

Visit each profile and extract data

Download profile images

Save everything in JSON and CSV formats



📁 Output Structure
students_data/
│
├── student_1_data.json
├── student_1_profile_pic.jpg
├── student_2_data.json
├── student_2_profile_pic.jpg
└── students_data.csv





⚠️ Important Notes

🚫 Legal Disclaimer
This project is for educational and research use only.
Scraping LinkedIn content violates their User Agreement
.
Use responsibly and at your own risk.

🔒 Data Privacy
The students_data.csv and JSON files are .gitignore-protected.
Do not upload or share scraped data publicly.

🐢 Rate Limiting
Built-in time delays help prevent detection.
Do not lower these delays — it increases your risk of restriction.

👀 Profile Visibility
LinkedIn users may see your profile views when you scrape.



🛠 Troubleshooting
Issue	Fix
Login / Captcha issues	Disable headless mode and complete verification manually
Selectors not found	Update XPaths/CSS selectors if LinkedIn layout changes
ChromeDriver error	Ensure ChromeDriver matches your Chrome version
Incomplete data	Reduce MAX_PROFILES or increase delay between actions


📜 License

This project is provided as-is for educational purposes only.
The author assumes no responsibility for misuse or policy violations.
