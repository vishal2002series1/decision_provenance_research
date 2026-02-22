from src.provenance import ProvenanceGraph
from src.llm_engine import BedrockEngine

def run_experiment():
    # 1. Initialize
    tracker = ProvenanceGraph()
    llm = BedrockEngine(region="us-east-1") # Ensure your AWS CLI is configured!

    print("--- 🚀 Starting Agent with Provenance Tracking ---")

    # 2. Simulate User Input
    user_query = "Is the borrower eligible for a loan? Income: 50k, Debt: 10k."
    tracker.add_step("USER_INPUT", {"query": user_query}, {"status": "received"})

    # 3. Step 1: Reasoning (Using AWS)
    prompt = f"Analyze this loan application: {user_query}. Return a JSON with debt_to_income ratio."
    response = llm.generate(prompt)
    
    # LOG THE REASONING (This is the crucial audit step)
    tracker.add_step("REASONING", {"prompt": prompt}, {"response": response})

    # 4. Step 2: Decision
    decision = "APPROVED" if "low risk" in response.lower() or "eligible" in response.lower() else "MANUAL_REVIEW"
    tracker.add_step("DECISION", {"logic": "threshold_check"}, {"final_verdict": decision})

    # 5. The Audit
    tracker.verify_integrity()

if __name__ == "__main__":
    run_experiment()