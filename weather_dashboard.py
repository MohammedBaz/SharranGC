import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set page configuration
st.set_page_config(layout="wide", page_title="Weather Data Dashboard", page_icon="🌤️")

# --- Helper Function for Unique Columns ---
def deduplicate_columns(df_columns):
    """
    Ensures all column names are unique by appending a suffix to duplicates.
    Example: ['A', 'B', 'A'] -> ['A', 'B', 'A_1']
    """
    new_cols = []
    counts = {}
    for col in df_columns:
        cur_count = counts.get(col, 0)
        if cur_count > 0:
            new_cols.append(f"{col}_{cur_count}")
        else:
            new_cols.append(col)
        counts[col] = cur_count + 1
    return new_cols

# --- Page Title and Introduction ---
st.title("🌤️ Weather Data Dashboard")
st.markdown("""
This dashboard visualizes pre-cleaned weather station data from a public GitHub repository.
""")

# --- Function to load data ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_data_from_github(url):
    """Loads and processes pre-cleaned data from a raw GitHub URL."""
    try:
        # Load the data. No need to skip headers as the file is clean.
        df = pd.read_csv(url)
        
        # Clean and deduplicate column names to prevent errors
        cleaned_cols = df.columns.str.strip().str.replace('.', '', regex=False)
        df.columns = deduplicate_columns(cleaned_cols)

        # List of columns that should be numeric
        numeric_cols = [
            'Out Temp', 'Temp', 'Hum', 'Pt', 'Speed', 'Bar', 'Rain', 'Rad', 'Rate'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # --- Datetime Processing ---
        if 'Date' in df.columns and 'Time' in df.columns:
            # Use dayfirst=True to handle dates like '13/04/23'
            df['datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), errors='coerce', dayfirst=True)
            df.dropna(subset=['datetime'], inplace=True)
            df.set_index('datetime', inplace=True)
            df.sort_index(inplace=True)
        else:
            st.error("Dataset must contain 'Date' and 'Time' columns.")
            return None
            
        return df
        
    except Exception as e:
        st.error(f"Failed to load or process data. Error: {e}")
        return None

# --- Main App Logic ---

# IMPORTANT: This URL points to your NEWLY CLEANED data file.
DATA_URL = "https://raw.githubusercontent.com/MohammedBaz/SharranGC/refs/heads/main/WD_clean.csv" 

# Load the data
df = load_data_from_github(DATA_URL)

if df is not None and not df.empty:
    # --- Key Metrics Display ---
    st.header("Latest Conditions")
    
    # Use the column names identified from the data file: 'Temp', 'Hum', 'Speed', 'Bar'
    metric_cols = ['Temp', 'Hum', 'Speed', 'Bar']
    existing_metric_cols = [col for col in metric_cols if col in df.columns]

    if not df.dropna(subset=existing_metric_cols).empty:
        latest_data = df.dropna(subset=existing_metric_cols).iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)

        def display_metric(column, label, value, unit="", help_text=""):
            with column:
                if pd.notna(value):
                    st.metric(label=label, value=f"{value:.1f} {unit}", help=help_text)
                else:
                    st.metric(label=label, value="N/A", help=help_text)

        display_metric(col1, "🌡️ Temperature", latest_data.get('Temp'), "°C", "Outside Temperature")
        display_metric(col2, "💧 Humidity", latest_data.get('Hum'), "%", "Outside Humidity")
        display_metric(col3, "💨 Wind Speed", latest_data.get('Speed'), "km/h", "Current Wind Speed")
        display_metric(col4, "Barometer", latest_data.get('Bar'), "mbar", "Barometric Pressure")
    else:
        st.warning("No recent valid data to display metrics.")


    # --- Charts Section ---
    # Create a copy for plotting to avoid modifying the cached dataframe
    df_plot = df.copy()

    # Identify time gaps greater than a threshold (e.g., 2 hours)
    time_diff = df_plot.index.to_series().diff()
    gap_threshold = pd.Timedelta(hours=2)
    
    # Insert a row with NaN values where a gap is detected
    # This tells Plotly to create a break in the line
    gaps = df_plot[time_diff > gap_threshold].index
    for gap_start in gaps:
        gap_row = pd.DataFrame([pd.NA] * len(df_plot.columns)).T
        gap_row.columns = df_plot.columns
        gap_row.index = [gap_start - pd.Timedelta(seconds=1)]
        df_plot = pd.concat([df_plot, gap_row]).sort_index()

    st.header("Weather Trends")

    if 'Temp' in df_plot.columns and 'Pt' in df_plot.columns:
        st.subheader("Temperature & Dew Point")
        # Plot the modified dataframe
        fig_temp = px.line(df_plot.reset_index(), x='datetime', y=['Temp', 'Pt'],
                           title="Temperature and Dew Point Over Time",
                           labels={'value': 'Temperature (°C)', 'variable': 'Measurement', 'datetime': 'Time'},
                           template="plotly_white")
        st.plotly_chart(fig_temp, use_container_width=True)

    if 'Speed' in df_plot.columns:
        st.subheader("Wind Speed")
        fig_wind = px.line(df_plot.reset_index(), x='datetime', y='Speed',
                           title="Wind Speed Over Time",
                           labels={'Speed': 'Speed (km/h)', 'datetime': 'Time'},
                           template="plotly_white")
        st.plotly_chart(fig_wind, use_container_width=True)

    if 'Rain' in df_plot.columns:
        st.subheader("Cumulative Rainfall")
        fig_rain = px.area(df_plot.reset_index(), x='datetime', y='Rain',
                           title="Cumulative Rainfall",
                           labels={'Rain': 'Rainfall (mm)', 'datetime': 'Time'},
                           template="plotly_white")
        st.plotly_chart(fig_rain, use_container_width=True)

    if 'Rad' in df_plot.columns:
        st.subheader("Solar Radiation")
        fig_solar = px.line(df_plot.reset_index(), x='datetime', y='Rad',
                            title="Solar Radiation Over Time",
                            labels={'Rad': 'Radiation (W/m²)', 'datetime': 'Time'},
                            template="plotly_white", color_discrete_sequence=['orange'])
        st.plotly_chart(fig_solar, use_container_width=True)

    # --- Data Table ---
    st.header("Raw Data Viewer")
    # Show the original, unmodified dataframe
    st.dataframe(df)

else:
    st.error("Could not load or display data. Please check the GitHub URL and file content.")
