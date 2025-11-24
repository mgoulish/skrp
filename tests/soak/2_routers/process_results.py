#!/usr/bin/env python3

import os
import shutil
import sys
import subprocess


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
subprocess.run ( ["gnuplot", gnuplot_file_path] )

subprocess.run ( ["display", image_file_path] )

