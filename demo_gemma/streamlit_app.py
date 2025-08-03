import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import json
from pathlib import Path
import numpy as np
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Gemma Model Analysis Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_all_results(output_dir: str = "output") -> pd.DataFrame:
    """Load all result files and combine into a single DataFrame."""
    results = []
    output_path = Path(output_dir)
    
    if not output_path.exists():
        st.error(f"Output directory {output_dir} does not exist!")
        return pd.DataFrame()
    
    json_files = list(output_path.glob("results_*.json"))
    st.info(f"Found {len(json_files)} result files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.extend(data)
        except Exception as e:
            st.error(f"Error loading {json_file}: {e}")
    
    if not results:
        st.error("No results found!")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df_data = []
    for result in results:
        df_data.append({
            'model_name': result['model_name'],
            'text': result['event']['text'],
            'true_year': result['event']['year'],
            'extracted_year': result['extracted_year'],
            'is_correct': result['is_correct'],
            'confidence_score': result['confidence_score'],
            'category': result['event']['primary_category'],  # Renamed as requested
            'violence_level': result['event']['violence_level'],
            'cultural_region': result['event']['cultural_region'],
            'historical_period': result['event']['historical_period'],
            'year_error': abs(result['extracted_year'] - result['event']['year']) if result['extracted_year'] else None,
            'century': (result['event']['year'] // 100) + 1 if result['event']['year'] < 2000 else 21
        })
    
    df = pd.DataFrame(df_data)
    st.success(f"Loaded {len(df)} results from {df['model_name'].nunique()} models")
    return df

def create_region_map(df_filtered: pd.DataFrame) -> go.Figure:
    """Create an interactive map showing accuracy by cultural region."""
    
    # Define region coordinates (simplified world map positions)
    region_coords = {
        'Western': {'lat': 45, 'lon': -100, 'color': '#1f77b4'},
        'Eastern': {'lat': 35, 'lon': 100, 'color': '#ff7f0e'},
        'Middle Eastern': {'lat': 30, 'lon': 50, 'color': '#2ca02c'},
        'African': {'lat': 0, 'lon': 20, 'color': '#d62728'},
        'Latin American': {'lat': -15, 'lon': -60, 'color': '#9467bd'}
    }
    
    # Calculate accuracy by region and model
    region_stats = []
    for region in df_filtered['cultural_region'].unique():
        region_data = df_filtered[df_filtered['cultural_region'] == region]
        
        for model in region_data['model_name'].unique():
            model_data = region_data[region_data['model_name'] == model]
            accuracy = model_data['is_correct'].mean() * 100
            count = len(model_data)
            avg_confidence = model_data['confidence_score'].mean()
            
            region_stats.append({
                'region': region,
                'model': model,
                'accuracy': accuracy,
                'count': count,
                'avg_confidence': avg_confidence,
                'lat': region_coords[region]['lat'],
                'lon': region_coords[region]['lon'],
                'color': region_coords[region]['color']
            })
    
    if not region_stats:
        return go.Figure()
    
    stats_df = pd.DataFrame(region_stats)
    
    # Create the map
    fig = go.Figure()
    
    # Add scatter points for each region
    for region in stats_df['region'].unique():
        region_data = stats_df[stats_df['region'] == region]
        
        fig.add_trace(go.Scattergeo(
            lon=region_data['lon'],
            lat=region_data['lat'],
            mode='markers',
            marker=dict(
                size=region_data['accuracy'] * 2,  # Size based on accuracy
                color=region_data['color'],
                opacity=0.8,
                line=dict(width=2, color='white')
            ),
            text=[f"{row['model']}<br>Accuracy: {row['accuracy']:.1f}%<br>Count: {row['count']}" 
                  for _, row in region_data.iterrows()],
            hoverinfo='text',
            name=region
        ))
    
    fig.update_layout(
        title="Model Accuracy by Cultural Region",
        geo=dict(
            scope='world',
            projection_type='equirectangular',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 230, 255)',
            showcountries=True,
            countrycolor='rgb(255, 255, 255)',
            showframe=False
        ),
        height=600,
        showlegend=True
    )
    
    return fig

def create_time_analysis(df_filtered: pd.DataFrame) -> go.Figure:
    """Create time-based analysis by century and historical period."""
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Accuracy by Century', 'Accuracy by Historical Period', 
                       'Sample Size by Century', 'Sample Size by Historical Period'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Plot 1: Accuracy by century
    century_acc = df_filtered.groupby(['century', 'model_name'])['is_correct'].agg(['mean', 'count']).reset_index()
    century_acc['accuracy_pct'] = century_acc['mean'] * 100
    
    for model in century_acc['model_name'].unique():
        model_data = century_acc[century_acc['model_name'] == model]
        fig.add_trace(
            go.Scatter(x=model_data['century'], y=model_data['accuracy_pct'], 
                      mode='lines+markers', name=f'{model} (Accuracy)', 
                      line=dict(width=3), marker=dict(size=8)),
            row=1, col=1
        )
    
    # Plot 2: Accuracy by historical period
    period_acc = df_filtered.groupby(['historical_period', 'model_name'])['is_correct'].agg(['mean', 'count']).reset_index()
    period_acc['accuracy_pct'] = period_acc['mean'] * 100
    
    for model in period_acc['model_name'].unique():
        model_data = period_acc[period_acc['model_name'] == model]
        fig.add_trace(
            go.Scatter(x=model_data['historical_period'], y=model_data['accuracy_pct'], 
                      mode='lines+markers', name=f'{model} (Accuracy)', 
                      line=dict(width=3), marker=dict(size=8), showlegend=False),
            row=1, col=2
        )
    
    # Plot 3: Sample size by century
    century_count = df_filtered.groupby(['century', 'model_name']).size().reset_index(name='count')
    for model in century_count['model_name'].unique():
        model_data = century_count[century_count['model_name'] == model]
        fig.add_trace(
            go.Bar(x=model_data['century'], y=model_data['count'], name=f'{model} (Count)', 
                   opacity=0.7, showlegend=False),
            row=2, col=1
        )
    
    # Plot 4: Sample size by historical period
    period_count = df_filtered.groupby(['historical_period', 'model_name']).size().reset_index(name='count')
    for model in period_count['model_name'].unique():
        model_data = period_count[period_count['model_name'] == model]
        fig.add_trace(
            go.Bar(x=model_data['historical_period'], y=model_data['count'], name=f'{model} (Count)', 
                   opacity=0.7, showlegend=False),
            row=2, col=2
        )
    
    fig.update_layout(
        title="Time-based Analysis",
        height=800,
        showlegend=True
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Century", row=1, col=1)
    fig.update_yaxes(title_text="Accuracy (%)", row=1, col=1)
    fig.update_xaxes(title_text="Historical Period", row=1, col=2)
    fig.update_yaxes(title_text="Accuracy (%)", row=1, col=2)
    fig.update_xaxes(title_text="Century", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_xaxes(title_text="Historical Period", row=2, col=2)
    fig.update_yaxes(title_text="Count", row=2, col=2)
    
    return fig

def create_model_comparison(df_filtered: pd.DataFrame) -> go.Figure:
    """Create comprehensive model comparison charts."""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Overall Accuracy', 'Confidence Distribution', 
                       'Error Distribution', 'Accuracy by Category'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Plot 1: Overall accuracy
    model_acc = df_filtered.groupby('model_name')['is_correct'].agg(['mean', 'count']).reset_index()
    model_acc['accuracy_pct'] = model_acc['mean'] * 100
    
    fig.add_trace(
        go.Bar(x=model_acc['model_name'], y=model_acc['accuracy_pct'], 
               text=[f'{acc:.1f}%<br>(n={count})' for acc, count in zip(model_acc['accuracy_pct'], model_acc['count'])],
               textposition='auto', name='Accuracy'),
        row=1, col=1
    )
    
    # Plot 2: Confidence distribution
    for model in df_filtered['model_name'].unique():
        model_data = df_filtered[df_filtered['model_name'] == model]['confidence_score']
        fig.add_trace(
            go.Histogram(x=model_data, name=model, opacity=0.7, nbinsx=20),
            row=1, col=2
        )
    
    # Plot 3: Error distribution
    error_df = df_filtered[df_filtered['year_error'].notna()]
    for model in error_df['model_name'].unique():
        model_data = error_df[error_df['model_name'] == model]['year_error']
        fig.add_trace(
            go.Histogram(x=model_data, name=model, opacity=0.7, nbinsx=20),
            row=2, col=1
        )
    
    # Plot 4: Accuracy by category
    cat_acc = df_filtered.groupby(['category', 'model_name'])['is_correct'].mean().reset_index()
    cat_acc['accuracy_pct'] = cat_acc['is_correct'] * 100
    
    for model in cat_acc['model_name'].unique():
        model_data = cat_acc[cat_acc['model_name'] == model]
        fig.add_trace(
            go.Scatter(x=model_data['category'], y=model_data['accuracy_pct'], 
                      mode='markers', name=model, marker=dict(size=10)),
            row=2, col=2
        )
    
    fig.update_layout(
        title="Model Comparison Analysis",
        height=800,
        showlegend=True
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Model", row=1, col=1)
    fig.update_yaxes(title_text="Accuracy (%)", row=1, col=1)
    fig.update_xaxes(title_text="Confidence Score", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=1, col=2)
    fig.update_xaxes(title_text="Year Error", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_xaxes(title_text="Category", row=2, col=2)
    fig.update_yaxes(title_text="Accuracy (%)", row=2, col=2)
    
    # Rotate x-axis labels for category plot
    fig.update_xaxes(tickangle=45, row=2, col=2)
    
    return fig

def create_interactive_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Create interactive filters in the sidebar."""
    st.sidebar.header("📊 Data Filters")
    
    # Model selection
    models = st.sidebar.multiselect(
        "Select Models",
        options=sorted(df['model_name'].unique()),
        default=sorted(df['model_name'].unique())
    )
    
    # Category selection
    categories = st.sidebar.multiselect(
        "Select Categories",
        options=sorted(df['category'].unique()),
        default=sorted(df['category'].unique())
    )
    
    # Violence level selection
    violence_levels = st.sidebar.multiselect(
        "Select Violence Levels",
        options=sorted(df['violence_level'].unique()),
        default=sorted(df['violence_level'].unique())
    )
    
    # Cultural region selection
    regions = st.sidebar.multiselect(
        "Select Cultural Regions",
        options=sorted(df['cultural_region'].unique()),
        default=sorted(df['cultural_region'].unique())
    )
    
    # Historical period selection
    periods = st.sidebar.multiselect(
        "Select Historical Periods",
        options=sorted(df['historical_period'].unique()),
        default=sorted(df['historical_period'].unique())
    )
    
    # Century range
    century_range = st.sidebar.slider(
        "Select Century Range",
        min_value=int(df['century'].min()),
        max_value=int(df['century'].max()),
        value=(int(df['century'].min()), int(df['century'].max()))
    
    # Apply filters
    filtered_df = df[
        (df['model_name'].isin(models)) &
        (df['category'].isin(categories)) &
        (df['violence_level'].isin(violence_levels)) &
        (df['cultural_region'].isin(regions)) &
        (df['historical_period'].isin(periods)) &
        (df['century'] >= century_range[0]) &
        (df['century'] <= century_range[1])
    ]
    
    st.sidebar.info(f"Showing {len(filtered_df)} events out of {len(df)} total")
    
    return filtered_df

def display_summary_metrics(df_filtered: pd.DataFrame):
    """Display summary metrics in cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_events = len(df_filtered)
        st.metric("Total Events", total_events)
    
    with col2:
        overall_accuracy = df_filtered['is_correct'].mean() * 100
        st.metric("Overall Accuracy", f"{overall_accuracy:.1f}%")
    
    with col3:
        avg_confidence = df_filtered['confidence_score'].mean()
        st.metric("Avg Confidence", f"{avg_confidence:.3f}")
    
    with col4:
        avg_error = df_filtered['year_error'].mean() if df_filtered['year_error'].notna().any() else 0
        st.metric("Avg Year Error", f"{avg_error:.1f}")

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">🧠 Gemma Model Analysis Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("Interactive analysis of Gemma model performance across different categories, regions, and time periods.")
    
    # Load data
    with st.spinner("Loading data..."):
        df = load_all_results()
    
    if df.empty:
        st.error("No data loaded. Please check your data files.")
        return
    
    # Create filters
    df_filtered = create_interactive_filters(df)
    
    if df_filtered.empty:
        st.warning("No data matches the selected filters. Please adjust your selection.")
        return
    
    # Display summary metrics
    st.subheader("📈 Summary Metrics")
    display_summary_metrics(df_filtered)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Regional Analysis", "⏰ Time Analysis", "📊 Model Comparison", "📋 Data Explorer"])
    
    with tab1:
        st.subheader("🗺️ Regional Analysis")
        st.markdown("Explore model performance across different cultural regions.")
        
        map_fig = create_region_map(df_filtered)
        st.plotly_chart(map_fig, use_container_width=True)
        
        # Regional statistics table
        st.subheader("Regional Statistics")
        region_stats = df_filtered.groupby(['cultural_region', 'model_name']).agg({
            'is_correct': ['mean', 'count'],
            'confidence_score': 'mean',
            'year_error': 'mean'
        }).round(3)
        region_stats.columns = ['Accuracy', 'Count', 'Avg Confidence', 'Avg Error']
        region_stats['Accuracy'] = region_stats['Accuracy'] * 100
        st.dataframe(region_stats, use_container_width=True)
    
    with tab2:
        st.subheader("⏰ Time-based Analysis")
        st.markdown("Analyze model performance across different time periods and centuries.")
        
        time_fig = create_time_analysis(df_filtered)
        st.plotly_chart(time_fig, use_container_width=True)
    
    with tab3:
        st.subheader("📊 Model Comparison")
        st.markdown("Compare the three Gemma models across various metrics.")
        
        comparison_fig = create_model_comparison(df_filtered)
        st.plotly_chart(comparison_fig, use_container_width=True)
    
    with tab4:
        st.subheader("📋 Data Explorer")
        st.markdown("Explore the raw data with interactive filtering.")
        
        # Show sample of the data
        st.dataframe(
            df_filtered[['model_name', 'category', 'cultural_region', 'historical_period', 
                        'violence_level', 'true_year', 'extracted_year', 'is_correct', 
                        'confidence_score']].head(20),
            use_container_width=True
        )
        
        # Download button
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="Download filtered data as CSV",
            data=csv,
            file_name="gemma_analysis_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main() 