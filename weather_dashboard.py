import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set page configuration
st.set_page_config(layout="wide", page_title="Weather Data Dashboard", page_icon="🌤️")

# --- Page Title and Introduction ---
st.title("🌤️ Weather Data Dashboard")
st.markdown("""
This dashboard automatically loads and visualizes weather station data 
directly from a public GitHub repository.
""")

# --- Function to load data ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_data_from_github(url):
    """Loads data from a raw GitHub URL."""
    try:
        # Use header=1 to skip the first row and use the second row as the header
        df = pd.read_csv(url, header=1)
        return df
    except Exception as e:
        st.error(f"Failed to load data from the URL. Please check the URL and file format. Error: {e}")
        return None

# --- Main App Logic ---

# IMPORTANT: Replace this with the raw URL to YOUR WD.csv file on GitHub
DATA_URL = "https://raw.githubusercontent.com/YourUsername/YourRepoName/main/WD.csv" 

# Load the data
df = load_data_from_github(DATA_URL)

if df is not None and not df.empty:
    # --- Data Preprocessing ---
    if 'Date' in df.columns and 'Time' in df.columns:
        try:
            # Combine Date and Time, coercing errors to NaT (Not a Time)
            df['datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), errors='coerce')
            df.dropna(subset=['datetime'], inplace=True)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
        except Exception as e:
            st.error(f"Could not process Date and Time columns. Error: {e}")
            st.stop()
    else:
        st.warning("The dataset must contain 'Date' and 'Time' columns.")
        st.stop()


    # --- Key Metrics Display ---
    st.header("Latest Conditions")
    latest_data = df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    def display_metric(column, label, value, unit="", help_text=""):
        with column:
            st.metric(label=label, value=f"{value:.1f} {unit}" if isinstance(value, (int, float)) else str(value), help=help_text)

    display_metric(col1, "🌡️ Temperature", latest_data.get('Out Temp', 'N/A'), "°C", "Outside Temperature")
    display_metric(col2, "💧 Humidity", latest_data.get('Out Hum', 'N/A'), "%", "Outside Humidity")
    display_metric(col3, "💨 Wind Speed", latest_data.get('Wind Speed', 'N/A'), "km/h", "Current Wind Speed")
    display_metric(col4, "Barometer", latest_data.get('Bar', 'N/A'), "mbar", "Barometric Pressure")

    # --- Charts Section ---
    st.header("Weather Trends")

    if 'Out Temp' in df.columns and 'Dew Pt.' in df.columns:
        st.subheader("Temperature & Dew Point")
        fig_temp = px.line(df.reset_index(), x='datetime', y=['Out Temp', 'Dew Pt.'],
                           title="Temperature and Dew Point Over Time",
                           labels={'value': 'Temperature (°C)', 'datetime': 'Time'},
                           template="plotly_white")
        fig_temp.update_layout(legend_title_text='Measurement')
        st.plotly_chart(fig_temp, use_container_width=True)

    if 'Wind Speed' in df.columns:
        st.subheader("Wind Speed")
        fig_wind = px.line(df.reset_index(), x='datetime', y='Wind Speed',
                           title="Wind Speed Over Time",
                           labels={'Wind Speed': 'Speed (km/h)', 'datetime': 'Time'},
                           template="plotly_white")
        st.plotly_chart(fig_wind, use_container_width=True)

    c1, c2 = st.columns((1,1))
    with c1:
        if 'Rain' in df.columns:
            st.subheader("Cumulative Rainfall")
            fig_rain = px.area(df.reset_index(), x='datetime', y='Rain',
                               title="Cumulative Rainfall",
                               labels={'Rain': 'Rainfall (mm)', 'datetime': 'Time'},
                               template="plotly_white")
            st.plotly_chart(fig_rain, use_container_width=True)
    with c2:
        if 'Solar Rad.' in df.columns:
            st.subheader("Solar Radiation")
            fig_solar = px.line(df.reset_index(), x='datetime', y='Solar Rad.',
                                title="Solar Radiation Over Time",
                                labels={'Solar Rad.': 'Radiation (W/m²)', 'datetime': 'Time'},
                                template="plotly_white", color_discrete_sequence=['orange'])
            st.plotly_chart(fig_solar, use_container_width=True)

    # --- Data Table ---
    st.header("Raw Data")
    if st.checkbox("Show full data table"):
        st.dataframe(df)
    else:
        st.dataframe(df.head())

else:
    st.warning("Could not load data. Please ensure the GitHub URL in the script is correct and the file is public.")
