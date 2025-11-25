#!/usr/bin/env python3

import psutil
import time
import sys


def monitor ( pid ) :
  proc = psutil.Process(pid)
  start_time = time.time()
  print(f"Monitoring PID {pid} — {proc.name()}")
  print("Elapsed (s)  CPU (%)    RSS (MB)    Memory (%)")
  print("-" * 50)

  try:
    while True:
      time.sleep(5)
      elapsed = int(time.time() - start_time)

      # If the process died during the sleep, these calls will raise NoSuchProcess
      cpu_percent    = proc.cpu_percent ( interval=None )   # calculate since last call to this fn.
      memory_info    = proc.memory_info ( )
      memory_rss_mb  = memory_info.rss / 1024 / 1024    # Show Resident Set Size in MB
      memory_percent = proc.memory_percent()

      print(f"{elapsed:11d}   {cpu_percent:6.2f}   {memory_rss_mb:8.2f}   {memory_percent:8.2f}")

  except psutil.NoSuchProcess:
    print("\nProcess has terminated.")
  except KeyboardInterrupt:
    print("\nMonitoring stopped by user.")



#===========================================
# Main
#===========================================

if len(sys.argv) != 2:
  print("Usage: python monitor_pid.py <PID>")
  sys.exit(1)

pid = int(sys.argv[1])

monitor ( pid )
