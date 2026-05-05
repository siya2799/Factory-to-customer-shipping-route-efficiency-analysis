import streamlit as st
import pandas as pd
import plotly.express as px
#App Layout
st.set_page_config(page_title="Shipping Efficiency Dashboard", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap');

/* Apply font globally */
html, body, [class*="css"]  {
    font-family: 'Montserrat', sans-serif;
}

/* Make headings stand out */
h1, h2, h3 {
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
st.title("🚚 Shipping Route Efficiency Dashboard")
#Load Data
@st.cache_data
def load_data():
    df = pd.read_csv("Data/Nassau Candy Distributor.csv")
    region_kpi = pd.read_csv("Data/Region_KPI_table.csv")
    state_kpi = pd.read_csv("Data/State_KPI_table.csv")
    state_mapping = pd.read_csv("Data/State_Mapping.csv")
    state_mapping_with_coords = pd.read_csv("Data/state_mapping_with_coords.csv")
    return df, region_kpi, state_kpi, state_mapping , state_mapping_with_coords
df, region_kpi, state_kpi, state_mapping, state_mapping_with_coords = load_data()
#Sidebar Filters
st.sidebar.header("Filter")
#Converting for filters
df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce', dayfirst=True)
df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce', dayfirst=True)
df = df.dropna(subset=['Order Date'])
df['Lead Time'] = (df['Ship Date'] - df['Order Date']).dt.days
#Date filter
date_range = st.sidebar.date_input("Select Date Range", value = [df['Order Date'].min().date(), df['Order Date'].max().date()])
#Region filter
region = st.sidebar.multiselect("Select Region(s)", options=df['Region'].unique(), default=df['Region'].unique())
#State filter
state = st.sidebar.multiselect("Select State(s)", options=df['State/Province'].unique(), default=df['State/Province'].unique())
#Ship Mode filter
ship_mode = st.sidebar.multiselect("Select Ship Mode(s)", options=df['Ship Mode'].unique(), default=df['Ship Mode'].unique())
#Lead Time Slider 
Lead_time = st.sidebar.slider("Lead Time Threshold", int(df['Lead Time'].min()), int(df['Lead Time'].max()), (0,10))
#Apply filters
filtered_df = df.copy()
if region:
    filtered_df = filtered_df[filtered_df['Region'].isin(region)]
if state:
    filtered_df = filtered_df[filtered_df['State/Province'].isin(state)]
if ship_mode:
    filtered_df = filtered_df[filtered_df['Ship Mode'].isin(ship_mode)]
if Lead_time:
    filtered_df = filtered_df[(filtered_df['Lead Time'] >= Lead_time[0]) & (filtered_df['Lead Time'] <= Lead_time[1])]
#Defining delayed shipments for filtered df
filtered_df['Lead_Time'] = (filtered_df['Ship Date'] - filtered_df['Order Date']).dt.days
threshold = filtered_df['Lead_Time'].quantile(0.75)
filtered_df['Is_Delayed'] = filtered_df['Lead_Time'] > threshold 
#Merging state KPI table with state mapping for geographic visualizations
state_kpi['State_Name'] = state_kpi['Route__State'].str.split(' → ').str[-1]
state_kpi['Country'] = state_kpi['Route__State'].str.split(' → ').str[0]
state_kpi_merge = state_kpi.merge(state_mapping_with_coords[['State/Province', 'Country', 'Lat', 'Lon']],left_on=['State_Name', 'Country'],right_on=['State/Province', 'Country'],how='left')
state_kpi_merge['Lat'] = pd.to_numeric(state_kpi_merge['Lat'], errors='coerce')
state_kpi_merge['Lon'] = pd.to_numeric(state_kpi_merge['Lon'], errors='coerce')
state_kpi_merge = state_kpi_merge.dropna(subset=['Lat', 'Lon'])
#Dashboard
tab1, tab2 , tab3, tab4 , tab5 = st.tabs(["📊 Route Efficiency","🌍 Geographic Analysis", "🚨 Bottleneck Analysis","🚚 Ship Mode Performance","🔍 Route Drill-Down Analysis"])
#Route Efficiency Overview
with tab1:
    st.subheader("📊 Route Efficiency Overview")
    subtab1, subtab2 = st.tabs(["🌍 Region Level", "📍 State Level"])
    with subtab1:
        st.subheader("Region-Level Route Efficiency")
        col1, col2 = st.columns(2)
        with col1:
            fig_region_fast = px.bar(region_kpi.sort_values('Avg_Lead_Time').head(3), x='Avg_Lead_Time', y='Route__Region', title='Fastest Route -Region Level', orientation='h')
            st.plotly_chart(fig_region_fast, use_container_width=True)
        with col2:
            fig_region_eff = px.scatter(region_kpi, x="Route_Volume", y="Avg_Lead_Time", size="Route_Volume", color="Route_Efficiency_Score", title='Route Efficiency Analysis', hover_name = 'Route__Region')
            st.plotly_chart(fig_region_eff, use_container_width=True)
    with subtab2:
        st.subheader("State-Level Route Efficiency")
        col1, col2 = st.columns(2)
        with col1:
            fig_state_fast = px.bar(state_kpi.sort_values('Avg_Lead_Time').head(10), x='Avg_Lead_Time', y='Route__State', title='Fastest Route - State Level', orientation='h')
            st.plotly_chart(fig_state_fast, use_container_width=True)
        with col2:
            fig_state_eff = px.scatter(state_kpi, x="Route_Volume", y="Avg_Lead_Time", size="Route_Volume", color="Route_Efficiency_Score", title='State Efficiency Analysis', hover_name = 'Route__State')
            st.plotly_chart(fig_state_eff, use_container_width=True)
#Geographic Shipping Map
with tab2:
    st.subheader("🌍 Geographic Analysis - Shipping Efficiency")
    fig = px.scatter_mapbox(state_kpi_merge,lat="Lat",lon="Lon",size="Route_Volume",color="Route_Efficiency_Score",hover_name="State_Name",hover_data={"State_Name": True,"Route_Volume": True,"Avg_Lead_Time": True,"Route_Efficiency_Score": True},zoom=3,height=600,color_continuous_scale="RdYlGn", size_max=35)
    fig.update_traces(textposition='top center', marker=dict(opacity=0.8))
    fig.update_layout(mapbox_style="carto-positron")
    st.plotly_chart(fig, use_container_width=True)
    subtab1, subtab2 = st.tabs(["🌍 Region Level", "📍 State Level"])
    with subtab1:
        st.subheader("Region-Level Efficiency Map")
        fig_region_map = px.bar(region_kpi.sort_values('Route_Efficiency_Score'), x='Route_Efficiency_Score', y='Route__Region', title='Region Efficiency Distribution', orientation='h')
        st.plotly_chart(fig_region_map, use_container_width=True)
    with subtab2:
        st.subheader("State-Level Efficiency Map")
        fig_state_map = px.bar(state_kpi.sort_values('Route_Efficiency_Score'), x='Route_Efficiency_Score', y='Route__State', title='State Efficiency Distribution', orientation='h')
        st.plotly_chart(fig_state_map, use_container_width=True)
#Bottleneck Visualization
with tab3:
    st.subheader("🚨 Bottleneck Analysis")
    subtab1, subtab2 = st.tabs(["🌍 Region Level", "📍 State Level"])
    with subtab1:
        st.subheader("Region-Level Bottlenecks")
        region_bottlenecks = region_kpi[(region_kpi['Route_Volume'] > region_kpi['Route_Volume'].quantile(0.75)) & (region_kpi['Delay_Frequency_RegionLevel'] > region_kpi['Delay_Frequency_RegionLevel'].quantile(0.75))]
        fig = px.scatter(region_bottlenecks, x='Route_Volume', y='Delay_Frequency_RegionLevel', size='Avg_Lead_Time', color='Route__Region', title='Region Bottlenecks')
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Delay Composition")
        region_delay = filtered_df.groupby('Region')['Is_Delayed'].mean().reset_index()
        region_delay['On_Time'] = 1 - region_delay['Is_Delayed']
        region_melt = region_delay.melt(
        id_vars='Region',
        value_vars=['Is_Delayed', 'On_Time'],
        var_name='Status',
        value_name='Percentage')
        fig = px.pie(
        region_melt,
        names='Status',
        values='Percentage',
        color='Status',
        title="Delay Distribution (Region Level)",
        hole=0.5)
        st.plotly_chart(fig, use_container_width=True)
    with subtab2:
        st.subheader("State-Level Bottlenecks")
        state_bottlenecks = state_kpi[(state_kpi['Route_Volume'] > state_kpi['Route_Volume'].quantile(0.75)) & (state_kpi['Delay_Frequency_StateLevel'] > state_kpi['Delay_Frequency_StateLevel'].quantile(0.75))]
        fig = px.scatter(state_bottlenecks, x='Route_Volume', y='Delay_Frequency_StateLevel', size='Avg_Lead_Time', color='Route__State', title='State Bottlenecks')
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Delay Composition")
        state_delay = filtered_df.groupby('State/Province')['Is_Delayed'].mean().reset_index()
        state_delay['On_Time'] = 1 - state_delay['Is_Delayed']
        state_melt = state_delay.melt(
        id_vars='State/Province',
        value_vars=['Is_Delayed', 'On_Time'],
        var_name='Status',
        value_name='Percentage')
        fig = px.pie(
        state_melt,
        names='Status',
        values='Percentage',
        color='Status',
        title="Delay Distribution (State Level)",
        hole=0.5)
        st.plotly_chart(fig, use_container_width=True)
#Ship Mode Comparison
with tab4:
    st.header("🚚 Ship Mode Performance")
    ship_mode_analysis= filtered_df.groupby('Ship Mode').agg(Average_Lead_Time=('Lead Time', 'mean'), Delay_Frequency=('Is_Delayed', 'mean'), Total_Shipments=('Order ID', 'count')).reset_index()
    ship_mode_analysis['Delay_Frequency'] = ship_mode_analysis['Delay_Frequency'] * 100
    fig = px.box(ship_mode_analysis, x='Ship Mode', y=['Average_Lead_Time', 'Delay_Frequency'], title='Ship Mode Performance')
    st.plotly_chart(fig, use_container_width=True)
    #Lead Time Distribution by Ship Mode
    fig = px.histogram(filtered_df, x='Lead Time', color='Ship Mode', title='Lead Time Distribution by Ship Mode', nbins=30, barmode='overlay')
    st.plotly_chart(fig, use_container_width=True)
#Route Drill-Down
with tab5:
    st.header("🔍 Route Drill-Down Analysis")
    subtab1, subtab2 = st.tabs(["🌍 Region Drill", "📍 State Drill"])
    with subtab1:
        selected_region = st.selectbox("Select Region", df['Region'].unique())
        region_data = filtered_df[filtered_df['Region'] == selected_region]
        fig=px.line(region_data, x='Order Date', y='Lead Time', title=f'Shipment timeline - {selected_region}')
        st.plotly_chart(fig, use_container_width=True)
    with subtab2:
        selected_state = st.selectbox("Select State", df['State/Province'].unique())
        state_data = filtered_df[filtered_df['State/Province'] == selected_state]
        fig=px.line(state_data, x='Order Date', y='Lead Time', title=f'Shipment timeline - {selected_state}')
        st.plotly_chart(fig, use_container_width=True)
#Correlation Insight
with tab5:
    with subtab1:
        st.subheader("Correlation Analysis - Region Level")
        region_corr = region_kpi[['Avg_Lead_Time', 'Route_Volume', 'Delay_Frequency_RegionLevel', 'Route_Efficiency_Score']].corr()
        fig = px.imshow(region_corr, text_auto=True, title='Region KPI Correlation Matrix')
        st.plotly_chart(fig, use_container_width=True)
    with subtab2:
        st.subheader("Correlation Analysis - State Level")
        state_corr = state_kpi[['Avg_Lead_Time', 'Route_Volume', 'Delay_Frequency_StateLevel', 'Route_Efficiency_Score']].corr()
        fig = px.imshow(state_corr, text_auto=True, title='State KPI Correlation Matrix')
        st.plotly_chart(fig, use_container_width=True)
