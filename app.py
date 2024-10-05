import streamlit as st
import pandas as pd
from src.main_functions import *
from src.top_unicorn_list import list_of_unicorns
import logging
import sys
import io
from logging import StreamHandler
import time

# Set up logging if not already configured
if 'log_initialized' not in st.session_state:
    st.session_state['log_stream'] = io.StringIO()
    log_stream = st.session_state['log_stream']

    # Set up the in-memory handler
    memory_handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    memory_handler.setFormatter(formatter)

    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(memory_handler)

    # Create a console handler for real-time logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Logger initialized")

    # Mark logging as initialized
    st.session_state['log_initialized'] = True

else:
    # Retrieve the existing log_stream
    log_stream = st.session_state['log_stream']
    logger = logging.getLogger()


proxycurl_api_key = st.secrets["proxycurl_api_key"]
rapidapi_api_key = st.secrets["rapidapi_api_key"]
supabase_url = st.secrets["supabase_url"]
supabase_key = st.secrets["supabase_key"]

# Function to cache CSV conversion
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

supabase_client = create_supabase_client(supabase_url, supabase_key)

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
    start_time = time.time()
    logging.info("Search button pressed by user.")

    with st.spinner("Searching for profiles..."):
        # Create a dictionary for easier lookup
        company_url_lookup = {comp["company_name"]: comp["company_linkedin_url"] for comp in list_of_unicorns}
        
        for company_name in past_company_name:
            company_url = company_url_lookup[company_name]
            list_of_profiles_retrieved = query_stealth_founder_table(supabase_client, company_name)
            if len(list_of_profiles_retrieved):
                linkedin_profile_list.extend(list_of_profiles_retrieved)
                time.sleep(0.7)
                st.success(f"Profiles found for company {company_name}")
            else:
                time.sleep(0.7)
                st.error(f"No profiles found or an error occurred for company {company_name}.")
        logging.info(f"Search process completed in {time.time() - start_time} seconds.")
        st.write(f"Found {len(linkedin_profile_list)} profiles.")
        logging.info(f"Search completed. Total profiles found: {len(linkedin_profile_list)}")
    if len(linkedin_profile_list):
        for profile in linkedin_profile_list:
            display_profile_card(profile)
    
        logging.info(f"Displaying {len(linkedin_profile_list)} profiles to user.")
        # Allow users to save profiles as CSV
        df = pd.DataFrame(linkedin_profile_list)

        # Convert DataFrame to CSV using cached function
        csv = convert_df_to_csv(df)

        # Provide a download button
        st.download_button(
                label="Download Profiles as CSV",
                data=csv,
                file_name=f"stealth_founders_profiles.csv",
                mime="text/csv",
            )
    log_contents = st.session_state['log_stream'].getvalue()
    if log_contents:
            send_log_via_email_async(
                    sender_email=st.secrets["sender_email"],
                    sender_password=st.secrets["sender_password"],
                    receiver_email=st.secrets["receiver_email"],
                    log_content=log_contents
                )
            logging.info("Logs sent after scraping.")
            st.session_state['log_stream'].truncate(0)
            st.session_state['log_stream'].seek(0)
    else:
            logging.warning("No logs captured to send via email.")  
else:
    st.info("Get started by selecting up to three companies.")
