import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collection.poller import collector

try:
    snapshot = collector.collect_now()
    if snapshot:
        print("Success! Snapshot collected.")
    else:
        print("Failed to collect snapshot! Returned None.")
except Exception as e:
    import traceback
    traceback.print_exc()
