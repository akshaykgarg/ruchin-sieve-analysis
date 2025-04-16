import sqlite3
import os
import datetime

DATABASE_PATH = 'web_app/beach_sand.db'

def init_db():
    """Initialize the database with the required tables."""
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Drop tables if they exist
    cursor.execute('DROP TABLE IF EXISTS sieve_data')
    cursor.execute('DROP TABLE IF EXISTS analysis_results')
    cursor.execute('DROP TABLE IF EXISTS samples')
    
    # Create samples table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT DEFAULT 'original',
        date TEXT NOT NULL,
        location TEXT,
        d10 REAL,
        d25 REAL,
        d50 REAL,
        d60 REAL,
        d75 REAL,
        cu REAL,
        so REAL,
        percent_passing_0063 REAL,
        criteria_met INTEGER,
        d50_meets_criteria INTEGER DEFAULT 0,
        cu_meets_criteria INTEGER DEFAULT 0,
        so_meets_criteria INTEGER DEFAULT 0,
        fines_meets_criteria INTEGER DEFAULT 0,
        plot_file TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create sieve_data table to store individual sieve measurements
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sieve_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id INTEGER,
        sieve_size REAL,
        weight_retained REAL,
        percent_retained REAL,
        cumulative_retained REAL,
        percent_passing REAL,
        FOREIGN KEY (sample_id) REFERENCES samples (id) ON DELETE CASCADE
    )
    ''')
    
    # Create analysis_results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id INTEGER NOT NULL,
        d10 REAL,
        d25 REAL,
        d50 REAL,
        d60 REAL,
        d75 REAL,
        cu REAL,
        so REAL,
        plot_filename TEXT,
        date_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sample_id) REFERENCES samples (id) ON DELETE CASCADE
    )
    ''')
    
    # Create an index on the sample_id column for faster lookups
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_sieve_data_sample_id ON sieve_data (sample_id)
    ''')
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {DATABASE_PATH}")

def add_test_data():
    """Add some test data to the database."""
    # Use absolute path for database
    db_path = os.path.abspath(DATABASE_PATH)
    print(f"Using database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if we already have test data
    cursor.execute("SELECT COUNT(*) FROM samples")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"Test data already exists ({count} samples). Skipping...")
        conn.close()
        return
    
    print("Adding test data...")
    
    # Sample data
    samples = [
        {
            'name': 'Beach Sample 1 - Original',
            'type': 'original',
            'date': datetime.date.today().isoformat(),
            'location': 'North Beach',
            'd10': 0.148,
            'd25': 0.205,
            'd50': 0.240,
            'd60': 0.265,
            'd75': 0.315,
            'cu': 1.79,
            'so': 1.24,
            'percent_passing_0063': 3.2,
            'criteria_met': 3,
            'd50_meets_criteria': 0,
            'cu_meets_criteria': 1,
            'so_meets_criteria': 1,
            'fines_meets_criteria': 1,
            'plot_file': 'sample1_original_distribution.png'
        },
        {
            'name': 'Beach Sample 1 - 1mm Underflow',
            'type': 'underflow',
            'date': datetime.date.today().isoformat(),
            'location': 'North Beach',
            'd10': 0.165,
            'd25': 0.225,
            'd50': 0.275,
            'd60': 0.300,
            'd75': 0.345,
            'cu': 1.82,
            'so': 1.24,
            'percent_passing_0063': 2.1,
            'criteria_met': 4,
            'd50_meets_criteria': 1,
            'cu_meets_criteria': 1,
            'so_meets_criteria': 1,
            'fines_meets_criteria': 1,
            'plot_file': 'sample1_underflow_distribution.png'
        },
        {
            'name': 'Beach Sample 2 - Original',
            'type': 'original',
            'date': (datetime.date.today() - datetime.timedelta(days=7)).isoformat(),
            'location': 'South Beach',
            'd10': 0.105,
            'd25': 0.165,
            'd50': 0.195,
            'd60': 0.215,
            'd75': 0.245,
            'cu': 2.05,
            'so': 1.22,
            'percent_passing_0063': 6.8,
            'criteria_met': 2,
            'd50_meets_criteria': 0,
            'cu_meets_criteria': 1,
            'so_meets_criteria': 1,
            'fines_meets_criteria': 0,
            'plot_file': 'sample2_original_distribution.png'
        }
    ]
    
    # Insert sample data
    for sample in samples:
        print(f"Adding sample: {sample['name']}")
        cursor.execute('''
        INSERT INTO samples (
            name, type, date, location, d10, d25, d50, d60, d75, cu, so, 
            percent_passing_0063, criteria_met, d50_meets_criteria, 
            cu_meets_criteria, so_meets_criteria, fines_meets_criteria, plot_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sample['name'], sample['type'], sample['date'], sample['location'],
            sample['d10'], sample['d25'], sample['d50'], sample['d60'], sample['d75'],
            sample['cu'], sample['so'], sample['percent_passing_0063'], sample['criteria_met'],
            sample['d50_meets_criteria'], sample['cu_meets_criteria'], 
            sample['so_meets_criteria'], sample['fines_meets_criteria'], sample['plot_file']
        ))
        
        sample_id = cursor.lastrowid
        print(f"Sample added with ID: {sample_id}")
        
        # Add sieve data for this sample
        # The sieve data is different for each sample, so we'll generate it based on the D values
        sieve_sizes = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.063, 'pan']
        
        for sieve_size in sieve_sizes:
            # Generate some reasonable values
            if sieve_size == 'pan':
                size_val = 0.001  # For calculations
                percent_passing = 0
            else:
                size_val = sieve_size
                # Calculate percent passing using a log-normal approximation
                if size_val > sample['d50'] * 10:
                    percent_passing = 0.1
                elif size_val > sample['d50'] * 5:
                    percent_passing = 1
                elif size_val > sample['d50'] * 2:
                    percent_passing = 5
                elif size_val > sample['d50']:
                    percent_passing = 25
                elif size_val > sample['d25']:
                    percent_passing = 50
                elif size_val > sample['d10']:
                    percent_passing = 75
                elif size_val > 0.063:
                    percent_passing = 90
                else:
                    percent_passing = 97
            
            # For percent retained, we'll work backwards from percent passing
            if sieve_size == 4.0:
                cumulative_retained = 0
            else:
                prev_idx = sieve_sizes.index(sieve_size) - 1
                prev_size = sieve_sizes[prev_idx]
                if prev_size == 'pan':
                    prev_passing = 0
                else:
                    # Find the percent passing for the previous sieve
                    if prev_size > sample['d50'] * 10:
                        prev_passing = 0.1
                    elif prev_size > sample['d50'] * 5:
                        prev_passing = 1
                    elif prev_size > sample['d50'] * 2:
                        prev_passing = 5
                    elif prev_size > sample['d50']:
                        prev_passing = 25
                    elif prev_size > sample['d25']:
                        prev_passing = 50
                    elif prev_size > sample['d10']:
                        prev_passing = 75
                    elif prev_size > 0.063:
                        prev_passing = 90
                    else:
                        prev_passing = 97
                
                cumulative_retained = 100 - percent_passing
            
            if sieve_size == 4.0:
                percent_retained = 0
            else:
                prev_idx = sieve_sizes.index(sieve_size) - 1
                prev_size = sieve_sizes[prev_idx]
                if prev_size == 'pan':
                    prev_cumulative = 100
                else:
                    prev_cumulative = 100 - prev_passing
                
                percent_retained = cumulative_retained - prev_cumulative
            
            # Assume a 500g sample for weight calculation
            weight_retained = 500 * (percent_retained / 100)
            
            cursor.execute('''
            INSERT INTO sieve_data (
                sample_id, sieve_size, weight_retained, percent_retained, 
                cumulative_retained, percent_passing
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                sample_id, 
                sieve_size if sieve_size != 'pan' else sieve_size, 
                weight_retained, 
                percent_retained, 
                cumulative_retained, 
                percent_passing
            ))
    
    conn.commit()
    
    # Verify data was added
    cursor.execute("SELECT COUNT(*) FROM samples")
    sample_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sieve_data")
    sieve_count = cursor.fetchone()[0]
    
    print(f"Added {sample_count} samples with {sieve_count} sieve data points")
    
    conn.close()
    print("Test data added successfully")

if __name__ == "__main__":
    init_db()
    add_test_data() 