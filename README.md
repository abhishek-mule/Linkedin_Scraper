
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

```bash
git clone [https://github.com/abhishek-mule/Linkedin_Scraper.git](https://github.com/abhishek-mule/Linkedin_Scraper.git)
cd Linkedin_Scraper
````

### 2\. Install Dependencies

Install all required libraries using `pip`.

```bash
pip install -r requirements.txt
```

### 3\. Configure Credentials

You **must** open `linkedin_college_scraper.py` and replace the placeholder values with your own LinkedIn credentials.

```python
# --- REQUIRED CONFIGURATION ---
EMAIL = "your_linkedin_email@example.com"
PASSWORD = "your_linkedin_password"

# --- OPTIONAL CONFIGURATION ---
SEARCH_KEYWORD = "Priyadarshini Engineering College, Hingna Road"
OUTPUT_FOLDER = "students_data"
CSV_FILE = "students_data.csv"
MAX_PROFILES = 50  # Maximum number of profiles to scrape
```

### 4\. Chrome & WebDriver Setup

This tool uses Chrome. The required ChromeDriver dependency is **automatically managed** if you have Google Chrome installed, thanks to `webdriver_manager`.

-----

## ▶️ Usage

Simply run the main Python script from your terminal:

```bash
python linkedin_college_scraper.py
```

The script will perform the following steps automatically:

1.  Log in to LinkedIn using your configured credentials.
2.  Search for profiles based on the `SEARCH_KEYWORD`.
3.  Collect profile URLs and visit each one.
4.  Extract data, download images, and save the output.

-----

## 📁 Output Structure

All extracted data will be neatly organized within the `students_data/` folder (or whatever you set for `OUTPUT_FOLDER`).

```bash
students_data/
│
├── student_1_data.json          # Detailed JSON data for individual profile
├── student_1_profile_pic.jpg    # Downloaded profile photo
├── student_2_data.json
├── student_2_profile_pic.jpg
└── students_data.csv            # Summary CSV of all scraped profiles
```

-----

## 🛑 Important Notes & Disclaimer

### ⚠️ Legal Disclaimer - Use at Your Own Risk

This project is created strictly for **educational and research purposes**.

**Scraping LinkedIn content violates their User Agreement.** The author assumes **no responsibility** for any misuse, policy violations, or account restrictions that may occur from using this tool. **Use responsibly and at your own risk.**

### 🔒 Data Privacy

  * The output files (`.csv` and `.json`) are **`.gitignore` protected**. **DO NOT** upload or share any scraped data publicly.
  * LinkedIn users **may see your profile view** when the scraper visits their page.

### 🐢 Rate Limiting

The built-in time delays are essential for preventing detection. **Do not lower these delays**—it significantly increases your risk of being restricted or banned by LinkedIn.

-----

## 🛠 Troubleshooting

| Issue | Potential Fix |
| :--- | :--- |
| **Login / Captcha issues** | Disable headless mode in the script and manually complete the verification or login. |
| **Selectors not found** | LinkedIn's layout changes. You may need to update XPaths/CSS selectors in the script. |
| **ChromeDriver error** | Ensure Google Chrome is installed and that your `webdriver-manager` package is up-to-date. |
| **Incomplete data** | Try increasing the delay between actions or reducing the `MAX_PROFILES` limit. |

-----

## 🧾 License

This project is provided **as-is** for educational purposes only.

## ✨ Author

**Abhishek Mule**
*💼 Developer | 💡 Innovator*
*📧 your\_email@example.com*

```



