import pandas as pd
import time
import statistics
from src.middleware import track_provenance, audit_log

# Load the full dataset
try:
    df = pd.read_csv("data/german_credit_full.csv")
except FileNotFoundError:
    print("❌ Run 'generate_data.py' first!")
    exit()

# --- 1. THE BASELINE (No Middleware) ---
def agent_logic_only(row):
    """Raw logic without any overhead"""
    row_dict = row.to_dict()
    if row_dict.get('SavingAccounts') == 'rich': return "good"
    elif row_dict.get('CreditAmount', 0) < 3000 and row_dict.get('Housing') == 'own': return "good"
    else: return "bad"

# --- 2. THE EXPERIMENT (With Middleware) ---
@track_provenance(action_type="AGENT_EVALUATION")
def agent_with_provenance(row):
    return agent_logic_only(row) # Calls the exact same logic

def run_scientific_benchmark():
    print(f"--- 📊 Scientific Benchmark (N={len(df)}) ---")
    
    # Run Baseline
    start_base = time.time()
    for _, row in df.iterrows():
        agent_logic_only(row)
    end_base = time.time()
    avg_base = (end_base - start_base) / len(df)
    
    print(f"🔹 Baseline (Logic Only): {avg_base:.6f}s per decision")

    # Run Experiment
    start_exp = time.time()
    for _, row in df.iterrows():
        agent_with_provenance(row)
    end_exp = time.time()
    avg_exp = (end_exp - start_exp) / len(df)
    
    print(f"🔸 Experiment (With DPG): {avg_exp:.6f}s per decision")
    
    # The Metrics for the Paper
    overhead = avg_exp - avg_base
    overhead_pct = (overhead / avg_base) * 100
    
    print(f"\nRESULTS FOR PAPER:")
    print(f"------------------")
    print(f"Absolute Overhead: {overhead * 1000:.4f} ms") # Convert to ms
    print(f"Relative Overhead: {overhead_pct:.2f}%")
    print(f"------------------")

if __name__ == "__main__":
    run_scientific_benchmark()