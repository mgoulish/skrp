#!/usr/bin/env python3


import sys
import subprocess
import os

if len(sys.argv) < 4:
    print("Usage: python process_results.py <client_log_file> [<output_dir>]")
    sys.exit(1)

ROUTER_VERSION    = sys.argv[1]
TIMESTAMP         = sys.argv[2]
RESULTS_ROOT      = sys.argv[3]

TEST              = 'connection_rate'
TEST_RESULTS_DIR  = f"{RESULTS_ROOT}/test_results"
DATA_DIR          = f"{RESULTS_ROOT}/data"
GRAPH_DIR         = f"{RESULTS_ROOT}/graphs"


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


# Parse the log file (skip header, read CSV lines)
data = []
with open(input_file_path, 'r') as f:
    lines = f.readlines()
    for line in lines[1:]:  # Skip "second,connections" header
        if line.strip():
            sec, cnt = line.strip().split(',')
            data.append((int(sec), int(cnt)))

# Write data.dat
with open(data_file_path, 'w') as f:
    for sec, cnt in data:
        f.write(f"{sec} {cnt}\n")

# Create plot.gp
gnuplot_file_path = f"{GRAPH_DIR}/{file_name}.gplot"
image_file_path   = f"{GRAPH_DIR}/{file_name}.jpg"

print ( f"Writing gnuplot script to {gnuplot_file_path}" )
with open ( gnuplot_file_path, "w" ) as gplot_file :
  gplot_file.write ( f'set title "TCP Connection Rate Test {TIMESTAMP}" font ",30"\n' )
  gplot_file.write ( f'set   autoscale\n' )
  gplot_file.write ( f'unset key\n' )
  gplot_file.write ( f'set xlabel "Time (seconds)" font ",24"\n' )
  gplot_file.write ( f'set ylabel "Connections per second" font ",24"\n' )
  gplot_file.write ( f'set yrange [0:]\n' )
  gplot_file.write ( f'set terminal jpeg size 2000, 500\n' )
  gplot_file.write ( f'set output "{image_file_path}"\n' )
  gplot_file.write ( f'plot "{data_file_path}"  with linespoints lt rgb "red" lw 3\n' )


print ( f"Running gnuplot with command 'gnuplot {gnuplot_file_path}'" )
subprocess.run   ( ["gnuplot", gnuplot_file_path] )  # Wait for completion
print ( f"Displaying images with command 'display {image_file_path}'" )
subprocess.Popen ( ["display", image_file_path] )    # Don't wait for completion

