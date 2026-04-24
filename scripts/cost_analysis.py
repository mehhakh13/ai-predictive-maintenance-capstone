import pandas as pd
import os

def run_cost_analysis(file_path):
    print(f"Loading data...")
    try:
        df = pd.read_parquet(file_path)
        target_unis = [10, 11, 12]
        df = df[df['UniversityID'].isin(target_unis)].copy()
        
        cost_col = 'DMC (deferred maintenance cost)'
        
        # --- DETECTIVE STEP ---
        print("\n--- DATA INSPECTION ---")
        print(f"Column Type: {df[cost_col].dtype}")
        print("First 5 values in this column:")
        print(df[cost_col].head())
        # ----------------------

        # Force everything to be a string first, then clean, then convert
        df[cost_col] = df[cost_col].astype(str).str.replace(r'[$, ]', '', regex=True)
        df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)
        
        print(f"\nTotal after cleaning: ${df[cost_col].sum():,.2f}")

        # Final Summary
        uni_analysis = df.groupby(['UniversityID', 'PPM/UPM'])[cost_col].sum().reset_index()
        pd.options.display.float_format = '${:,.2f}'.format
        print("\n--- FINAL RESULTS ---")
        print(uni_analysis)
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    target_file = os.path.join(os.path.dirname(__file__), '..', 'FMUCD_USA.parquet')
    run_cost_analysis(target_file)