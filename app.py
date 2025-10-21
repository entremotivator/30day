import streamlit as st
import pandas as pd
import io
import json
import requests
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

# Page configuration
st.set_page_config(page_title="Social Media Habit Tracker", page_icon="🔥", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .big-metric {
        font-size: 3em;
        font-weight: bold;
        text-align: center;
    }
    .sync-status {
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        margin: 10px 0;
    }
    .sync-success {
        background-color: #d4edda;
        color: #155724;
    }
    .sync-error {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🔥 30-Day Social Media Posting Challenge")
st.markdown("### *Build your consistency habit across 10 platforms - Synced with Google Sheets*")

# Platform list
platforms = [
    "Facebook", "Instagram", "X (Twitter)", "Threads", "Pinterest",
    "TikTok", "YouTube", "LinkedIn", "Fanbase", "Facebook Groups"
]

# Google Sheets Configuration
SPREADSHEET_ID = "1UkuTf8VwGPIilTxhTEdP9K-zdtZFnThazFdGyxVYfmg"

# Initialize session state
if 'df' not in st.session_state:
    start_date = datetime.now()
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
    
    data = {"Day": [i+1 for i in range(30)], "Date": dates}
    for platform in platforms:
        data[platform] = [False] * 30
    
    st.session_state.df = pd.DataFrame(data)

if 'challenge_start_date' not in st.session_state:
    st.session_state.challenge_start_date = datetime.now().strftime("%Y-%m-%d")

if 'last_sync' not in st.session_state:
    st.session_state.last_sync = None

if 'sync_status' not in st.session_state:
    st.session_state.sync_status = None

if 'connected' not in st.session_state:
    st.session_state.connected = False

# Function to connect to Google Sheets
def connect_to_sheets(credentials_json):
    try:
        creds_dict = json.loads(credentials_json)
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        return None

# Function to load data from Google Sheets
def load_from_sheets(client):
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        data = sheet.get_all_values()
        
        if len(data) > 0:
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Convert Day column to int
            df['Day'] = pd.to_numeric(df['Day'], errors='coerce')
            
            # Convert platform columns to boolean
            for platform in platforms:
                if platform in df.columns:
                    df[platform] = df[platform].map({'TRUE': True, 'FALSE': False, True: True, False: False}).fillna(False)
            
            return df
        return None
    except Exception as e:
        st.error(f"Error loading from sheets: {str(e)}")
        return None

# Function to save data to Google Sheets
def save_to_sheets(client, df):
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        # Convert boolean to string for sheets
        df_to_save = df.copy()
        for platform in platforms:
            if platform in df_to_save.columns:
                df_to_save[platform] = df_to_save[platform].astype(str).str.upper()
        
        # Clear and update
        sheet.clear()
        sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
        
        return True
    except Exception as e:
        st.error(f"Error saving to sheets: {str(e)}")
        return False

# Sidebar
st.sidebar.header("☁️ Google Sheets Sync")

# Connection status
if st.session_state.connected:
    st.sidebar.success("✅ Connected to Google Sheets")
    if st.session_state.last_sync:
        st.sidebar.caption(f"Last sync: {st.session_state.last_sync}")
else:
    st.sidebar.warning("⚠️ Not connected to Google Sheets")

# Service Account JSON upload
st.sidebar.markdown("#### Setup Connection")
st.sidebar.caption("Upload your Google Service Account JSON file:")

credentials_file = st.sidebar.file_uploader("Service Account JSON", type=['json'], label_visibility="collapsed")

if credentials_file is not None:
    credentials_json = credentials_file.read().decode('utf-8')
    client = connect_to_sheets(credentials_json)
    
    if client:
        st.session_state.connected = True
        st.session_state.client = client
        st.sidebar.success("✅ Connected!")
    else:
        st.sidebar.error("❌ Connection failed")

# Sync buttons
if st.session_state.connected:
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("⬇️ Load from Sheets", use_container_width=True):
            loaded_df = load_from_sheets(st.session_state.client)
            if loaded_df is not None:
                st.session_state.df = loaded_df
                st.session_state.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.sync_status = "success_load"
                st.rerun()
    
    with col2:
        if st.button("⬆️ Save to Sheets", use_container_width=True):
            if save_to_sheets(st.session_state.client, st.session_state.df):
                st.session_state.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.sync_status = "success_save"
                st.rerun()
    
    # Auto-save option
    auto_save = st.sidebar.checkbox("🔄 Auto-save on changes", value=False)
    
    if auto_save and 'auto_save_enabled' not in st.session_state:
        st.session_state.auto_save_enabled = True

# Display sync status
if st.session_state.sync_status == "success_load":
    st.sidebar.markdown('<div class="sync-status sync-success">✅ Data loaded from Google Sheets!</div>', unsafe_allow_html=True)
    st.session_state.sync_status = None
elif st.session_state.sync_status == "success_save":
    st.sidebar.markdown('<div class="sync-status sync-success">✅ Data saved to Google Sheets!</div>', unsafe_allow_html=True)
    st.session_state.sync_status = None

st.sidebar.markdown("---")

# Challenge info
st.sidebar.markdown("### 📊 Challenge Info")
st.sidebar.markdown(f"**📅 Started:** {st.session_state.challenge_start_date}")
days_elapsed = (datetime.now() - datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")).days + 1
if days_elapsed <= 30:
    st.sidebar.markdown(f"**📍 Day {days_elapsed} of 30**")
else:
    st.sidebar.markdown(f"**🎉 Challenge Complete!**")

st.sidebar.markdown("---")

# Local file operations
st.sidebar.markdown("### 💾 Local Backup")
csv_buffer = io.StringIO()
st.session_state.df.to_csv(csv_buffer, index=False)
st.sidebar.download_button(
    label="📥 Download CSV",
    data=csv_buffer.getvalue(),
    file_name=f"habit_tracker_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True
)

uploaded_file = st.sidebar.file_uploader("📤 Upload CSV", type=['csv'])
if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
    for platform in platforms:
        if platform in st.session_state.df.columns:
            st.session_state.df[platform] = st.session_state.df[platform].astype(bool)
    st.sidebar.success("✅ CSV loaded!")

# Setup instructions expander
with st.sidebar.expander("📖 Setup Instructions"):
    st.markdown("""
    **How to connect to Google Sheets:**
    
    1. Go to [Google Cloud Console](https://console.cloud.google.com/)
    2. Create a new project
    3. Enable Google Sheets API
    4. Create Service Account credentials
    5. Download JSON key file
    6. Share your Google Sheet with the service account email
    7. Upload the JSON file here
    
    **Sheet Format:**
    - First row: Headers (Day, Date, platform names)
    - Column A: Day numbers (1-30)
    - Column B: Dates
    - Columns C-L: Platform names (TRUE/FALSE values)
    """)

# Link to Google Sheet
st.sidebar.markdown("---")
st.sidebar.markdown(f"[📊 Open Google Sheet](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)")

# Calculate statistics
total_posts = sum([st.session_state.df[platform].sum() for platform in platforms if platform in st.session_state.df.columns])
total_possible = 30 * len(platforms)
completion_rate = (total_posts / total_possible * 100)

# Calculate streak
current_streak = 0
longest_streak = 0
temp_streak = 0

for i in range(30):
    posts_today = sum([st.session_state.df.loc[i, platform] for platform in platforms if platform in st.session_state.df.columns])
    if posts_today >= 5:
        temp_streak += 1
        longest_streak = max(longest_streak, temp_streak)
        if i < days_elapsed:
            current_streak = temp_streak
    else:
        temp_streak = 0
        if i < days_elapsed:
            current_streak = 0

days_with_all_posts = sum([all([st.session_state.df.loc[i, platform] for platform in platforms if platform in st.session_state.df.columns]) for i in range(30)])

# Main dashboard
st.markdown("## 📊 Your Progress Dashboard")

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🔥 Current Streak")
    st.markdown(f"<div class='big-metric'>{current_streak}</div>", unsafe_allow_html=True)
    st.markdown(f"<center>Longest: {longest_streak} days</center>", unsafe_allow_html=True)

with col2:
    st.markdown("### ✅ Completion")
    st.markdown(f"<div class='big-metric'>{completion_rate:.0f}%</div>", unsafe_allow_html=True)
    st.markdown(f"<center>{int(total_posts)} / {total_possible} posts</center>", unsafe_allow_html=True)

with col3:
    st.markdown("### 🎯 Perfect Days")
    st.markdown(f"<div class='big-metric'>{days_with_all_posts}</div>", unsafe_allow_html=True)
    st.markdown(f"<center>All 10 platforms</center>", unsafe_allow_html=True)

with col4:
    avg_per_day = total_posts / 30
    st.markdown("### 📈 Daily Average")
    st.markdown(f"<div class='big-metric'>{avg_per_day:.1f}</div>", unsafe_allow_html=True)
    st.markdown(f"<center>platforms per day</center>", unsafe_allow_html=True)

# Progress bar
st.markdown("### Overall Progress")
progress_col1, progress_col2 = st.columns([4, 1])
with progress_col1:
    st.progress(completion_rate / 100)
with progress_col2:
    st.markdown(f"**{int(total_posts)}/{total_possible}**")

st.markdown("---")

# Habit grid view
st.markdown("## 📅 30-Day Habit Grid")

view_mode = st.radio("View Mode:", ["Compact Grid", "Detailed Checklist"], horizontal=True)

if view_mode == "Compact Grid":
    for week in range(6):
        cols = st.columns(5)
        for day_in_week in range(5):
            day_idx = week * 5 + day_in_week
            if day_idx < 30:
                with cols[day_in_week]:
                    row = st.session_state.df.iloc[day_idx]
                    posts_count = sum([row[platform] for platform in platforms if platform in st.session_state.df.columns])
                    
                    if posts_count == 10:
                        status = "✅"
                    elif posts_count >= 5:
                        status = "🟡"
                    elif posts_count > 0:
                        status = "🟠"
                    else:
                        status = "⚪"
                    
                    with st.expander(f"**Day {day_idx + 1}** {status}", expanded=False):
                        st.caption(row['Date'])
                        st.progress(posts_count / 10)
                        st.caption(f"{posts_count}/10 platforms")
                        
                        for platform in platforms:
                            if platform in st.session_state.df.columns:
                                checked = st.checkbox(
                                    platform,
                                    value=st.session_state.df.loc[day_idx, platform],
                                    key=f"compact_{day_idx}_{platform}"
                                )
                                if checked != st.session_state.df.loc[day_idx, platform]:
                                    st.session_state.df.loc[day_idx, platform] = checked
                                    if st.session_state.connected and auto_save:
                                        save_to_sheets(st.session_state.client, st.session_state.df)

else:
    filter_option = st.selectbox(
        "Filter days:",
        ["All Days", "Incomplete Only", "Perfect Days", "This Week"]
    )
    
    for idx, row in st.session_state.df.iterrows():
        posts_count = sum([row[platform] for platform in platforms if platform in st.session_state.df.columns])
        
        show_day = True
        if filter_option == "Incomplete Only" and posts_count == 10:
            show_day = False
        elif filter_option == "Perfect Days" and posts_count < 10:
            show_day = False
        elif filter_option == "This Week" and idx >= 7:
            show_day = False
        
        if show_day:
            if posts_count == 10:
                icon = "✅"
            elif posts_count >= 5:
                icon = "🟡"
            else:
                icon = "❌"
            
            with st.expander(f"{icon} **Day {row['Day']}** - {row['Date']} ({posts_count}/10)", expanded=(idx == days_elapsed - 1)):
                st.progress(posts_count / 10)
                
                col1, col2 = st.columns(2)
                
                for i, platform in enumerate(platforms):
                    if platform in st.session_state.df.columns:
                        target_col = col1 if i < 5 else col2
                        with target_col:
                            checked = st.checkbox(
                                platform,
                                value=st.session_state.df.loc[idx, platform],
                                key=f"detailed_{idx}_{platform}"
                            )
                            if checked != st.session_state.df.loc[idx, platform]:
                                st.session_state.df.loc[idx, platform] = checked
                                if st.session_state.connected and auto_save:
                                    save_to_sheets(st.session_state.client, st.session_state.df)
                
                if posts_count == 10:
                    st.success("🎉 Perfect day! All platforms completed!")
                elif posts_count == 0:
                    st.warning("⚠️ No posts yet today. Start building your habit!")

# Platform insights
st.markdown("---")
st.markdown("## 📊 Platform Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Most Consistent Platforms")
    platform_stats = {platform: st.session_state.df[platform].sum() for platform in platforms if platform in st.session_state.df.columns}
    sorted_platforms = sorted(platform_stats.items(), key=lambda x: x[1], reverse=True)
    
    for platform, count in sorted_platforms[:5]:
        percentage = (count / 30) * 100
        st.markdown(f"**{platform}**: {count}/30 days ({percentage:.0f}%)")
        st.progress(percentage / 100)

with col2:
    st.markdown("### Need More Attention")
    for platform, count in sorted_platforms[-5:]:
        percentage = (count / 30) * 100
        st.markdown(f"**{platform}**: {count}/30 days ({percentage:.0f}%)")
        st.progress(percentage / 100)

# Motivational footer
st.markdown("---")
if completion_rate == 100:
    st.balloons()
    st.success("🎊 INCREDIBLE! You've completed the entire 30-day challenge! You're a social media champion! 🏆")
elif completion_rate >= 75:
    st.success("🔥 You're crushing it! Keep up the amazing work!")
elif completion_rate >= 50:
    st.info("💪 Great progress! You're halfway there!")
elif completion_rate >= 25:
    st.warning("📈 Nice start! Build that momentum!")
else:
    st.info("🚀 Every journey starts with a single step. You've got this!")

st.caption("💡 **Pro Tip:** Enable auto-save to automatically sync your progress to Google Sheets!")
