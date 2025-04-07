import os
import pandas as pd

def create_standard_excel(file_path):
    """
    Creates a standard Excel file with a normal header row.
    
    The file will have a sheet named 'sheet_1' and include the DataFrame's column names.
    """
    df = pd.DataFrame({
        'SiO2': [72.0, 68.5, 76.2],
        'Al2O3': [14.2, 15.8, 12.5],
        'FeOt': [3.5, 4.2, 2.8],
        'CaO': [1.8, 2.2, 1.2],
        'MgO': [0.8, 1.5, 0.5],
        'Na2O': [3.2, 3.8, 3.6],
        'K2O': [4.5, 3.9, 5.2],
        'Sample': ['Sample1', 'Sample2', 'Sample3']
    })
    df.to_excel(file_path, index=False, sheet_name='sheet_1', header=False)
    print(f"Created standard Excel file at: {file_path}")

def create_header1_excel(file_path):
    """
    Creates an Excel file where the intended header row is not the first row.
    
    The file will have a first row with junk values, and the second row
    (row index 1) will contain the intended header.
    
    Since we want to preserve the raw rows (including duplicates) we write without
    letting pandas add its own header.
    """
    # Define rows: row 0 is junk; row 1 is the intended header.
    rows = [
        ["meta", "comp", "comp", "comp", "comp"],
        ["Sample", "SiO2", "FeOt", "Na2O", "MgO"],
        ["name1", 1.5, 2.5, 3.5, 12.1],
        ["name2", 1.3, 1.4, 1.6, 11.1],
        ["name3", 1.2, 2.1, 1.7, 10.1]
    ]
    df = pd.DataFrame(rows)
    # Write the DataFrame as-is (i.e. without writing a separate header)
    df.to_excel(file_path, index=False, header=False, sheet_name='sheet_1')
    print(f"Created Excel file with intended header row in row 1 at: {file_path}")

if __name__ == '__main__':
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    standard_file = os.path.join(output_dir, "test_data_standard.xlsx")
    header1_file = os.path.join(output_dir, "test_data_header1.xlsx")
    
    create_standard_excel(standard_file)
    create_header1_excel(header1_file)
