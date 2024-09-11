import streamlit as st
import pandas as pd
from src.main_functions import proxy_employee_search, linkedin_profile_scraper, store_profiles_to_csv, stealth_company_urls_list
from src.top_unicorn_list import list_of_unicorns

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

proxycurl_api_key = st.secrets["proxycurl_api_key"]
rapidapi_api_key = st.secrets["rapidapi_api_key"]

# Function to cache CSV conversion
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

def display_profile_card(profile):
    with st.container(border=True):
        # Displaying basic profile information
        st.markdown(f"### {profile['full_name']}")
        st.markdown(f"**{profile['job_title']}**")
        st.markdown(f"📍 {profile['location']}")
        st.markdown(f"👥 Followers: {profile['follower_count']} | 🔗 Connections: {profile['connection_count']}")
        st.markdown(profile['headline'])
        st.markdown(f"[View LinkedIn Profile]({profile['linkedin_url']})")

        # Experience Section
        st.markdown("#### Experience")
        for exp in profile['experience'][:3]:  # Show only the top 3 experiences
            st.markdown(f"- **{exp['title']}** at **{exp['company']}** from {exp['date_range']} ({exp['duration']})")
        
        if len(profile['experience']) > 3:
            st.write(f"More experience available in the CSV download.")

        # Education Section
        st.markdown("#### Education")
        for edu in profile['education']:
            st.markdown(f"- **{edu['degree']}** in {edu['field_of_study']} | {edu['school']} ({edu['date_range']})")

    # Add spacing between cards
    st.markdown("---")

# Custom CSS for further styling
st.markdown("""
<style>
    .stContainer {
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
        background-color: #fff;
    }
    .stContainer > div > div > p {
        margin-bottom: 0.5rem;
    }
    .stContainer h3 {
        margin-bottom: 0.5rem;
    }
    .stContainer ul {
        margin-bottom: 0.5rem;
        padding-left: 1rem;
    }
    .stContainer .element-container {
        margin-bottom: 0.5rem;
    }
    h3, h4 {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for fixed sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            position: fixed;
            top: 0;
            height: 100vh;
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("assets/Group 5-2.png", width=150)  # Adjust the width as necessary

    # Add a short description under the logo
    st.markdown("""
        ### Stealth Founder Search & Tracking
        Use this tool to find and track stealth founders. Enter a company name and search for founders who have moved into stealth mode.
    """)

# Streamlit app title
st.title("Stealth Founder Search & Tracking")

# Sidebar or main input for selecting companies
st.subheader("Select a past company from the list")

# Dropdown or selection box for companies
past_company = st.selectbox("Select a stealth company:", [comp["name"] for comp in list_of_unicorns])

# Show selected company URL
past_company_url = next((comp["url"] for comp in list_of_unicorns if comp["name"] == past_company), None)

# Get the past company URL (example: Freshworks)
selected_company_urls = stealth_company_urls_list
linkedin_profile_list = []
total_linkedin_profiles_found = 0

# Button to trigger search
if st.button("Search"):
    logging.info(f"Initiating search for employees from {past_company} currently building in stealth.")
    st.write(f"Searching for employees from {past_company} currently building in stealth.")
    with st.spinner("Searching for profiles..."):
        if past_company_url:
            for url in selected_company_urls:
                logging.info(f"Searching stealth employees from {past_company} to {url}")
                search_results = proxy_employee_search(proxycurl_api_key, url, past_company_url)
                if 'error' not in search_results:
                    logging.info(f"Found {search_results['total_results']} profiles at {url}.")
                    total_linkedin_profiles_found = total_linkedin_profiles_found + search_results['total_results']
                    for item in search_results['profiles']:
                        linkedin_profile_list.append(item)
                else:
                    st.error(f"Error: {search_results['error']}")
                    logging.error(f"Error while searching {url}: {search_results['error']}")
        
            st.write(f"Found {total_linkedin_profiles_found} profiles.")
            logging.info(f"Search completed. Total profiles found: {total_linkedin_profiles_found}")
            
    with st.spinner("Scraping individual profiles."):
        complete_profiles = []
        for item in linkedin_profile_list:
            logging.info(f"Scraping profile: {item}")
            profile = linkedin_profile_scraper(rapidapi_api_key, item)
            if 'error' not in profile:
                complete_profiles.append(profile)
                logging.info(f"Successfully scraped profile: {item}")
            else:
                logging.error(f"Failed to scrape profile: {item}. Error: {profile['error']}")
        
    # Display the profiles
    if complete_profiles:
        for profile in complete_profiles:
            display_profile_card(profile)

        # Allow users to save profiles as CSV
    
        df = pd.DataFrame(complete_profiles)

        # Convert DataFrame to CSV using cached function
        csv = convert_df_to_csv(df)

        # Provide a download button
        st.download_button(
                label="Download Profiles as CSV",
                data=csv,
                file_name=f"{past_company}_stealth_founders_profiles.csv",
                mime="text/csv",
            )
    else:
        st.warning("No profiles found for the selected company.")
else:
    st.error("Please select a valid company.")
