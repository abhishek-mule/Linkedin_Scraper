#!/usr/bin/env python
"""
LinkedIn Profile Explorer - Web Application Launcher
----------------------------------------------------
This script launches the LinkedIn Profile Explorer web application.
"""

import os
import subprocess
import webbrowser
import time
import sys

def check_requirements():
    """Check if required packages are installed."""
    try:
        import flask
        from PIL import Image
        return True
    except ImportError:
        return False

def install_requirements():
    """Install the required packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_web.txt"])
        return True
    except subprocess.CalledProcessError:
        print("Failed to install requirements. Please install them manually using:")
        print("pip install -r requirements_web.txt")
        return False

def check_data_exists():
    """Check if the scraped data exists."""
    # Check for the CSV file first
    if not os.path.exists("pec_profiles.csv"):
        print("Warning: 'pec_profiles.csv' file not found!")
        print("The application may not work properly without this data file.")
        return False
    
    # Check for the profiles directory
    if not os.path.exists("pec_profiles"):
        print("Warning: 'pec_profiles' directory not found!")
        print("The application will work with basic data, but detailed profiles may not display correctly.")
        return False
    
    # Check for profile JSON files
    json_files = [f for f in os.listdir("pec_profiles") if f.endswith(".json") and not f.endswith("_urls.json")]
    if not json_files:
        print("Warning: No profile JSON files found in 'pec_profiles' directory!")
        print("The application will work with basic data, but detailed profiles may not display correctly.")
    else:
        print(f"Found {len(json_files)} profile JSON files in 'pec_profiles' directory.")
    
    return True

def main():
    """Main function to launch the web application."""
    print("\n" + "="*60)
    print(" LinkedIn Profile Explorer - Web Application Launcher ")
    print("="*60 + "\n")
    
    # Check if requirements are installed
    if not check_requirements():
        print("Required packages are not installed.")
        if not install_requirements():
            return
        
    # Ensure static directory exists
    if not os.path.exists("static"):
        os.makedirs("static")
        print("Created 'static' directory.")
    
    # Generate default profile image if it doesn't exist
    if not os.path.exists("static/default-profile.jpg"):
        print("Generating default profile image...")
        try:
            import generate_default_image
            generate_default_image.generate_silhouette_avatar()
            print("Default profile image generated successfully.")
        except Exception as e:
            print(f"Warning: Failed to generate default profile image: {e}")
            print("The application will still run, but profile images may not display properly.")
    
    # Check if data exists
    check_data_exists()
    
    # Launch the web application
    print("\nStarting the LinkedIn Profile Explorer web application...")
    print("Press Ctrl+C to stop the application when you're done.\n")
    
    # Open web browser with a slight delay to ensure the server is running
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:5000")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the Flask application
    try:
        import app
        app.app.run(debug=False)
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as e:
        print(f"\nError starting application: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure app.py exists in the current directory.")
        print("2. Make sure the CSV file path is correct in app.py.")
        print("3. Check that all required Python packages are installed.")
        print("4. Make sure the profile data JSON files are in the correct location.")

if __name__ == "__main__":
    main() 