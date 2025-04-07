
import os
import pandas as pd

def create_standard_csv(file_path):
    """
    Creates a standard CSV file with a normal header row.
    
    The file will include the DataFrame's column names as the first row.
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
    # Write to CSV with header=True so the column names are included.
    df.to_csv(file_path, index=False)
    print(f"Created standard CSV file at: {file_path}")

def create_header1_csv(file_path):
    """
    Creates a CSV file where the intended header row is not the first row.
    
    The file is built from raw rows: row 0 contains junk values,
    and row 1 contains the intended header.
    """
    rows = [
        ["meta", "comp", "comp", "comp", "comp"],
        ["Sample", "SiO2", "FeOt", "Na2O", "MgO"],
        ["name1", 1.5, 2.5, 3.5, 12.1],
        ["name2", 1.3, 1.4, 1.6, 11.1],
        ["name3", 1.2, 2.1, 1.7, 10.1]
    ]
    df = pd.DataFrame(rows)
    # Write the file without a header, so that the rows remain exactly as provided.
    df.to_csv(file_path, index=False, header=False)
    print(f"Created CSV file with intended header row in row 1 at: {file_path}")

if __name__ == '__main__':
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    standard_csv = os.path.join(output_dir, "test_data_standard.csv")
    header1_csv = os.path.join(output_dir, "test_data_header1.csv")
    
    create_standard_csv(standard_csv)
    create_header1_csv(header1_csv)
