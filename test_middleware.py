from src.middleware import track_provenance, audit_log
import time

# --- SIMULATION OF A REAL AGENTIC WORKFLOW ---

@track_provenance(action_type="DATA_FETCH")
def fetch_user_data(user_id):
    print(f"   ... Fetching data for {user_id} ...")
    # Simulating a DB call
    return {"id": user_id, "credit_score": 720, "annual_income": 85000}

@track_provenance(action_type="RISK_ANALYSIS")
def analyze_risk(user_data):
    print(f"   ... Analyze risk for {user_data['id']} ...")
    # Simulating complex logic
    risk_score = (user_data["annual_income"] / 1000) + user_data["credit_score"]
    return {"risk_score": risk_score, "level": "LOW" if risk_score > 600 else "HIGH"}

@track_provenance(action_type="FINAL_VERDICT")
def make_decision(analysis):
    print(f"   ... Finalizing decision ...")
    verdict = "APPROVED" if analysis["level"] == "LOW" else "DENIED"
    return {"final_decision": verdict}

# --- THE EXECUTION ---

def run_real_world_simulation():
    print("--- 🏭 STARTING PRODUCTION SIMULATION ---")
    
    # 1. The Agent runs normally
    user = fetch_user_data("User_12345")
    analysis = analyze_risk(user)
    decision = make_decision(analysis)
    
    print(f"\n✅ User Result: {decision}")
    
    # 2. The Provenance Graph was built silently in the background
    print(f"\n📜 Audit Log Generated: {len(audit_log.chain)} steps tracked.")
    audit_log.verify_integrity()
    
    # 3. Visualize it
    audit_log.visualize("figure_2_middleware_demo.png")

if __name__ == "__main__":
    run_real_world_simulation()