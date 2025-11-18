#!/usr/bin/env python3

import os


#================================================
# Main 
#================================================
results_root = "../../../results/iperf/throughput"
results_dir  = f"{results_root}/test_results"
graphics_dir = f"{results_root}/graphics"

print ( f"TEMP   results: {results_dir}   graphics: {graphics_dir}" )
os.makedirs ( graphics_dir, exist_ok=True)
data_file_path = f"{graphics_dir}/data"

print ( f"data_file_path == {data_file_path}" )

# 
data_dict = {}
for file_name in os.listdir ( results_dir ) :
  n_threads = int(file_name.split('_')[1])
  results_file_path = f"{results_dir}/{file_name}"
  throughput = 0
  units      = 'none'
  with open ( results_file_path, 'r') as rf :
    summary_line = 'none'
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
    words = summary_line.split()
    for i in range(len(words)) :
      if words[i].endswith('bits/sec') :  # Gbits/sec or Mbits/sec
        units      = words[i]
        throughput = words[i-1]
        data_dict[n_threads] = throughput


sorted_items = sorted(data_dict.items())
sorted_dict = dict(sorted_items)
print ( sorted_dict )

with open ( data_file_path, 'w' ) as df :
  for datum in sorted_dict :
    df.write ( f"{datum}   {sorted_dict[datum]}\n" )

