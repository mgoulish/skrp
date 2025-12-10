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
  print ( "" )
  print ( "   statistic value    |   probability of false negative" )
  print ( "  --------------------+-----------------------------------" )
  print ( "        -3.43         |             0.01                  " )
  print ( "        -3.90         |             0.001                 " )
  print ( "        -4.17         |             0.0001                " )
  print ( "  --------------------+-----------------------------------" )
  print (f"    our score:   {adf_result[0]:.2f}" )
  print ( '' )



#--------------------------------------------
# Large-window rolling mean
# Draw an image of the data with the rolling mean in red, superimposed.
#--------------------------------------------
def rolling_mean ( filename, results_root, timestamp ) :

  output_dir = f"{results_root}/graphs"
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
  
  rolling_mean_file_path = f"{output_dir}/rolling_mean_plot.png"
  plt.figure ( figsize= ( 12, 6))
  plt.plot ( data, color='lightgray', alpha=0.7, label='Raw data')
  plt.plot ( np.arange ( window-1, n), rolling, color='red', linewidth=2, label=f'Rolling mean  ( window={window:,})')
  plt.ylabel ( 'Measurement')
  plt.title ( 'Throughput + Rolling Mean ' + timestamp)
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
  gplot_file.write ( f'set title "Soak Test Throughput {TIMESTAMP}" font ",30"\n' )
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

rolling_mean ( data_file_path, RESULTS_ROOT, TIMESTAMP )

#-------------------------------------------------------------
# Process resource usage file
#-------------------------------------------------------------

RESOURCE_USAGE_DIR  = f"{RESULTS_ROOT}/resource_usage"
print ( f"processing resource usage data in dir {RESOURCE_USAGE_DIR}" )

# Remove all the files that I put there on a previous run
for input_file_name in os.listdir ( RESOURCE_USAGE_DIR ) :
  if input_file_name.endswith(".data")  or  \
     input_file_name.endswith(".gplot") or  \
     input_file_name.endswith(".jpg") :
    os.remove ( f'{RESOURCE_USAGE_DIR}/{input_file_name}' )


for input_file_name in os.listdir ( RESOURCE_USAGE_DIR ) :
  router_name = input_file_name.split('_')[1].capitalize()
  input_file_path = os.path.join ( RESOURCE_USAGE_DIR, input_file_name)
  output_file_path = input_file_path + ".data"
  line_count = 0
  with open ( input_file_path, 'r' ) as input_file:
    print ( f"input file: {input_file_path}" )
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
  if os.path.exists(output_file_path):
    print(f"'{output_file_path}' was created.")
  else:
    print(f"'{file_path}' was not created.")
    sys.exit(1)
  gnuplot_script_file_name = f"{input_file_name}.gplot"
  gnuplot_script_file_path = f"{RESOURCE_USAGE_DIR}/{gnuplot_script_file_name}"
  print ( f"gnuplot script file path: {gnuplot_script_file_path}" )

  gnuplot_output_image_path = f"{RESOURCE_USAGE_DIR}/router_{router_name}_resource_usage.jpg"
  print ( f"gunplot output image path: {gnuplot_output_image_path}" )

  # Make the gnuplot script for resource usage
  with open ( gnuplot_script_file_path, "w" ) as gsf :   # gnuplot script file 
    gsf.write ( f'set title "Router {router_name} CPU and Memory Usage : {TIMESTAMP}"  font ",30"\n' )
    gsf.write ( f'datafile ="{output_file_path}"\n' )
    # Step by 5 on X axis because the monitoring program
    # takes a sample every 5 seconds.
    gsf.write ( 'interval = 5\n' ) 
    gsf.write ( 'set terminal jpeg size 2000, 1000\n' )
    gsf.write ( f'set output "{gnuplot_output_image_path}"\n' )
    gsf.write ( 'unset border\n' )
    gsf.write ( f'unset key\n' )
    gsf.write ( f'set arrow 1 from graph 0,0 to graph 0,1 nohead lc rgb "#cc0000" lw 2\n' )
    gsf.write ( f'set arrow 2 from graph 1,0 to graph 1,1 nohead lc rgb "#0066cc" lw 2\n' )
    gsf.write ( f'set arrow 3 from graph 0,0 to graph 1,0 nohead lc rgb "black"   lw 1.5\n' )
    gsf.write ( f'set grid ytics y2tics back lc rgb "gray" lw 1\n' )
    gsf.write ( f'set xrange [0:*]\n' )
    gsf.write ( f'label_font_size   = 24  \n' )
    gsf.write ( f'tic_font_size     = 16  \n' )
    gsf.write ( f'xlabel_font_size  = 24  \n' )
    gsf.write ( f'set ylabel "CPU Usage (%)" font sprintf("arial,%d", label_font_size) textcolor rgb "#cc0000" offset 1.5,0\n' )
    gsf.write ( f'set y2label "Memory Usage (MB)" font sprintf("arial,%d", label_font_size) textcolor rgb "#0066cc" offset 2,0\n' )
    gsf.write ( f'set ytics  font sprintf("arial,%d", tic_font_size)   nomirror textcolor rgb "#cc0000"\n' )
    gsf.write ( f'set y2tics font sprintf("arial,%d", tic_font_size)   nomirror textcolor rgb "#0066cc"\n' )
    gsf.write ( f'set xlabel "Time (seconds)" font sprintf("arial,%d", xlabel_font_size)\n' )
    gsf.write ( f'plot datafile using (interval * $0):1 with lines lw 2.5 lc rgb "#cc0000" title "CPU Usage (%)"  axes x1y1, \\\n' )
    gsf.write ( f'     \'\' using (interval * $0):2 with lines lw 2.5 lc rgb "#0066cc" title "Memory Usage (MB)" axes x1y2\n' )

  # Run gnuplot on the script created above, then display the resulting image
  print ( f"Running gnuplot with this command: gnuplot {gnuplot_script_file_path} " )
  try : 
    result = subprocess.run ( ["gnuplot", gnuplot_script_file_path] )  # Wait for completion
    print("gnuplot result stdout:", result.stdout)
    print("gnuplot result stderr:", result.stderr)
  except subprocess.CalledProcessError as e :
    print("Command failed with error:", e)
    print("Stderr:", e.stderr)

  # Did gnuplot create the expected jpg file?
  if not os.path.exists ( gnuplot_output_image_path ) :
    print ( f"{gnuplot_output_image_path} was not created" )
    sys.exit ( 1 )
  print ( f"Displaying {gnuplot_output_image_path}" )
  subprocess.Popen ( ["display", gnuplot_output_image_path] )    # Don't wait for completion


