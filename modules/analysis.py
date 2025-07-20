import streamlit as st
from .utils import get_numeric_columns

def show_analysis_tab(df):
    """Display analysis tab content"""
    st.subheader("Analysis")


    # From (column selection)
    from_column = st.selectbox("From Column:", df.columns.tolist())

    # I need (value selection from selected column)
    column_values = df[from_column].dropna().unique().tolist()
    # Add "All" option at the beginning
    column_values.insert(0, "All")
    selected_value = st.selectbox("I need value:", column_values)

    # To do (function selection)
    functions = ["Add", "Subtract", "Multiply", "Divide", "Count", "Sum", "Average"]
    selected_function = st.selectbox("To do operation:", functions)

    # On the column (target column selection)
    target_column = st.selectbox("On the column:", df.columns.tolist())

    # Value for arithmetic operations (show only when needed)
    operation_value = None
    if selected_function in ["Add", "Subtract", "Multiply", "Divide"]:
        operation_value = st.number_input("With value:", value=1.0)

    # Apply function button
    if st.button("Apply"):
        perform_analysis(df, from_column, selected_value, selected_function, target_column, operation_value)
        if selected_value == "All":
            filtered_df = df
            st.subheader("📋 All Data")
        else:
            filtered_df = df[df[from_column] == selected_value]
            st.subheader(f"📋 Data where {from_column} = {selected_value}")
    
        st.dataframe(filtered_df, use_container_width=True)

def perform_analysis(df, from_column, selected_value, selected_function, target_column, operation_value):
    """Perform the selected analysis operation"""
    
    # Check if "All" is selected or filter by specific value
    if selected_value == "All":
        filtered_df = df  # Use entire dataset
        filter_description = "all data"
    else:
        filtered_df = df[df[from_column] == selected_value]
        filter_description = f"'{selected_value}'"

    if selected_function == "Count":
        result = filtered_df.shape[0]
        st.success(f"Count of rows for {filter_description}: {result}")

    elif selected_function == "Sum" and df[target_column].dtype in ["int64", "float64"]:
        result = filtered_df[target_column].sum()
        st.success(f"Sum of '{target_column}' for {filter_description}: {result}")

    elif selected_function == "Average" and df[target_column].dtype in ["int64", "float64"]:
        result = filtered_df[target_column].mean()
        st.success(f"Average of '{target_column}' for {filter_description}: {result:.2f}")

    elif selected_function in ["Add", "Subtract", "Multiply", "Divide"]:
        if df[target_column].dtype in ["int64", "float64"]:
            # First, sum all values in the target column for filtered rows
            total_sum = filtered_df[target_column].sum()

            # Then perform the operation on that total
            if selected_function == "Add":
                final_result = total_sum + operation_value
            elif selected_function == "Subtract":
                final_result = total_sum - operation_value
            elif selected_function == "Multiply":
                final_result = total_sum * operation_value
            elif selected_function == "Divide":
                final_result = total_sum / operation_value

            st.success(f"Total sum of '{target_column}' for {filter_description}: {total_sum}")
            st.success(f"After {selected_function} {operation_value}: {final_result}")
        else:
            st.error("Mathematical operations only work on numeric columns")
