#!/usr/bin/env python3

import os
import sys
import pprint


def new_cpu ( cpu_values_set ) :
  return dict.fromkeys ( cpu_values_set, None )



def new_threads ( threads_values_set ) :
  return dict.fromkeys ( threads_values_set, None )



def new_iterations ( iterations_values_set ) :
  return dict.fromkeys ( iterations_values_set, None )



def new_test_result ( ) :
  keys = [ 'throughput',
           'units' ]
  test_result = dict.fromkeys ( keys, None )
  return test_result



# Needs to know the number of threads, because 
# that affects how the throughput value in the file
# can be found.
def find_throughput_from_file ( file_path, n_threads ) :
  val   = 0.0
  units = None
  if n_threads == '1' :
    with open(file_path, 'r') as file:
      for line in file:
        if 'receiver' in line :
          words = line.split()
          for i in range(len(words)) :
            if 'bits/sec' in words[i] :
              val   = float(words[i-1])
              units = words[i]
  else :
    with open(file_path, 'r') as file:
      for line in file:
        if 'receiver' in line and 'SUM' in line :
          words = line.split()
          for i in range(len(words)) :
            if 'bits/sec' in words[i] :
              val   = float(words[i-1])
              units = words[i]
  return val, units



def make_gnuplot_file ( CPUs, RESULTS_ROOT, ROUTER_VERSION ) :
  file_path = f"{RESULTS_ROOT}/graphs/gplot"
  print ( f"make_gnuplot_file: file: {file_path}" )
  with open ( file_path, 'w') as f :
    f.write("# Read command line args\n")
    f.write(f"set title \"Throughput vs Per-Router CPU Allocation\\n Router Version {ROUTER_VERSION}\" font \",24\"\n")
    f.write('set autoscale\n')
    f.write('unset key\n')
    f.write('set xlabel "Iperf3 Sender Threads"  font ",20"\n')
    f.write('set xrange [ 0 : 11 ]\n')
    f.write('set ylabel "Throughput (Gbits/sec)"  font ",20"\n')
    f.write('set yrange [ 0 : 20 ]\n')
    f.write('set ytics 0, 2\n')
    f.write('set terminal jpeg size 1000, 1000\n')
    f.write(f'set output "{RESULTS_ROOT}/graphs/all_cpus.jpg"\n')
    f.write('plot ')
    colors = ['red', 'orange', 'gold', 'greenyellow', 'dark-turquoise', 
              'forest-green', 'blue', 'dark-violet', 'gray40', 'gray0' ]
    count = 1
    for CPU in CPUs:
      color_number = count - 1
      if color_number > len(colors) - 1 :
        color_number = len(colors) - 1
      color = colors[color_number]
      f.write ( f'"{RESULTS_ROOT}/data/cpu_{CPU}.data" u (last_x{count}=$1):(last_y{count}=$2) with linespoints lt rgb "{color}" lw 3 pt 7 ps 2, \\\n' )
      count += 1
    
    count = 1
    for CPU in CPUs :
      color_number = count - 1
      if color_number > len(colors) - 1 :
        color_number = len(colors) - 1
      f.write ( f"'+' u (last_x{count}):(last_y{count}):(\"{CPU}%\") every ::0::0 w labels offset -1,1 tc rgb \"{colors[color_number]}\" font \",16\", \\\n" )
      count += 1
      



    


#==================================================
# main 
#==================================================

if len(sys.argv) < 2 :
  print ("give me router version on command line")
  sys.exit(1)

ROUTER_VERSION    = sys.argv[1]
TEST              = 'throughput'
RESULTS_ROOT      = f"../../../results/{ROUTER_VERSION}/{TEST}"
TEST_RESULTS_DIR  = f"{RESULTS_ROOT}/test_results"
DATA_DIR          = f"{RESULTS_ROOT}/data"

cpus_set       = set()
threads_set    = set()
iterations_set = set()

# Go through all the files to collect all
# values of CPUs, threads, and iterations
for file_name in os.listdir ( TEST_RESULTS_DIR ) :
  name_components = file_name.split('_')
  if name_components[0] != 'cpu' or name_components[2] != 'threads' or name_components[4] != 'iteration' :
    print ( f"error parsing file name: {file_name}" )
    sys.exit(1)

  cpu_val       = name_components[1]
  threads_val   = name_components[3]
  iteration_val = name_components[5]

  cpus_set.add       ( cpu_val )
  threads_set.add    ( threads_val )
  iterations_set.add ( iteration_val )
  print (f"parsed file {file_name}")

# Make the dictionary tree that will hold all
# the throughput values.
CPUs = new_cpu ( cpus_set )
for cpu_value in CPUs :
  CPUs[cpu_value] = new_threads ( threads_set )
  for threads_value in CPUs[cpu_value] :
    CPUs[cpu_value][threads_value] = new_iterations ( iterations_set )
    for iteration_value in CPUs[cpu_value][threads_value] :
      CPUs[cpu_value][threads_value][iteration_value] = new_test_result ( )

# Now go through all the files again to read
# the throughput values.  The payload.
for file_name in os.listdir ( TEST_RESULTS_DIR ) :
  file_path = os.path.join ( TEST_RESULTS_DIR, file_name )
  name_components = file_name.split('_')
  if name_components[0] != 'cpu' or name_components[2] != 'threads' or name_components[4] != 'iteration' :
    print ( f"error parsing file name: {file_name}" )
    sys.exit(1)

  cpu_val       = name_components[1]
  threads_val   = name_components[3]
  iteration_val = name_components[5]

  throughput, units = find_throughput_from_file ( file_path, threads_val )

  if units != 'Gbits/sec' :
    print ( f"error: unknown units:{units} in file {file_name}" )
    sys.exit ( 1 )
  
  CPUs[cpu_val][threads_val][iteration_val]['throughput'] = throughput
  CPUs[cpu_val][threads_val][iteration_val]['units']      = units

# Walk through the dictionary tree to get down to 
# the test iterations, and find and store their averages.
for cpu_val in CPUs :
  for threads_val in CPUs[cpu_val] :
    throughput_sum = 0.0
    for iteration_val in CPUs[cpu_val][threads_val] :
      test_result = CPUs[cpu_val][threads_val][iteration_val]
      throughput_sum += test_result [ 'throughput' ]
    throughput_avg = throughput_sum / len(CPUs[cpu_val][threads_val])
    #print ( f"cpu {cpu_val}  threads {threads_val} : throughput: {throughput_avg:.2f} " )
    CPUs[cpu_val][threads_val]['average'] = throughput_avg

# Now make the data files that will be used by gnuplot for the graphs.
for cpu_val in CPUs :
  data_file_path = f"{DATA_DIR}/cpu_{cpu_val}.data"
  print ( f"writing data file: {data_file_path}" )
  with open ( data_file_path, 'w') as f :
    for threads_val, test_results in sorted(CPUs[cpu_val].items(), key=lambda item: int(item[0])):
      f.write(f"{threads_val} {test_results['average']:.2f}\n")


make_gnuplot_file ( sorted(CPUs.keys(), key=int, reverse=True), RESULTS_ROOT, ROUTER_VERSION )

