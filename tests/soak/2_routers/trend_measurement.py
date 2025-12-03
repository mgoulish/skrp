#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm
import sys
import math

# =============================================================================
# Change this to your actual file name / format
# =============================================================================
# One number per line (most common for this kind of measurement)
filename = sys.argv[1]

# If it is a single-column csv instead:
# filename = 'measurements.csv'
# data = np.loadtxt(filename, delimiter=',')
# =============================================================================

data = np.loadtxt(filename)

n = len(data)
print(f"Loaded {n:,} points")
print(f"Mean: {np.mean(data):.6f}")
print(f"Std:  {np.std(data):.6f}")
print(f"Min/Max: {np.min(data):.6f} / {np.max(data):.6f}\n")

# 1. Linear regression (trend per step and total drift)
x = np.arange(n)
slope, intercept, r, p_value, se = linregress(x, data)

total_drift = slope * n
print("=== Linear regression ===")
print(f"Slope per measurement : {slope:.12f}")
print(f"Total drift over all {n:,} points: {total_drift:+.6f}")
print(f"R²                    : {r**2:.9f}")
print(f"p-value (slope ≠ 0)   : {p_value:.2e}")
if abs(total_drift) < 0.05:   # you can adjust this threshold
    print("→ Practically negligible trend (total drift < 0.05)")
else:
    print("→ Noticeable total drift")

# 2. Augmented Dickey-Fuller test (null = non-stationary / trend exists)
# Schwert (2002) max lag length — the most commonly used rule for large samples
maxlag = math.floor(12 * (n / 100) ** (1 / 4))

print(f"Using fixed lags = {maxlag} (Schwert rule — recommended for large n)")

adf_result = adfuller(data, maxlag=maxlag, autolag=None, regression='c')

print("ADF statistic :", adf_result[0])
print("p-value      :", adf_result[1])
print("Used lag     :", adf_result[2])


#print("\n=== Augmented Dickey-Fuller test ===")
#adf = adfuller(data, regression='c')   # 'c' = constant, no linear trend in test
#print(f"ADF statistic : {adf[0]:.6f}")
#print(f"p-value       : {adf[1]:.6f}")
#print("Critical values:")
#for k, v in adf[4].items():
    #print(f"   {k}: {v:.6f}")
#if adf[1] < 0.05:
    #print("→ Stationary (no unit root / no strong trend) at 5% level")
#else:
    #print("→ Cannot reject non-stationary (possible trend or unit root)")


# 3. Large-window rolling mean (visual + quantitative)
window = n // 50          # ≈2% of data, catches very slow drifts
rolling = np.convolve(data, np.ones(window)/window, mode='valid')
roll_std = np.std(rolling)

print(f"\n=== Rolling mean (window = {window:,} ≈ {100*window/n:.1f}% of data) ===")
print(f"Std of rolling mean: {roll_std:.6f}")
if roll_std < 0.02:
    print("→ Rolling mean is essentially flat")
else:
    print("→ Rolling mean shows some slow variation")

# Plot data + rolling mean
plt.figure(figsize=(12, 6))
plt.plot(data, color='lightgray', alpha=0.7, label='Raw data')
#plt.plot(np.arange(window-1, n), rolling, rolling, color='red', linewidth=2, label=f'Rolling mean (window={window:,})')
plt.plot(np.arange(window-1, n), rolling, color='red', linewidth=2, label=f'Rolling mean (window={window:,})')
plt.ylabel('Measurement')
plt.title('Data + very slow rolling mean')
plt.legend()
#plt.show()
plt.savefig('rolling_mean_plot.png', dpi=300, bbox_inches='tight')  # saves to file
plt.close()

