#!/usr/bin/env python
# Sieve Analysis Calculator
#this is for ruchin
import numpy as np
import matplotlib.pyplot as plt
from colorama import init, Fore, Style

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

def main():
    # Complete beach sand sieve analysis data - in descending order of sieve size
    sieve_sizes_original = [28, 20, 19, 14, 10, 6.3, 5, 4.75, 3.35, 2.36, 2, 1.18, 0.600, 0.425, 0.300, 0.212, 0.150, 0.075, 0.063, 0]
    percent_passing_original = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 99.0, 90.0, 87.0, 59.0, 38.0, 21.0, 14.0, 9.0, 5.0, 0.0, 0.0, 0.0]
    
    # Part 1: Analyze the original sample
    print("\n===== ORIGINAL SAMPLE ANALYSIS =====")
    original_results = analyze_sample(sieve_sizes_original, percent_passing_original, "Original Sample")
    original_criteria = evaluate_criteria(original_results)
    print_analysis_results(original_results, original_criteria)
    plot_distribution(original_results, "original_sample_distribution.png")
    
    # Part 2: Analyze the 1mm screen underflow
    print("\n===== 1mm SCREEN UNDERFLOW ANALYSIS =====")
    underflow_1mm_sizes, underflow_1mm_passing = generate_underflow_data(sieve_sizes_original, percent_passing_original, 1.0)
    underflow_1mm_results = analyze_sample(underflow_1mm_sizes, underflow_1mm_passing, "1mm Screen Underflow")
    underflow_1mm_criteria = evaluate_criteria(underflow_1mm_results)
    print_analysis_results(underflow_1mm_results, underflow_1mm_criteria)
    plot_distribution(underflow_1mm_results, "1mm_underflow_distribution.png")
    
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
    plot_distribution(overflow_results, "0075mm_overflow_distribution.png")
    
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