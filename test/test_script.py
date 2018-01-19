import os
import json
import time
import random
import sys

MAX_LEN = 1000000
TMP_FILE = '/tmp/kk.json'
N_ITER = 100

for i in range(N_ITER):
    if os.path.exists(TMP_FILE):
        with open(TMP_FILE, 'r') as f:
            l = json.load(f)
    else:
        l = []
    
    l = [i**2 for i in range(random.randint(0, MAX_LEN))]
    
    with open(TMP_FILE, 'w') as f:
        json.dump(l, f)

sys.exit(0)