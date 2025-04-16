#!/usr/bin/env python
import os
import sys
import sqlite3
import tempfile
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add parent directory to path so we can import the existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from import_excel_to_sqlite import import_excel_to_sqlite

# Import functions from sieve_analysis.py
from sieve_analysis import (
    interpolate, find_diameter_at_percent, analyze_sample,
    plot_distribution, generate_envelope_curves, plot_with_envelope
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'beach_sand.db')
app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['STATIC_FOLDER'], 'plots'), exist_ok=True)

# Add template filter for formatting dates
@app.template_filter('formatdate')
def formatdate_filter(date_str):
    """Format a date string for display."""
    if not date_str:
        return ""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%b %d, %Y')
    except:
        return date_str

# Add context processor for the current date (for the footer)
@app.context_processor
def inject_now():
    return {'now': datetime.now}

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def get_sample(sample_id):
    """Get a sample by ID from the database."""
    conn = get_db_connection()
    sample = conn.execute('SELECT * FROM samples WHERE id = ?', (sample_id,)).fetchone()
    conn.close()
    return sample

def get_sieve_data(sample_id):
    """Get sieve data for a sample from the database."""
    conn = get_db_connection()
    sieve_data = conn.execute('SELECT * FROM sieve_data WHERE sample_id = ? ORDER BY sieve_size DESC', (sample_id,)).fetchall()
    conn.close()
    return sieve_data

def prepare_analysis_data(sieve_data):
    """Convert sieve data to format required by analysis functions."""
    sieve_sizes = []
    percent_passing = []
    
    for row in sieve_data:
        sieve_sizes.append(row['sieve_size'])
        percent_passing.append(row['percent_passing'])
    
    return sieve_sizes, percent_passing

def check_criteria_compliance(analysis_results):
    """Check if analysis results meet design criteria."""
    d50 = analysis_results['d50']
    cu = analysis_results['cu']
    so = analysis_results['so']
    
    # Get percent passing at 0.063mm for fine content
    sieve_sizes = analysis_results['sieve_sizes']
    percent_passing = analysis_results['percent_passing']
    fine_content = interpolate(0.063, sieve_sizes, percent_passing)
    
    criteria = {
        'd50_compliant': 0.25 <= d50 <= 0.35,
        'd50_actual': round(d50, 4),
        'cu_compliant': cu < 2.5,
        'cu_actual': round(cu, 2),
        'so_compliant': 1.1 <= so <= 1.7,
        'so_actual': round(so, 2),
        'fines_compliant': fine_content < 5.0,
        'fines_actual': round(fine_content, 2)
    }
    
    criteria['total_compliant'] = sum([
        criteria['d50_compliant'],
        criteria['cu_compliant'],
        criteria['so_compliant'],
        criteria['fines_compliant']
    ])
    
    return criteria

@app.route('/')
def index():
    """Home page - show list of samples."""
    conn = get_db_connection()
    recent_samples = conn.execute('SELECT * FROM samples ORDER BY date_added DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('index.html', recent_samples=recent_samples)

@app.route('/samples')
def samples():
    """Show a list of all samples."""
    conn = get_db_connection()
    samples = conn.execute('SELECT * FROM samples ORDER BY date_added DESC').fetchall()
    conn.close()
    return render_template('samples.html', samples=samples)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle file upload and import to database."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash(f'File type not allowed. Please upload {", ".join(app.config["ALLOWED_EXTENSIONS"])}', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Save the file temporarily
            filename = secure_filename(file.filename)
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            
            # Import the data
            try:
                sample_name = request.form.get('sample_name', 'Unnamed Sample')
                import_excel_to_sqlite(temp_path, app.config['DATABASE'], sample_name)
                flash('File successfully uploaded and data imported', 'success')
                os.remove(temp_path)
                os.rmdir(temp_dir)
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Error importing data: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('upload.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/sample/<int:sample_id>')
def sample_detail(sample_id):
    """View details of a single sample."""
    sample = get_sample(sample_id)
    if not sample:
        flash('Sample not found', 'danger')
        return redirect(url_for('index'))
    
    sieve_data = get_sieve_data(sample_id)
    
    return render_template('sample_detail.html', 
                          sample=sample, 
                          sieve_data=sieve_data)

@app.route('/sample/<int:sample_id>/analyze')
def analyze(sample_id):
    """Run analysis on a sample and save results."""
    sample = get_sample(sample_id)
    if not sample:
        flash('Sample not found', 'danger')
        return redirect(url_for('index'))
    
    sieve_data = get_sieve_data(sample_id)
    sieve_sizes, percent_passing = prepare_analysis_data(sieve_data)
    
    # Run analysis
    try:
        analysis_results = analyze_sample(sieve_sizes, percent_passing)
        
        # Generate plot and save to static folder
        plot_filename = f"sample_{sample_id}_distribution.png"
        plot_path = os.path.join(app.config['STATIC_FOLDER'], 'plots', plot_filename)
        plot_distribution(sieve_sizes, percent_passing, analysis_results, 
                          sample['name'], save_path=plot_path)
        
        # Save analysis results to database
        conn = get_db_connection()
        
        # Check if analysis already exists
        existing = conn.execute('SELECT id FROM analysis_results WHERE sample_id = ?', 
                               (sample_id,)).fetchone()
        
        if existing:
            # Update existing analysis
            conn.execute('''
                UPDATE analysis_results
                SET d10 = ?, d25 = ?, d50 = ?, d60 = ?, d75 = ?, cu = ?, so = ?, plot_filename = ?
                WHERE sample_id = ?
            ''', (
                analysis_results['d10'], analysis_results['d25'], analysis_results['d50'],
                analysis_results['d60'], analysis_results['d75'], analysis_results['cu'],
                analysis_results['so'], plot_filename, sample_id
            ))
        else:
            # Insert new analysis
            conn.execute('''
                INSERT INTO analysis_results 
                (sample_id, d10, d25, d50, d60, d75, cu, so, plot_filename)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sample_id, analysis_results['d10'], analysis_results['d25'], analysis_results['d50'],
                analysis_results['d60'], analysis_results['d75'], analysis_results['cu'],
                analysis_results['so'], plot_filename
            ))
        
        conn.commit()
        conn.close()
        
        flash('Analysis completed successfully', 'success')
    except Exception as e:
        flash(f'Error during analysis: {str(e)}', 'danger')
    
    return redirect(url_for('sample_detail', sample_id=sample_id))

@app.route('/compare', methods=['GET', 'POST'])
def compare_samples():
    """Compare multiple samples."""
    conn = get_db_connection()
    all_samples = conn.execute('SELECT * FROM samples ORDER BY name').fetchall()
    
    if request.method == 'POST':
        sample_ids = request.form.getlist('sample_ids')
        if not sample_ids:
            flash('Please select at least one sample to compare', 'warning')
            return render_template('compare_samples.html', all_samples=all_samples, selected_sample_ids=[])
        
        # Convert to integers
        sample_ids = [int(id) for id in sample_ids]
        
        # Get samples and analyses
        samples = []
        analyses = []
        criteria_results = []
        
        for sample_id in sample_ids:
            sample = conn.execute('SELECT * FROM samples WHERE id = ?', (sample_id,)).fetchone()
            if sample:
                samples.append(sample)
                
                analysis = conn.execute('SELECT * FROM analysis_results WHERE sample_id = ?', 
                                      (sample_id,)).fetchone()
                
                if analysis:
                    analyses.append(analysis)
                    
                    sieve_data = conn.execute('''
                        SELECT * FROM sieve_data 
                        WHERE sample_id = ? 
                        ORDER BY sieve_size DESC
                    ''', (sample_id,)).fetchall()
                    
                    sieve_sizes = [row['sieve_size'] for row in sieve_data]
                    percent_passing = [row['percent_passing'] for row in sieve_data]
                    
                    criteria = check_criteria_compliance({
                        'd50': analysis['d50'],
                        'cu': analysis['cu'],
                        'so': analysis['so'],
                        'sieve_sizes': sieve_sizes,
                        'percent_passing': percent_passing
                    })
                    
                    criteria_results.append(criteria)
        
        # Generate combined plot if we have analyses for all samples
        combined_plot = None
        if len(analyses) == len(samples) and len(samples) > 0:
            plt.figure(figsize=(10, 6))
            
            # Plot each sample
            for i, sample_id in enumerate(sample_ids):
                sieve_data = conn.execute('''
                    SELECT * FROM sieve_data 
                    WHERE sample_id = ? 
                    ORDER BY sieve_size DESC
                ''', (sample_id,)).fetchall()
                
                sieve_sizes = [row['sieve_size'] for row in sieve_data]
                percent_passing = [row['percent_passing'] for row in sieve_data]
                
                # Plot with different marker and line style for each sample
                markers = ['o', 's', '^', 'd', 'v', '<', '>', 'p', '*']
                linestyles = ['-', '--', '-.', ':']
                
                marker = markers[i % len(markers)]
                linestyle = linestyles[i % len(linestyles)]
                
                plt.semilogx(sieve_sizes, percent_passing, marker=marker, linestyle=linestyle, 
                           label=samples[i]['name'])
            
            plt.xlabel('Particle Size (mm)')
            plt.ylabel('Percent Passing (%)')
            plt.title('Particle Size Distribution Comparison')
            plt.grid(True, which="both", ls="-")
            plt.legend()
            
            # Save the plot
            combined_plot = f"combined_plot_{uuid.uuid4().hex[:8]}.png"
            plot_path = os.path.join(app.config['STATIC_FOLDER'], 'plots', combined_plot)
            plt.savefig(plot_path)
            plt.close()
            
            combined_plot = f"plots/{combined_plot}"
        
        conn.close()
        
        return render_template('compare_samples.html', 
                              all_samples=all_samples,
                              selected_sample_ids=sample_ids,
                              samples=samples,
                              analyses=analyses,
                              criteria_results=criteria_results,
                              combined_plot=combined_plot)
    
    conn.close()
    return render_template('compare_samples.html', all_samples=all_samples, selected_sample_ids=[])

@app.route('/download/<int:sample_id>')
def download(sample_id):
    """Download sample data as Excel file."""
    sample = get_sample(sample_id)
    if not sample:
        flash('Sample not found', 'danger')
        return redirect(url_for('index'))
    
    sieve_data = get_sieve_data(sample_id)
    
    # Create DataFrame from sieve data
    data = {
        'Sieve Size (mm)': [row['sieve_size'] for row in sieve_data],
        'Weight Retained (g)': [row['weight_retained'] for row in sieve_data],
        'Percent Retained (%)': [row['percent_retained'] for row in sieve_data],
        'Cumulative Retained (%)': [row['cumulative_retained'] for row in sieve_data],
        'Percent Passing (%)': [row['percent_passing'] for row in sieve_data],
    }
    
    df = pd.DataFrame(data)
    
    # Create a temporary file for the Excel
    temp_dir = tempfile.mkdtemp()
    filename = f"{secure_filename(sample['name'])}_sieve_data.xlsx"
    filepath = os.path.join(temp_dir, filename)
    
    # Write to Excel
    df.to_excel(filepath, index=False, sheet_name='Sieve Data')
    
    # Return the file for download
    return send_file(filepath, 
                     as_attachment=True, 
                     download_name=filename, 
                     last_modified=datetime.now())

@app.route('/delete/<int:sample_id>', methods=['POST'])
def delete(sample_id):
    """Delete a sample and its associated data."""
    sample = get_sample(sample_id)
    if not sample:
        flash('Sample not found', 'danger')
        return redirect(url_for('index'))
    
    try:
        conn = get_db_connection()
        # Delete the sample (cascade will remove sieve data)
        conn.execute('DELETE FROM samples WHERE id = ?', (sample_id,))
        conn.commit()
        conn.close()
        flash(f'Sample "{sample["name"]}" deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting sample: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/envelope')
def generate_envelope():
    """Generate and display grading envelope."""
    conn = get_db_connection()
    
    # Get all samples that have analysis results
    samples_with_analysis = conn.execute('''
        SELECT s.id, s.name 
        FROM samples s
        JOIN analysis_results a ON s.id = a.sample_id
        ORDER BY s.name
    ''').fetchall()
    
    # Generate envelope plot
    envelope_filename = "grading_envelope.png"
    envelope_path = os.path.join(app.config['STATIC_FOLDER'], 'plots', envelope_filename)
    
    # Get data for all samples to include in the envelope plot
    sample_data = []
    
    for sample in samples_with_analysis:
        sieve_data = conn.execute('''
            SELECT sieve_size, percent_passing 
            FROM sieve_data 
            WHERE sample_id = ? 
            ORDER BY sieve_size DESC
        ''', (sample['id'],)).fetchall()
        
        analysis = conn.execute('''
            SELECT d10, d25, d50, d60, d75, cu, so 
            FROM analysis_results 
            WHERE sample_id = ?
        ''', (sample['id'],)).fetchone()
        
        if sieve_data and analysis:
            sample_data.append({
                'name': sample['name'],
                'sieve_sizes': [row['sieve_size'] for row in sieve_data],
                'percent_passing': [row['percent_passing'] for row in sieve_data],
                'analysis': dict(analysis)
            })
    
    if sample_data:
        # Generate envelope for D50 = 0.35mm
        plot_with_envelope(
            sample_data,
            d50_target=0.35,
            cu_max=2.5,
            so_range=(1.1, 1.7),
            fines_max=5.0,
            title="Beach Sand Grading Envelope (D50 = 0.35mm)",
            save_path=envelope_path
        )
    
    conn.close()
    
    return render_template('envelope.html', 
                          samples=samples_with_analysis,
                          envelope_plot=f"plots/{envelope_filename}" if sample_data else None)

# Create database tables if they don't exist
def init_db():
    conn = get_db_connection()
    
    # Create samples table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create sieve_data table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sieve_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL,
            sieve_size REAL NOT NULL,
            weight_retained REAL NOT NULL,
            percent_retained REAL NOT NULL,
            cumulative_retained REAL NOT NULL,
            percent_passing REAL NOT NULL,
            FOREIGN KEY (sample_id) REFERENCES samples (id)
        )
    ''')
    
    # Create analysis_results table
    conn.execute('''
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
            FOREIGN KEY (sample_id) REFERENCES samples (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5001) 