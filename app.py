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
    # Create StringIO for capturing logs
    st.session_state['log_stream'] = io.StringIO()
    log_stream = st.session_state['log_stream']

    # Create a custom logger
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent messages from propagating to the root logger

    # Set up the in-memory handler
    memory_handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    memory_handler.setFormatter(formatter)
    logger.addHandler(memory_handler)

    # Create a console handler for real-time logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Logger initialized")

    # Mark logging as initialized
    st.session_state['logger'] = logger
    st.session_state['log_initialized'] = True

else:
    # Retrieve the existing logger and log_stream
    logger = st.session_state['logger']
    log_stream = st.session_state['log_stream']


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
    # Custom CSS for styling
    st.markdown("""
    <style>
    .profile-container {
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        background-color: #ffffff;
    }
    .profile-container h3 {
        color: #2c3e50;
        margin: 0 0 0.5rem 0;
        font-size: 1.6rem;
        font-weight: 600;
    }
    .profile-container h4 {
        color: #34495e;
        margin: 1.5rem 0 0.5rem 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    .profile-container p {
        margin: 0 0 0.8rem 0;
        font-size: 0.95rem;
        line-height: 1.5;
        color: #555;
    }
    .profile-container ul {
        margin: 0 0 1rem 0;
        padding-left: 1.2rem;
    }
    .profile-container li {
        margin-bottom: 0.6rem;
        font-size: 0.9rem;
        line-height: 1.4;
        color: #555;
    }
    .label-container {
        margin-bottom: 0.8rem;
    }
    .label {
    display: inline-block;
    padding: 0.3em 0.6em;
    font-size: 0.7rem;
    font-weight: 600;
    color: #FFFFFF;
    border-radius: 50px;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}
.label-role { background-color: #4A69BD; }
.label-senior { background-color: #52BE80; }
.label-repeat { background-color: #A569BD; }
    .profile-container a {
        color: #3498db;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    .profile-container a:hover {
        color: #2980b9;
        text-decoration: underline;
    }
    .more-info {
        font-style: italic;
        color: #7f8c8d;
        font-size: 0.85rem;
    }
    .profile-divider {
    border-top: 1px solid #e0e0e0;
    margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Build the HTML content
    html_content = '<div class="profile-container">'
    
    # Full name
    html_content += f"<h3>{profile['first_name']} {profile['last_name']}</h3>"
    
    # Labels container
    labels_html = '<div class="label-container">'
    
    # Role at company searched
    if 'role_at_company_searched' in profile and profile['role_at_company_searched']:
        labels_html += f'<span class="label label-role">{profile["role_at_company_searched"]}</span>'
    
    # Key labels
    if profile.get('is_senior_operator'):
        labels_html += '<span class="label label-senior">Senior Operator</span>'
    if profile.get('is_repeat_founder'):
        labels_html += '<span class="label label-repeat">Repeat Founder</span>'
    
    labels_html += '</div>'
    html_content += labels_html
    
    # Location
    if profile.get('location'):
        html_content += f'<p>📍 {profile["location"]}</p>'
    
    # LinkedIn profile link
    html_content += f'<p><a href="{profile["linkedin_url"]}" target="_blank">View LinkedIn Profile</a></p>'
    
    # Experience
    html_content += '<h4>Experience</h4><ul>'
    for exp in profile['experience'][:3]:
        html_content += f'<li><strong>{exp["title"]}</strong> at <strong>{exp["company"]}</strong><br><span style="font-size: 0.85rem; color: #7f8c8d;">{exp["date_range"]} ({exp["duration"]})</span></li>'
    html_content += '</ul>'
    
    if len(profile['experience']) > 3:
        html_content += '<p class="more-info">More experience available in the CSV download.</p>'
    
    # Education
    if profile.get('education'):
        html_content += '<h4>Education</h4><ul>'
        for edu in profile['education'][:2]:
            html_content += f'<li><strong>{edu["degree"]}</strong> in {edu["field_of_study"]} | {edu["school"]}<br><span style="font-size: 0.85rem; color: #7f8c8d;">{edu["date_range"]}</span></li>'
        html_content += '</ul>'
    
    # Close the container div
    html_content += '</div>'
    
    # Output the HTML content
    st.markdown(html_content, unsafe_allow_html=True)

    #Output a divider after content
    st.markdown('<div class="profile-divider"></div>', unsafe_allow_html=True)
    
    # Add spacing between cards
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)



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
logger.info(f"User selected {len(past_company_name)} companies for search: {past_company_name}")

# Get the past company URL (example: Freshworks)
linkedin_profile_list = []
total_linkedin_profiles_found = 0

# Button to trigger search
if st.button("Search"):
    start_time = time.time()
    logger.info("Search button pressed by user.")

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
        logger.info(f"Search process completed in {time.time() - start_time} seconds.")
        st.write(f"Found {len(linkedin_profile_list)} profiles.")
        logger.info(f"Search completed. Total profiles found: {len(linkedin_profile_list)}")
    if len(linkedin_profile_list):
        for profile in linkedin_profile_list:
            display_profile_card(profile)
    
        logger.info(f"Displaying {len(linkedin_profile_list)} profiles to user.")
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
            logger.info("Logs sent after scraping.")
            st.session_state['log_stream'].truncate(0)
            st.session_state['log_stream'].seek(0)
    else:
            logger.info("No logs captured to send via email.")  
else:
    st.info("Get started by selecting up to three companies.")
