import pandas as pd
import random

def generate_synthetic_data(n=1000):
    print(f"--- 🧪 Generating {n} rows of Synthetic Data ---")
    
    data = {
        "Age": [random.randint(18, 75) for _ in range(n)],
        "Sex": [random.choice(["male", "female"]) for _ in range(n)],
        "Job": [random.randint(0, 3) for _ in range(n)],
        "Housing": [random.choice(["own", "rent", "free"]) for _ in range(n)],
        "SavingAccounts": [random.choice(["little", "moderate", "rich", "quite rich"]) for _ in range(n)],
        "CheckingAccount": [random.choice(["little", "moderate", "rich"]) for _ in range(n)],
        "CreditAmount": [random.randint(500, 15000) for _ in range(n)],
        "Duration": [random.randint(6, 72) for _ in range(n)],
        "Purpose": [random.choice(["radio/TV", "education", "furniture", "car", "business"]) for _ in range(n)],
        "Risk": [random.choice(["good", "bad"]) for _ in range(n)] # Ground truth (ignored by agent)
    }
    
    df = pd.read_json(pd.DataFrame(data).to_json()) # Ensure clean serialization
    df.to_csv("data/german_credit_full.csv", index=False)
    print(f"✅ Saved 'data/german_credit_full.csv' with {n} rows.")

if __name__ == "__main__":
    generate_synthetic_data(1000)