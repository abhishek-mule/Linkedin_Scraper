import os
import csv
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from generate_default_image import generate_silhouette_avatar
import threading
import time
from datetime import datetime

# Import LinkedIn scraping functions
from search_specific_students import (
    setup_webdriver, 
    login_to_linkedin,
    format_name,
    search_for_specific_profile,
    enhanced_scrape_profile_data,
    verify_priyadarshini_profile,
    log_message,
    check_for_captcha_or_restriction,
    handle_captcha
)

app = Flask(__name__)
app.secret_key = "linkedin_scraper_secret_key"

# Configuration
CSV_FILE = "pec_profiles.csv"
PROFILES_FOLDER = "pec_profiles"
LINKEDIN_EMAIL = "cavad48528@cotigz.com"  # LinkedIn login email
LINKEDIN_PASSWORD = "Pass@cavad48528"  # LinkedIn login password
COLLEGE_COMPANY = "Priyadarshini College of Engineering, Hingna Road"

# Maintain a global webdriver instance
global_driver = None
driver_lock = threading.Lock()
last_activity_time = datetime.now()

def initialize_driver():
    """Initialize the global webdriver if it doesn't exist"""
    global global_driver, last_activity_time
    
    with driver_lock:
        if global_driver is None:
            try:
                print("Initializing LinkedIn webdriver...")
                global_driver = setup_webdriver()
                
                # Login to LinkedIn
                if not login_to_linkedin(global_driver, LINKEDIN_EMAIL, LINKEDIN_PASSWORD):
                    print("Failed to login to LinkedIn")
                    if global_driver:
                        global_driver.quit()
                    global_driver = None
                    return None
                
                last_activity_time = datetime.now()
                print("LinkedIn webdriver initialized successfully")
            except Exception as e:
                print(f"Error initializing webdriver: {e}")
                if global_driver:
                    try:
                        global_driver.quit()
                    except:
                        pass
                global_driver = None
                return None
    
    return global_driver

def shutdown_driver():
    """Shutdown the global webdriver"""
    global global_driver
    
    with driver_lock:
        if global_driver:
            try:
                global_driver.quit()
            except:
                pass
            global_driver = None

def update_activity():
    """Update the last activity time"""
    global last_activity_time
    last_activity_time = datetime.now()

def check_driver_timeout():
    """Check if the driver has been inactive for too long and should be reset"""
    global last_activity_time
    
    # If inactive for more than 30 minutes, reset the driver
    if (datetime.now() - last_activity_time).total_seconds() > 1800:
        print("Driver timeout detected, resetting...")
        shutdown_driver()
        return True
    return False

def load_profiles_from_csv():
    """Load all profiles from the CSV file"""
    profiles = []
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up the profile data
                profile = {
                    'id': row.get('ID', ''),
                    'name': row.get('Name', ''),
                    'url': row.get('Profile URL', ''),
                    'about': row.get('About', ''),
                    'role_type': row.get('Role Type', 'Student'),  # Faculty or Student
                    'current_company': row.get('Current Company', ''),
                    'current_position': row.get('Current Position', ''),
                    'current_location': row.get('Location', ''),
                    'current_duration': '',  # Not in new CSV format
                    'all_experiences': row.get('Current Position', '') + ' at ' + row.get('Current Company', ''),
                    'current_education': '',  # Will be parsed from All Education Details
                    'current_degree': '',     # Will be parsed from All Education Details
                    'all_education': row.get('All Education Details', ''),
                    'email': row.get('Email', ''),
                    'phone': row.get('Phone', ''),
                    'website': row.get('Website', ''),
                    'skills': row.get('Skills', ''),
                    'profile_pic': row.get('Profile Picture Path', '')
                }
                
                # Parse first education entry for current education display
                if profile['all_education']:
                    edu_parts = profile['all_education'].split('|')[0].strip().split(' at ')
                    if len(edu_parts) >= 2:
                        profile['current_degree'] = edu_parts[0].strip()
                        profile['current_education'] = edu_parts[1].split(',')[0].strip()
                
                # Create profile image URL
                if profile['profile_pic'] and os.path.exists(profile['profile_pic']):
                    profile['image_url'] = url_for('profile_image', profile_id=profile['id'])
                else:
                    profile['image_url'] = url_for('static', filename='default-profile.jpg')
                
                profiles.append(profile)
        
        return profiles
    except Exception as e:
        print(f"Error loading profiles from CSV: {e}")
        return []

def search_profiles(filters=None):
    """Search profiles by various fields with advanced filtering
    
    Args:
        filters (dict): A dictionary containing search filters with keys:
            - name: Filter by profile name
            - company: Filter by company name
            - position: Filter by job position
            - education: Filter by education institution or degree
            - location: Filter by location
            - skills: Filter by skills
            - role_type: Filter by role type (Faculty or Student)
    
    Returns:
        list: List of profiles matching the search criteria
    """
    profiles = load_profiles_from_csv()
    
    # If no filters provided, return all profiles
    if not filters or not any(filters.values()):
        return profiles
    
    filtered_profiles = profiles.copy()
    
    # Filter by role_type if specified
    if filters.get('role_type'):
        filtered_profiles = [p for p in filtered_profiles 
                        if p.get('role_type', '').lower() == filters['role_type'].lower()]
    
    # Filter by name
    if filters.get('name'):
        name_query = filters['name'].lower().strip()
        name_matches = []
        for profile in filtered_profiles:
            profile_name = profile.get('name', '').lower()
            if name_query in profile_name:
                name_matches.append(profile)
        filtered_profiles = name_matches
    
    # Filter by company
    if filters.get('company'):
        company_query = filters['company'].lower().strip()
        company_matches = []
        for profile in filtered_profiles:
            company = profile.get('current_company', '').lower()
            if company_query in company:
                company_matches.append(profile)
        filtered_profiles = company_matches
    
    # Filter by position
    if filters.get('position'):
        position_query = filters['position'].lower().strip()
        position_matches = []
        for profile in filtered_profiles:
            position = profile.get('current_position', '').lower()
            experiences = profile.get('all_experiences', '').lower()
            if position_query in position or position_query in experiences:
                position_matches.append(profile)
        filtered_profiles = position_matches
    
    # Filter by education
    if filters.get('education'):
        education_query = filters['education'].lower().strip()
        education_matches = []
        for profile in filtered_profiles:
            education = profile.get('current_education', '').lower()
            all_education = profile.get('all_education', '').lower()
            degree = profile.get('current_degree', '').lower()
            if (education_query in education or 
                education_query in all_education or 
                education_query in degree):
                education_matches.append(profile)
        filtered_profiles = education_matches
    
    # Filter by location
    if filters.get('location'):
        location_query = filters['location'].lower().strip()
        location_matches = []
        for profile in filtered_profiles:
            location = profile.get('current_location', '').lower()
            if location_query in location:
                location_matches.append(profile)
        filtered_profiles = location_matches
    
    # Filter by skills
    if filters.get('skills'):
        skills_query = filters['skills'].lower().strip()
        skills_matches = []
        for profile in filtered_profiles:
            skills = profile.get('skills', '').lower()
            if skills_query in skills:
                skills_matches.append(profile)
        filtered_profiles = skills_matches
    
    return filtered_profiles

def get_profile_by_id(profile_id):
    """Get a specific profile by ID"""
    profiles = load_profiles_from_csv()
    
    for profile in profiles:
        if profile['id'] == profile_id:
            return profile
    
    return None

@app.route('/')
def index():
    """Homepage with search functionality"""
    # Collect search filters from request args
    search_filters = {
        'name': request.args.get('name', ''),
        'company': request.args.get('company', ''),
        'position': request.args.get('position', ''),
        'education': request.args.get('education', ''),
        'location': request.args.get('location', ''),
        'skills': request.args.get('skills', ''),
        'role_type': request.args.get('role_type', '')
    }
    
    # Search for profiles matching the filters
    profiles = search_profiles(search_filters)
    
    return render_template('index.html', profiles=profiles, request=request)

@app.route('/simple')
def index_simple():
    """Simple homepage with search functionality"""
    query = request.args.get('q', '')
    # Use legacy search approach for simple view
    profiles = search_profiles({'name': query})
    return render_template('index_simple.html', profiles=profiles, query=query)

@app.route('/search_linkedin', methods=['GET', 'POST'])
def search_linkedin():
    """Direct LinkedIn profile search interface and handler."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if not full_name:
            flash('Please enter a name to search.', 'warning')
            return render_template('search_linkedin.html', search_status='not_started')
        
        try:
            # Create directory for search results if it doesn't exist
            results_dir = 'linkedin_search_results'
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            # Generate a timestamp for this search
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Store search request in a file
            search_request = {
                'timestamp': timestamp,
                'search_name': full_name,
                'status': 'pending'
            }
            
            request_file = os.path.join(results_dir, f'request_{timestamp}.json')
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(search_request, f)
            
            # For immediate feedback, return a waiting template
            # In a real implementation, this would trigger a background task
            # Here we'll simulate it with a redirect to a result that will be generated
            
            # Start the search in a separate process
            import subprocess
            subprocess.Popen(['python', 'search_specific_students.py', 
                             '--name', full_name, 
                             '--timestamp', timestamp], 
                             shell=True)
            
            flash(f'Searching for "{full_name}" on LinkedIn...', 'info')
            return render_template('search_linkedin.html', 
                                  search_name=full_name,
                                  search_status='searching')
        
        except Exception as e:
            flash(f'Error starting search: {str(e)}', 'danger')
            app.logger.error(f"Search error: {str(e)}")
            return render_template('search_linkedin.html', 
                                  search_name=full_name,
                                  search_status='error',
                                  error_message=str(e))
    
    # GET request - just show the search form
    return render_template('search_linkedin.html', search_status='not_started')

def perform_linkedin_search(search_name):
    """Perform a LinkedIn search for the given name
    
    Args:
        search_name (str): The name to search for on LinkedIn
    
    Returns:
        dict: A dictionary with search results including status and profile data
    """
    global global_driver
    result = {
        'status': 'searching',
        'message': f'Searching LinkedIn for "{search_name}"...',
        'profile_data': None,
        'error': None,
        'search_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Check if driver needs to be reset due to inactivity
    if check_driver_timeout():
        result['status'] = 'error'
        result['message'] = 'Search session timed out. Please try again.'
        result['error'] = 'Session timeout'
        return result
    
    try:
        # Initialize or get the global driver
        driver = initialize_driver()
        if not driver:
            result['status'] = 'error'
            result['message'] = 'Failed to initialize LinkedIn browser. Please try again later.'
            result['error'] = 'Driver initialization failed'
            return result
        
        # Update the activity timestamp
        update_activity()
        
        # Format the name for searching
        formatted_name = format_name(search_name) if len(search_name.split()) > 1 else search_name
        
        # Search for the profile
        profile_url = search_for_specific_profile(driver, formatted_name)
        
        if not profile_url:
            result['status'] = 'not_found'
            result['message'] = f'No LinkedIn profile found for "{search_name}"'
            return result
        
        # Generate a unique profile ID
        profile_id = f"search_{int(time.time())}"
        
        # Scrape profile data
        profile_data = enhanced_scrape_profile_data(driver, profile_url, profile_id)
        
        if not profile_data:
            result['status'] = 'error'
            result['message'] = f'Found profile at {profile_url}, but failed to extract data'
            result['error'] = 'Data extraction failed'
            return result
        
        # Add the search name to the profile data
        profile_data['search_name'] = search_name
        profile_data['formatted_name'] = formatted_name
        
        # Verify if it's a Priyadarshini College profile
        profile_data = verify_priyadarshini_profile(profile_data)
        
        # Set success status
        result['status'] = 'success'
        result['message'] = f'Successfully found and extracted profile data for "{search_name}"'
        result['profile_data'] = profile_data
        result['profile_url'] = profile_url
        
        # Update activity timestamp
        update_activity()
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        result['status'] = 'error'
        result['message'] = f'Error searching LinkedIn: {str(e)}'
        result['error'] = str(e)
        
        # Take a screenshot if possible
        try:
            if global_driver:
                error_ss = os.path.join('static', f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                global_driver.save_screenshot(error_ss)
                result['error_screenshot'] = error_ss
        except:
            pass
            
        return result

@app.route('/profile/<profile_id>')
def profile_detail(profile_id):
    """Detail page for a specific profile"""
    profile = get_profile_by_id(profile_id)
    
    if not profile:
        flash("Profile not found", "error")
        return redirect(url_for('index'))
    
    # Try to load more detailed data from JSON file
    json_file = os.path.join(PROFILES_FOLDER, f"{profile_id}_data.json")
    detailed_data = {}
    
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                detailed_data = json.load(f)
            
            # Check if experiences and educations are properly formatted
            if 'experiences' in detailed_data and detailed_data['experiences'] is None:
                detailed_data['experiences'] = []
            
            if 'educations' in detailed_data and detailed_data['educations'] is None:
                detailed_data['educations'] = []
                
        except Exception as e:
            flash(f"Error loading detailed profile data: {e}", "warning")
            print(f"Error loading JSON data for profile {profile_id}: {e}")
    else:
        # If JSON file doesn't exist, create a basic structure from CSV data
        detailed_data = {
            'id': profile['id'],
            'name': profile['name'],
            'url': profile['url'],
            'about': [profile['about']] if profile['about'] else [],
            'experiences': [],
            'educations': [],
            'profile_pic': profile['profile_pic']
        }
        
        # If we have experience data in CSV, parse it
        if profile['all_experiences']:
            for exp_text in profile['all_experiences'].split('|'):
                exp_text = exp_text.strip()
                if exp_text:
                    detailed_data['experiences'].append({
                        'title': profile['current_position'] or '',
                        'company': profile['current_company'] or '',
                        'description': exp_text
                    })
        
        # If we have education data in CSV, parse it
        if profile['all_education']:
            for edu_text in profile['all_education'].split('|'):
                edu_text = edu_text.strip()
                if edu_text:
                    detailed_data['educations'].append({
                        'institution_name': profile['current_education'] or '',
                        'degree': profile['current_degree'] or '',
                        'description': edu_text
                    })
    
    return render_template('profile_detail.html', profile=profile, detailed_data=detailed_data)

@app.route('/profile/image/<profile_id>')
def profile_image(profile_id):
    """Serve the profile image directly from the original location"""
    profile = get_profile_by_id(profile_id)
    
    if profile and profile['profile_pic'] and os.path.exists(profile['profile_pic']):
        return send_file(profile['profile_pic'], mimetype='image/jpeg')
    else:
        # Return the default profile image
        return send_file('static/default-profile.jpg', mimetype='image/jpeg')

@app.route('/linkedin_result/<timestamp>')
def linkedin_result(timestamp):
    """Display LinkedIn search result data for a specific search timestamp."""
    try:
        # Check if the result file exists
        result_file = os.path.join('linkedin_search_results', f'result_{timestamp}.json')
        if not os.path.exists(result_file):
            flash('Search result not found.', 'danger')
            return redirect(url_for('search_linkedin'))
        
        # Load the search result data
        with open(result_file, 'r', encoding='utf-8') as f:
            search_result = json.load(f)
        
        return render_template('search_linkedin.html', 
                              search_name=search_result.get('search_name', ''),
                              search_result=search_result)
    except Exception as e:
        flash(f'Error loading search result: {str(e)}', 'danger')
        return redirect(url_for('search_linkedin'))

@app.route('/save_linkedin_profile', methods=['POST'])
def save_linkedin_profile():
    """Save a LinkedIn profile to the PEC profiles database."""
    try:
        profile_data_json = request.form.get('profile_data')
        if not profile_data_json:
            flash('No profile data provided.', 'danger')
            return redirect(url_for('search_linkedin'))
        
        # Parse the JSON data
        profile_data = json.loads(profile_data_json)
        
        # Prepare data for CSV
        csv_data = {
            'Name': profile_data.get('name', ''),
            'Role': 'Student' if profile_data.get('role_type') == 'student' else 'Faculty',
            'LinkedIn URL': profile_data.get('linkedin_url', ''),
            'Current Company': profile_data.get('current_company', ''),
            'Current Position': profile_data.get('current_position', ''),
            'Location': profile_data.get('location', ''),
            'About': profile_data.get('about', ''),
            'Skills': profile_data.get('skills', ''),
            'Profile Image': profile_data.get('profile_pic', ''),
            'Email': profile_data.get('email', ''),
            'Phone': profile_data.get('phone', ''),
            'Graduation Year': profile_data.get('graduation_year', ''),
            'Department': profile_data.get('department', '')
        }
        
        # Check if the profiles directory exists
        profiles_dir = 'pec_profiles'
        if not os.path.exists(profiles_dir):
            os.makedirs(profiles_dir)
        
        # Check if the CSV file exists
        csv_file = os.path.join(profiles_dir, 'pec_profiles.csv')
        file_exists = os.path.isfile(csv_file)
        
        # Write to CSV file
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data.keys())
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(csv_data)
        
        # Process experiences (if available) to a separate CSV
        if profile_data.get('experiences'):
            experiences_csv = os.path.join(profiles_dir, 'experiences.csv')
            exp_exists = os.path.isfile(experiences_csv)
            
            exp_fieldnames = ['Name', 'Title', 'Company', 'Date Range', 'Location', 'Description']
            
            with open(experiences_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=exp_fieldnames)
                
                if not exp_exists:
                    writer.writeheader()
                
                for exp in profile_data.get('experiences', []):
                    writer.writerow({
                        'Name': profile_data.get('name', ''),
                        'Title': exp.get('title', ''),
                        'Company': exp.get('company', ''),
                        'Date Range': exp.get('date_range', ''),
                        'Location': exp.get('location', ''),
                        'Description': exp.get('description', '')
                    })
        
        # Process educations (if available) to a separate CSV
        if profile_data.get('educations'):
            educations_csv = os.path.join(profiles_dir, 'educations.csv')
            edu_exists = os.path.isfile(educations_csv)
            
            edu_fieldnames = ['Name', 'Institution', 'Degree', 'Date Range', 'Description']
            
            with open(educations_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=edu_fieldnames)
                
                if not edu_exists:
                    writer.writeheader()
                
                for edu in profile_data.get('educations', []):
                    writer.writerow({
                        'Name': profile_data.get('name', ''),
                        'Institution': edu.get('institution_name', ''),
                        'Degree': edu.get('degree', ''),
                        'Date Range': edu.get('date_range', ''),
                        'Description': edu.get('description', '')
                    })
        
        flash(f'Profile for {profile_data.get("name")} successfully saved to database!', 'success')
        return redirect(url_for('search_linkedin'))
        
    except Exception as e:
        flash(f'Error saving profile: {str(e)}', 'danger')
        return redirect(url_for('search_linkedin'))

@app.teardown_appcontext
def cleanup(exception=None):
    """Clean up resources when the application context ends"""
    pass  # We handle driver shutdown separately

if __name__ == '__main__':
    # Ensure the static directory exists
    os.makedirs('static', exist_ok=True)
    
    # Generate default profile image if it doesn't exist
    if not os.path.exists('static/default-profile.jpg'):
        generate_silhouette_avatar()
    
    try:
        app.run(debug=True)
    finally:
        # Ensure driver is shut down when app exits
        shutdown_driver() 