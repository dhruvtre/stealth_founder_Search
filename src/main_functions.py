#List of original imports
import requests
import asyncio
import aiohttp
import streamlit as st

#List of logging specific and email specific imports
import logging
import smtplib
from email.message import EmailMessage
import threading

async def proxy_employee_search_async(proxy_api_key, current_company_profile_url, past_company_profile_url):
    headers = {'Authorization': 'Bearer ' + proxy_api_key}
    api_endpoint = 'https://nubela.co/proxycurl/api/v2/search/person'

    params = {
        'country': 'IN',
        'current_company_linkedin_profile_url': current_company_profile_url,
        'past_company_linkedin_profile_url': past_company_profile_url,
        'page_size': '10'
    }
    
    logging.info(f"Making async API request to {api_endpoint} for company {current_company_profile_url} from {past_company_profile_url}")
    
    # Use aiohttp to make an async request
    async with aiohttp.ClientSession() as session:
        async with session.get(api_endpoint, headers=headers, params=params) as response:
            if response.status == 200:
                response_data = await response.json()  # Await the JSON response
                profiles = [profile['linkedin_profile_url'] for profile in response_data['results']]
                total_results = response_data.get('total_result_count', len(profiles))
                logging.info(f"Async API request successful. Found {total_results} profiles.")

                return {
                    'profiles': profiles,
                    'total_results': total_results,
                }
            else:
                logging.error(f"Async API request failed with status code {response.status}")
                return {'error': f"Request failed with status code {response.status}"}
    
async def search_all_stealth_companies(proxy_api_key, past_company_profile_url):
    # Create a list of async tasks for all company URLs
    tasks = []
    stealth_company_urls_list = [
    "https://www.linkedin.com/company/warmstealth/",
    "https://www.linkedin.com/company/stealthmode14/",
    "https://www.linkedin.com/company/stealth-startup-51/",
    "https://www.linkedin.com/company/stealthaistartup/"
    ]
    for current_company_url in stealth_company_urls_list:
        tasks.append(proxy_employee_search_async(proxy_api_key, current_company_url, past_company_profile_url))

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)
    logging.info(f"All async tasks completed for searching stealth companies.")

    # You can now process the results from all the concurrent API calls
    all_profiles = []
    for result in results:
        if 'error' not in result:
            all_profiles.extend(result['profiles'])  # Combine all found profiles into one list
        else:
            logging.error(f"Error occurred: {result['error']}")

    logging.info(f"Total profiles found across all companies: {len(all_profiles)}")
    return all_profiles  # Return the list of profiles or handle as needed

def run_search_all_companies_sync(proxy_api_key, past_company_profile_url):
    return asyncio.run(search_all_stealth_companies(proxy_api_key, past_company_profile_url))

async def linkedin_profile_scraper(api_key, linkedin_url):
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
    # Using aiohttp for asynchronous request
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=querystring) as response:
            if response.status == 200:
                response_data = await response.json()
                profile_data = response_data.get('data', {})

                # Profile fields with safe defaults if missing
                profile = {
                    "first_name": profile_data.get('first_name', ''),
                    "last_name": profile_data.get('last_name', ''),
                    "full_name": profile_data.get('full_name', ''),
                    "headline": profile_data.get('headline', ''),
                    "linkedin_url": profile_data.get('linkedin_url', ''),
                    "job_title": profile_data.get('job_title', ''),
                    "follower_count": profile_data.get('follower_count', ''),
                    "connection_count": profile_data.get('connection_count', ''),
                    "city": profile_data.get('city', ''),
                    "location": profile_data.get('location', ''),


            # Experience details
                    "experience": [{
                        "company": exp.get('company', ''),
                        "company_linkedin_url": exp.get('company_linkedin_url', ''),
                        "date_range": exp.get('date_range', ''),
                        "duration": exp.get('duration', ''),
                        "title": exp.get('title', '')
                    } for exp in profile_data.get('experiences', [])],

            # Education details
                    "education": [{
                        "school": edu.get('school', ''),
                        "degree": edu.get('degree', ''),
                        "field_of_study": edu.get('field_of_study', ''),
                        "date_range": edu.get('date_range', '')
                    } for edu in profile_data.get('educations', [])]
                }
                logging.info(f"Successfully scraped LinkedIn profile: {linkedin_url}")
                return profile

            else:
                logging.error(f"Failed to scrape LinkedIn profile: {linkedin_url}. Status code: {response.status}")
                return {'error': f"Request failed with status code {response.status}"}

async def scrape_multiple_profiles(api_key, linkedin_urls, batch_size=20):
    all_profiles = []
    
    # Split the LinkedIn URLs into batches of 20 (or the specified batch_size)
    for i in range(0, len(linkedin_urls), batch_size):
        batch_urls = linkedin_urls[i:i + batch_size]  # Get a batch of up to 20 URLs

        tasks = []
        # Create async tasks for each LinkedIn URL in the batch
        for linkedin_url in batch_urls:
            tasks.append(linkedin_profile_scraper(api_key, linkedin_url))

        # Execute the tasks concurrently
        results = await asyncio.gather(*tasks)

        # Process the results
        for result in results: 
            if isinstance(result, Exception): 
                logging.error(f"Error occurred during scraping: {str(result)}") 
            elif 'error' not in result: 
                all_profiles.append(result) # Append valid profile data 
            else: 
                logging.error(f"Error occurred: {result['error']}")

        logging.info(f"Processed batch {i // batch_size + 1}: {len(batch_urls)} profiles")

    logging.info(f"Total profiles scraped: {len(all_profiles)}")
    return all_profiles

def run_scrape_multiple_profiles_sync(api_key, linkedin_urls, batch_size=20):
    return asyncio.run(scrape_multiple_profiles(api_key, linkedin_urls, batch_size=20))

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
            'Job Title', 'Follower Count', 'Connection Count', 'City', 'Location', 'Experience', 'Education', 'is_repeat_founder', 'is_senior_operator'
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
                education,
                profile.get('is_repeat_founder', ''),
                profile.get('is_senior_operator', '')
            ])

    print(f"Profiles saved to {filename}")

# Example Usage:
# profiles = [linkedin_profile_scraper(api_key, url1), linkedin_profile_scraper(api_key, url2), ...]
# store_profiles_to_csv(profiles)

#function to record log contents and email it to admin

def send_log_via_email(sender_email, sender_password, receiver_email, log_content):
    """
    Sends the log content via email as a text attachment.
    """
    
    msg = EmailMessage()
    msg['Subject'] = 'Application Logs'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content('Please find the attached logs from the latest run of the application.')

    # Attach the log content as a text file if the log_content file is not empty
    if log_content:
        msg.add_attachment(log_content, subtype='plain', filename='app_logs.txt', charset='utf-8')
    else:
        logging.warning("No log content to attach.")

    # Send the email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        logging.info("Logs sent successfully via email.")
    except smtplib.SMTPAuthenticationError:
        logging.error("Authentication failed. Check your email credentials.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def send_log_via_email_async(sender_email, sender_password, receiver_email, log_content):
    """
    Sends the log content via email asynchronously.
    """
    threading.Thread(target=send_log_via_email, args=(sender_email, sender_password, receiver_email, log_content)).start()

from supabase import create_client, Client

# Initialize Supabase client
def create_supabase_client(supabase_url, supabase_key):
    supabase: Client = create_client(supabase_url, supabase_key)
    return supabase

def query_stealth_founder_table(supabase, past_company):
    try:
        response = supabase.table("Unicorn-Stealth-Founder-Profiles").select("*").eq("search_company", past_company).eq("is_founder", True).execute()

        # Check if the response contains data
        if response:
            logging.info(f"Successfully retrieved profiles for {past_company}.")
            list_of_profiles = response.data
            logging.info(f"Found {len(list_of_profiles)} for {past_company}.")
            return list_of_profiles
        else:
            logging.warning(f"No profiles found for {past_company}.")
            return []

    except Exception as e: 
        logging.error(f"Error querying profiles for {past_company}: {str(e)}")
        return []