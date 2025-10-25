You want me to take the code block content and re-format it, starting from the `git clone` command.

Here is the formatted output for the "Setup Instructions," "Usage," and "Output Structure" sections, ensuring all code blocks are correctly enclosed:

````markdown
### 1. Clone the Repository
Start by getting a local copy of the project.

```bash
git clone [https://github.com/abhishek-mule/Linkedin_Scraper.git](https://github.com/abhishek-mule/Linkedin_Scraper.git)
cd Linkedin_Scraper
````

### 2\. Install Dependencies

Install all required libraries using pip.

```bash
pip install -r requirements.txt
```

### 3\. Configure Credentials

You must open `linkedin_college_scraper.py` and replace the placeholder values with your own LinkedIn credentials.

```python
# --- REQUIRED CONFIGURATION ---
EMAIL = "your_linkedin_email@example.com"
PASSWORD = "your_linkedin_password"
```

```python
# --- OPTIONAL CONFIGURATION ---
SEARCH_KEYWORD = "IIT Bombay, Mumbai"
OUTPUT_FOLDER = "students_data"
CSV_FILE = "students_data.csv"
MAX_PROFILES = 50 # Maximum number of profiles to scrape
```

### 4\. Chrome & WebDriver Setup

This tool uses Chrome. The required ChromeDriver dependency is automatically managed if you have Google Chrome installed, thanks to `webdriver_manager`.

-----

## ▶️ Usage

Simply run the main Python script from your terminal:

```bash
python linkedin_college_scraper.py
```

The script will perform the following steps automatically:

  * Log in to LinkedIn using your configured credentials.
  * Search for profiles based on the `SEARCH_KEYWORD`.
  * Collect profile URLs and visit each one.
  * Extract data, download images, and save the output.

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

```
```
