#!/usr/bin/env python3

import os
import sys
import pprint
import subprocess
import shutil




def new_cpu ( cpu_values_set ) :
  return dict.fromkeys ( cpu_values_set, None )



def new_sender_threads ( sender_threads_values_set ) :
  return dict.fromkeys ( sender_threads_values_set, None )



def new_router_threads ( sender_threads_values_set ) :
  return dict.fromkeys ( sender_threads_values_set, None )



def new_iterations ( iterations_values_set ) :
  return dict.fromkeys ( iterations_values_set, None )



def new_test_result ( ) :
  keys = [ 'throughput',
           'units' ]
  test_result = dict.fromkeys ( keys, None )
  return test_result



# Needs to know the number of sender-threads, because 
# that affects how the throughput value in the file
# can be found.
def find_throughput_from_file ( file_path, n_sender_threads ) :
  val   = 0.0
  units = None
  if n_sender_threads == '1' :
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




#==================================================
# main 
#==================================================

if len(sys.argv) < 2 :
  print ( "error: give me router version on command line" )
  sys.exit( 1 )

if not shutil.which ( "gnuplot" ) :
  print ( "error: I need gnuplot installed." )
  sys.exit ( 1 )

if not shutil.which ( "display" ) :
  print ( "error: can't find gnuplot utility 'display' ." )
  sys.exit ( 1 )



ROUTER_VERSION    = sys.argv[1]
TIMESTAMP         = sys.argv[2]
TEST              = 'throughput'
RESULTS_ROOT      = f"../../../results/{ROUTER_VERSION}/{TEST}/{TIMESTAMP}"
TEST_RESULTS_DIR  = f"{RESULTS_ROOT}/test_results"
GRAPH_DIR         = f"{RESULTS_ROOT}/graphs"

cpus_set            = set()
sender_threads_set  = set()
router_threads_set  = set()
iterations_set      = set()

# Here is an example of the expected file name format:
#   cpu_300_sender-threads_2_router-threads_4_iteration_1
# components:
#        0    cpu
#        2    sender-threads
#        4    router-threads
#        6    iteration

#---------------------------------------------------------
# Go through all the files to collect all values of 
# CPUs, sender threads, router threads, and iterations.
#---------------------------------------------------------
for file_name in os.listdir ( TEST_RESULTS_DIR ) :
  name_components = file_name.split('_')
  if name_components[0] != 'cpu'            or \
     name_components[2] != 'sender-threads' or \
     name_components[4] != 'router-threads' or \
     name_components[6] != 'iteration' :
    print ( f"error parsing file name: {TEST_RESULTS_DIR}/{file_name}" )
    print ( f"name components: {name_components}" )
    sys.exit(1)

  cpu_val             = name_components[1]
  sender_threads_val  = name_components[3]
  router_threads_val  = name_components[5]
  iteration_val       = name_components[7]

  cpus_set.add            ( cpu_val )
  sender_threads_set.add  ( sender_threads_val )
  router_threads_set.add  ( router_threads_val )
  iterations_set.add      ( iteration_val )
  print (f"parsed file {file_name}")


# Make the dictionary tree that will hold all
# the throughput values.
CPUs = new_cpu ( cpus_set )
for cpu_value in CPUs :
  sender_threads_dict = new_sender_threads ( sender_threads_set )
  CPUs[cpu_value] = sender_threads_dict
  for sender_threads_value in sender_threads_dict :
    router_threads_dict = new_router_threads ( router_threads_set )
    sender_threads_dict[sender_threads_value] = router_threads_dict
    for router_threads_value in router_threads_dict :
      iterations_dict = new_iterations ( iterations_set )
      router_threads_dict[router_threads_value] = iterations_dict
      for iteration_value in iterations_dict :
        iterations_dict[iteration_value] = new_test_result ( )


# Now go through all the files again to read
# the throughput values.  This is the payload.
for file_name in os.listdir ( TEST_RESULTS_DIR ) :
  print ( f"reading throughput values for {TEST_RESULTS_DIR}/{file_name}" )
  file_path = os.path.join ( TEST_RESULTS_DIR, file_name )
  name_components = file_name.split('_')
  # No need to confirm that file name is well-formed,
  # since we just did that, above.

  cpu_val             = name_components[1]
  sender_threads_val  = name_components[3]
  router_threads_val  = name_components[5]
  iteration_val       = name_components[7]

  throughput, units = find_throughput_from_file ( file_path, sender_threads_val )

  if units != 'Gbits/sec' :
    if units == 'Mbits/sec' :
      throughput = float(throughput) / 1000.0
      units = 'Gbits/sec'
    else :
      print ( f"error: unknown units:{units} in file {file_name}" )
      sys.exit ( 1 )
  
  print ( f"  throughput is {throughput}" )
  CPUs[cpu_val][sender_threads_val][router_threads_val][iteration_val]['throughput'] = throughput
  CPUs[cpu_val][sender_threads_val][router_threads_val][iteration_val]['units']      = units

#----------------------------------------------------------
# Walk through the dictionary tree to get down to 
# the test iterations, and find and store their averages.
#----------------------------------------------------------
throughput_global_minimum = 10000.0
throughput_global_maximum = -10000.0

for cpu_val in CPUs :
  sender_threads_dict = CPUs[cpu_val]
  for sender_threads_val in sender_threads_dict :
    router_threads_dict = sender_threads_dict[sender_threads_val]
    for router_threads_val in router_threads_dict :
      throughput_sum = 0.0
      iteration_dict = router_threads_dict[router_threads_val]
      for iteration_val in iteration_dict:
        test_result_dict = iteration_dict[iteration_val]
        if None == test_result_dict [ 'throughput' ] :
          print ( f"None value at cpu {cpu_val} sender_threads {sender_threads_val} router_threads {router_threads_val} iteration {iteration_val}" )
          sys.exit(1)
        else :
          throughput_sum += test_result_dict [ 'throughput' ]
      throughput_avg = throughput_sum / len(iteration_dict)
      # It's a little icky to change the iteraton dict like
      # this, and overload it to store the average across iterations. 
      # But. Who's gonna know?
      iteration_dict['average'] = throughput_avg

      if throughput_avg < throughput_global_minimum :
        throughput_global_minimum = throughput_avg
      if throughput_avg > throughput_global_maximum :
        throughput_global_maximum = throughput_avg

# Now make the data files that will be used by gnuplot for the graphs.
#
# Each data file will represent a different CPU allocation.
# Gnuplot will create a 2-dimensional graph where:
#    * X-axis shows number of router threads 
#    * Y-axis shows the number of sender threads.
#
# Each data file should look something like this:
#             10 15 20 25 30
#             8 12 18 22 28
#             5 10 15 20 25
#             3 7 12 17 22
#             1 5 10 15 20
# There are no explicit Y values. Those are encoded implicitly
# as the row numbers, where the top row will be at the top of the
# graph.

for cpu_val in CPUs :
  gnuplot_script_file_path =   f"{GRAPH_DIR}/cpu_{cpu_val}.gplot"
  gnuplot_data_file_path   =   f"{GRAPH_DIR}/cpu_{cpu_val}.data"
  print ( f"writing script file: {gnuplot_script_file_path}  and data file: {gnuplot_data_file_path}" )
  # Data file Y-axis is sender threads
  sender_threads_dict = CPUs[cpu_val]
  with open ( gnuplot_data_file_path, 'w' ) as f:
    # Sender threads on the Y-axis
    sorted_y_vals = sorted(sender_threads_dict.keys(), key=int)
    for sender_threads_val in sorted_y_vals :
      print ( f"sender_threads_val: {sender_threads_val}" )
      # Router threads on the X-axis
      sorted_x_vals = sorted ( router_threads_dict.keys(), key=int )
      router_threads_dict = sender_threads_dict[sender_threads_val]
      for router_threads_val in sorted_x_vals :
        iteration_dict = router_threads_dict[router_threads_val]
        f.write ( f"{iteration_dict['average']:.2f} ")
      f.write ( "\n" )

  # And now write the gnupplot script to the same directory.
  gnuplot_image_file_path   =   f"{GRAPH_DIR}/cpu_{cpu_val}.jpg"
  print ( f"writing gnuplot script {gnuplot_script_file_path}" )
  with open ( gnuplot_script_file_path, 'w' ) as f :
    f.write (  "set terminal png size 1200, 1000\n" )
    f.write ( f"set output '{gnuplot_image_file_path}'\n" )
    f.write (  "set palette rgbformulae 33,13,10\n" )
    f.write (  "set colorbox\n" )
    f.write ( f'set title "Version {ROUTER_VERSION} : Throughput for CPU {cpu_val}" font ",24" \n' )
    f.write (  'set xlabel "Router Threads" font ",20" \n' )
    f.write (  'set ylabel "Sender Threads" font ",20" \n' )

    # X Tics -----------------
    f.write (  "set xtics font \",16\" (" )
    count = 0
    for x in sorted_x_vals :
      f.write ( f'"{x}" {count}, ' )
      count += 1
    f.write (  ")\n" )

    # Y Tics -----------------
    f.write (  "set ytics font \",16\" (" )
    count = 0
    for y in sorted_y_vals :
      f.write ( f'"{y}" {count}, ' )
      count += 1
    f.write (  ")\n" )

    f.write ( f"set cbrange [{throughput_global_minimum}:{throughput_global_maximum}]\n" )
    f.write (  "set autoscale xfix\n" )
    f.write (  "set autoscale yfix\n" )
    f.write (  "set autoscale cbfix\n" )
    f.write ( f"plot '{gnuplot_data_file_path}' matrix with image title \"\", \\\n" )
    f.write (  "     \"\"     matrix using 1:2:(sprintf('%.1f', $3)) with labels center font \",16\"" )

  # Now that we have the gnuplot file, let's call gnuplot on it.
  subprocess.call ( ["gnuplot", gnuplot_script_file_path ] )
  if os.path.exists ( gnuplot_image_file_path ) :
    subprocess.Popen ( ["display", gnuplot_image_file_path ] )
  else :
    print ( f"error: image file {gnuplot_image_file_path} was not created" )

    
    

