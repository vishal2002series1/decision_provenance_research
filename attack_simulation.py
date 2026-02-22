from src.provenance import ProvenanceGraph

def simulate_attack():
    print("--- ⚔️ STARTING SECURITY ATTACK SIMULATION ⚔️ ---")
    
    # 1. Create a legitimate graph
    tracker = ProvenanceGraph()
    tracker.add_step("USER_INPUT", {"income": "50k"}, {})
    
    # The AI decides to REJECT based on low income
    tracker.add_step("DECISION", {"rule": "income < 60k"}, {"verdict": "REJECTED"})
    
    print("\n[State 1] Original Graph Created. Verdict: REJECTED")
    tracker.verify_integrity() # Should Pass

    # 2. The Attack: A "hacker" modifies the log in memory/database
    print("\n[Attack] ⚠️ Hacker is altering the Decision Node to 'APPROVED'...")
    
    # Access the node directly (simulating DB access)
    target_node = tracker.chain[1] 
    
    # CHANGE THE DATA
    target_node.output_data = {"verdict": "APPROVED"} 
    
    # NOTE: The node.node_hash is still the OLD hash (signed with REJECTED).
    # The data no longer matches the signature.

    # 3. Run the Audit
    print("[Defense] Running Forensic Audit...")
    is_valid = tracker.verify_integrity()

    if not is_valid:
        print("\n🏆 SUCCESS: The system detected the tampering! The graph is invalid.")
    else:
        print("\n💀 FAILURE: The attack succeeded (This should not happen).")

if __name__ == "__main__":
    simulate_attack()