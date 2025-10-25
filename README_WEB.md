# LinkedIn Profile Explorer Web Application

This web application allows you to browse and search through LinkedIn profiles collected by the LinkedIn scraper. The application provides a user-friendly interface to explore the profiles, view details, and search for specific individuals.

## Features

- **Search Functionality**: Search for profiles by name
- **Profile Listings**: View all scraped profiles in a responsive grid layout
- **Detailed Profile View**: See comprehensive information about each profile, including:
  - Profile picture
  - Basic information (name, title, company)
  - Work experience
  - Education history
  - Skills (if available)
  - Contact information (if available)
- **Direct Links**: Open LinkedIn profiles directly in LinkedIn

## Prerequisites

- Python 3.6 or higher
- The scraped LinkedIn data (CSV file and JSON files)
- Required Python packages (see `requirements_web.txt`)

## Installation

1. Ensure you have run the LinkedIn scraper and have the data in the `students_data` folder
2. Install the required packages:

```bash
pip install -r requirements_web.txt
```

3. Generate the default profile image (this will happen automatically when running the app, but you can run it manually):

```bash
python generate_default_image.py
```

## Running the Application

To start the web application, run:

```bash
python app.py
```

Then open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

## Application Structure

- `app.py`: Main application file containing Flask routes and data loading logic
- `templates/`: HTML templates for rendering pages
  - `layout.html`: Base template with shared layout elements
  - `index.html`: Home page with search and profile listing
  - `profile_detail.html`: Detailed view of a single profile
- `static/`: Static assets
  - `default-profile.jpg`: Default profile image used when no profile picture is available
- `generate_default_image.py`: Script to generate the default profile image

## Customization

You can customize the application by:

1. Modifying the templates in the `templates/` folder
2. Adjusting the styles in the CSS sections of the HTML files
3. Adding additional search functionality in `app.py`
4. Changing the default profile image generation in `generate_default_image.py`

## Data Privacy Considerations

This application is designed for educational purposes. When using LinkedIn profile data, make sure to:

1. Comply with LinkedIn's terms of service
2. Respect user privacy
3. Use the data only for lawful purposes
4. Consider adding password protection to the web application if deployed publicly

## Troubleshooting

If the application doesn't run properly:

1. Make sure the CSV file path is correct in `app.py`
2. Check that the profile data JSON files are in the correct location
3. Verify that all required Python packages are installed
4. Check the console for error messages that might indicate issues with file paths or missing data 