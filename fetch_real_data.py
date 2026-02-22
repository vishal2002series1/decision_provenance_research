from ucimlrepo import fetch_ucirepo 
import pandas as pd

def fetch_german_credit():
    print("--- 📥 Downloading Real Benchmark Data (UCI Statlog German Credit) ---")
    
    # ID 144 is the standard 'Statlog (German Credit Data)'
    german_credit = fetch_ucirepo(id=144) 
    
    # Get features (X) and targets (y)
    X = german_credit.data.features
    y = german_credit.data.targets
    
    # Combine them for our agent to process
    # Note: The target column is often named 'class' (1=Good, 2=Bad)
    df = pd.concat([X, y], axis=1)
    
    # Save to local CSV for the agent to read
    output_path = "data/german_credit_real.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ Data fetched successfully!")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Saved to: {output_path}")
    
    # Preview for the user
    print("\nSample Data:")
    print(df.head(3))

if __name__ == "__main__":
    fetch_german_credit()