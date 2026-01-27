import pickle
import pandas as pd
import os

cache_path = r".cache/bases_2025-12-31.pkl"

if os.path.exists(cache_path):
    try:
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"Type of loaded data: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Keys in pickle: {list(data.keys())}")
            for k, v in data.items():
                print(f"Key: {k}, Type: {type(v)}")
                if isinstance(v, pd.DataFrame):
                    print(f"  - Columns: {list(v.columns)[:10]}...")
        else:
            print("Data is not a dict.")
            
    except Exception as e:
        print(f"Error loading pickle: {e}")
else:
    print("Cache file not found.")
