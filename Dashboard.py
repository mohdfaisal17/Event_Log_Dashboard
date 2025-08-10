import pandas as pd
import streamlit as st
import win32evtlog
from datetime import datetime

# Function to fetch event logs from a given log type
def fetch_event_logs(log_type, max_events=200):
    server = 'localhost'
    hand = win32evtlog.OpenEventLog(server, log_type)

    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    events_data = []

    while True:
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        if not events:
            break
        for event in events:
            events_data.append({
                "LogType": log_type,
                "SourceName": event.SourceName,
                "EventID": event.EventID & 0xFFFF,
                "TimeGenerated": event.TimeGenerated.Format(),
                "EventCategory": event.EventCategory
            })
            if len(events_data) >= max_events:
                break
        if len(events_data) >= max_events:
            break

    return pd.DataFrame(events_data)


# Streamlit UI
st.set_page_config(page_title="Faisal Event Viewer Dashboard", layout="wide")
st.title("🖥 Faisal's Event Viewer Dashboard")

# Sidebar
log_type_choice = st.sidebar.multiselect(
    "Select Log Types to View",
    ["Security", "Application", "System"],
    default=["Security"]
)

max_events_choice = st.sidebar.slider("Max Events per Log", 50, 1000, 200)

# Fetch and combine logs
dfs = []
for log_type in log_type_choice:
    try:
        df_temp = fetch_event_logs(log_type, max_events_choice)
        dfs.append(df_temp)
    except Exception as e:
        st.error(f"Error reading {log_type} log: {e}")

if dfs:
    df = pd.concat(dfs, ignore_index=True)
    df["TimeGenerated"] = pd.to_datetime(df["TimeGenerated"])
else:
    st.warning("No logs found.")
    st.stop()

# Filters
source_filter = st.sidebar.selectbox("Filter by Source", ["All"] + sorted(df["SourceName"].unique().tolist()))
if source_filter != "All":
    df = df[df["SourceName"] == source_filter]

# Display Data Table
st.subheader("📋 Event Logs Table")
st.dataframe(df)

# Event count chart
st.subheader("📊 Event Count by Event ID")
event_counts = df["EventID"].value_counts().head(100)
st.bar_chart(event_counts)

# Events over time
st.subheader("⏳ Events Over Time")
time_counts = df.groupby(df["TimeGenerated"].dt.hour).size()
st.line_chart(time_counts)

st.success("✅ Dashboard Loaded Successfully")
