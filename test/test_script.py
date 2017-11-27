import os
import json
import time

N_ITER = 1000000
TMP_FILE = '/tmp/kk.json'

while True:
    if os.path.exists(TMP_FILE):
        with open(TMP_FILE, 'r') as f:
            l = json.load(f)
    else:
        l = []
    
    l = [i**2 for i in range(N_ITER)]
    
    with open(TMP_FILE, 'w') as f:
        json.dump(l, f)

    time.sleep(10)