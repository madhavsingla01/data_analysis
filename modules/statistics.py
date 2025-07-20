import streamlit as st
import pandas as pd
import numpy as np
from .utils import get_numeric_columns, get_categorical_columns, calculate_data_quality_score

def show_statistics_tab(df):
    """Display statistics tab content"""
    st.subheader("Statistical Summary")
    
    
    
    # Get column types
    numeric_cols = get_numeric_columns(df)
    categorical_cols = get_categorical_columns(df)
    
    # Data Quality Score
    show_data_quality(df)
    
    # Numeric Statistics
    if numeric_cols:
        show_numeric_statistics(df, numeric_cols)
    
    # Categorical Statistics
    if categorical_cols:
        show_categorical_statistics(df, categorical_cols)
    
    # Dataset Overview
    show_dataset_overview(df, numeric_cols, categorical_cols)

def show_data_quality(df):
    """Display data quality metrics"""
    st.subheader("📊 Data Quality Score")
    
    quality_metrics = calculate_data_quality_score(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Data Completeness", f"{quality_metrics['completeness']:.1f}%")
    with col2:
        st.metric("Data Uniqueness", f"{quality_metrics['uniqueness']:.1f}%")
    with col3:
        st.metric("Overall Quality Score", f"{quality_metrics['overall']:.1f}%")

def show_numeric_statistics(df, numeric_cols):
    """Display numeric column statistics"""
    st.subheader("📈 Numeric Column Statistics")
    
    # Existing statistics table code...
    stats_data = []
    for col in numeric_cols:
        try:
            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "No mode"
        except:
            mode_val = "No mode"
        
        stats_data.append({
            'Column': col,
            'Min': df[col].min(),
            'Max': df[col].max(),
            'Median': df[col].median(),
            'Mode': mode_val,
            'Mean': df[col].mean(),
            'Std Dev': df[col].std()
        })
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)
    
    # Add filtering interface
    st.markdown("---")
    st.subheader("🔍 Find Data")
    
    col1, col2 = st.columns(2)  # Fixed: 2 columns instead of 3
    
    with col1:
        find_options = ["Min", "Max", "Count", "Enter your number"]
        find_operation = st.selectbox("**Find:**", find_options, key="stats_find")
        
        # Show number input if "Enter your number" is selected
        enter_value = None
        if find_operation == "Enter your number":
            enter_value = st.number_input("**Enter value:**", value=0.0, key="stats_value")
    
    with col2:
        for_col = st.selectbox("**For:**", df.columns.tolist(), key="stats_for")
    
    if st.button("Apply", key="stats_apply"):
        perform_stats_filtering(df, find_operation, for_col, enter_value)  # Removed from_col


def perform_stats_filtering(df, find_operation, for_column, enter_value):  # Removed from_column parameter
    """Filter and show dataframe based on selected criteria"""
    
    if find_operation == "Min":
        min_val = df[for_column].min()
        filtered_df = df[df[for_column] == min_val]
        st.success(f"Showing rows where '{for_column}' has minimum value ({min_val})")
    
    elif find_operation == "Max":
        max_val = df[for_column].max()
        filtered_df = df[df[for_column] == max_val]
        st.success(f"Showing rows where '{for_column}' has maximum value ({max_val})")
    
    elif find_operation == "Count":
        # Show all rows for the selected column
        filtered_df = df.copy()
        count_val = len(filtered_df)
        st.success(f"Showing all {count_val} rows with '{for_column}' data")
    
    elif find_operation == "Enter your number":
        filtered_df = df[df[for_column] == enter_value]
        st.success(f"Showing rows where '{for_column}' equals {enter_value}")
    
    # Show the filtered dataframe
    if len(filtered_df) > 0:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("No matching data found!")



def show_categorical_statistics(df, categorical_cols):
    """Display categorical column statistics"""
    st.subheader("📝 Categorical Column Statistics")
    
    cat_stats = []
    for col in categorical_cols:
        try:
            mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else "No mode"
            mode_count = df[col].value_counts().iloc[0] if not df[col].empty else 0
        except:
            mode_val = "No mode"
            mode_count = 0
        
        cat_stats.append({
            'Column': col,
            'Unique Values': df[col].nunique(),
            'Most Frequent (Mode)': mode_val,
            'Mode Count': mode_count,
            'Missing Values': df[col].isnull().sum()
        })
    
    cat_stats_df = pd.DataFrame(cat_stats)
    st.dataframe(cat_stats_df, use_container_width=True)

def show_dataset_overview(df, numeric_cols, categorical_cols):
    """Display dataset overview"""
    st.subheader("📋 Dataset Overview")
    
    quality_metrics = calculate_data_quality_score(df)
    
    overview_col1, overview_col2 = st.columns(2)
    
    with overview_col1:
        st.write("**Basic Information:**")
        st.write(f"• Total Rows: {len(df):,}")
        st.write(f"• Total Columns: {len(df.columns)}")
        st.write(f"• Numeric Columns: {len(numeric_cols)}")
        st.write(f"• Categorical Columns: {len(categorical_cols)}")
    
    with overview_col2:
        st.write("**Data Issues:**")
        st.write(f"• Missing Values: {quality_metrics['missing_cells']:,}")
        st.write(f"• Duplicate Rows: {quality_metrics['duplicate_rows']:,}")
        st.write(f"• Empty Columns: {df.isnull().all().sum()}")
        st.write(f"• Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
