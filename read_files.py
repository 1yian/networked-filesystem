import subprocess
import random
import re
import numpy as np
import csv
from tqdm import tqdm

def extract_time(time_str):
    # For elapsed time which is in the format `0:02.66`
    if ':' in time_str:
        minutes, seconds = time_str.split(':')
        return 60 * float(minutes) + float(seconds)
    # For user and system time which are in the format `0.01`
    else:
        return float(time_str)

# Number of trials and loops
num_trials = 10
n = 50

# List to store results for each trial
results = []

for trial in tqdm(range(num_trials), desc="Trials"):
    real_times, user_times, sys_times = [], [], []
    for i in tqdm(range(1, n + 1), desc=f"Trial {trial + 1} Iterations", leave=False):
        skip = random.randint(0, 199)
        cmd = f"time dd if=file_{i} of=/dev/null bs=1M count=10 skip={skip}"
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, shell=True, text=True).stderr
        
        user_time_str = re.search(r'(\d+.\d+)user', result)
        sys_time_str = re.search(r'(\d+.\d+)system', result)
        elapsed_time_str = re.search(r'(\d+:\d+.\d+)elapsed', result)

        if user_time_str and sys_time_str and elapsed_time_str:
            real_times.append(extract_time(elapsed_time_str.group(1)))
            user_times.append(extract_time(user_time_str.group(1)))
            sys_times.append(extract_time(sys_time_str.group(1)))
        else:
            print(f"Failed to extract time for Trial {trial + 1}, Iteration {i}")
            continue

    # Compute statistics using numpy
    real_times_np, user_times_np, sys_times_np = np.array(real_times), np.array(user_times), np.array(sys_times)
    
    results.append([
        np.mean(real_times_np), np.std(real_times_np),
        np.mean(user_times_np), np.std(user_times_np),
        np.mean(sys_times_np), np.std(sys_times_np)
    ])

# Write results to CSV
with open('results.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Mean Real', 'Std Dev Real', 'Mean User', 'Std Dev User', 'Mean Sys', 'Std Dev Sys'])
    writer.writerows(results)

