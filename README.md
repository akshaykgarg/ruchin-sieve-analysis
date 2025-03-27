# Beach Sand Sieve Analysis

This is a Python script to analyze beach sand sieve data and calculate various parameters such as D10, D25, D50, D60, D75, Coefficient of Uniformity (Cu), and Trask Sorting Coefficient (So).

## Setup

The script requires Python with the packages NumPy and Matplotlib. It uses the virtualenvwrapper environment named `ruchin_sieve`.

### Environment Setup

1. Ensure you have virtualenvwrapper installed:
   ```
   pip install virtualenvwrapper
   ```

2. Set up virtualenvwrapper by adding the following to your `.bashrc` or `.zshrc`:
   ```
   export WORKON_HOME=$HOME/.virtualenvs
   source /opt/homebrew/bin/virtualenvwrapper.sh  # Path may vary based on your system
   ```

3. Activate the `ruchin_sieve` environment:
   ```
   workon ruchin_sieve
   ```

4. If the environment doesn't exist, create it:
   ```
   mkvirtualenv ruchin_sieve
   pip install numpy matplotlib
   ```

## Usage

1. Activate the environment:
   ```
   workon ruchin_sieve
   ```

2. Run the script:
   ```
   python sieve_analysis.py
   ```

3. The script will output:
   - The calculated parameters (D10, D25, D50, D60, D75, Cu, So)
   - A classification of the sand's sorting
   - A particle size distribution curve saved as 'particle_size_distribution.png'

## Interpreting Results

- **D10, D25, D50, D60, D75**: Particle sizes (in mm) at which 10%, 25%, 50%, 60%, and 75% of the sample passes through the sieve.
- **Coefficient of Uniformity (Cu)**: Calculated as Cu = D60/D10. Indicates how well-graded the sample is.
- **Trask Sorting Coefficient (So)**: Calculated as So = √(D75/D25). Indicates the degree of sorting:
  - So < 1.2: Very well sorted
  - 1.2 < So < 1.5: Well sorted
  - 1.5 < So < 2.0: Moderately sorted
  - 2.0 < So < 4.0: Poorly sorted
  - So > 4.0: Very poorly sorted 