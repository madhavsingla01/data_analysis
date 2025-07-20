import streamlit as st
import pandas as pd
import re


def upload_file():
    """Handle file upload"""
    return st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx"])


def read_uploaded_file_basic(uploaded_file):
    """Read file without any processing UI - for sidebar use"""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            preview_df = pd.read_excel(uploaded_file, header=None, nrows=5)
            likely_header_row = preview_df.notnull().sum(axis=1).idxmax()
            df = pd.read_excel(uploaded_file, header=likely_header_row)

        return df, None

    except Exception as e:
        return None, str(e)


def read_uploaded_file(uploaded_file):
    """Read and process uploaded file"""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            preview_df = pd.read_excel(uploaded_file, header=None, nrows=5)
            likely_header_row = preview_df.notnull().sum(axis=1).idxmax()
            df = pd.read_excel(uploaded_file, header=likely_header_row)

        # Then show data processing options to user
        df = process_data_with_user_options(df)
        # Let user select columns to convert to datetime
        df = convert_selected_columns_to_datetime(df)
        # Let user filter by date range (if datetime columns exist)
        df = filter_by_date_range(df)

        return df, None

    except Exception as e:
        return None, str(e)


def process_data_with_user_options(df):
    """Let user configure how to process the data - Sidebar Version"""

    st.subheader("🔧 Data Processing")

    # Show original data info
    st.info(f"📊 Original: {len(df):,} rows × {len(df.columns)} columns")

    # Option 1: Auto-detect or manual
    processing_mode = st.radio(
        "**Choose processing mode:**",
        ["Use all data as-is", "Manual selection", "Auto-detect data start/end"],
        key="sidebar_processing_mode",
    )

    if processing_mode == "Use all data as-is":
        st.success("✅ Using complete dataset")
        return df

    elif processing_mode == "Manual selection":
        return manual_data_selection_sidebar(df)

    else:  # Auto-detect
        return auto_detect_with_options_sidebar(df)


def auto_detect_with_options_sidebar(df):
    """Auto-detect with user-configurable options - Sidebar Version"""

    st.write("**Auto-Detection Settings:**")

    # User can specify skip words
    skip_words_input = st.text_input(
        "Words to skip:",
        value="statement,account,customer,period,report,opening,balance,total,summary",
        help="Rows containing these words will be skipped",
        key="sidebar_skip_words",
    )

    skip_words = [
        word.strip().upper() for word in skip_words_input.split(",") if word.strip()
    ]

    # Detection method
    detection_method = st.selectbox(
        "Detect data start by:",
        [
            "Date patterns",
            "Numeric patterns",
            "Non-empty after empty",
            "First non-header row",
        ],
        key="sidebar_detection_method",
    )

    # Data end detection
    cut_at_empty = st.checkbox(
        "Cut when first column ends", value=True, key="sidebar_cut_empty"
    )

    # Add apply button for better control
    if st.button("🔍 Apply Auto-Detection", key="sidebar_apply_detection"):
        result_df = apply_auto_detection(df, skip_words, detection_method, cut_at_empty)
        return result_df
    else:
        # Show preview of what would happen without actually applying
        st.info("👆 Click 'Apply Auto-Detection' to process the data")
        return df


def manual_data_selection_sidebar(df):
    """Let user manually select data range - Sidebar Version"""

    st.write("**Manual Data Range Selection:**")

    # Show current range
    st.info(f"📊 Available rows: 0 to {len(df) - 1}")

    start_row = st.number_input(
        "Start from row:",
        min_value=0,
        max_value=len(df) - 1,
        value=0,
        key="sidebar_start_row",
    )

    end_row = st.number_input(
        "End at row:",
        min_value=start_row,
        max_value=len(df) - 1,
        value=len(df) - 1,
        key="sidebar_end_row",
    )

    # Show what will be selected
    selected_count = end_row - start_row + 1
    st.info(f"📊 Will select: {selected_count:,} rows")

    # Preview selection
    if st.checkbox("Show preview", key="sidebar_preview_check"):
        preview_df = df.iloc[start_row : end_row + 1]
        st.dataframe(preview_df.head(5), use_container_width=True)
        if len(preview_df) > 5:
            st.info(f"Showing first 5 rows of {len(preview_df)} selected rows")

    # Apply selection
    result_df = df.iloc[start_row : end_row + 1].copy()

    if len(result_df) != len(df):
        st.success(f"✅ Selected: {len(result_df):,} rows (rows {start_row}-{end_row})")

    return result_df


def apply_auto_detection(df, skip_words, detection_method, cut_at_empty):
    """Apply auto-detection with user settings"""

    if df.empty:
        return df

    first_column = df.columns[0]
    first_col_data = df[first_column]

    # Find data start based on user's choice
    data_start_index = find_data_start_dynamic(
        first_col_data, skip_words, detection_method
    )

    if data_start_index is None:
        st.warning("Could not detect data start automatically. Using full dataset.")
        return df

    # Cut at empty if requested
    if cut_at_empty:
        data_portion = first_col_data[data_start_index:]
        null_mask = (
            data_portion.isnull()
            | (data_portion == "")
            | (data_portion.astype(str).str.strip() == "")
        )

        if null_mask.any():
            first_null_in_data = null_mask.idxmax()
            df_result = df.loc[data_start_index : first_null_in_data - 1].copy()
        else:
            df_result = df.loc[data_start_index:].copy()
    else:
        df_result = df.loc[data_start_index:].copy()

    st.success(
        f"✅ Processed data: {len(df_result)} rows (started from row {data_start_index})"
    )

    return df_result


def find_data_start_dynamic(first_col_data, skip_words, detection_method):
    """Find data start using user-specified method"""

    for index, value in first_col_data.items():
        if pd.isna(value) or value == "" or str(value).strip() == "":
            continue

        value_str = str(value).strip()

        # Skip user-specified words
        if any(skip_word in value_str.upper() for skip_word in skip_words):
            continue

        # Apply detection method
        if detection_method == "Date patterns":
            if is_date_pattern(value_str):
                return index

        elif detection_method == "Numeric patterns":
            if is_numeric_pattern(value_str):
                return index

        elif detection_method == "Non-empty after empty":
            # First non-empty value after encountering empty ones
            return index

        elif detection_method == "First non-header row":
            # First value that doesn't look like a header
            if not looks_like_header(value_str):
                return index

    return None


def is_date_pattern(value_str):
    """Check for date patterns"""
    date_patterns = [
        r"\d{1,2}-\d{1,2}-\d{4}",
        r"\d{4}-\d{1,2}-\d{1,2}",
        r"\d{1,2}/\d{1,2}/\d{4}",
    ]
    return any(re.match(pattern, value_str) for pattern in date_patterns)


def is_numeric_pattern(value_str):
    """Check for numeric patterns"""
    try:
        float(value_str.replace(",", ""))
        return True
    except:
        return False


def looks_like_header(value_str):
    """Check if value looks like a header"""
    # Headers are usually short, all caps, or contain common header words
    header_indicators = ["DATE", "TYPE", "NUMBER", "AMOUNT", "DESCRIPTION", "ID"]
    return len(value_str) < 20 and (
        value_str.isupper()
        or any(indicator in value_str.upper() for indicator in header_indicators)
    )


def convert_selected_columns_to_datetime(df):
    """Let user select which columns to convert to datetime - Sidebar Version"""

    st.subheader("🕒 DateTime Conversion")

    # Show current column types in compact format
    if st.checkbox("Show column types", key="sidebar_show_types"):
        for col in df.columns:
            st.text(f"{col}: {df[col].dtype}")

    # Let user select columns to convert
    columns_to_convert = st.multiselect(
        "**Select columns to convert:**",
        options=df.columns.tolist(),
        help="Choose columns that contain date/time data",
        key="sidebar_datetime_cols",  # Unique key
    )

    # Convert selected columns
    if columns_to_convert:
        if st.button("Convert Selected Columns", key="sidebar_convert_btn"):
            converted_successfully = []
            conversion_errors = []

            for col in columns_to_convert:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    converted_successfully.append(col)
                except Exception as e:
                    conversion_errors.append(f"{col}: {str(e)}")

            # Show results
            if converted_successfully:
                st.success(f"✅ Converted: {', '.join(converted_successfully)}")

            if conversion_errors:
                st.error(f"❌ Failed: {', '.join(conversion_errors)}")

            st.rerun()

    return df


def filter_by_date_range(df):
    """Let user filter data by date range - Sidebar Version"""

    # Find datetime columns
    datetime_cols = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)

    if not datetime_cols:
        st.info("ℹ️ No datetime columns found")
        return df

    st.subheader("📅 Date Range Filter")

    # Let user choose which datetime column to filter by
    date_column = st.selectbox(
        "**Select datetime column:**",
        options=datetime_cols,
        key="sidebar_date_column",
    )

    # Get min and max dates from selected column
    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()

    # Show available date range
    st.info(f"📅 Available: {min_date} to {max_date}")

    # Date range selection
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "**Start:**",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="sidebar_start_date",
        )

    with col2:
        end_date = st.date_input(
            "**End:**",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="sidebar_end_date",
        )

    # Add skip filter option
    skip_filter = st.checkbox("Skip date filtering", key="sidebar_skip_date_filter")

    if skip_filter:
        st.info("📊 Using all data (no date filter)")
        return df

    # Apply date filter
    if start_date <= end_date:
        # Convert date inputs to datetime for comparison
        start_datetime = pd.to_datetime(start_date)
        end_datetime = (
            pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        )

        # Filter dataframe
        filtered_df = df[
            (df[date_column] >= start_datetime) & (df[date_column] <= end_datetime)
        ].copy()

        # Show filtering results
        original_count = len(df)
        filtered_count = len(filtered_df)

        if filtered_count != original_count:
            st.success(
                f"✅ Filtered: {filtered_count:,} rows (from {original_count:,})"
            )
        else:
            st.info("📊 No filtering applied - all data included")

        return filtered_df
    else:
        st.error("❌ Start date must be before end date")
        return df
