#!/usr/bin/env python
"""
LinkedIn Profile Search Runner
-----------------------------
This script runs the LinkedIn profile search for Priyadarshini College students
with improved error handling and user guidance.
"""

import os
import sys
import subprocess
import time
import webbrowser

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        "selenium",
        "beautifulsoup4", 
        "webdriver-manager"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_requirements(packages):
    """Install the missing required packages"""
    print("Installing required packages...")
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}. Please install it manually using:")
            print(f"pip install {package}")
            return False
    
    return True

def open_linkedin_manually():
    """Open LinkedIn in a browser for manual login if needed"""
    print("\nOpening LinkedIn in your browser for manual login...")
    print("Please log in to your LinkedIn account in the browser window.")
    print("This will help resolve any CAPTCHA or security verification issues.")
    
    webbrowser.open("https://www.linkedin.com/login")
    
    input("\nAfter logging in, press Enter to continue...\n")

def run_search_script():
    """Run the LinkedIn search script"""
    script_path = "search_specific_students.py"
    
    if not os.path.exists(script_path):
        print(f"Error: Script file {script_path} not found!")
        return False
    
    print("\nStarting LinkedIn profile search...")
    print("Note: If the script encounters a CAPTCHA, you will need to solve it manually.")
    print("The browser window will open and you'll need to verify your identity.\n")
    
    try:
        subprocess.check_call([sys.executable, script_path])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        return False
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
        return False

def handle_captcha_instructions():
    """Provide instructions for handling CAPTCHA challenges"""
    print("\n" + "="*60)
    print(" HANDLING CAPTCHA CHALLENGES ")
    print("="*60)
    print("LinkedIn may present CAPTCHA challenges to verify you're human.")
    print("If you see a CAPTCHA during script execution:")
    print("1. Complete the CAPTCHA in the browser window that appears")
    print("2. After solving the CAPTCHA, the script will continue automatically")
    print("3. If multiple CAPTCHAs appear, you may need to manually log in")
    print("\nIf the script gets stuck waiting for CAPTCHA resolution:")
    print("1. Restart this runner script")
    print("2. When prompted, choose to log in manually first")
    print("3. The script will resume from where it left off\n")

def main():
    print("\n" + "="*60)
    print(" LinkedIn Profile Search for Priyadarshini College Students ")
    print("="*60 + "\n")
    
    # Check if required packages are installed
    missing_packages = check_requirements()
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        if not install_requirements(missing_packages):
            print("Failed to install all required packages. Exiting...")
            return
    
    # Display CAPTCHA handling instructions
    handle_captcha_instructions()
    
    # Ask if user wants to log in manually first
    manual_login = input("Do you want to log in to LinkedIn manually first? (y/n): ").strip().lower()
    if manual_login == 'y':
        open_linkedin_manually()
    
    # Run the search script
    success = run_search_script()
    
    if success:
        print("\nLinkedIn profile search completed successfully!")
        
        # Check if output folder exists and has files
        output_folder = "pec_specific_students"
        if os.path.exists(output_folder) and os.listdir(output_folder):
            print(f"\nResults have been saved to the '{output_folder}' folder.")
            
            csv_file = os.path.join(output_folder, "pec_specific_students.csv")
            if os.path.exists(csv_file):
                print(f"The main CSV file with all results is: {csv_file}")
                
                # Ask if user wants to open the results
                open_results = input("\nDo you want to open the results folder? (y/n): ").strip().lower()
                if open_results == 'y':
                    os.startfile(os.path.abspath(output_folder)) if sys.platform == 'win32' else subprocess.call(['open', output_folder])
        else:
            print("No results were found or saved.")
    else:
        print("\nLinkedIn profile search encountered errors.")
        print("Check the output for details on what went wrong.")
        print("You can try running the script again with manual login to resolve any issues.")

if __name__ == "__main__":
    main() 