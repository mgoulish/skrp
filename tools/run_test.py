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

# User-settable parameters as command-line arguments
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

# Calculate the total number of tests we will be doing,
# so we can give him some idea of progress.
n_tests = len(ITERATIONS) * len(CPU_LIMITS) * len(ROUTER_THREADS) * len(SENDER_THREADS)

# Which test we are doing determines what program
# we call 
if TEST != 'throughput' and TEST != 'soak' :
  print ( "Test must be 'throughput' or 'soak'" )
  sys.exit ( 1 )

# TODO  How do I make this work for the 1_router test.  If I care.
#       And what about 0 routers ???

# TODO -- set all params based on test name
#         add test name of short_soak

post_processor_path = None
if TEST == 'throughput' : 
  post_processor_path = f"{SKRP_ROOT}/tests/throughput/2_routers/process_results.py"
elif TEST == 'soak' :   
  post_processor_path = f"{SKRP_ROOT}/tests/soak/2_routers/process_results.py"

monitor_process_path = f"{SKRP_ROOT}/tools/monitor_process.py"

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
            proc_a = subprocess.Popen(cmd_a, stdout=log_a, stderr=subprocess.STDOUT)
        print("Router A started")
        time.sleep(3)

        # Start the monitor for Router A
        monitor_a_cmd = [ monitor_process_path, str(proc_a.pid) ]
        with open ( f"{RESOURCE_USAGE_DIR}/router_a", "w" ) as resource_usage_a :
            monitor_a = subprocess.Popen ( monitor_a_cmd, stdout=resource_usage_a, stderr=subprocess.STDOUT )
        
        # Start Router B --------------------------------
        cmd_b = [
            "systemd-run", "--quiet", "--user", "--scope",
            "-p", f"CPUQuota={CPU}%",
            ROUTER, "--config", "./B.conf"
        ]
        with open(f"{RESULT_ROOT}/routers/B.log", "w") as log_b:
            proc_b = subprocess.Popen(cmd_b, stdout=log_b, stderr=subprocess.STDOUT)
        
        # Give plenty of time for the routers to set up the network
        time.sleep(3)

        # Start the monitor for Router B
        monitor_b_cmd = [ monitor_process_path, str(proc_b.pid) ]
        with open ( f"{RESOURCE_USAGE_DIR}/router_b", "w" ) as resource_usage_b :
            monitor_b = subprocess.Popen ( monitor_b_cmd, stdout=resource_usage_b, stderr=subprocess.STDOUT )
        
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
            
                # Run the client
                cmd_client = [
                    "iperf3", "-c", "127.0.0.1", "-p", "5800",
                    "-P", ST, "-t", str(DURATION)
                ]
                with open(f"{TEST_RESULTS_DIR}/{RESULT_NAME}", "w") as result_file:
                    subprocess.run(cmd_client, stdout=result_file, check=True)
                print(" ")
                test_count += 1
                print(f"test {test_count} of {n_tests} complete")
                time.sleep(5)
        
        time.sleep(5)
        print(" ")
        print(f"killing server at PID {proc_server.pid}")
        proc_server.kill()
        print("killing routers...")
        subprocess.run(["pkill", "skrouterd"])          # TODO THIS isn't right -- use proc structs
        subprocess.run(["pkill", "monitor_process"])
        time.sleep(2)
        subprocess.run(["pkill", "skrouterd"])
        subprocess.run(["pkill", "monitor_process"])
        time.sleep(2)
        print("Printing remaining routers: (there should be none.)")
        try:
            output = subprocess.check_output(["ps", "-aef"])
            for line in output.decode().splitlines():
                if "skrouterd" in line and "grep" not in line:
                    print(line)
        except:
            pass
        print("Done printing remaining routers.")
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
