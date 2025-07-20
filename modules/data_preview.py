import streamlit as st


def show_data_preview(df):
    """Display data preview tab content"""
    st.subheader("Preview of Data")

    # Show basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # Show dataframe
    st.dataframe(df, use_container_width=True)


def show_data_preview_clean(df):
    """Display clean data preview without processing options"""
    st.subheader("Preview of Data")
    
    # Just show the dataframe - processing is done in sidebar
    st.dataframe(df, use_container_width=True)
    
    # Optional: Show some quick insights
    if st.checkbox("Show Quick Insights"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Data Types:**")
            for col in df.columns[:10]:  # Show first 10 columns
                st.write(f"• {col}: {df[col].dtype}")
        
        with col2:
            st.write("**Missing Values:**")
            missing = df.isnull().sum()
            missing_cols = missing[missing > 0].head(10)
            
            if len(missing_cols) > 0:
                for col_name in missing_cols.index:  # Fix: iterate over .index
                    st.write(f"• {col_name}: {missing[col_name]} missing")
            else:
                st.write("• No missing values found!")
