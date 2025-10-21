import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(page_title="Social Media Habit Tracker", page_icon="🔥", layout="wide")

# Custom CSS for better habit tracker styling
st.markdown("""
<style>
    .big-metric {
        font-size: 3em;
        font-weight: bold;
        text-align: center;
    }
    .streak-emoji {
        font-size: 2em;
    }
    .day-card {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .completed-day {
        background-color: #d4edda;
        border: 2px solid #28a745;
    }
    .partial-day {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
    }
    .incomplete-day {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Title with motivational header
st.title("🔥 30-Day Social Media Posting Challenge")
st.markdown("### *Build your consistency habit across 10 platforms*")

# Platform list
platforms = [
    "Facebook", "Instagram", "X (Twitter)", "Threads", "Pinterest",
    "TikTok", "YouTube", "LinkedIn", "Fanbase", "Facebook Groups"
]

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

# Sidebar
st.sidebar.header("⚙️ Settings")

# Challenge info
st.sidebar.markdown(f"**📅 Challenge Started:** {st.session_state.challenge_start_date}")
days_elapsed = (datetime.now() - datetime.strptime(st.session_state.challenge_start_date, "%Y-%m-%d")).days + 1
if days_elapsed <= 30:
    st.sidebar.markdown(f"**📍 Day {days_elapsed} of 30**")
else:
    st.sidebar.markdown(f"**🎉 Challenge Complete!**")

st.sidebar.markdown("---")

# File operations
uploaded_file = st.sidebar.file_uploader("📂 Load Progress", type=['csv'])
if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
    for platform in platforms:
        if platform in st.session_state.df.columns:
            st.session_state.df[platform] = st.session_state.df[platform].astype(bool)
    st.sidebar.success("✅ Progress loaded!")

csv_buffer = io.StringIO()
st.session_state.df.to_csv(csv_buffer, index=False)
st.sidebar.download_button(
    label="💾 Save Progress",
    data=csv_buffer.getvalue(),
    file_name=f"habit_tracker_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

if st.sidebar.button("🔄 Reset Challenge"):
    for platform in platforms:
        st.session_state.df[platform] = False
    st.session_state.challenge_start_date = datetime.now().strftime("%Y-%m-%d")
    st.rerun()

# Calculate statistics
total_posts = sum([st.session_state.df[platform].sum() for platform in platforms])
total_possible = 30 * len(platforms)
completion_rate = (total_posts / total_possible * 100)

# Calculate streak
current_streak = 0
longest_streak = 0
temp_streak = 0

for i in range(30):
    posts_today = sum([st.session_state.df.loc[i, platform] for platform in platforms])
    if posts_today >= 5:  # At least 5 platforms posted
        temp_streak += 1
        longest_streak = max(longest_streak, temp_streak)
        if i < days_elapsed:
            current_streak = temp_streak
    else:
        temp_streak = 0
        if i < days_elapsed:
            current_streak = 0

days_with_all_posts = sum([all([st.session_state.df.loc[i, platform] for platform in platforms]) for i in range(30)])

# Main dashboard
st.markdown("## 📊 Your Progress Dashboard")

# Top metrics row
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

# Progress bar with label
st.markdown("### Overall Progress")
progress_col1, progress_col2 = st.columns([4, 1])
with progress_col1:
    st.progress(completion_rate / 100)
with progress_col2:
    st.markdown(f"**{int(total_posts)}/{total_possible}**")

st.markdown("---")

# Habit grid view
st.markdown("## 📅 30-Day Habit Grid")

# View selector
view_mode = st.radio("View Mode:", ["Compact Grid", "Detailed Checklist"], horizontal=True)

if view_mode == "Compact Grid":
    # Create a visual grid
    st.markdown("*Click on a day below to mark platforms*")
    
    # Create 6 rows of 5 days each
    for week in range(6):
        cols = st.columns(5)
        for day_in_week in range(5):
            day_idx = week * 5 + day_in_week
            if day_idx < 30:
                with cols[day_in_week]:
                    row = st.session_state.df.iloc[day_idx]
                    posts_count = sum([row[platform] for platform in platforms])
                    
                    # Determine status
                    if posts_count == 10:
                        status = "✅"
                        color = "#28a745"
                    elif posts_count >= 5:
                        status = "🟡"
                        color = "#ffc107"
                    elif posts_count > 0:
                        status = "🟠"
                        color = "#fd7e14"
                    else:
                        status = "⚪"
                        color = "#6c757d"
                    
                    # Create expandable day card
                    with st.expander(f"**Day {day_idx + 1}** {status}", expanded=False):
                        st.caption(row['Date'])
                        st.progress(posts_count / 10)
                        st.caption(f"{posts_count}/10 platforms")
                        
                        # Quick checkboxes
                        for platform in platforms:
                            checked = st.checkbox(
                                platform,
                                value=st.session_state.df.loc[day_idx, platform],
                                key=f"compact_{day_idx}_{platform}"
                            )
                            st.session_state.df.loc[day_idx, platform] = checked

else:  # Detailed Checklist
    # Filter options
    filter_option = st.selectbox(
        "Filter days:",
        ["All Days", "Incomplete Only", "Perfect Days", "This Week"]
    )
    
    for idx, row in st.session_state.df.iterrows():
        posts_count = sum([row[platform] for platform in platforms])
        
        # Apply filter
        show_day = True
        if filter_option == "Incomplete Only" and posts_count == 10:
            show_day = False
        elif filter_option == "Perfect Days" and posts_count < 10:
            show_day = False
        elif filter_option == "This Week" and idx >= 7:
            show_day = False
        
        if show_day:
            # Style based on completion
            if posts_count == 10:
                card_class = "completed-day"
                icon = "✅"
            elif posts_count >= 5:
                card_class = "partial-day"
                icon = "🟡"
            else:
                card_class = "incomplete-day"
                icon = "❌"
            
            with st.expander(f"{icon} **Day {row['Day']}** - {row['Date']} ({posts_count}/10)", expanded=(idx == days_elapsed - 1)):
                # Progress bar
                st.progress(posts_count / 10)
                
                # Platform checkboxes in grid
                col1, col2 = st.columns(2)
                
                for i, platform in enumerate(platforms):
                    target_col = col1 if i < 5 else col2
                    with target_col:
                        checked = st.checkbox(
                            platform,
                            value=st.session_state.df.loc[idx, platform],
                            key=f"detailed_{idx}_{platform}"
                        )
                        st.session_state.df.loc[idx, platform] = checked
                
                # Add notes section
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
    platform_stats = {platform: st.session_state.df[platform].sum() for platform in platforms}
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

st.caption("💡 **Pro Tip:** Consistency beats perfection. Even posting to 5+ platforms daily builds a strong habit!")
