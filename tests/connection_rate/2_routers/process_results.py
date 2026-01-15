#!/usr/bin/env python3


import sys
import subprocess
import os
from collections import defaultdict


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
print ( f"looking for result files in {TEST_RESULTS_DIR}" )

# Parse the log files (skip header, read CSV lines)
file_names       = os.listdir ( TEST_RESULTS_DIR )
data = []
for file_name in file_names :
  input_file_path  = f"{TEST_RESULTS_DIR}/{file_name}"
  print ( f"processing file {input_file_path}" )
  with open(input_file_path, 'r') as f:
    lines = f.readlines()
    for line in lines[1:]:  # Skip "second,connections" header
      if line.strip():
        sec, cnt = line.strip().split(',')
        data.append((int(sec), int(cnt)))

sums = defaultdict(int)
for second, count in data:
    sums[second] += count



# Write data.dat
data_file_path = f"{GRAPH_DIR}/{file_name}.data"
sorted_data = sorted(data, key=lambda x: x[0])
with open(data_file_path, 'w') as f:
    for second in sorted(sums) :
        f.write(f"{second} {sums[second]}\n")

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
  gplot_file.write ( f'set terminal jpeg size 2000, 1000\n' )
  gplot_file.write ( f'set output "{image_file_path}"\n' )
  gplot_file.write ( f'plot "{data_file_path}"  with linespoints lt rgb "red" lw 3\n' )


print ( f"Running gnuplot with command 'gnuplot {gnuplot_file_path}'" )
subprocess.run   ( ["gnuplot", gnuplot_file_path] )  # Wait for completion
print ( f"Displaying images with command 'display {image_file_path}'" )
subprocess.Popen ( ["display", image_file_path] )    # Don't wait for completion

