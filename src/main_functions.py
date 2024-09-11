import requests
import asyncio
import aiohttp
import streamlit as st

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

stealth_company_urls_list = [
    "https://www.linkedin.com/company/warmstealth/",
    "https://www.linkedin.com/company/stealthmode14/",
    "https://www.linkedin.com/company/stealth-startup-51/",
    "https://www.linkedin.com/company/stealthaistartup/"
]


def proxy_employee_search(proxy_api_key, current_company_profile_url, past_company_profile_url):
    headers = {'Authorization': 'Bearer ' + proxy_api_key}
    api_endpoint = 'https://nubela.co/proxycurl/api/v2/search/person'

    params = {
        'country': 'IN',
        'current_company_linkedin_profile_url': current_company_profile_url,
        'past_company_linkedin_profile_url': past_company_profile_url,
        'page_size': '10'
    }
    logging.info(f"Making API request to {api_endpoint} for company {current_company_profile_url} from {past_company_profile_url}")
    response = requests.get(api_endpoint, params=params, headers=headers)

    # Parse the response
    if response.status_code == 200:
        response_data = response.json()
        profiles = [profile['linkedin_profile_url'] for profile in response_data['results']]
        total_results = response_data.get('total_result_count', len(profiles))
        logging.info(f"API request successful. Found {total_results} profiles.")

        return {
            'profiles': profiles,
            'total_results': total_results,
        }
    else:
        logging.error(f"API request failed with status code {response.status_code}")
        return {'error': f"Request failed with status code {response.status_code}"}
    

def linkedin_profile_scraper(api_key, linkedin_url):
    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
    querystring = {
        "linkedin_url": linkedin_url,
        "include_skills": "false",
        "include_certifications": "false",
        "include_publications": "false",
        "include_honors": "false",
        "include_volunteers": "false",
        "include_projects": "false",
        "include_patents": "false",
        "include_courses": "false",
        "include_organizations": "false",
        "include_company_public_url": "false"
    }
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    logging.info(f"Scraping LinkedIn profile: {linkedin_url}")
    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        response_data = response.json().get('data', {})

        # Profile fields with safe defaults if missing
        profile = {
            "first_name": response_data.get('first_name', ''),
            "last_name": response_data.get('last_name', ''),
            "full_name": response_data.get('full_name', ''),
            "headline": response_data.get('headline', ''),
            "linkedin_url": response_data.get('linkedin_url', ''),
            "job_title": response_data.get('job_title', ''),
            "follower_count": response_data.get('follower_count', ''),
            "connection_count": response_data.get('connection_count', ''),
            "city": response_data.get('city', ''),
            "location": response_data.get('location', ''),


            # Experience details
            "experience": [{
                "company": exp.get('company', ''),
                "company_linkedin_url": exp.get('company_linkedin_url', ''),
                "date_range": exp.get('date_range', ''),
                "duration": exp.get('duration', ''),
                "title": exp.get('title', '')
            } for exp in response_data.get('experiences', [])],

            # Education details
            "education": [{
                "school": edu.get('school', ''),
                "degree": edu.get('degree', ''),
                "field_of_study": edu.get('field_of_study', ''),
                "date_range": edu.get('date_range', '')
            } for edu in response_data.get('educations', [])]
        }
        logging.info(f"Successfully scraped LinkedIn profile: {linkedin_url}")
        return profile

    else:
        logging.error(f"Failed to scrape LinkedIn profile: {linkedin_url}. Status code: {response.status_code}")
        return {'error': f"Request failed with status code {response.status_code}"}
    
import csv
import os

def store_profiles_to_csv(profiles, filename=None):
    # Prompt user to save a file name if not provided
    if filename is None:
        filename = input("Enter the file name to save CSV (without .csv extension): ") + ".csv"

    # Check if file already exists and modify the filename if needed
    counter = 1
    original_filename = filename
    while os.path.isfile(filename):
        filename = f"{original_filename.split('.csv')[0]}_{counter}.csv"
        counter += 1
    logging.info(f"Saving profiles to CSV file: {filename}")
    # Write data to the CSV
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write headers
        writer.writerow([
            'Full Name', 'First Name', 'Last Name', 'Headline', 'LinkedIn URL',
            'Job Title', 'Follower Count', 'Connection Count', 'City', 'Location', 'Experience', 'Education'
        ])

        # Write each profile
        for profile in profiles:
            experience = "\n".join([f"{exp['company']} | {exp['title']} | {exp['date_range']} | {exp['duration']}"
                                    for exp in profile.get('experience', [])])
            education = "\n".join([f"{edu['school']} | {edu['degree']} | {edu['field_of_study']} | {edu['date_range']}"
                                   for edu in profile.get('education', [])])

            writer.writerow([
                profile.get('full_name', ''),
                profile.get('first_name', ''),
                profile.get('last_name', ''),
                profile.get('headline', ''),
                profile.get('linkedin_url', ''),
                profile.get('job_title', ''),
                profile.get('follower_count', ''),
                profile.get('connection_count', ''),
                profile.get('city', ''),
                profile.get('location', ''),
                experience,
                education
            ])

    print(f"Profiles saved to {filename}")

# Example Usage:
# profiles = [linkedin_profile_scraper(api_key, url1), linkedin_profile_scraper(api_key, url2), ...]
# store_profiles_to_csv(profiles)