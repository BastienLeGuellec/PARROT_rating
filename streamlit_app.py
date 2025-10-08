import streamlit as st
from pathlib import Path
import pandas as pd
from datetime import datetime
import json
import os

# --- Configuration ---
DATA_DIR = Path("data")
USERS_FILE = Path("users.xlsx")
USER_REPORT_MAPPING_FILE = Path("user_report_mapping.json")
LOGS_DIR = Path("logs")
st.set_page_config(layout="wide", page_title="MetaRate")

def initialize_admin_user():
    """
    Checks if the 'is_admin' column exists in the users file.
    If not, it adds the column and sets the first user as an admin.
    """
    if USERS_FILE.exists():
        users_df = pd.read_excel(USERS_FILE)
        if 'is_admin' not in users_df.columns:
            users_df['is_admin'] = False
            users_df.loc[0, 'is_admin'] = True
            users_df.to_excel(USERS_FILE, index=False)

# --- Logging Function ---
def log_action(username, action, report_id="", rating="", comments=""):
    """Appends a log entry to the specified Excel file."""
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / f"{username}_action_log.xlsx"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    columns=['Timestamp', 'Username', 'Action', 'Report ID', 'Rating', 'Comments']
    new_log_entry = pd.DataFrame([[timestamp, username, action, report_id, rating, comments]], columns=columns)
    
    try:
        if log_file.exists():
            log_df = pd.read_excel(log_file)
            if list(log_df.columns) != columns:
                log_df = new_log_entry
            else:
                log_df = pd.concat([log_df, new_log_entry], ignore_index=True)
        else:
            log_df = new_log_entry
        
        log_df.to_excel(log_file, index=False)

    except Exception as e:
        st.sidebar.error(f"Log Error: {e}")

# --- Data Loading Functions ---

@st.cache_data
def load_users():
    """Loads user data from the excel file."""
    if not USERS_FILE.exists():
        st.error(f"User file not found at {USERS_FILE}")
        return None
    return pd.read_excel(USERS_FILE)

def get_report_file_for_user(username):
    """Gets the report file for a given user from the mapping file."""
    if not USER_REPORT_MAPPING_FILE.exists():
        return Path("rating_reports.jsonl") # Fallback to default if no mapping file
    with open(USER_REPORT_MAPPING_FILE, 'r') as f:
        mapping = json.load(f)
    for report_file, users in mapping.items():
        if username in users:
            return Path(report_file)
    return Path("rating_reports.jsonl") # Fallback for users not in mapping

def load_reports(file_path):
    """Loads reports from a JSONL file."""
    if not file_path.exists():
        return []
    reports = []
    with open(file_path, 'r') as f:
        for line in f:
            reports.append(json.loads(line))
    return reports

@st.cache_data
def load_all_reports(report_file):
    """Loads all reports from a given report file."""
    if report_file is None:
        return []
    return load_reports(report_file)

def get_report_by_id(rating_id, report_file):
    """Gets a report by its rating_id from a given report file."""
    reports = load_all_reports(report_file)
    for report in reports:
        if report.get("rating_id") == rating_id:
            return report
    return None

def get_rated_reports(username):
    """Gets the set of report numbers that the user has already rated."""
    log_file = LOGS_DIR / f"{username}_action_log.xlsx"
    if not log_file.exists():
        return set()
    try:
        log_df = pd.read_excel(log_file)
        return set(log_df[log_df['Action'] == 'Submit Rating']['Report ID'].unique())
    except Exception:
        return set()

# --- Page Drawing Functions ---

def draw_login_page():
    st.title("MetaRate Login")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_column_width=True)

    users_df = load_users()
    if users_df is None: return

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user_record = users_df[users_df['username'] == username]
            if not user_record.empty and str(user_record.iloc[0]['password']) == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.is_admin = user_record.iloc[0].get('is_admin', False)
                st.session_state.page = "progress"
                log_action(username, "Login Success")
                st.rerun()
            else:
                st.error("Invalid username or password")
                if username: # Log failed attempt
                    log_action(username, "Login Fail")

def draw_progress_page():
    st.title("Your Progress")
    username = st.session_state.username

    if st.sidebar.button("Logout"):
        log_action(st.session_state.username, "Logout")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        del st.session_state.username
        if 'is_admin' in st.session_state:
            del st.session_state.is_admin
        st.rerun()
    
    report_file = get_report_file_for_user(username)
    all_reports = load_all_reports(report_file)
    rated_reports = get_rated_reports(username)
    
    total_reports = len(all_reports)
    rated_count = len(rated_reports)
    
    progress = rated_count / total_reports if total_reports > 0 else 0
    
    st.progress(progress)
    st.markdown(f"You have rated **{rated_count}** out of **{total_reports}** reports.")
    
    if st.button("Start Rating" if rated_count == 0 else "Continue Rating"):
        reports_to_rate = [r for r in all_reports if r.get('rating_id') not in rated_reports]
        if reports_to_rate:
            st.session_state.page = "rating"
            st.session_state.selected_report_id = reports_to_rate[0]['rating_id']
            st.rerun()
        else:
            st.success("You have rated all available reports!")

def draw_rating_page():
    selected_report_id = st.session_state.selected_report_id
    username = st.session_state.username
    report_file = get_report_file_for_user(username)
    report = get_report_by_id(selected_report_id, report_file)

    if report is None:
        st.error("Report not found.")
        st.session_state.page = "progress"
        st.rerun()
        return

    st.title(f"Rating Report: {selected_report_id}")

    if st.sidebar.button("⬅️ Back to Progress"):
        log_action(username, "Back to Progress", report_id=selected_report_id)
        st.session_state.page = "progress"
        del st.session_state.selected_report_id
        st.rerun()

    st.subheader("Report to Rate")
    st.text(report.get("report_to_rate", "N/A"))

    st.subheader("Rating")
    rating = st.radio(
        "Rate the error in the report:",
        ("No error", "Laterality error", "Negation error", "Other error")
    )
    comments = st.text_area("Comments:")

    if st.button("Submit Rating"):
        log_action(username, "Submit Rating", report_id=selected_report_id, rating=rating, comments=comments)
        st.success("Rating submitted!")

        all_reports = load_all_reports(report_file)
        rated_reports = get_rated_reports(username)
        rated_reports.add(selected_report_id)

        reports_to_rate = [r for r in all_reports if r.get('rating_id') not in rated_reports]
        
        if reports_to_rate:
            st.session_state.selected_report_id = reports_to_rate[0]['rating_id']
            st.rerun()
        else:
            st.session_state.page = "progress"
            if 'selected_report_id' in st.session_state:
                del st.session_state.selected_report_id
            st.rerun()

def draw_admin_page():
    st.title("Admin Page")

    if st.sidebar.button("⬅️ Back to Progress"):
        st.session_state.page = "progress"
        st.rerun()

    st.subheader("Action Logs")
    log_files = [f for f in LOGS_DIR.iterdir() if f.name.endswith("_action_log.xlsx")]
    if not log_files:
        st.warning("No log files found.")
    else:
        log_filenames = [f.name for f in log_files]
        selected_log = st.selectbox("Select a log file to view:", log_filenames)
        if selected_log:
            log_df = pd.read_excel(LOGS_DIR / selected_log)
            st.dataframe(log_df)

    st.subheader("User List")
    if USERS_FILE.exists():
        users_df = pd.read_excel(USERS_FILE)
        st.dataframe(users_df)
    else:
        st.warning("Users file not found.")

# --- Main App Router ---

initialize_admin_user()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.page = "login"

if not st.session_state.logged_in:
    draw_login_page()
else:
    if st.session_state.page == "progress":
        draw_progress_page()
    elif st.session_state.page == "rating":
        draw_rating_page()
    elif st.session_state.page == "admin" and st.session_state.get('is_admin'):
        draw_admin_page()
    else:
        st.session_state.page = "progress"
        st.rerun()
