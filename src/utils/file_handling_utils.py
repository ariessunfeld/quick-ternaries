"""Utility files for handling xlsx and csv files, like finding the optimal header row"""

import pandas as pd

def find_header_row_excel(file, max_rows_scan, sheet_name):
    """Returns the 'best' header row for an Excel file"""

    min_score = float('inf')
    best_header_row = None

    try:
        df = pd.read_excel(file, sheet_name)
    except FileNotFoundError as err:
        print(err)
        return None

    n_rows_search = min(len(df), max_rows_scan)

    for i in range(n_rows_search):
        df = pd.read_excel(file, sheet_name, header=i, nrows=n_rows_search+1)

        columns = df.columns.tolist()
        num_unnamed = sum('unnamed' in str(name).lower() for name in columns)
        num_unique = len(set(columns))
        type_consistency = sum(df[col].apply(type).nunique() == 1 for col in df.columns)

        total_score = num_unnamed - num_unique - type_consistency

        if total_score < min_score:
            min_score = total_score
            best_header_row = i

    return best_header_row

def find_header_row_csv(file, max_rows_scan):
    """Returns the 'best' header row for a CSV file"""
    
    min_score = float('inf')
    best_header_row = None

    try:
        df = pd.read_csv(file)
    except FileNotFoundError as err:
        print(err)
        return None

    n_rows_search = min(len(df)-1, max_rows_scan)

    for i in range(n_rows_search):
        df = pd.read_csv(file, header=i, nrows=n_rows_search+1)

        columns = df.columns.tolist()
        num_unnamed = sum('unnamed' in str(name).lower() for name in columns)
        num_unique = len(set(columns))
        type_consistency = sum(df[col].apply(type).nunique() == 1 for col in df.columns)

        total_score = num_unnamed - num_unique - type_consistency

        if total_score < min_score:
            min_score = total_score
            best_header_row = i

    return best_header_row
