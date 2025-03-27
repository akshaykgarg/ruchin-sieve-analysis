#!/usr/bin/env python
# Sieve Analysis Calculator
import numpy as np
import matplotlib.pyplot as plt

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
    
    # Print results
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
    
    # Optional: Create a particle size distribution curve
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