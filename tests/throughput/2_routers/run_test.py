#!/usr/bin/env python3

import os
import subprocess
import time
import datetime

#----------------------------------------------------------
# Begin user-settable parameters 
#----------------------------------------------------------

# Set this based on which version of the Router software you have installed.
ROUTER_VERSION = "3.4.1_test"

# And set this to which test you want to run.
TEST = "throughput"

# How long should each test last?
# I tried 60 seconds, and they were indistinguishable from 15 seconds
# with respect to stability of results.
DURATION = 15

# Each graphed result will the the average of several identically 
# configured tests, the number controlled by this variable.
ITERATIONS = ["1", "2", "3"]

# The CPU allocation for each router during the tests.
CPU_LIMITS = ["500", "400", "300", "200", "100", "50", "25"]

ROUTER_THREADS = ["1", "2", "4", "5", "7", "10"]

SENDER_THREADS = ["1", "2", "5", "10"]
#----------------------------------------------------------
# End user-settable parameters 
#----------------------------------------------------------

RESULT_ROOT = f"../../../results/{ROUTER_VERSION}/{TEST}"
TEST_RESULTS_DIR = f"../../../results/{ROUTER_VERSION}/{TEST}/test_results"
print(f"TEST_RESULTS_DIR == {TEST_RESULTS_DIR}")

os.makedirs(f"{RESULT_ROOT}/test_results", exist_ok=True)
os.makedirs(f"{RESULT_ROOT}/data", exist_ok=True)
os.makedirs(f"{RESULT_ROOT}/graphs", exist_ok=True)
os.makedirs(f"{RESULT_ROOT}/routers", exist_ok=True)

# Your router is installed in the standard place.
ROUTER = "/usr/local/sbin/skrouterd"

print(f"Starting routers from {ROUTER}")
print(datetime.datetime.now())

for RT in ROUTER_THREADS:
    print("===========================================================")
    print(f"Router threads {RT} ")
    print("===========================================================")
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
        print("===========================================================")
        print(f"CPU {CPU} ")
        print("===========================================================")

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
        time.sleep(5)
        
        # Start Router B --------------------------------
        cmd_b = [
            "systemd-run", "--quiet", "--user", "--scope",
            "-p", f"CPUQuota={CPU}%",
            ROUTER, "--config", "./B.conf"
        ]
        with open(f"{RESULT_ROOT}/routers/B.log", "w") as log_b:
            proc_b = subprocess.Popen(cmd_b, stdout=log_b, stderr=subprocess.STDOUT)
        
        # Give plenty of time for the routers to set up the network
        time.sleep(10)
        
        # Start the server. This is only done once.
        proc_server = subprocess.Popen(["iperf3", "-s", "-p", "5801"])
        print("server started")
        
        for ST in SENDER_THREADS:
            print("===========================================================")
            print(f"sender threads {ST} ")
            print("===========================================================")
            time.sleep(1)
            for ITERATION in ITERATIONS:
                print(" ")
                print(" ")
                print("----------------------------------")
                print(f"iteration {ITERATION}")
                print("----------------------------------")
                RESULT_NAME = f"cpu_{CPU}_sender-threads_{ST}_router-threads_{RT}_iteration_{ITERATION}"
            
                # Run the client
                cmd_client = [
                    "iperf3", "-c", "127.0.0.1", "-p", "5800",
                    "-P", ST, "-t", str(DURATION)
                ]
                with open(f"{TEST_RESULTS_DIR}/{RESULT_NAME}", "w") as result_file:
                    subprocess.run(cmd_client, stdout=result_file, check=True)
                print(" ")
                print(f"router threads {RT} sender threads {ST} iteration {ITERATION} complete")
                time.sleep(5)
        
        time.sleep(5)
        print(" ")
        print(f"killing server at PID {proc_server.pid}")
        proc_server.kill()
        print("killing routers...")
        subprocess.run(["pkill", "skrouterd"])
        time.sleep(2)
        subprocess.run(["pkill", "skrouterd"])
        time.sleep(2)
        print("Any routers remaining?")
        try:
            output = subprocess.check_output(["ps", "-aef"])
            for line in output.decode().splitlines():
                if "skrouterd" in line and "grep" not in line:
                    print(line)
        except:
            pass
        print(" ")
        print(" ")
        print(" ")

print(datetime.datetime.now())

print(" ")
print("=======================================")
print("Running results post-processing")
print("=======================================")
print(" ")
time.sleep(10)

subprocess.run(["./process_results.py", ROUTER_VERSION])

print(" ")
print(" ")
print("done")
print(" ")
print(" ")
