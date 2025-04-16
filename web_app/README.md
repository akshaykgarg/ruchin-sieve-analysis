# Beach Sand Analysis Web Application

A Flask-based web application for analyzing beach sand samples using sieve analysis. The application allows users to upload sieve analysis data, processes it to calculate key parameters (D50, Cu, So), and evaluates the samples against established criteria for beach replenishment projects.

## Features

- Upload and import sieve analysis data from Excel files
- Calculate key parameters:
  - D50 (median particle size)
  - Cu (coefficient of uniformity)
  - So (sorting coefficient)
  - Percent passing through 0.063mm sieve
- Generate particle size distribution plots
- Evaluate compliance with established criteria
- Compare different samples
- Download results in CSV format
- Visual dashboard displaying all samples and their metrics

## Installation

1. Clone the repository
2. Create a virtual environment (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database
   ```bash
   python init_db.py
   ```

## Usage

1. Start the Flask application
   ```bash
   python app.py
   ```
2. Open your browser and navigate to http://localhost:5000
3. Upload your sieve analysis data in Excel format
4. View the analysis results

## Data Format

The application expects Excel files with the following columns:
- Sieve Size (mm): The size of each sieve in millimeters
- Weight Retained (g): The weight of sand retained on each sieve

## Development

The application is built with:
- Flask (web framework)
- SQLite (database)
- Pandas (data processing)
- Matplotlib (plotting)
- Bootstrap 5 (frontend)

## Project Structure

```
web_app/
│
├── app.py                 # Main Flask application
├── init_db.py             # Database initialization script
├── requirements.txt       # Dependencies
│
├── static/                # Static files
│   ├── css/               # CSS stylesheets
│   │   └── style.css      # Custom styles
│   ├── js/                # JavaScript files
│   │   └── script.js      # Custom scripts
│   └── plots/             # Generated plots
│
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Home page
│   ├── upload.html        # Upload form
│   ├── samples.html       # List of samples
│   └── sample_detail.html # Sample analysis page
│
└── uploads/               # Uploaded files
```

## License

MIT 