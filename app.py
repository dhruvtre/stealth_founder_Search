import streamlit as st
import pandas as pd
from src.main_functions import *
from src.top_unicorn_list import list_of_unicorns

import logging
start_time = time.time()
if 'logs_sent' not in st.session_state:
    st.session_state.logs_sent = False

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    st.image("assets/Group 5-2.png", width=150) 

    
    st.markdown("""
        ## 🚀 Dealey Founder Database
        Extract valuable signals and find the "needles in the haystack." 
        
        Start your search for stealth founders from our list of 120 Indian Unicorns. More signals being added soon! 🔍
    """)

# Streamlit app title
st.title("🚨 Discover & Track Stealth Founders")

st.markdown("""#### Select upto 3 unicorns from the list. Dealey will find founders building in stealth from those companies.""")

# Multiselect option for choosing past companies.
past_company_name = st.multiselect("Choose past companies to get started", [comp["company_name"] for comp in list_of_unicorns], default=None, help="You can pick up to three companies at once to get started.", max_selections=3, placeholder="Choose upto three companies to get started.", label_visibility="visible")
logging.info(f"User selected {len(past_company_name)} companies for search: {past_company_name}")

# Get the past company URL (example: Freshworks)
linkedin_profile_list = []
total_linkedin_profiles_found = 0

# Button to trigger search
if st.button("Search"):
    logging.info("Search button pressed by user.")
    # Create a dictionary for easier lookup
    company_url_lookup = {comp["company_name"]: comp["company_linkedin_url"] for comp in list_of_unicorns}

    with st.spinner("Searching for profiles..."):
        for company_name in past_company_name:
            company_url = company_url_lookup[company_name] 
            logging.info(f"Initiating search for employees from {company_name} currently building in stealth.")
            st.write(f"Searching for employees from {company_name} currently building in stealth.")
            if company_url:
                logging.info(f"Searching stealth employees from {company_url} across all stealth companies.")
                search_results = run_search_all_companies_sync(proxycurl_api_key, company_url)

                if search_results:
                    linkedin_profile_list.extend(search_results)
                    total_linkedin_profiles_found = len(search_results)
                    logging.info(f"Found {total_linkedin_profiles_found} profiles.")
                else:
                    st.error("No profiles found or an error occurred.")
    logging.info(f"Search process completed in {time.time() - start_time} seconds.")
    linkedin_profile_list = list(set(linkedin_profile_list))
    st.write(f"Found {len(linkedin_profile_list)} profiles.")
    logging.info(f"Search completed. Total profiles found: {len(linkedin_profile_list)}")
            
    with st.spinner("Scraping individual profiles."):
        complete_profiles = run_scrape_multiple_profiles_sync(rapidapi_api_key, linkedin_profile_list)
        
    # Display the profiles
    if complete_profiles:
        logging.info(f"Profile Scraping process completed in {time.time() - start_time} seconds.")
        for profile in complete_profiles:
            display_profile_card(profile)
        logging.info(f"Displaying {len(complete_profiles)} profiles to user.")

        # Allow users to save profiles as CSV
    
        df = pd.DataFrame(complete_profiles)

        # Convert DataFrame to CSV using cached function
        csv = convert_df_to_csv(df)

        # Provide a download button
        st.download_button(
                label="Download Profiles as CSV",
                data=csv,
                file_name=f"stealth_founders_profiles.csv",
                mime="text/csv",
            )
        
        if not st.session_state.logs_sent:
            log_contents = log_stream.getvalue()
            if log_contents:
                send_log_via_email_async(
                    sender_email=st.secrets["sender_email"],
                    sender_password=st.secrets["sender_password"],
                    receiver_email=st.secrets["receiver_email"],
                    log_content=log_contents
                )
                logging.info("Logs sent after scraping.")
                st.session_state.logs_sent = True
                log_stream.truncate(0)
                log_stream.seek(0)
            else:
                logging.warning("No logs captured to send via email.")
    else:
        st.warning("No profiles found for the selected company.")
else:
    st.error("Please select a valid company.")
