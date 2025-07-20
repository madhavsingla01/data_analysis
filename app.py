
import streamlit as st
import pandas as pd
import io
from typing import Optional, Tuple
from modules.file_handler import (
    upload_file,
    read_uploaded_file_basic,
    convert_selected_columns_to_datetime,
    filter_by_date_range,
    process_data_with_user_options,
)
from modules.data_preview import show_data_preview_clean
from modules.analysis import show_analysis_tab
from modules.statistics import show_statistics_tab

# Page Configuration
st.set_page_config(
    page_title="Data Analyzer Pro",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "Data Analyzer Pro - Your comprehensive data analysis tool"
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1E88E5;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #f0f2f6, #ffffff);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .status-success {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

class SessionManager:
    """Manages session state variables"""
    
    @staticmethod
    def initialize_session_state():
        """Initialize all session state variables"""
        defaults = {
            'original_data': None,
            'processed_data': None,
            'current_filename': None,
            'processing_history': [],
            'data_loaded': False
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def reset_data():
        """Reset data to original state"""
        if st.session_state.original_data is not None:
            st.session_state.processed_data = st.session_state.original_data.copy()
            st.session_state.processing_history = []
            st.success("🔄 Data reset to original state")
    
    @staticmethod
    def add_to_history(action: str):
        """Add processing action to history"""
        st.session_state.processing_history.append(action)

def create_download_button(df: pd.DataFrame, filename: str) -> None:
    """Create download buttons for different formats"""
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{filename}_processed.csv",
            mime="text/csv",
            key="download_csv"
        )
    
    with col2:
        # Excel download
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        st.download_button(
            label="📥 Download Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{filename}_processed.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel"
        )

def render_data_metrics(df: pd.DataFrame, original_df: Optional[pd.DataFrame] = None) -> None:
    """Render data metrics with enhanced styling"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Rows", f"{len(df):,}")
    
    with col2:
        st.metric("📋 Columns", len(df.columns))
    
    with col3:
        memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
        st.metric("💾 Memory", f"{memory_usage:.1f} MB")
    
    with col4:
        null_count = df.isnull().sum().sum()
        st.metric("❌ Missing", f"{null_count:,}")
    
    with col5:
        if original_df is not None and len(df) != len(original_df):
            delta = len(df) - len(original_df)
            st.metric("🔧 Changed", "Yes", delta=f"{delta:+,} rows")
        else:
            st.metric("🔧 Status", "Original")

def render_sidebar() -> Optional[pd.DataFrame]:
    """Render sidebar with file upload and processing options"""
    with st.sidebar:
        st.header("📁 File Management")
        uploaded_file = upload_file()
        
        if uploaded_file is None:
            st.info("👆 Upload a file to get started")
            SessionManager.reset_data()
            return None
        
        # Process file upload
        if not st.session_state.data_loaded or uploaded_file.name != st.session_state.current_filename:
            with st.spinner("🔄 Loading file..."):
                df, error = read_uploaded_file_basic(uploaded_file)
                
                if error:
                    st.error(f"❌ Error: {error}")
                    return None
                
                # Store data in session
                st.session_state.original_data = df.copy()
                st.session_state.processed_data = df.copy()
                st.session_state.current_filename = uploaded_file.name
                st.session_state.data_loaded = True
                st.session_state.processing_history = []
                
                st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
        
        # Show file info
        if st.session_state.data_loaded:
            original_df = st.session_state.original_data
            st.markdown("---")
            st.markdown("### 📊 Data Information")
            st.info(f"**Original:** {len(original_df):,} rows × {len(original_df.columns)} columns")
            
            # Processing section
            st.markdown("---")
            st.markdown("### 🔧 Data Processing")
            
            # Step 1: Data cleaning and processing
            with st.expander("🧹 Data Cleaning", expanded=True):
                processed_df = process_data_with_user_options(st.session_state.processed_data)
            
            # Step 2: DateTime conversion
            with st.expander("📅 DateTime Conversion"):
                processed_df = convert_selected_columns_to_datetime(processed_df)
            
            # Step 3: Date filtering
            with st.expander("📊 Date Range Filtering"):
                processed_df = filter_by_date_range(processed_df)
            
            # Update processed data
            st.session_state.processed_data = processed_df
            
            # Show processing summary
            st.markdown("---")
            st.markdown("### 📈 Processing Summary")
            
            if len(processed_df) != len(original_df):
                st.markdown(f"""
                <div class="status-success">
                    <strong>🎉 Processing Complete</strong><br>
                    Final: {len(processed_df):,} rows × {len(processed_df.columns)} columns
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-warning">
                    <strong>📊 Data Ready</strong><br>
                    {len(processed_df):,} rows × {len(processed_df.columns)} columns
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Reset Data", key="reset_data", use_container_width=True):
                    SessionManager.reset_data()
                    st.rerun()
            
            with col2:
                if st.button("📥 Export Data", key="export_toggle", use_container_width=True):
                    st.session_state.show_export = not st.session_state.get('show_export', False)
            
            # Export options
            if st.session_state.get('show_export', False):
                st.markdown("### 📤 Export Options")
                create_download_button(processed_df, uploaded_file.name.split('.')[0])
            
            return processed_df
    
    return None

def render_welcome_screen():
    """Render the welcome screen when no data is loaded"""
    st.markdown('<h1 class="main-header">📊 Data Analyzer Pro</h1>', unsafe_allow_html=True)
    st.markdown("### 🚀 Welcome to your comprehensive data analysis platform!")
    
    # Feature showcase
    col1, col2, col3 = st.columns(3)
    
    features = [
        {
            "title": "📋 Data Preview & Processing",
            "items": [
                "📁 Support for CSV and Excel files",
                "🧹 Smart data cleaning options", 
                "📅 DateTime conversion tools",
                "📊 Date range filtering",
                "🔍 Real-time data preview"
            ]
        },
        {
            "title": "📊 Advanced Analysis",
            "items": [
                "🎯 Flexible filtering system",
                "🧮 Mathematical operations",
                "📈 Aggregation functions",
                "🔢 Statistical calculations",
                "📋 Custom value analysis"
            ]
        },
        {
            "title": "📈 Statistics & Export",
            "items": [
                "📊 Comprehensive data overview",
                "🎯 Data quality metrics",
                "📉 Distribution analysis", 
                "📥 Multiple export formats",
                "💾 Processing history tracking"
            ]
        }
    ]
    
    for i, feature in enumerate(features):
        with [col1, col2, col3][i]:
            st.markdown(f"### {feature['title']}")
            for item in feature['items']:
                st.markdown(f"- {item}")
    
    st.markdown("---")
    
    # Quick start guide
    st.markdown("### 🎯 Quick Start Guide")
    steps = st.columns(4)
    
    with steps[0]:
        st.markdown("**1️⃣ Upload**\n\nClick the sidebar to upload your CSV or Excel file")
    
    with steps[1]:
        st.markdown("**2️⃣ Process**\n\nUse the sidebar tools to clean and prepare your data")
    
    with steps[2]:
        st.markdown("**3️⃣ Analyze**\n\nExplore your data using the Analysis and Statistics tabs")
    
    with steps[3]:
        st.markdown("**4️⃣ Export**\n\nDownload your processed data in your preferred format")
    
    st.info("👈 **Ready to get started? Upload a file from the sidebar!**")

def main():
    """Main application function"""
    # Initialize session state
    SessionManager.initialize_session_state()
    
    # Render sidebar and get processed data
    processed_df = render_sidebar()
    
    # Main content area
    if processed_df is not None and st.session_state.data_loaded:
        # Header
        st.markdown('<h1 class="main-header">📊 Data Analyzer Pro</h1>', unsafe_allow_html=True)
        
        # File information header
        st.markdown("### 📁 Current Dataset")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"**File:** {st.session_state.current_filename}")
        
        with col2:
            if st.button("ℹ️ File Info", use_container_width=True):
                st.session_state.show_file_info = not st.session_state.get('show_file_info', False)
        
        # Show detailed file info if requested
        if st.session_state.get('show_file_info', False):
            with st.expander("📊 Detailed File Information", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Data Types:**")
                    st.dataframe(processed_df.dtypes.to_frame(name='Type'), use_container_width=True)
                
                with col2:
                    st.write("**Missing Values:**")
                    missing_data = processed_df.isnull().sum().to_frame(name='Missing')
                    missing_data['Percentage'] = (missing_data['Missing'] / len(processed_df) * 100).round(2)
                    st.dataframe(missing_data[missing_data['Missing'] > 0], use_container_width=True)
        
        # Data metrics
        st.markdown("### 📊 Dataset Metrics")
        render_data_metrics(processed_df, st.session_state.original_data)
        
        st.markdown("---")
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["📋 Data Preview", "📊 Analysis", "📈 Statistics"])
        
        with tab1:
            show_data_preview_clean(processed_df)
        
        with tab2:
            show_analysis_tab(processed_df)
        
        with tab3:
            show_statistics_tab(processed_df)
    
    else:
        # Show welcome screen
        render_welcome_screen()

if __name__ == "__main__":
    main()


# import streamlit as st
# import pandas as pd
# from modules.file_handler import (
#     upload_file,
#     read_uploaded_file_basic,
#     convert_selected_columns_to_datetime,
#     filter_by_date_range,
#     process_data_with_user_options,
# )
# from modules.data_preview import show_data_preview_clean
# from modules.analysis import show_analysis_tab
# from modules.statistics import show_statistics_tab

# # Simple page config
# st.set_page_config(
#     page_title="Data Analyzer",
#     layout="wide",
#     page_icon="📊"
# )

# # Initialize session state
# if 'original_data' not in st.session_state:
#     st.session_state.original_data = None
# if 'processed_data' not in st.session_state:
#     st.session_state.processed_data = None
# if 'current_filename' not in st.session_state:
#     st.session_state.current_filename = None

# # Sidebar
# with st.sidebar:
#     st.header("📁 Upload File")
#     uploaded_file = upload_file()
    
#     if uploaded_file is None:
#         st.info("Upload a file to start")
#         st.session_state.original_data = None
#         st.session_state.processed_data = None
#     else:
#         # Load file only when new file is uploaded
#         if (st.session_state.original_data is None or 
#             uploaded_file.name != st.session_state.current_filename):
            
#             df, error = read_uploaded_file_basic(uploaded_file)
            
#             if error:
#                 st.error(f"Error: {error}")
#                 st.stop()
            
#             # Store original data
#             st.session_state.original_data = df.copy()
#             st.session_state.processed_data = df.copy()
#             st.session_state.current_filename = uploaded_file.name
#             st.success("✅ File loaded!")
        
#         # Show current data info
#         if st.session_state.original_data is not None:
#             df = st.session_state.original_data
#             st.write(f"**Rows:** {len(df):,}")
#             st.write(f"**Columns:** {len(df.columns)}")
            
#             st.markdown("---")
#             st.header("🔧 Processing Options")
#             st.write("Choose what to apply:")
            
#             # Get current data
#             current_df = st.session_state.processed_data
            
#             # Optional processing steps
#             if st.checkbox("🧹 Clean Data"):
#                 current_df = process_data_with_user_options(current_df)
            
#             if st.checkbox("📅 Convert Dates"):
#                 current_df = convert_selected_columns_to_datetime(current_df)
            
#             if st.checkbox("📊 Filter by Date"):
#                 current_df = filter_by_date_range(current_df)
            
#             # Update processed data
#             st.session_state.processed_data = current_df
            
#             # Reset button
#             st.markdown("---")
#             if st.button("🔄 Reset to Original"):
#                 st.session_state.processed_data = st.session_state.original_data.copy()
#                 st.rerun()

# # Main area
# if uploaded_file and st.session_state.processed_data is not None:
#     df = st.session_state.processed_data
    
#     st.title("📊 Data Analyzer")
#     st.write(f"**File:** {uploaded_file.name}")
    
#     # Simple metrics
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("Rows", f"{len(df):,}")
#     with col2:
#         st.metric("Columns", len(df.columns))
#     with col3:
#         if len(df) != len(st.session_state.original_data):
#             st.metric("Status", "Processed", delta=f"{len(df) - len(st.session_state.original_data):+,}")
#         else:
#             st.metric("Status", "Original")
    
#     # Simple tabs
#     tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Analysis", "📈 Statistics"])
    
#     with tab1:
#         show_data_preview_clean(df)
    
#     with tab2:
#         show_analysis_tab(df)
    
#     with tab3:
#         show_statistics_tab(df)

# else:
#     # Simple welcome
#     st.title("📊 Data Analyzer")
#     st.write("### Upload a CSV or Excel file to get started")
    
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.write("**📋 View Data**")
#         st.write("- Preview your data")
#         st.write("- Clean and process") 
#         st.write("- Convert dates")
    
#     with col2:
#         st.write("**📊 Analyze**")
#         st.write("- Filter data")
#         st.write("- Calculate values")
#         st.write("- Apply functions")
    
#     with col3:
#         st.write("**📈 Statistics**")
#         st.write("- Data overview")
#         st.write("- Quality metrics")
#         st.write("- Summary stats")
    
#     st.info("👈 Upload a file from the sidebar")
