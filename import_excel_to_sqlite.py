#!/usr/bin/env python3
"""
Excel Sieve Analysis Data Importer
Parses an Excel file containing sieve analysis data and loads it into an SQLite database.

The specific format expected is:
- Sieve sizes in the leftmost data column (Sieve Size, mm)
- Sample names in row 2 (Sample-BS 001, Sample-BS 002, etc.)
- % Passing headers in row 3, aligned with sample names
- Actual data starts from row 4
"""

import sqlite3
import pandas as pd
import os
import numpy as np

DB_PATH = "sieve_analysis.db"
EXCEL_PATH = "sample data.xlsx"

def create_database():
    """Creates the SQLite database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create samples table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Create sieve_data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sieve_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id INTEGER NOT NULL,
        sieve_size REAL NOT NULL,
        percent_passing REAL NOT NULL,
        FOREIGN KEY (sample_id) REFERENCES samples (id) ON DELETE CASCADE, 
        UNIQUE(sample_id, sieve_size) 
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

def import_excel_to_sqlite():
    """
    Parses the Excel file with sieve analysis data and imports it into SQLite.
    
    The Excel file should have a specific structure:
    - Sieve sizes in the leftmost column (usually B)
    - Sample names in row 2 (usually columns C, E, G, etc.)
    - % Passing headers in row 3 (usually columns C, E, G, etc.)
    - Actual data starting from row 4
    """
    if not os.path.exists(EXCEL_PATH):
        print(f"ERROR: Excel file not found at {EXCEL_PATH}")
        return
        
    print(f"Reading Excel file: {EXCEL_PATH}")
    
    try:
        # Read the Excel file, skipping the first row which is typically empty
        # Row 2 (index 1) contains sample names
        # Row 3 (index 2) contains column headers like "Sieve Size, mm" and "% Passing"
        # Row 4+ (index 3+) contains the actual data
        df = pd.read_excel(EXCEL_PATH, skiprows=1)
        
        # Print the column names for debugging
        print("Excel columns after skiprows=1:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
            
        # First row of df now has the column headers (originally row 3 in Excel)
        # Get the sieve size column name (usually the leftmost column)
        sieve_col = None
        
        # Read the first few rows to check for "Sieve Size" text
        df_first_rows = pd.read_excel(EXCEL_PATH, nrows=5, header=None)
        print("\nChecking first 5 rows for 'Sieve Size' text:")
        for idx, row in df_first_rows.iterrows():
            print(f"Row {idx}: {row.values}")
        
        # Try different approach - read without setting any headers
        df_raw = pd.read_excel(EXCEL_PATH, header=None)
        
        # Find the row containing 'Sieve Size'
        sieve_row_idx = None
        for idx, row in df_raw.iterrows():
            row_values = [str(val).strip() for val in row.values if pd.notna(val)]
            row_text = " ".join(row_values).lower()
            if 'sieve size' in row_text:
                sieve_row_idx = idx
                print(f"Found 'Sieve Size' in row {idx}: {row_values}")
                break
                
        if sieve_row_idx is None:
            print("ERROR: Could not find row containing 'Sieve Size'")
            return
            
        # Re-read with the correct header rows
        # Sample names should be in the row above 'Sieve Size'
        sample_row_idx = sieve_row_idx - 1
        
        # Read sample names from the row above sieve_row_idx
        df_samples = pd.read_excel(EXCEL_PATH, header=sample_row_idx)
        
        # Read actual data with sieve_row_idx as header
        df_data = pd.read_excel(EXCEL_PATH, header=sieve_row_idx)
        
        print("\nSample row columns:")
        for i, col in enumerate(df_samples.columns):
            print(f"  {i}: {col}")
            
        print("\nData row columns:")
        for i, col in enumerate(df_data.columns):
            print(f"  {i}: {col}")
        
        # Now find the Sieve Size column in df_data
        sieve_col = None
        for col in df_data.columns:
            col_str = str(col).lower()
            if 'sieve' in col_str and 'size' in col_str:
                sieve_col = col
                print(f"Found sieve column: '{sieve_col}'")
                break
                
        # If still not found, try a more flexible approach
        if not sieve_col:
            print("Trying flexible approach to find sieve column...")
            # Look for the leftmost column containing numeric values
            for col in df_data.columns:
                values = pd.to_numeric(df_data[col], errors='coerce')
                if values.notna().sum() > 5:  # At least 5 numeric values
                    sieve_col = col
                    print(f"Using column '{sieve_col}' as sieve size column (contains numeric values)")
                    break
        
        if not sieve_col:
            print("ERROR: Could not find 'Sieve Size' column")
            return
        
        # Extract all sieve sizes (should be from second row onward in the dataframe)
        sieve_sizes = pd.to_numeric(df_data[sieve_col], errors='coerce').dropna().tolist()
        print(f"Found {len(sieve_sizes)} sieve sizes")
        
        # Find sample columns from the sample header row (df_samples)
        # These are the columns with "Sample-BS" in their name
        sample_columns = []
        for col in df_samples.columns:
            if isinstance(col, str) and 'Sample-BS' in col:
                sample_columns.append(col)
        
        if not sample_columns:
            print("ERROR: No sample columns found - could not find 'Sample-BS' in column names")
            print(f"Available columns in sample row: {list(df_samples.columns)}")
            return
            
        print(f"Found {len(sample_columns)} sample columns: {sample_columns}")
        
        # Create a mapping from sample names to data columns
        # We need to find which columns in df_data correspond to the data for each sample
        sample_data_pairs = []
        
        # The sample columns in df_samples should map to "% Passing" columns in df_data
        # The mapping will depend on column positions
        
        for sample_col in sample_columns:
            # Get the position of this column in df_samples
            sample_idx = list(df_samples.columns).index(sample_col)
            
            # Find the corresponding data column in df_data
            # It should be at the same position
            if sample_idx < len(df_data.columns):
                data_col = df_data.columns[sample_idx]
                sample_data_pairs.append((sample_col, data_col))
                print(f"Mapped sample '{sample_col}' (index {sample_idx}) to data column '{data_col}'")
            else:
                print(f"Warning: Could not find data column for sample '{sample_col}'")
        
        if not sample_data_pairs:
            print("ERROR: Could not map any samples to data columns")
            return
        
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert the data
        total_samples = 0
        total_datapoints = 0
        
        for sample_name, percent_col in sample_data_pairs:
            # Insert the sample
            cursor.execute("INSERT OR IGNORE INTO samples (name) VALUES (?)", (sample_name,))
            if cursor.rowcount > 0:
                print(f"Added new sample: {sample_name}")
                total_samples += 1
            
            # Get the sample_id
            cursor.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
            sample_id = cursor.fetchone()[0]
            
            # Get percentage values for this sample
            percent_values = df_data[percent_col].tolist()
            
            # Insert sieve data points
            sample_datapoints = 0
            for i, sieve_size in enumerate(sieve_sizes):
                if i < len(percent_values):
                    try:
                        # Convert to float in case it's stored as string with % sign
                        percent_value = percent_values[i]
                        if isinstance(percent_value, str):
                            percent_value = float(percent_value.replace('%', ''))
                        
                        # Only insert valid numbers
                        if pd.notna(percent_value):
                            # The values are stored as decimal (0-1) in Excel, 
                            # but we want percentage (0-100)
                            if percent_value <= 1:
                                percent_value *= 100
                                
                            cursor.execute("""
                                INSERT OR REPLACE INTO sieve_data 
                                (sample_id, sieve_size, percent_passing)
                                VALUES (?, ?, ?)
                            """, (sample_id, sieve_size, percent_value))
                            sample_datapoints += 1
                    except (ValueError, TypeError) as e:
                        print(f"Error processing data for {sample_name}, sieve {sieve_size}: {e}")
            
            print(f"  Inserted {sample_datapoints} data points for {sample_name}")
            total_datapoints += sample_datapoints
        
        conn.commit()
        conn.close()
        
        print(f"Successfully imported {total_samples} samples with {total_datapoints} data points")
        
    except Exception as e:
        print(f"ERROR: Failed to process Excel file: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

def verify_data_from_db():
    """Reads data from SQLite and displays it for verification."""
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # First, get a list of all samples
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM samples ORDER BY name")
        samples = cursor.fetchall()
        
        if not samples:
            print("No samples found in the database")
            return
            
        print(f"\nFound {len(samples)} samples in the database:")
        for sample_id, name in samples:
            # Count data points for this sample
            cursor.execute("SELECT COUNT(*) FROM sieve_data WHERE sample_id = ?", (sample_id,))
            data_count = cursor.fetchone()[0]
            print(f"  {name}: {data_count} data points")
        
        # Now create a pivot table view of all data
        query = """
        SELECT 
            sd.sieve_size, 
            s.name as sample_name, 
            sd.percent_passing
        FROM sieve_data sd
        JOIN samples s ON sd.sample_id = s.id
        ORDER BY s.name, sd.sieve_size DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No data found in the database")
            return
            
        # Create a pivot table with sieve sizes as rows and sample names as columns
        pivot_df = df.pivot(index='sieve_size', columns='sample_name', values='percent_passing')
        
        # Sort by sieve size descending
        pivot_df = pivot_df.sort_index(ascending=False)
        
        # Display the data
        print("\nSieve Data from Database:")
        print(pivot_df.to_string(float_format="%.1f%%"))
        
    except Exception as e:
        print(f"ERROR: Failed to verify data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def main():
    """Main function to run the import and verification."""
    print("\n=== Sieve Analysis Data Importer ===")
    
    # Check for virtualenv
    venv = os.environ.get('VIRTUAL_ENV', '')
    if venv:
        print(f"Using Python environment: {os.path.basename(venv)}")
        if 'ruchin_sieve' not in venv:
            print("WARNING: Not running in 'ruchin_sieve' environment!")
    else:
        print("WARNING: Not running in a virtual environment")
    
    # Create the database if it doesn't exist
    create_database()
    
    # Import data from Excel
    if import_excel_to_sqlite():
        # Verify the imported data
        verify_data_from_db()
    
    print("\n=== Import completed ===")

if __name__ == "__main__":
    main() 