import streamlit as st
import pandas as pd
import plotly.express as px
#App Layout
st.set_page_config(page_title="Shipping Efficiency Dashboard", layout="wide")
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
            fig_region_eff = px.bar(region_kpi.sort_values('Route_Efficiency_Score', ascending=False).head(3), x='Route_Efficiency_Score', y='Route__Region', title='Top Efficient Regions', orientation='h')
            st.plotly_chart(fig_region_eff, use_container_width=True)
    with subtab2:
        st.subheader("State-Level Route Efficiency")
        col1, col2 = st.columns(2)
        with col1:
            fig_state_fast = px.bar(state_kpi.sort_values('Avg_Lead_Time').head(10), x='Avg_Lead_Time', y='Route__State', title='Fastest Route - State Level', orientation='h')
            st.plotly_chart(fig_state_fast, use_container_width=True)
        with col2:
            fig_state_eff = px.bar(state_kpi.sort_values('Route_Efficiency_Score', ascending=False).head(10), x='Route_Efficiency_Score', y='Route__State', title='Top Efficient States', orientation='h')
            st.plotly_chart(fig_state_eff, use_container_width=True)
#Geographic Shipping Map
with tab2:
    st.subheader("🌍 Geographic Analysis - Shipping Efficiency")
    fig = px.scatter_mapbox(state_kpi_merge,lat="Lat",lon="Lon",size="Route_Volume",color="Route_Efficiency_Score",hover_name="State_Name",hover_data={"Route_Volume": True,"Avg_Lead_Time": True,"Route_Efficiency_Score": True},zoom=3,height=600,color_continuous_scale="RdYlGn")
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
    with subtab2:
        st.subheader("State-Level Bottlenecks")
        state_bottlenecks = state_kpi[(state_kpi['Route_Volume'] > state_kpi['Route_Volume'].quantile(0.75)) & (state_kpi['Delay_Frequency_StateLevel'] > state_kpi['Delay_Frequency_StateLevel'].quantile(0.75))]
        fig = px.scatter(state_bottlenecks, x='Route_Volume', y='Delay_Frequency_StateLevel', size='Avg_Lead_Time', color='Route__State', title='State Bottlenecks')
        st.plotly_chart(fig, use_container_width=True)
#Ship Mode Comparison
with tab4:
    st.header("🚚 Ship Mode Performance")
    ship_mode_analysis= filtered_df.groupby('Ship Mode').agg(Average_Lead_Time=('Lead Time', 'mean'), Delay_Frequency=('Is_Delayed', 'mean'), Total_Shipments=('Order ID', 'count')).reset_index()
    ship_mode_analysis['Delay_Frequency'] = ship_mode_analysis['Delay_Frequency'] * 100
    fig = px.bar(ship_mode_analysis, x='Ship Mode', y=['Average_Lead_Time', 'Delay_Frequency'], title='Ship Mode Performance', barmode='group')
    st.plotly_chart(fig, use_container_width=True)
#Route Drill-Down
with tab5:
    st.header("🔍 Route Drill-Down Analysis")
    subtab1, subtab2 = st.tabs(["🌍 Region Drill", "📍 State Drill"])
    with subtab1:
        selected_region = st.selectbox("Select Region", df['Region'].unique())
        region_data = filtered_df[filtered_df['Region'] == selected_region]
        fig=px.histogram(region_data, x='Lead Time', title=f'Lead Time Distribution - {selected_region}')
        st.plotly_chart(fig, use_container_width=True)
    with subtab2:
        selected_state = st.selectbox("Select State", df['State/Province'].unique())
        state_data = filtered_df[filtered_df['State/Province'] == selected_state]
        fig=px.histogram(state_data, x='Lead Time', title=f'Lead Time Distribution - {selected_state}')
        st.plotly_chart(fig, use_container_width=True)
