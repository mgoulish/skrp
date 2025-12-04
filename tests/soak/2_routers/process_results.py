#!/usr/bin/env python3

import os
import shutil
import sys
import subprocess
import math
import matplotlib.pyplot as plt





#-----------------------------------------------------------------------------------
# Augmented Dickey-Fuller test  ( null = non-stationary / trend exists)
# Schwert  ( 2002) max lag length — the most commonly used rule for large samples
#-----------------------------------------------------------------------------------
import numpy as np
from statsmodels.tsa.stattools import adfuller

def augmented_dickie_fuller_test ( filename ) :
  data = np.loadtxt ( filename )
  n = len(data)

  print ( '-----------------------------------------------' )
  print ( "Augmented Dickey-Fuller Test " )
  print ( '-----------------------------------------------' )
  print ( "   ( This will take a few seconds... )" )
  maxlag = math.floor (12 *  (n / 100) ** (1 / 4))
  adf_result = adfuller ( data, maxlag=maxlag, autolag=None, regression='c')
  print ( "  ADF statistic :", adf_result[0] )
  print ( "  p-value       :",  adf_result[1] )
  print ( "  Used lag      :",  adf_result[2] )
  print ( '' )



#--------------------------------------------
# Large-window rolling mean
# Draw an image of the data with the rolling mean in red, superimposed.
#--------------------------------------------
def rolling_mean ( filename ) :
  data = np.loadtxt ( filename )

  #---------------------------------------------------
  # Basic Statistics
  #---------------------------------------------------
  n = len(data)

  window = n // 50          # ≈2% of data, catches very slow drifts
  rolling = np.convolve ( data, np.ones ( window)/window, mode='valid')
  
  print ( '-------------------------------------------------------' )
  print ( f" Making Rolling Mean with window == {window:,}" )
  print ( '-------------------------------------------------------' )
  
  rolling_mean_file_path = 'rolling_mean_plot.png'
  plt.figure ( figsize= ( 12, 6))
  plt.plot ( data, color='lightgray', alpha=0.7, label='Raw data')
  plt.plot ( np.arange ( window-1, n), rolling, color='red', linewidth=2, label=f'Rolling mean  ( window={window:,})')
  plt.ylabel ( 'Measurement')
  plt.title ( 'Data + rolling mean')
  plt.legend ( )
  plt.savefig ( rolling_mean_file_path, dpi=300, bbox_inches='tight')  # saves to file
  plt.close ( )
  print ( f"  rolling mean plot written to {rolling_mean_file_path}" )
  print ( '\n\n' )
  subprocess.Popen ( ["display", rolling_mean_file_path] )    # Don't wait for completion
  

#==================================================
# main 
#==================================================

if len(sys.argv) < 4 :
  print ( "error: give me router-version timestamp results-root" )
  sys.exit( 1 )

if not shutil.which ( "gnuplot" ) :
  print ( "error: I need gnuplot installed." )
  sys.exit ( 1 )

if not shutil.which ( "display" ) :
  print ( "error: can't find gnuplot utility 'display' ." )
  sys.exit ( 1 )



ROUTER_VERSION    = sys.argv[1]
TIMESTAMP         = sys.argv[2]
RESULTS_ROOT      = sys.argv[3]

TEST_RESULTS_DIR  = f"{RESULTS_ROOT}/test_results"
GRAPH_DIR         = f"{RESULTS_ROOT}/graphs/soak"

os.makedirs ( GRAPH_DIR, exist_ok = True )


#-------------------------------------------------------------
# Process throughput results file
#-------------------------------------------------------------
print ( f"looking for result in {TEST_RESULTS_DIR}" )

# There should only be one file.
file_name        = os.listdir ( TEST_RESULTS_DIR ) [ 0 ]
input_file_path  = f"{TEST_RESULTS_DIR}/{file_name}"
print ( "found input file : ", input_file_path )
data_file_path = f"{GRAPH_DIR}/{file_name}.data"
print ( "data_file_path: ", data_file_path )


# Go through all lines of the results file, picking out the 'sum'
# lines for each snapshot.

with open ( data_file_path, 'w' ) as data_file :
  with open ( input_file_path, 'r' ) as input_file :
    for line in input_file :
      if 'SUM' in line \
        and 'sender' not in line \
        and 'receiver' not in line :
        words = line.split()
        for i in range(len(words)) :
          if words[i].endswith('bits/sec') :
             data_file.write ( f"{words[i-1]}\n" )
  
gnuplot_file_path = f"{GRAPH_DIR}/{file_name}.gplot"
image_file_path   = f"{GRAPH_DIR}/{file_name}.jpg"

print ( f"Writing gnuplot script to {gnuplot_file_path}" )
with open ( gnuplot_file_path, "w" ) as gplot_file :
  gplot_file.write ( f'set title "Soak Test {TIMESTAMP}" font ",30"\n' )
  gplot_file.write ( f'set   autoscale\n' )
  gplot_file.write ( f'unset key\n' )
  gplot_file.write ( f'set xlabel "Time (seconds)" font ",24"\n' )
  gplot_file.write ( f'set ylabel "Throughput (Gbits/sec)" font ",24"\n' )
  gplot_file.write ( f'set yrange [0:]\n' )
  gplot_file.write ( f'set terminal jpeg size 2000, 500\n' )
  gplot_file.write ( f'set output "./{image_file_path}"\n' )
  gplot_file.write ( f'plot "{data_file_path}"  with linespoints lt rgb "red" lw 3\n' )


print ( f"Running gnuplot..." )
subprocess.run   ( ["gnuplot", gnuplot_file_path] )  # Wait for completion
subprocess.Popen ( ["display", image_file_path] )    # Don't wait for completion

augmented_dickie_fuller_test ( data_file_path )

rolling_mean ( data_file_path )

#-------------------------------------------------------------
# Process resource usage file
#-------------------------------------------------------------

RESOURCE_USAGE_DIR  = f"{RESULTS_ROOT}/resource_usage"

for input_file_name in os.listdir ( RESOURCE_USAGE_DIR ) :
  if input_file_name.endswith(".data") :
    continue
  input_file_path = os.path.join ( RESOURCE_USAGE_DIR, input_file_name)
  output_file_path = input_file_path + ".data"
  line_count = 0
  with open ( input_file_path, 'r' ) as input_file:
    with open ( output_file_path, 'w' ) as output_file :
      for line in input_file:
        line_count += 1
        if line_count <= 3 : # The first 3 lines are header
          continue
        if 'terminated' in line :
          continue
        words = line.split()
        if len(words) < 3 :
          continue
        #print ( f"line {line_count}: {words}" )
        cpu = words [ 1 ]
        mem = words [ 2 ]
        output_file.write ( f"{cpu}   {mem}\n" )
  print ( f"data output file: {output_file_path}" )



