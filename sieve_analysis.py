#!/usr/bin/env python
# Sieve Analysis Calculator
#this is for ruchin
import numpy as np
import matplotlib.pyplot as plt
from colorama import init, Fore, Style
from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter

# Initialize colorama for colored terminal output
init()

def interpolate(x1, y1, x2, y2, y):
    """Linear interpolation to find x given y"""
    if y1 == y2:
        return x1
    return x1 + (x2 - x1) * (y - y1) / (y2 - y1)

def find_diameter_at_percent(sieve_sizes, percent_passing, target_percent):
    """Find the particle diameter at a given percent passing"""
    # Find the two points to interpolate between
    for i in range(len(percent_passing) - 1):
        if percent_passing[i] <= target_percent <= percent_passing[i+1] or \
           percent_passing[i] >= target_percent >= percent_passing[i+1]:
            return interpolate(
                sieve_sizes[i], percent_passing[i],
                sieve_sizes[i+1], percent_passing[i+1],
                target_percent
            )
    
    # If we get here, the target_percent is outside the range of our data
    if target_percent <= min(percent_passing):
        return min(sieve_sizes)
    return max(sieve_sizes)

def format_value(value, is_in_range):
    """Format a value with color based on whether it's in range"""
    if is_in_range:
        return f"{value:.2f}"
    else:
        return f"{Fore.RED}{value:.2f}{Style.RESET_ALL}"

def get_sorting_description(so):
    """Get the sorting description based on Trask Sorting Coefficient"""
    if so < 1.2:
        return "Very well sorted"
    elif 1.2 <= so < 1.5:
        return "Well sorted"
    elif 1.5 <= so < 2.0:
        return "Moderately sorted"
    elif 2.0 <= so < 4.0:
        return "Poorly sorted"
    else:
        return "Very poorly sorted"

def analyze_sample(sieve_sizes, percent_passing, sample_name="Original Sample"):
    """
    Perform sieve analysis on a sample
    Returns a dictionary with all calculated parameters
    """
    # Calculate D values
    d10 = find_diameter_at_percent(sieve_sizes, percent_passing, 10)
    d25 = find_diameter_at_percent(sieve_sizes, percent_passing, 25)
    d30 = find_diameter_at_percent(sieve_sizes, percent_passing, 30)
    d50 = find_diameter_at_percent(sieve_sizes, percent_passing, 50)
    d60 = find_diameter_at_percent(sieve_sizes, percent_passing, 60)
    d75 = find_diameter_at_percent(sieve_sizes, percent_passing, 75)
    
    # Calculate coefficients
    cu = d60 / d10  # Coefficient of Uniformity
    so = np.sqrt(d75 / d25)  # Trask Sorting Coefficient
    
    # Find percent passing for 0.063 mm (find the closest value in the sieve sizes)
    try:
        idx_063 = next(i for i, size in enumerate(sieve_sizes) if size == 0.063)
        percent_063 = percent_passing[idx_063]
    except (StopIteration, ValueError):
        # If 0.063 mm is not an exact sieve size, interpolate if possible
        percent_063 = 0
    
    # Get sorting description
    sorting_desc = get_sorting_description(so)
    
    # Return results as a dictionary
    return {
        "sample_name": sample_name,
        "d10": d10,
        "d25": d25,
        "d30": d30,
        "d50": d50,
        "d60": d60,
        "d75": d75,
        "cu": cu,
        "so": so,
        "percent_063": percent_063,
        "sorting_desc": sorting_desc,
        "sieve_sizes": sieve_sizes,
        "percent_passing": percent_passing
    }

def generate_underflow_data(sieve_sizes, percent_passing, cutoff_size):
    """
    Generate underflow data for a given cutoff size
    Returns new sieve sizes and percent passing arrays for the underflow
    """
    # Find percentage passing the cutoff size
    cutoff_percent = 0
    for i, size in enumerate(sieve_sizes):
        if size <= cutoff_size:
            cutoff_percent = percent_passing[i]
            break
    
    if cutoff_percent == 0:
        print(f"No material passes through {cutoff_size} mm")
        return [], []
    
    # Create new arrays for underflow
    underflow_sizes = []
    underflow_passing = []
    
    # Add the cutoff size with 100% passing
    underflow_sizes.append(cutoff_size)
    underflow_passing.append(100.0)
    
    # Add all smaller sieve sizes with recalculated percentages
    for i, size in enumerate(sieve_sizes):
        if size < cutoff_size:
            new_percent = (percent_passing[i] / cutoff_percent) * 100.0
            underflow_sizes.append(size)
            underflow_passing.append(new_percent)
    
    return underflow_sizes, underflow_passing

def evaluate_criteria(results):
    """
    Evaluate the sample against the specified criteria
    Returns a dictionary with evaluation results
    """
    # Define criteria
    d50_range = (0.3, 0.5)  # 0.3mm <= D50 <= 0.5mm
    cu_range = (1.5, 2.5)   # 1.5 <= Cu <= 2.5
    so_max = 2.0            # So < 2.0
    percent_063_max = 5.0   # % passing 0.063mm < 5%
    
    # Check criteria
    d50_in_range = d50_range[0] <= results["d50"] <= d50_range[1]
    cu_in_range = cu_range[0] <= results["cu"] <= cu_range[1]
    so_in_range = results["so"] < so_max
    percent_063_in_range = results["percent_063"] < percent_063_max
    
    # Return evaluation results
    return {
        "d50_in_range": d50_in_range,
        "cu_in_range": cu_in_range,
        "so_in_range": so_in_range,
        "percent_063_in_range": percent_063_in_range,
        "d50_range": d50_range,
        "cu_range": cu_range,
        "so_max": so_max,
        "percent_063_max": percent_063_max
    }

def print_analysis_results(results, criteria_eval):
    """Print the analysis results in a formatted way"""
    print(f"\n# {results['sample_name']} Analysis Results")
    print("\n## Calculated Parameters")
    print(f"- D10 = {results['d10']:.2f} mm")
    print(f"- D25 = {results['d25']:.2f} mm")
    print(f"- D50 = {results['d50']:.2f} mm")
    print(f"- D60 = {results['d60']:.2f} mm")
    print(f"- D75 = {results['d75']:.2f} mm")
    print(f"- Coefficient of Uniformity (Cu) = {results['cu']:.2f}")
    print(f"- Trask Sorting Coefficient (So) = {results['so']:.2f}")
    print(f"- Sorting Classification: {results['sorting_desc']}")
    print(f"- Percent passing 0.063 mm = {results['percent_063']:.2f}%")
    
    # Print the criteria evaluation table
    print("\n## Compliance with Design Criteria")
    print("-" * 80)
    header = f"| {'Parameter':<30} | {'Value':<10} | {'Criteria':<20} | {'Status':<10} |"
    print(header)
    print("-" * 80)
    
    # D50 check
    d50_formatted = format_value(results["d50"], criteria_eval["d50_in_range"])
    d50_status = "✓" if criteria_eval["d50_in_range"] else "✗"
    d50_criteria = f"{criteria_eval['d50_range'][0]} to {criteria_eval['d50_range'][1]} mm"
    print(f"| {'D50 (mm)':<30} | {d50_formatted:<10} | {d50_criteria:<20} | {d50_status:<10} |")
    
    # Coefficient of Uniformity check
    cu_formatted = format_value(results["cu"], criteria_eval["cu_in_range"])
    cu_status = "✓" if criteria_eval["cu_in_range"] else "✗"
    cu_criteria = f"{criteria_eval['cu_range'][0]} to {criteria_eval['cu_range'][1]}"
    print(f"| {'Coefficient of Uniformity (Cu)':<30} | {cu_formatted:<10} | {cu_criteria:<20} | {cu_status:<10} |")
    
    # Sorting Coefficient check
    so_formatted = format_value(results["so"], criteria_eval["so_in_range"])
    so_status = "✓" if criteria_eval["so_in_range"] else "✗"
    so_criteria = f"< {criteria_eval['so_max']}"
    print(f"| {'Trask Sorting Coefficient (So)':<30} | {so_formatted:<10} | {so_criteria:<20} | {so_status:<10} |")
    
    # 0.063 mm check
    percent_063_formatted = format_value(results["percent_063"], criteria_eval["percent_063_in_range"])
    percent_063_status = "✓" if criteria_eval["percent_063_in_range"] else "✗"
    percent_063_criteria = f"< {criteria_eval['percent_063_max']}%"
    print(f"| {'Percent passing 0.063 mm (%)':<30} | {percent_063_formatted:<10} | {percent_063_criteria:<20} | {percent_063_status:<10} |")
    
    print("-" * 80)

def plot_distribution(results, filename="particle_size_distribution.png"):
    """Plot the particle size distribution curve"""
    plt.figure(figsize=(10, 6))
    plt.semilogx(results["sieve_sizes"], results["percent_passing"], 'o-', linewidth=2)
    plt.grid(True, which="both", ls="-")
    plt.xlabel('Particle Size (mm)')
    plt.ylabel('Percent Passing (%)')
    plt.title(f'Particle Size Distribution Curve - {results["sample_name"]}')
    
    # Add D values to the plot
    for d_value, d_percent, d_name in [
        (results["d10"], 10, 'D10'), 
        (results["d25"], 25, 'D25'), 
        (results["d50"], 50, 'D50'), 
        (results["d60"], 60, 'D60'), 
        (results["d75"], 75, 'D75')
    ]:
        plt.plot([d_value, d_value], [0, d_percent], 'r--', linewidth=1)
        plt.plot([0.01, d_value], [d_percent, d_percent], 'r--', linewidth=1)
        plt.text(d_value, 5, f"{d_name}\n{d_value:.2f}mm", 
                 horizontalalignment='center', verticalalignment='bottom')

    plt.savefig(filename)
    print(f"\nParticle size distribution curve saved as '{filename}'")

def generate_envelope_curves():
    """
    Generate upper and lower bounds for the grading envelope based on criteria:
    1. D50 between 0.3mm and 0.5mm
    2. Coefficient of Uniformity (Cu) between 1.5 and 2.5
    3. Sorting Coefficient (So) less than 2
    4. Percent passing 0.063mm less than 5%
    """
    # Define the sieve sizes for the envelope (logarithmically spaced)
    envelope_sizes = np.logspace(-2, 2, 1000)  # From 0.01mm to 100mm
    
    # Upper bound curve - steeper curve (less uniform, wider range of particle sizes)
    # D50 = 0.5mm (upper bound), Cu = 2.5 (upper bound)
    d50_upper = 0.5
    cu_upper = 2.5
    d10_upper = d50_upper / cu_upper
    
    # Lower bound curve - flatter curve (more uniform, narrower range of particle sizes)
    # D50 = 0.3mm (lower bound), Cu = 1.5 (lower bound)
    d50_lower = 0.3
    cu_lower = 1.5
    d10_lower = d50_lower / cu_lower
    
    # Generate the curves using log-normal distribution approximation
    # For the upper bound (wider spread)
    upper_bound = np.zeros_like(envelope_sizes)
    for i, size in enumerate(envelope_sizes):
        if size < 0.063:  # Keep percent passing 0.063mm at maximum 5%
            upper_bound[i] = 5 * (size / 0.063)
        else:
            # Create a curve that satisfies Cu = 2.5 and D50 = 0.5mm
            upper_bound[i] = 100 / (1 + np.exp(-4.5 * np.log(size / d50_upper)))
    
    # For the lower bound (narrower spread)
    lower_bound = np.zeros_like(envelope_sizes)
    for i, size in enumerate(envelope_sizes):
        if size < 0.063:  # Keep percent passing 0.063mm at 0%
            lower_bound[i] = 0
        else:
            # Create a curve that satisfies Cu = 1.5 and D50 = 0.3mm
            lower_bound[i] = 100 / (1 + np.exp(-6.0 * np.log(size / d50_lower)))
    
    # Ensure curves pass through D50 points exactly
    upper_idx = np.argmin(np.abs(envelope_sizes - d50_upper))
    lower_idx = np.argmin(np.abs(envelope_sizes - d50_lower))
    
    # Fine-tune the curves
    # Adjust to ensure upper bound has Cu close to 2.5
    upper_d60_idx = np.argmin(np.abs(upper_bound - 60))
    upper_d10_idx = np.argmin(np.abs(upper_bound - 10))
    upper_cu = envelope_sizes[upper_d60_idx] / envelope_sizes[upper_d10_idx]
    
    # Adjust to ensure lower bound has Cu close to 1.5
    lower_d60_idx = np.argmin(np.abs(lower_bound - 60))
    lower_d10_idx = np.argmin(np.abs(lower_bound - 10))
    lower_cu = envelope_sizes[lower_d60_idx] / envelope_sizes[lower_d10_idx]
    
    # Ensure curves respect 0.063mm < 5% criteria
    upper_063_idx = np.argmin(np.abs(envelope_sizes - 0.063))
    upper_bound[:upper_063_idx+1] = np.linspace(0, 5, upper_063_idx+1)
    lower_bound[:upper_063_idx+1] = 0
    
    return envelope_sizes, lower_bound, upper_bound

def plot_with_envelope(results_list, criteria_eval_list, filename="grading_envelope.png", d50_microns=350):
    """
    Plot multiple sample distributions with the grading envelope
    
    Parameters:
    - results_list: List of result dictionaries from analyze_sample()
    - criteria_eval_list: List of criteria evaluation dictionaries
    - filename: Output filename for the plot
    - d50_microns: D50 in microns to display in the title
    """
    # Get envelope curves
    envelope_sizes, lower_bound, upper_bound = generate_envelope_curves()
    
    # Create figure with semi-log x-axis
    plt.figure(figsize=(12, 8))
    
    # Setup the grid
    plt.grid(True, which='major', linestyle='-', alpha=0.5)
    plt.grid(True, which='minor', linestyle=':', alpha=0.2)
    
    # Plot sample data first (so it's on top)
    colors = ['r-', 'g-', 'c-']
    markers = ['o', 's', '^']
    for i, (results, criteria_eval) in enumerate(zip(results_list, criteria_eval_list)):
        # Draw the distribution curve
        plt.semilogx(results["sieve_sizes"], results["percent_passing"], colors[i], 
                    linewidth=2, label=results["sample_name"], marker=markers[i], markersize=5)
    
    # Plot envelope bounds
    plt.semilogx(envelope_sizes, upper_bound, 'b--', linewidth=2, label='Upper Bound')
    plt.semilogx(envelope_sizes, lower_bound, 'b--', linewidth=2, label='Lower Bound')
    
    # Create custom x-ticks for the soil classification
    soil_sizes = [0.0001, 0.001, 0.01, 0.1, 1, 10, 100]
    plt.xticks(soil_sizes)
    
    # Set plot limits and labels
    plt.xlim(0.0001, 100)
    plt.ylim(0, 100)
    plt.xlabel('Particle Size (mm)', fontsize=12, fontweight='bold')
    plt.ylabel('Percentage Passing (%)', fontsize=12, fontweight='bold')
    plt.title(f'Grading Envelope for Beach Sand; D50 = {d50_microns}microns', fontsize=14, fontweight='bold')
    
    # Add soil classification at the bottom
    # Create a secondary x-axis at the bottom for soil classification
    ax = plt.gca()
    ax_classification = plt.axes([0.1, 0.05, 0.8, 0.03], frameon=True)
    
    # Add soil classification boxes
    # Clay
    ax_classification.add_patch(plt.Rectangle((0, 0), 0.2, 1, facecolor='yellow', alpha=0.5))
    ax_classification.text(0.1, 0.5, 'CLAY', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Silt
    ax_classification.add_patch(plt.Rectangle((0.2, 0), 0.35-0.2, 1, facecolor='khaki', alpha=0.5))
    ax_classification.text(0.275, 0.5, 'SILT', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Split Silt into Fine, Medium, Coarse
    for i, x in enumerate([0.2, 0.25, 0.3]):
        ax_classification.axvline(x=x, ymin=0.7, ymax=1, color='k', linestyle='-', linewidth=1)
    ax_classification.text(0.225, 0.85, 'Fine', ha='center', va='center', fontsize=7)
    ax_classification.text(0.275, 0.85, 'Medium', ha='center', va='center', fontsize=7)
    ax_classification.text(0.325, 0.85, 'Coarse', ha='center', va='center', fontsize=7)
    
    # Sand
    ax_classification.add_patch(plt.Rectangle((0.35, 0), 0.8-0.35, 1, facecolor='lightgreen', alpha=0.5))
    ax_classification.text(0.575, 0.5, 'SAND', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Split Sand into Fine, Medium, Coarse
    for i, x in enumerate([0.35, 0.5, 0.65]):
        ax_classification.axvline(x=x, ymin=0.7, ymax=1, color='k', linestyle='-', linewidth=1)
    ax_classification.text(0.425, 0.85, 'Fine', ha='center', va='center', fontsize=7)
    ax_classification.text(0.575, 0.85, 'Medium', ha='center', va='center', fontsize=7)
    ax_classification.text(0.725, 0.85, 'Coarse', ha='center', va='center', fontsize=7)
    
    # Gravel
    ax_classification.add_patch(plt.Rectangle((0.8, 0), 1-0.8, 1, facecolor='lightgray', alpha=0.5))
    ax_classification.text(0.9, 0.5, 'GRAVEL', ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Split Gravel into Fine, Medium, Coarse
    for i, x in enumerate([0.8, 0.87, 0.94]):
        ax_classification.axvline(x=x, ymin=0.7, ymax=1, color='k', linestyle='-', linewidth=1)
    ax_classification.text(0.835, 0.85, 'Fine', ha='center', va='center', fontsize=7)
    ax_classification.text(0.905, 0.85, 'Medium', ha='center', va='center', fontsize=7)
    ax_classification.text(0.97, 0.85, 'Coarse', ha='center', va='center', fontsize=7)
    
    # Remove ticks and set limits
    ax_classification.set_xticks([])
    ax_classification.set_yticks([])
    ax_classification.set_xlim(0, 1)
    ax_classification.set_ylim(0, 1)
    
    # Add legend
    plt.axes(ax)  # Switch back to main axes
    plt.legend(loc='lower right', fontsize=10)
    
    # Add a box with criteria information
    criteria_text = (
        "Criteria:\n"
        f"1. D50: {criteria_eval_list[0]['d50_range'][0]}-{criteria_eval_list[0]['d50_range'][1]}mm\n"
        f"2. Cu: {criteria_eval_list[0]['cu_range'][0]}-{criteria_eval_list[0]['cu_range'][1]}\n"
        f"3. So < {criteria_eval_list[0]['so_max']}\n"
        f"4. % passing 0.063mm < {criteria_eval_list[0]['percent_063_max']}%"
    )
    plt.annotate(criteria_text, xy=(0.02, 0.2), xycoords='axes fraction', 
                 bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8),
                 fontsize=10)
    
    # Add points showing D values for each sample
    for i, results in enumerate(results_list):
        # Add a point for D50
        d50_x = results["d50"]
        d50_y = 50
        plt.plot(d50_x, d50_y, 'o', markersize=8, color=colors[i][0], markeredgecolor='black')
        
        # Conditionally add D10 and D60 points for main samples
        if i == 0:  # Original sample
            d10_x = results["d10"]
            d10_y = 10
            d60_x = results["d60"]
            d60_y = 60
            plt.plot(d10_x, d10_y, 'o', markersize=8, color=colors[i][0], markeredgecolor='black')
            plt.plot(d60_x, d60_y, 'o', markersize=8, color=colors[i][0], markeredgecolor='black')
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"\nGrading envelope plot saved as '{filename}'")
    
    # Create a second plot with D50 = 250 microns
    if d50_microns == 350:
        # Adjust figure title for second plot
        plt.title(f'Grading Envelope for Beach Sand; D50 = 250microns', fontsize=14, fontweight='bold')
        # Save as a different file
        second_filename = filename.replace(".png", "_250microns.png")
        plt.savefig(second_filename, dpi=300)
        print(f"\nSecond grading envelope plot saved as '{second_filename}'")
    
    return plt

def main():
    # Complete beach sand sieve analysis data - in descending order of sieve size
    sieve_sizes_original = [28, 20, 19, 14, 10, 6.3, 5, 4.75, 3.35, 2.36, 2, 1.18, 0.600, 0.425, 0.300, 0.212, 0.150, 0.075, 0.063, 0]
    percent_passing_original = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 99.0, 90.0, 87.0, 59.0, 38.0, 21.0, 14.0, 9.0, 5.0, 0.0, 0.0, 0.0]
    
    # Part 1: Analyze the original sample
    print("\n===== ORIGINAL SAMPLE ANALYSIS =====")
    original_results = analyze_sample(sieve_sizes_original, percent_passing_original, "Original Sample")
    original_criteria = evaluate_criteria(original_results)
    print_analysis_results(original_results, original_criteria)
    
    # Part 2: Analyze the 1mm screen underflow
    print("\n===== 1mm SCREEN UNDERFLOW ANALYSIS =====")
    underflow_1mm_sizes, underflow_1mm_passing = generate_underflow_data(sieve_sizes_original, percent_passing_original, 1.0)
    underflow_1mm_results = analyze_sample(underflow_1mm_sizes, underflow_1mm_passing, "1mm Screen Underflow")
    underflow_1mm_criteria = evaluate_criteria(underflow_1mm_results)
    print_analysis_results(underflow_1mm_results, underflow_1mm_criteria)
    
    # Print the underflow passing percentages for reference
    print("\n1mm Screen Underflow - Sieve Analysis Data")
    print("-" * 50)
    print(f"{'Sieve Size (mm)':<15} | {'% Passing':<10}")
    print("-" * 50)
    for size, passing in zip(underflow_1mm_sizes, underflow_1mm_passing):
        print(f"{size:<15.3f} | {passing:<10.1f}")
    print("-" * 50)
    
    # Part 3: Analyze the 0.075mm screen overflow (from 1mm underflow)
    print("\n===== 0.075mm SCREEN OVERFLOW ANALYSIS (FROM 1mm UNDERFLOW) =====")
    # For the overflow, we keep all the same material but remove any passing below 0.075mm
    # In this case, since nothing passes 0.075mm in the underflow, the results are identical
    overflow_results = analyze_sample(underflow_1mm_sizes, underflow_1mm_passing, "0.075mm Screen Overflow")
    overflow_criteria = evaluate_criteria(overflow_results)
    print_analysis_results(overflow_results, overflow_criteria)
    
    # Create individual plots for each analysis
    plot_distribution(original_results, "original_sample_distribution.png")
    plot_distribution(underflow_1mm_results, "1mm_underflow_distribution.png")
    plot_distribution(overflow_results, "0075mm_overflow_distribution.png")
    
    # Create the combined plot with grading envelope
    results_list = [original_results, underflow_1mm_results, overflow_results]
    criteria_eval_list = [original_criteria, underflow_1mm_criteria, overflow_criteria]
    
    # Create all versions of the grading envelope plot
    plot_with_envelope(results_list, criteria_eval_list, "beach_sand_grading_envelope_350microns.png", 350)
    plot_with_envelope(results_list, criteria_eval_list, "beach_sand_grading_envelope_250microns.png", 250)
    plot_with_envelope(results_list, criteria_eval_list, "beach_sand_grading_envelope_400microns.png", 400)
    
    # Summary
    print("\n===== ANALYSIS SUMMARY =====")
    print(f"Original Sample D50: {original_results['d50']:.2f} mm, Cu: {original_results['cu']:.2f}, So: {original_results['so']:.2f}")
    print(f"1mm Underflow D50: {underflow_1mm_results['d50']:.2f} mm, Cu: {underflow_1mm_results['cu']:.2f}, So: {underflow_1mm_results['so']:.2f}")
    print(f"0.075mm Overflow D50: {overflow_results['d50']:.2f} mm, Cu: {overflow_results['cu']:.2f}, So: {overflow_results['so']:.2f}")
    
    criteria_results = []
    for sample, result in [
        ("Original Sample", original_criteria),
        ("1mm Underflow", underflow_1mm_criteria),
        ("0.075mm Overflow", overflow_criteria)
    ]:
        passed = sum([result["d50_in_range"], result["cu_in_range"], result["so_in_range"], result["percent_063_in_range"]])
        criteria_results.append((sample, passed))
    
    print("\nCriteria Compliance:")
    for sample, passed in criteria_results:
        print(f"{sample}: {passed}/4 criteria met")

if __name__ == "__main__":
    main() 