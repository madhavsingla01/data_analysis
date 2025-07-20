import pandas as pd
import numpy as np

def get_numeric_columns(df):
    """Get list of numeric columns"""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def get_categorical_columns(df):
    """Get list of categorical columns"""
    return df.select_dtypes(include=['object']).columns.tolist()

def calculate_data_quality_score(df):
    """Calculate overall data quality metrics"""
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()
    
    completeness_score = ((total_cells - missing_cells) / total_cells) * 100
    uniqueness_score = ((len(df) - duplicate_rows) / len(df)) * 100
    overall_quality = (completeness_score + uniqueness_score) / 2
    
    return {
        'completeness': completeness_score,
        'uniqueness': uniqueness_score,
        'overall': overall_quality,
        'missing_cells': missing_cells,
        'duplicate_rows': duplicate_rows
    }
