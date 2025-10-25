# 🚀 LinkedIn College Student Scraper

[![GitHub license](https://img.shields.io/badge/License-Educational-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.x-informational.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Working-brightgreen.svg)]()

---

## 🎯 Project Overview

A **Python-based automation tool** designed to search LinkedIn for students from a specific institution (initially configured for **Priyadarshini Engineering College, Hingna Road**). It extracts detailed profile information for educational or research purposes, saving the data locally in secure formats.

---

## ✨ Key Features

| Icon | Feature | Description |
| :--- | :--- | :--- |
| 🔍 | **Automated LinkedIn Search** | Searches for student profiles matching the `SEARCH_KEYWORD` (e.g., 'IIT Bombay' as per your original note). |
| 📋 | **Comprehensive Extraction** | Pulls structured data: Name, Headline, "About" section, Education, Experience, and Profile Photos. |
| 💾 | **Flexible Data Storage** | Saves individual profiles as **JSON files** and generates a **summary CSV** for bulk analysis. |
| 🛡️ | **Rate Limit Protection** | Includes built-in time delays to minimize the risk of detection and restrictions. |

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
Start by getting a local copy of the project.


<pre>
git clone [https://github.com/abhishek-mule/Linkedin_Scraper.git](https://github.com/abhishek-mule/Linkedin_Scraper.git)
cd Linkedin_Scraper
</pre>

2. Install DependenciesInstall all required libraries using 
<pre>
  pip.Bashpip install -r requirements.txt
</pre>


3. Configure CredentialsYou must open linkedin_college_scraper.py and replace the placeholder values with your own LinkedIn credentials.Python




🛑 Important Notes & Disclaimer⚠️ Legal Disclaimer - Use at Your Own RiskThis project is created strictly for educational and research purposes.Scraping LinkedIn content violates their User Agreement. The author assumes no responsibility for any misuse, policy violations, or account restrictions that may occur from using this tool. Use responsibly and at your own risk.🔒 Data PrivacyThe output files (.csv and .json) are .gitignore protected. DO NOT upload or share any scraped data publicly.LinkedIn users may see your profile view when the scraper visits their page.🐢 Rate LimitingThe built-in time delays are essential for preventing detection. Do not lower these delays—it significantly increases your risk of being restricted or banned by LinkedIn.🛠 TroubleshootingIssuePotential FixLogin / Captcha issuesDisable headless mode in the script and manually complete the verification or login.Selectors not foundLinkedIn's layout changes. You may need to update XPaths/CSS selectors in the script.ChromeDriver errorEnsure Google Chrome is installed and that your webdriver-manager package is up-to-date.Incomplete dataTry increasing the delay between actions or reducing the MAX_PROFILES limit.🧾 LicenseThis project is provided as-is for educational purposes only.✨ AuthorAbhishek Mule💼 Developer | 💡 Innovator📧 your_email@example.com
