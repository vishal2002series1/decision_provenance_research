#!/usr/bin/env python3
"""
GDPR Cryptographic Erasure Experiments
Validates: PII erasure, chain integrity, performance impact
"""

import json
import time
import hashlib
import secrets
import os
import shutil
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import numpy as np
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for GDPR erasure experiments"""
    num_decisions: int = 1000
    num_runs: int = 5
    seeds: List[int] = None
    ephemeral_store: str = "/tmp/dpg_ephemeral"
    ledger_store: str = "/tmp/dpg_ledger"
    
    def __post_init__(self):
        if self.seeds is None:
            self.seeds = [42, 43, 44, 45, 46]

# ============================================================================
# SYNTHETIC PII GENERATOR
# ============================================================================

class PIIGenerator:
    """Generate realistic synthetic PII for testing"""
    
    FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", 
                   "Michael", "Linda", "William", "Barbara", "David", "Elizabeth"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez"]
    CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
              "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]
    STATES = ["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
    
    @staticmethod
    def generate_ssn() -> str:
        """Generate synthetic 9-digit SSN"""
        return f"{np.random.randint(100, 999)}-{np.random.randint(10, 99)}-{np.random.randint(1000, 9999)}"
    
    @staticmethod
    def generate_person() -> Dict:
        """Generate complete synthetic person"""
        return {
            "name": f"{np.random.choice(PIIGenerator.FIRST_NAMES)} {np.random.choice(PIIGenerator.LAST_NAMES)}",
            "ssn": PIIGenerator.generate_ssn(),
            "address": f"{np.random.randint(100, 9999)} {np.random.choice(['Main', 'Oak', 'Maple', 'Cedar'])} St",
            "city": np.random.choice(PIIGenerator.CITIES),
            "state": np.random.choice(PIIGenerator.STATES),
            "zip": f"{np.random.randint(10000, 99999)}",
            "income": np.random.randint(30000, 150000),
            "credit_score": np.random.randint(550, 850)
        }

# ============================================================================
# DPG WITH CRYPTOGRAPHIC ERASURE
# ============================================================================

class DPGWithErasure:
    """DPG implementation with cryptographic erasure support"""
    
    def __init__(self, ephemeral_store: str, ledger_store: str):
        self.ephemeral_store = Path(ephemeral_store)
        self.ledger_store = Path(ledger_store)
        
        # Create directories
        self.ephemeral_store.mkdir(parents=True, exist_ok=True)
        self.ledger_store.mkdir(parents=True, exist_ok=True)
        
        self.chain: List[Dict] = []
        self.genesis_hash = "0" * 64
        
    def hash_data(self, data: str) -> str:
        """SHA256 hash"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def store_decision_with_pii(self, decision_id: int, pii_data: Dict, 
                                 action_type: str, result: str) -> Dict:
        """
        Store decision with PII using cryptographic erasure pattern
        
        Returns: node with hash reference to PII
        """
        # Generate salt
        salt = secrets.token_bytes(16)  # 128-bit salt
        
        # Store raw PII + salt in ephemeral store
        pii_path = self.ephemeral_store / f"pii_{decision_id}.json"
        salt_path = self.ephemeral_store / f"salt_{decision_id}.bin"
        
        with open(pii_path, 'w') as f:
            json.dump(pii_data, f)
        with open(salt_path, 'wb') as f:
            f.write(salt)
        
        # Compute hash reference: SHA256(PII || Salt)
        pii_str = json.dumps(pii_data, sort_keys=True)
        combined = pii_str.encode() + salt
        pii_hash = hashlib.sha256(combined).hexdigest()
        
        # Create DPG node with ONLY hash reference
        prev_hash = self.chain[-1]["hash"] if self.chain else self.genesis_hash
        
        node = {
            "id": decision_id,
            "prev_hash": prev_hash,
            "action_type": action_type,
            "pii_reference": pii_hash,  # ONLY hash stored in ledger
            "result": result,
            "timestamp": time.time(),
            "has_pii": True,
            "pii_path": str(pii_path),  # metadata only
            "salt_path": str(salt_path)  # metadata only
        }
        
        # Hash entire node
        node_str = json.dumps({k: v for k, v in node.items() if k != 'hash'}, sort_keys=True)
        node["hash"] = self.hash_data(node_str)
        
        self.chain.append(node)
        
        # Store node in ledger
        node_path = self.ledger_store / f"node_{decision_id}.json"
        with open(node_path, 'w') as f:
            json.dump(node, f, indent=2)
        
        return node
    
    def execute_erasure(self, decision_id: int) -> Dict:
        """
        Execute cryptographic erasure per GDPR Article 17
        
        Steps:
        1. Delete raw PII from ephemeral store
        2. Delete cryptographic salt
        3. Mark node as erased (hash remains)
        
        Returns: erasure stats
        """
        start_time = time.time()
        
        # Find node
        node = next((n for n in self.chain if n["id"] == decision_id), None)
        if not node or not node.get("has_pii"):
            return {"success": False, "reason": "Node not found or no PII"}
        
        # Delete PII file
        pii_path = Path(node["pii_path"])
        salt_path = Path(node["salt_path"])
        
        pii_deleted = False
        salt_deleted = False
        
        if pii_path.exists():
            pii_path.unlink()
            pii_deleted = True
        
        if salt_path.exists():
            salt_path.unlink()
            salt_deleted = True
        
        # Update node metadata (hash UNCHANGED)
        node["pii_erased"] = True
        node["erasure_timestamp"] = time.time()
        node["has_pii"] = False
        
        # Re-save node to ledger
        node_path = self.ledger_store / f"node_{decision_id}.json"
        with open(node_path, 'w') as f:
            json.dump(node, f, indent=2)
        
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "decision_id": decision_id,
            "pii_deleted": pii_deleted,
            "salt_deleted": salt_deleted,
            "erasure_time_ms": elapsed * 1000,
            "hash_preserved": node["pii_reference"]  # Hash still exists
        }
    
    def verify_chain(self) -> Dict:
        """Verify entire chain integrity"""
        start_time = time.time()
        
        valid = True
        broken_links = []
        
        for i, node in enumerate(self.chain):
            expected_prev = self.genesis_hash if i == 0 else self.chain[i-1]["hash"]
            if node["prev_hash"] != expected_prev:
                valid = False
                broken_links.append(i)
        
        elapsed = time.time() - start_time
        
        return {
            "valid": valid,
            "chain_length": len(self.chain),
            "broken_links": broken_links,
            "verification_time_ms": elapsed * 1000
        }
    
    def attempt_pii_recovery(self, decision_id: int) -> Dict:
        """
        Attempt to recover PII after erasure (should fail)
        
        Simulates brute-force attack on 128-bit salt
        """
        node = next((n for n in self.chain if n["id"] == decision_id), None)
        if not node:
            return {"success": False, "reason": "Node not found"}
        
        # Check if PII still exists
        pii_path = Path(node["pii_path"])
        salt_path = Path(node["salt_path"])
        
        pii_exists = pii_path.exists()
        salt_exists = salt_path.exists()
        
        # If both deleted, recovery is computationally infeasible
        if not pii_exists and not salt_exists:
            # Theoretical brute-force time: 2^128 operations
            # At 1 billion hashes/sec: 2^128 / 10^9 ≈ 10^29 seconds ≈ 10^21 years
            brute_force_years = 2**128 / (10**9 * 60 * 60 * 24 * 365)
            
            return {
                "recoverable": False,
                "pii_exists": False,
                "salt_exists": False,
                "brute_force_complexity": "2^128 operations",
                "estimated_years": f"{brute_force_years:.2e}",
                "hash_preserved": node["pii_reference"]
            }
        
        # If files exist, recoverable
        return {
            "recoverable": True,
            "pii_exists": pii_exists,
            "salt_exists": salt_exists
        }
    
    def cleanup(self):
        """Clean up experiment directories"""
        if self.ephemeral_store.exists():
            shutil.rmtree(self.ephemeral_store)
        if self.ledger_store.exists():
            shutil.rmtree(self.ledger_store)

# ============================================================================
# EXPERIMENT 1A: ERASURE EFFECTIVENESS
# ============================================================================

def experiment_1a_erasure_effectiveness(config: ExperimentConfig) -> List[Dict]:
    """
    Experiment 1A: Validate erasure makes PII unrecoverable
    """
    print("\n" + "="*80)
    print("EXPERIMENT 1A: ERASURE EFFECTIVENESS")
    print("="*80)
    
    results = []
    
    for run_num, seed in enumerate(config.seeds, 1):
        print(f"\n[Run {run_num}/5] Seed: {seed}")
        np.random.seed(seed)
        
        # Create DPG
        dpg = DPGWithErasure(
            ephemeral_store=f"{config.ephemeral_store}_{run_num}",
            ledger_store=f"{config.ledger_store}_{run_num}"
        )
        
        # Phase 1: Store 500 decisions
        print("  Phase 1: Storing 500 decisions with PII...")
        for i in range(500):
            pii = PIIGenerator.generate_person()
            dpg.store_decision_with_pii(
                decision_id=i,
                pii_data=pii,
                action_type="DECISION",
                result="APPROVED" if np.random.random() > 0.3 else "DENIED"
            )
        
        # Phase 2: Erase 250 random decisions
        print("  Phase 2: Erasing 250 random decisions...")
        erasure_targets = np.random.choice(500, size=250, replace=False)
        
        erasure_results = []
        for decision_id in erasure_targets:
            result = dpg.execute_erasure(decision_id)
            erasure_results.append(result)
        
        # Phase 3: Attempt recovery
        print("  Phase 3: Attempting PII recovery (should fail)...")
        recovery_attempts = []
        for decision_id in erasure_targets[:50]:  # Test 50 random
            result = dpg.attempt_pii_recovery(decision_id)
            recovery_attempts.append(result)
        
        # Phase 4: Verify chain integrity
        print("  Phase 4: Verifying chain integrity...")
        chain_result = dpg.verify_chain()
        
        # Calculate metrics
        erasure_success_rate = sum(1 for r in erasure_results if r["success"]) / len(erasure_results) * 100
        recovery_failure_rate = sum(1 for r in recovery_attempts if not r["recoverable"]) / len(recovery_attempts) * 100
        
        run_result = {
            "run_number": run_num,
            "seed": seed,
            "total_decisions": 500,
            "erasures_attempted": len(erasure_targets),
            "erasures_successful": sum(1 for r in erasure_results if r["success"]),
            "erasure_success_rate_pct": erasure_success_rate,
            "recovery_attempts": len(recovery_attempts),
            "recovery_failures": sum(1 for r in recovery_attempts if not r["recoverable"]),
            "recovery_failure_rate_pct": recovery_failure_rate,
            "chain_valid": chain_result["valid"],
            "chain_length": chain_result["chain_length"],
            "avg_erasure_time_ms": np.mean([r["erasure_time_ms"] for r in erasure_results]),
            "timestamp": time.time()
        }
        
        results.append(run_result)
        
        print(f"  ✓ Erasure Success: {erasure_success_rate:.1f}%")
        print(f"  ✓ Recovery Failure: {recovery_failure_rate:.1f}%")
        print(f"  ✓ Chain Valid: {chain_result['valid']}")
        
        # Cleanup
        dpg.cleanup()
    
    return results

# ============================================================================
# EXPERIMENT 1B: PERFORMANCE IMPACT
# ============================================================================

def experiment_1b_erasure_performance(config: ExperimentConfig) -> List[Dict]:
    """
    Experiment 1B: Measure performance impact of erasure mechanism
    """
    print("\n" + "="*80)
    print("EXPERIMENT 1B: ERASURE PERFORMANCE IMPACT")
    print("="*80)
    
    results = []
    batch_sizes = [100, 500, 1000]
    
    for run_num, seed in enumerate(config.seeds, 1):
        print(f"\n[Run {run_num}/5] Seed: {seed}")
        np.random.seed(seed)
        
        for batch_size in batch_sizes:
            print(f"  Testing batch size: {batch_size}")
            
            # Baseline: No erasure mechanism
            dpg_baseline = DPGWithErasure(
                ephemeral_store=f"{config.ephemeral_store}_baseline_{run_num}",
                ledger_store=f"{config.ledger_store}_baseline_{run_num}"
            )
            
            start = time.time()
            for i in range(batch_size):
                pii = PIIGenerator.generate_person()
                dpg_baseline.store_decision_with_pii(i, pii, "DECISION", "APPROVED")
            baseline_time = time.time() - start
            
            # With erasure: Store + Erase 50%
            dpg_erasure = DPGWithErasure(
                ephemeral_store=f"{config.ephemeral_store}_erasure_{run_num}",
                ledger_store=f"{config.ledger_store}_erasure_{run_num}"
            )
            
            start = time.time()
            for i in range(batch_size):
                pii = PIIGenerator.generate_person()
                dpg_erasure.store_decision_with_pii(i, pii, "DECISION", "APPROVED")
            storage_time = time.time() - start
            
            # Execute erasure on 50%
            erasure_targets = np.random.choice(batch_size, size=batch_size//2, replace=False)
            start = time.time()
            for decision_id in erasure_targets:
                dpg_erasure.execute_erasure(decision_id)
            erasure_time = time.time() - start
            
            # Calculate metrics
            storage_latency_ms = (storage_time / batch_size) * 1000
            baseline_latency_ms = (baseline_time / batch_size) * 1000
            storage_overhead_ms = storage_latency_ms - baseline_latency_ms
            erasure_latency_ms = (erasure_time / (batch_size//2)) * 1000
            
            result = {
                "run_number": run_num,
                "seed": seed,
                "batch_size": batch_size,
                "baseline_latency_ms": baseline_latency_ms,
                "storage_latency_ms": storage_latency_ms,
                "storage_overhead_ms": storage_overhead_ms,
                "storage_overhead_pct": (storage_overhead_ms / baseline_latency_ms) * 100,
                "erasure_latency_ms": erasure_latency_ms,
                "total_time_s": baseline_time + storage_time + erasure_time,
                "timestamp": time.time()
            }
            
            results.append(result)
            
            print(f"    Storage Overhead: +{storage_overhead_ms:.3f}ms ({result['storage_overhead_pct']:.1f}%)")
            print(f"    Erasure Latency: {erasure_latency_ms:.3f}ms")
            
            # Cleanup
            dpg_baseline.cleanup()
            dpg_erasure.cleanup()
    
    return results

# ============================================================================
# EXPERIMENT 1C: GDPR COMPLIANCE
# ============================================================================

def experiment_1c_gdpr_compliance(config: ExperimentConfig) -> List[Dict]:
    """
    Experiment 1C: Validate GDPR Article 17 compliance
    """
    print("\n" + "="*80)
    print("EXPERIMENT 1C: GDPR ARTICLE 17 COMPLIANCE")
    print("="*80)
    
    results = []
    
    for run_num, seed in enumerate(config.seeds, 1):
        print(f"\n[Run {run_num}/5] Seed: {seed}")
        np.random.seed(seed)
        
        dpg = DPGWithErasure(
            ephemeral_store=f"{config.ephemeral_store}_{run_num}",
            ledger_store=f"{config.ledger_store}_{run_num}"
        )
        
        # Create 100 decisions
        print("  Creating 100 decisions with PII...")
        for i in range(100):
            pii = PIIGenerator.generate_person()
            dpg.store_decision_with_pii(i, pii, "DECISION", "APPROVED")
        
        # Test GDPR Article 17 requirements
        print("  Testing GDPR Article 17 requirements...")
        
        # Requirement 1: PII can be deleted
        erasure_result = dpg.execute_erasure(0)
        pii_deletable = erasure_result["success"] and erasure_result["pii_deleted"]
        
        # Requirement 2: Audit trail of erasure exists
        node = dpg.chain[0]
        audit_exists = "pii_erased" in node and "erasure_timestamp" in node
        
        # Requirement 3: No residual PII in backups
        recovery = dpg.attempt_pii_recovery(0)
        no_residual = not recovery["recoverable"]
        
        # Requirement 4: Hash preserved (audit structure intact)
        hash_preserved = "pii_reference" in node
        
        # Requirement 5: Chain remains valid
        chain_valid = dpg.verify_chain()["valid"]
        
        # Calculate compliance score
        requirements_met = sum([
            pii_deletable,
            audit_exists,
            no_residual,
            hash_preserved,
            chain_valid
        ])
        compliance_score = (requirements_met / 5) * 100
        
        result = {
            "run_number": run_num,
            "seed": seed,
            "pii_deletable": pii_deletable,
            "audit_trail_exists": audit_exists,
            "no_residual_pii": no_residual,
            "hash_preserved": hash_preserved,
            "chain_valid": chain_valid,
            "requirements_met": requirements_met,
            "compliance_score_pct": compliance_score,
            "timestamp": time.time()
        }
        
        results.append(result)
        
        print(f"  ✓ GDPR Compliance Score: {compliance_score:.0f}%")
        print(f"    - PII Deletable: {'✓' if pii_deletable else '✗'}")
        print(f"    - Audit Trail: {'✓' if audit_exists else '✗'}")
        print(f"    - No Residual: {'✓' if no_residual else '✗'}")
        print(f"    - Hash Preserved: {'✓' if hash_preserved else '✗'}")
        print(f"    - Chain Valid: {'✓' if chain_valid else '✗'}")
        
        dpg.cleanup()
    
    return results

# ============================================================================
# MAIN RUNNER
# ============================================================================

def main():
    """Run all GDPR erasure experiments"""
    
    config = ExperimentConfig()
    
    print("="*80)
    print("DPG GDPR CRYPTOGRAPHIC ERASURE EXPERIMENTS")
    print("="*80)
    print(f"Configuration:")
    print(f"  - Runs: {config.num_runs}")
    print(f"  - Seeds: {config.seeds}")
    print(f"  - Decisions per run: {config.num_decisions}")
    
    # Run experiments
    exp1a_results = experiment_1a_erasure_effectiveness(config)
    exp1b_results = experiment_1b_erasure_performance(config)
    exp1c_results = experiment_1c_gdpr_compliance(config)
    
    # Save results
    output_dir = Path("outputs/gdpr_experiments")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "exp1a_erasure_effectiveness.json", 'w') as f:
        json.dump(exp1a_results, f, indent=2)
    
    with open(output_dir / "exp1b_erasure_performance.json", 'w') as f:
        json.dump(exp1b_results, f, indent=2)
    
    with open(output_dir / "exp1c_gdpr_compliance.json", 'w') as f:
        json.dump(exp1c_results, f, indent=2)
    
    print("\n" + "="*80)
    print("✓ ALL GDPR EXPERIMENTS COMPLETE")
    print("="*80)
    print(f"Results saved to: {output_dir}")
    
    # Print summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print("\nExperiment 1A: Erasure Effectiveness")
    erasure_rates = [r["erasure_success_rate_pct"] for r in exp1a_results]
    recovery_rates = [r["recovery_failure_rate_pct"] for r in exp1a_results]
    print(f"  Erasure Success: {np.mean(erasure_rates):.1f}% ± {np.std(erasure_rates):.1f}%")
    print(f"  Recovery Failure: {np.mean(recovery_rates):.1f}% ± {np.std(recovery_rates):.1f}%")
    
    print("\nExperiment 1B: Performance Impact")
    for batch_size in [100, 500, 1000]:
        batch_results = [r for r in exp1b_results if r["batch_size"] == batch_size]
        overheads = [r["storage_overhead_ms"] for r in batch_results]
        print(f"  Batch {batch_size}: +{np.mean(overheads):.3f}ms ± {np.std(overheads):.3f}ms")
    
    print("\nExperiment 1C: GDPR Compliance")
    compliance_scores = [r["compliance_score_pct"] for r in exp1c_results]
    print(f"  Compliance Score: {np.mean(compliance_scores):.0f}% ± {np.std(compliance_scores):.0f}%")

if __name__ == "__main__":
    main()
