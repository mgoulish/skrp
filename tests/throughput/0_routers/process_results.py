#!/usr/bin/env python3

import os


#================================================
# Main 
#================================================
results_root = "../../../results/iperf/throughput"
results_dir  = f"{results_root}/test_results"
graphics_dir = f"{results_root}/graphics"

os.makedirs ( graphics_dir, exist_ok=True)
data_file_path = f"{graphics_dir}/data"

# 
data_dict = {}

# I do not expect any other files in the results dir!
for file_name in os.listdir ( results_dir ) :
  n_threads = int(file_name.split('_')[1])

  # The data dict will have a list for each n_threads
  # value, because for each such value there are several
  # iterations run.
  # We will use this list to store all values, and then
  # average them later.
  if n_threads not in data_dict :
    data_dict[n_threads] = []

  results_file_path = f"{results_dir}/{file_name}"

  # Go through all the lines in the results file,
  # looking for the one that contains the summary information.
  # The format for that line is a little different in the case
  # of 1-thread tests.
  summary_line = 'none'
  with open ( results_file_path, "r" ) as rf :
    for line in rf:
      words = line.split()
      if n_threads > 1 : # plural threads
        if 'SUM' in line and 'receiver' in line :
          summary_line = line
          break
      else :             # 1 thread -- no SUM word 
        if 'receiver' in line :
          summary_line = line
          break

  # Extract the useful parts from the summary line.
  throughput = 0
  units      = 'none'
  words      = summary_line.split()
  for i in range(len(words)) :
    if words[i].endswith('bits/sec') :  # Gbits/sec or Mbits/sec
      units      = words[i]
      throughput = words[i-1]
      # Add the result of this iteration to the list.
      data_dict[n_threads].append ( throughput )


sorted_items = sorted(data_dict.items())
sorted_dict = dict(sorted_items)
#print ( sorted_dict )

with open ( data_file_path, 'w' ) as output :
  for n_threads_set in sorted_dict :
    throughput_sum = 0.0
    count = 0
    for iteration_value in sorted_dict[n_threads_set] :
      throughput_sum += float(iteration_value)
      count += 1
      print ( f"sum so far: {throughput_sum}" )
    avg = throughput_sum /count
    output.write ( f"{n_threads_set}   {avg:.2f}\n" )

#with open ( data_file_path, 'w' ) as df :
  #for datum in sorted_dict :
    #df.write ( f"{datum}   {sorted_dict[datum]}\n" )

