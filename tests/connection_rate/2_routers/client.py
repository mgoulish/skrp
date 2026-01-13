#!/usr/bin/env python3

import socket
import time
import sys
from collections import Counter

if len(sys.argv) < 4:
    print("Usage: python client.py <host> <port> <duration_seconds>")
    sys.exit(1)

host = sys.argv[1]
port = int(sys.argv[2])
duration = int(sys.argv[3])

start_time = time.time()
end_time = start_time + duration
completion_times = []

while time.time() < end_time:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            data = s.recv(1024)
            if data:
                completion_time = time.time() - start_time
                completion_times.append(completion_time)
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        continue

# Bin completions into seconds (second 1 covers 0-1s, second 2 covers 1-2s, etc.)
second_bins = Counter(int(t) for t in completion_times)

# Print results in CSV format
print("second,connections")
for sec in range(1, duration + 1):
    count = second_bins[sec - 1]
    print(f"{sec},{count}")
