import pandas as pd
import numpy as np
import os
import sys

# Define file paths
PREP_FILE = 'df_prep_consolidado.csv'
# Using raw string for Windows network path to avoid escape character issues
TARV_FILE = r'//SAP109/Bancos AMA/Arquivos Atuais/Bancos Atuais HIV/Mensais/PVHA_prim_ult.csv'

def load_data():
    print(">>> Loading PrEP data...")
    if not os.path.exists(PREP_FILE):
        print(f"Error: PrEP file not found at {PREP_FILE}")
        sys.exit(1)
        
    # Load PrEP
    # We need Cod_unificado for merging and dates for analysis
    cols_prep = ['Cod_unificado', 'dt_disp_max', 'dt_disp_min'] 
    try:
        df_prep = pd.read_csv(PREP_FILE, sep=';', encoding='latin-1', usecols=lambda c: c in cols_prep)
    except ValueError:
        # Fallback if columns missing, read all to debug or try to find equivalents
        print("Warning: Specific columns not found in PrEP, reading first 5 rows to debug...")
        df_temp = pd.read_csv(PREP_FILE, sep=';', encoding='latin-1', nrows=5)
        print(f"Available columns: {list(df_temp.columns)}")
        sys.exit(1)

    print(f"PrEP loaded: {len(df_prep)} rows.")
    
    print(">>> Loading TARV data...")
    cols_tarv = ['Cod_unificado', 'data_min', 'data_dispensa_prim']
    
    if not os.path.exists(TARV_FILE):
        print(f"Warning: TARV file not found at {TARV_FILE}")
        print("Attempting to check if it's a permission issue or path issue...")
        # Try local mock if testing or fail
        sys.exit(1)

    try:
        df_tarv = pd.read_csv(TARV_FILE, sep=';', encoding='latin-1', usecols=cols_tarv, low_memory=True)
    except Exception as e:
        print(f"Error reading TARV file: {e}")
        sys.exit(1)
        
    print(f"TARV loaded: {len(df_tarv)} rows.")
    
    return df_prep, df_tarv

def analyze(df_prep, df_tarv):
    print("\n>>> Processing Dates & Merging...")
    
    # 1. Standardize Dates
    # PrEP
    df_prep['dt_disp_max'] = pd.to_datetime(df_prep['dt_disp_max'], errors='coerce')
    df_prep['dt_disp_min'] = pd.to_datetime(df_prep['dt_disp_min'], errors='coerce')
    
    # TARV
    df_tarv['data_dispensa_prim'] = pd.to_datetime(df_tarv['data_dispensa_prim'], dayfirst=True, errors='coerce')
    # Note: 'data_min' in PVHA usually refers to notification or entry, 'data_dispensa_prim' is distinct.
    
    # 2. Merge
    # We want people who are in BOTH (Intersection) to analyze the transition
    df_merged = pd.merge(df_prep, df_tarv, on='Cod_unificado', how='inner', suffixes=('_prep', '_tarv'))
    
    total_intersection = len(df_merged)
    print(f"\nTotal users in both PrEP and TARV lists (by Cod_unificado): {total_intersection}")
    
    if total_intersection == 0:
        print("No overlap found. Check Cod_unificado formatting.")
        return

    # 3. Categorize
    # Error: TARV before or during PrEP
    # We define "During/Before" roughly as: First TARV <= Last PrEP
    # Why? Because if they started TARV *after* the last PrEP, they transitioned.
    # If they started TARV *before* the last PrEP, they were on PrEP while on TARV (error) or started TARV then PrEP (error/weird).
    
    # Let's create the diff
    df_merged['days_diff'] = (df_merged['data_dispensa_prim'] - df_merged['dt_disp_max']).dt.days
    
    # Categories
    # A) Valid Transition (TARV Start > PrEP Last) -> days_diff > 0
    # B) Error/Overlap (TARV Start <= PrEP Last) -> days_diff <= 0
    
    df_valid = df_merged[df_merged['days_diff'] > 0].copy()
    df_error = df_merged[df_merged['days_diff'] <= 0].copy()
    
    # Detailed Error breakdown
    # Error Type 1: TARV Start < PrEP Start (On TARV before even starting PrEP)
    error_before_start = df_error[df_error['data_dispensa_prim'] < df_error['dt_disp_min']]
    # Error Type 2: PrEP Start <= TARV Start <= PrEP Last (Started TARV while on PrEP)
    error_during = df_error[(df_error['data_dispensa_prim'] >= df_error['dt_disp_min'])]

    # 4. Report
    print("\n" + "="*50)
    print("RESULTS SUMMARY")
    print("="*50)
    
    print(f"Total Overlap: {total_intersection}")
    
    print(f"\n[GROUP 1] Valid Transitions (TARV started AFTER PrEP stopped):")
    print(f"Count: {len(df_valid)}")
    print(f"Percentage: {len(df_valid) / total_intersection * 100:.2f}%")
    
    print(f"\n[GROUP 2] Potential Errors (TARV started BEFORE or DURING PrEP):")
    print(f"Count: {len(df_error)}")
    print(f"Percentage: {len(df_error) / total_intersection * 100:.2f}%")
    
    print(f"  - Started TARV before PrEP Start: {len(error_before_start)} ({len(error_before_start)/total_intersection*100:.2f}%)")
    print(f"  - Started TARV during PrEP use:   {len(error_during)} ({len(error_during)/total_intersection*100:.2f}%)")
    
    # 5. Distribution of Time (Valid Transitions)
    if not df_valid.empty:
        print("\n" + "="*50)
        print("DISTRIBUTION OF TIME (Days between Last PrEP & First TARV)")
        print("(Only for Valid Transitions)")
        print("="*50)
        
        stats = df_valid['days_diff'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        print(stats)
        
        # Frequency buckets
        bins = [0, 30, 90, 180, 365, 99999]
        labels = ['< 1 month', '1-3 months', '3-6 months', '6-12 months', '> 1 year']
        dist = pd.cut(df_valid['days_diff'], bins=bins, labels=labels).value_counts().sort_index()
        print("\nTime Buckets:")
        print(dist)

    # Export for user inspection
    print("\nSaving detailed report to 'relatorio_prep_tarv_overlap.csv'...")
    df_merged['status'] = np.where(df_merged['days_diff'] > 0, 'Valid Transition', 'Error/Overlap')
    output_cols = ['Cod_unificado', 'dt_disp_min', 'dt_disp_max', 'data_dispensa_prim', 'days_diff', 'status']
    df_merged[output_cols].to_csv('relatorio_prep_tarv_overlap.csv', index=False, sep=';')
    print("Done.")

if __name__ == "__main__":
    df_p, df_t = load_data()
    analyze(df_p, df_t)
