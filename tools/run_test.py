#!/usr/bin/env python3

import os
import subprocess
import time
import datetime
import argparse
from datetime import datetime
import sys


TIMESTAMP = datetime.now().strftime("%Y-%m-%d-%H-%M")

# Find the SKRP root.
# It is the initial subset of the Current Working Directory 
# that ends with 'skrp'.
cwd = os.getcwd()
start_index = cwd.find('skrp')
if start_index == -1 :
    print("'skrp' not found in cwd")
    sys.exit(1)
end_index = start_index + len('skrp')
SKRP_ROOT = cwd[:end_index]
print ( f"SKRP_ROOT: {SKRP_ROOT}" )


def parse_list(arg):
    return arg.split(',')

parser = argparse.ArgumentParser(description="Run router tests with configurable parameters.")

#------------------------------------------------
# Default to a full-sized throughput test
#------------------------------------------------
parser.add_argument('--test',                            default="throughput",                help="Which test to run.")
parser.add_argument('--router-version',                  default="3.4.1",                     help="Version of the Router software installed.")
parser.add_argument('--router-threads', type=parse_list, default="1,2,4,5,7,10",              help="Router threads, comma-separated.")
parser.add_argument('--sender-threads', type=parse_list, default="1,2,5,10",                  help="Sender threads, comma-separated.")
parser.add_argument('--duration',       type=int,        default=15,                          help="Duration of each test in seconds.")
parser.add_argument('--iterations',     type=parse_list, default="1,2,3",                     help="List of iterations, comma-separated.")
parser.add_argument('--cpu-limits',     type=parse_list, default="500,400,300,200,100,50,25", help="CPU allocations for each router, comma-separated.")

args = parser.parse_args()



# Assign parsed arguments to variables
ROUTER_VERSION = args.router_version
TEST           = args.test
DURATION       = args.duration
ITERATIONS     = args.iterations
CPU_LIMITS     = args.cpu_limits
ROUTER_THREADS = args.router_threads
SENDER_THREADS = args.sender_threads



#----------------------------------------------------------------
# The test name causes specific values to be set for some args.
#----------------------------------------------------------------

post_processor_path = None

# throughput ----------------------------------------------------
if TEST == 'throughput' : 
  # You need a big machine to run this.
  post_processor_path = f"{SKRP_ROOT}/tests/throughput/2_routers/process_results.py"
  ROUTER_THREADS = ['1', '2', '4', '5', '10']
  SENDER_THREADS = ['1', '2', '4', '5', '10']
  DURATION       =   15
  ITERATIONS     = ['1', '2', '3']
  CPU_LIMITS     = ['500', '400', '300', '200', '100', '50']
# short_throughput ----------------------------------------------
elif TEST == 'short_throughput' :
  post_processor_path = f"{SKRP_ROOT}/tests/throughput/2_routers/process_results.py"
  ROUTER_THREADS = ['1', '2', '4']
  SENDER_THREADS = ['1', '2', '4']
  DURATION       =   15
  ITERATIONS     = ['1', '2', '3']
  CPU_LIMITS     = ['200', '100', '50']
# soak       ----------------------------------------------------
elif TEST == 'soak' :   
  post_processor_path = f"{SKRP_ROOT}/tests/soak/2_routers/process_results.py"
  ROUTER_THREADS = ['5']
  SENDER_THREADS = ['5']
  DURATION       =   0
  ITERATIONS     = ['1']
  CPU_LIMITS     = ['500']
# short_soak ----------------------------------------------------
elif TEST == 'short_soak' :
  post_processor_path = f"{SKRP_ROOT}/tests/soak/2_routers/process_results.py"
  ROUTER_THREADS = ['5']
  SENDER_THREADS = ['5']
  DURATION       =  100
  ITERATIONS     = ['1']
  CPU_LIMITS     = ['500']
else :
  print ( "Test must be 'throughput', 'soak', 'short_throughput', or 'short_soak'." )
  sys.exit ( 1 )

monitor_process_path = f"{SKRP_ROOT}/tools/monitor_process.py"


#--------------------------------------------
# Show the args and paths we are using.
#--------------------------------------------
print ( f"TEST            == {TEST}"           )
print ( f"ROUTER_VERSION  == {ROUTER_VERSION}" )
print ( f"DURATION        == {DURATION}"       )
print ( f"ITERATIONS      == {ITERATIONS}"     )
print ( f"CPU_LIMITS      == {CPU_LIMITS}"     )
print ( f"ROUTER_THREADS  == {ROUTER_THREADS}" )
print ( f"SENDER_THREADS  == {SENDER_THREADS}" )
print ( f"monitor process == {monitor_process_path}" )
print ( f"post processor  == {post_processor_path}" )




# Calculate the total number of tests we will be doing,
# so we can give him some idea of progress.
n_tests = len(ITERATIONS) * len(CPU_LIMITS) * len(ROUTER_THREADS) * len(SENDER_THREADS)


# TODO  How do I make this work for the 1_router test.  If I care.
#       And what about 0 routers ???

# TODO -- set all params based on test name
#         add test name of short_soak

RESULT_ROOT = f"{SKRP_ROOT}/results/{ROUTER_VERSION}/{TEST}/{TIMESTAMP}"
TEST_RESULTS_DIR = f"{RESULT_ROOT}/test_results"
print(f"TEST_RESULTS_DIR == {TEST_RESULTS_DIR}")
RESOURCE_USAGE_DIR=f"{RESULT_ROOT}/resource_usage"

os.makedirs(f"{TEST_RESULTS_DIR}",    exist_ok=True)
os.makedirs(f"{RESOURCE_USAGE_DIR}",  exist_ok=True)
os.makedirs(f"{RESULT_ROOT}/data",    exist_ok=True)
os.makedirs(f"{RESULT_ROOT}/graphs",  exist_ok=True)
os.makedirs(f"{RESULT_ROOT}/routers", exist_ok=True)

print ( f"RESOURCE_USAGE_DIR == {RESOURCE_USAGE_DIR}" )

# Your router is installed in the standard place.
ROUTER = "/usr/local/sbin/skrouterd"    # FIND THIS

print(f"Starting routers from {ROUTER}")
print(datetime.now())

test_count = 0

for RT in ROUTER_THREADS:
    # Create the router config files
    with open("A.conf.template", "r") as f:
        content = f.read()
    with open("A.conf", "w") as f:
        f.write(content.replace("N_THREADS", RT))
    
    with open("B.conf.template", "r") as f:
        content = f.read()
    with open("B.conf", "w") as f:
        f.write(content.replace("N_THREADS", RT))

    for CPU in CPU_LIMITS:
        # Start Router A --------------------------------
        # I don't want to constrain memory
        cmd_a = [
            "systemd-run", "--quiet", "--user", "--scope",
            "-p", f"CPUQuota={CPU}%",
            ROUTER, "--config", "./A.conf"
        ]
        with open(f"{RESULT_ROOT}/routers/A.log", "w") as log_a:
            router_a_proc = subprocess.Popen(cmd_a, stdout=log_a, stderr=subprocess.STDOUT)
        print("Router A started")
        time.sleep(3)

        # Start the monitor for Router A
        monitor_a_cmd = [ monitor_process_path, str(router_a_proc.pid) ]
        with open ( f"{RESOURCE_USAGE_DIR}/router_a", "w" ) as resource_usage_a :
            monitor_a_proc = subprocess.Popen ( monitor_a_cmd, stdout=resource_usage_a, stderr=subprocess.STDOUT )
        
        # Start Router B --------------------------------
        cmd_b = [
            "systemd-run", "--quiet", "--user", "--scope",
            "-p", f"CPUQuota={CPU}%",
            ROUTER, "--config", "./B.conf"
        ]
        with open(f"{RESULT_ROOT}/routers/B.log", "w") as log_b:
            router_b_proc = subprocess.Popen(cmd_b, stdout=log_b, stderr=subprocess.STDOUT)
        print("Router B started")
        
        # Give plenty of time for the routers to set up the network
        time.sleep(3)

        # Start the monitor for Router B
        monitor_b_cmd = [ monitor_process_path, str(router_b_proc.pid) ]
        with open ( f"{RESOURCE_USAGE_DIR}/router_b", "w" ) as resource_usage_b :
            monitor_b_proc = subprocess.Popen ( monitor_b_cmd, stdout=resource_usage_b, stderr=subprocess.STDOUT )
        
        # Give plenty of time for the routers to set up the network
        time.sleep(10)
        
        # Start the server. This is only done once.
        proc_server = subprocess.Popen(["iperf3", "-s", "-p", "5801"])
        print("server started")
        
        for ST in SENDER_THREADS:
            time.sleep(1)
            for ITERATION in ITERATIONS:
                print(" ")
                print(" ")
                RESULT_NAME = f"cpu_{CPU}_sender-threads_{ST}_router-threads_{RT}_iteration_{ITERATION}"
                result_path = f"{TEST_RESULTS_DIR}/{RESULT_NAME}"
                print ( f"Result path is {result_path}" )
            
                # Make the command we will use to run the client.
                cmd_client = [
                    "iperf3", "-c", "127.0.0.1", "-p", "5800",
                    "-P", ST, "-t", str(DURATION)
                ]
                # For the client use Popen, because then we can wait 
                # for the process to complete.
                # Maybe the process will complete because it has finished
                # its alotted time.
                # Or maybe it is running indefinitely (in a soak test), and
                # the user just killed it. Works either way.
                result_file  = open(result_path, "w")
                iperf_client = subprocess.Popen(cmd_client, stdout=result_file)

                if DURATION == 0 :
                  print(f"\n\niperf3 client running indefinitely. PID: {iperf_client.pid}")
                  print(f"Kill the process (e.g., via 'kill {iperf_client.pid}') when ready.\n\n")
                  time.sleep(5)


                # Wait for the iperf server to close.
                iperf_client.wait()
                print ( "\n\nThe iperf client has terminated.\n\n" )
                result_file.close()

                print(" ")
                test_count += 1
                print(f"test {test_count} of {n_tests} complete")
                time.sleep(5)
        
        time.sleep(5)
        print(" ")
        print(f"killing server at PID {proc_server.pid}")
        proc_server.kill()
        proc_server.wait()
        print ( "Done killing server." )

        print("Killing routers...")
        monitor_a_proc.kill()
        monitor_a_proc.wait()
        router_a_proc.kill()
        router_a_proc.wait()

        monitor_b_proc.kill()
        monitor_b_proc.wait()
        router_b_proc.kill()
        router_b_proc.wait()
        print ( "Done killing routers." )
        print(" ")
        print(" ")
        print(" ")

print(datetime.now())
print ( f"Results are at: {RESULT_ROOT}" )

print(" ")
print("=======================================")
print("Running results post-processing")
print("=======================================")
print(" ")
time.sleep(10)
print ( f"Calling {post_processor_path} {ROUTER_VERSION} {TIMESTAMP} {RESULT_ROOT}" )
subprocess.run([post_processor_path, ROUTER_VERSION, TIMESTAMP, RESULT_ROOT])

print(" ")
print(" ")
print("done")
print(" ")
print(" ")
