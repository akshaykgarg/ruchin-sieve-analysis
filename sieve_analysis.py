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

def main():
    # Hardcoded beach sand sieve analysis data - in descending order of sieve size
    sieve_sizes_original = [28, 20, 19, 14, 10, 6.3, 5, 4.75, 3.35, 2.36, 2, 1.18, 0.600, 0.425, 0.212, 0.150, 0.075, 0.063, 0]
    percent_passing_original = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 99.0, 99.0, 90.0, 87.0, 59.0, 38.0, 21.0, 9.0, 0.0, 0.0, 0.0, 0]
    
    # For our algorithm to work correctly with interpolation, we need data in ascending order of percent passing
    # Let's reverse the arrays
    sieve_sizes = list(reversed(sieve_sizes_original))
    percent_passing = list(reversed(percent_passing_original))
    
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
    
    # Find percent passing for 0.063 mm
    # Get the index where sieve size is 0.063 mm
    try:
        idx_063 = sieve_sizes_original.index(0.063)
        percent_063 = percent_passing_original[idx_063]
    except ValueError:
        # If 0.063 mm is not an exact sieve size, interpolate
        percent_063 = 0  # Default value from original data
    
    # Check against criteria
    d50_in_range = 0.3 <= d50 <= 0.5
    cu_in_range = 1.5 <= cu <= 2.5
    so_in_range = so < 2
    percent_063_in_range = percent_063 < 5
    
    # Determine sorting description based on Trask Sorting Coefficient
    if so < 1.2:
        sorting_desc = "Very well sorted"
    elif 1.2 <= so < 1.5:
        sorting_desc = "Well sorted"
    elif 1.5 <= so < 2.0:
        sorting_desc = "Moderately sorted"
    elif 2.0 <= so < 4.0:
        sorting_desc = "Poorly sorted"
    else:
        sorting_desc = "Very poorly sorted"
    
    # Print basic results
    print("\n# Beach Sand Sieve Analysis Results")
    print("\n## Calculated Parameters")
    print(f"- D10 = {d10:.2f} mm")
    print(f"- D25 = {d25:.2f} mm")
    print(f"- D50 = {d50:.2f} mm")
    print(f"- D60 = {d60:.2f} mm")
    print(f"- D75 = {d75:.2f} mm")
    print(f"- Coefficient of Uniformity (Cu) = {cu:.2f}")
    print(f"- Trask Sorting Coefficient (So) = {so:.2f}")
    print(f"- Sorting Classification: {sorting_desc}")
    print(f"- Percent passing 0.063 mm = {percent_063:.2f}%")
    
    # Print a table with criteria checking
    print("\n## Compliance with Design Criteria")
    print("-" * 80)
    header = f"| {'Parameter':<30} | {'Value':<10} | {'Criteria':<20} | {'Status':<10} |"
    print(header)
    print("-" * 80)
    
    # D50 check
    d50_formatted = format_value(d50, d50_in_range)
    d50_status = "✓" if d50_in_range else "✗"
    print(f"| {'D50 (mm)':<30} | {d50_formatted:<10} | {'0.3 to 0.5 mm':<20} | {d50_status:<10} |")
    
    # Coefficient of Uniformity check
    cu_formatted = format_value(cu, cu_in_range)
    cu_status = "✓" if cu_in_range else "✗"
    print(f"| {'Coefficient of Uniformity (Cu)':<30} | {cu_formatted:<10} | {'1.5 to 2.5':<20} | {cu_status:<10} |")
    
    # Sorting Coefficient check
    so_formatted = format_value(so, so_in_range)
    so_status = "✓" if so_in_range else "✗"
    print(f"| {'Trask Sorting Coefficient (So)':<30} | {so_formatted:<10} | {'< 2.0':<20} | {so_status:<10} |")
    
    # 0.063 mm check
    percent_063_formatted = format_value(percent_063, percent_063_in_range)
    percent_063_status = "✓" if percent_063_in_range else "✗"
    print(f"| {'Percent passing 0.063 mm (%)':<30} | {percent_063_formatted:<10} | {'< 5%':<20} | {percent_063_status:<10} |")
    
    print("-" * 80)
    
    # Create a particle size distribution curve
    plt.figure(figsize=(10, 6))
    plt.semilogx(sieve_sizes_original, percent_passing_original, 'o-', linewidth=2)
    plt.grid(True, which="both", ls="-")
    plt.xlabel('Particle Size (mm)')
    plt.ylabel('Percent Passing (%)')
    plt.title('Particle Size Distribution Curve')
    
    # Add D values to the plot
    for d_value, d_percent, d_name in [
        (d10, 10, 'D10'), (d25, 25, 'D25'), (d50, 50, 'D50'), 
        (d60, 60, 'D60'), (d75, 75, 'D75')
    ]:
        plt.plot([d_value, d_value], [0, d_percent], 'r--', linewidth=1)
        plt.plot([0.01, d_value], [d_percent, d_percent], 'r--', linewidth=1)
        plt.text(d_value, 5, f"{d_name}\n{d_value:.2f}mm", 
                 horizontalalignment='center', verticalalignment='bottom')

    plt.savefig('particle_size_distribution.png')
    print("\nParticle size distribution curve saved as 'particle_size_distribution.png'")

if __name__ == "__main__":
    main() 