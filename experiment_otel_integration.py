#!/usr/bin/env python3
"""
OpenTelemetry Integration Experiments
Validates: Dual export, backend compatibility, selective instrumentation
"""

import json
import time
import hashlib
import threading
import queue
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import numpy as np
from pathlib import Path

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class OTelExperimentConfig:
    """Configuration for OTel integration experiments"""
    num_decisions: int = 1000
    num_runs: int = 5
    seeds: List[int] = None
    otel_endpoint: str = "http://localhost:4317"  # Jaeger OTLP endpoint
    dpg_backend: str = "/tmp/dpg_otel_ledger"
    
    def __post_init__(self):
        if self.seeds is None:
            self.seeds = [42, 43, 44, 45, 46]

# ============================================================================
# DPG WITH OTEL DUAL EXPORT
# ============================================================================

class DPGWithOTel:
    """DPG with dual export to OpenTelemetry + DPG Ledger"""
    
    def __init__(self, ledger_path: str, otel_enabled: bool = True, 
                 otel_endpoint: Optional[str] = None):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.mkdir(parents=True, exist_ok=True)
        
        self.otel_enabled = otel_enabled
        self.chain: List[Dict] = []
        self.genesis_hash = "0" * 64
        
        # Statistics
        self.otel_export_count = 0
        self.dpg_export_count = 0
        self.export_failures = 0
        
        # Setup OpenTelemetry
        if otel_enabled:
            self._setup_otel(otel_endpoint)
    
    def _setup_otel(self, endpoint: Optional[str]):
        """Initialize OpenTelemetry exporter"""
        resource = Resource.create({"service.name": "dpg-agent"})
        provider = TracerProvider(resource=resource)
        
        if endpoint:
            try:
                # OTLP exporter for Jaeger/Tempo
                otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            except Exception as e:
                print(f"  [WARN] OTLP exporter failed: {e}, using console")
                # Fallback to console exporter
                console_exporter = ConsoleSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(console_exporter))
        
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(__name__)
    
    def hash_data(self, data: str) -> str:
        """SHA256 hash"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def log_decision(self, decision_id: int, action_type: str, 
                     inputs: Dict, outputs: Dict) -> Dict:
        """
        Log decision with dual export: OTel + DPG
        
        Returns: node with export stats
        """
        start_time = time.time()
        
        # EXPORT 1: OpenTelemetry span
        otel_success = False
        if self.otel_enabled:
            try:
                with self.tracer.start_as_current_span(f"{action_type}_{decision_id}") as span:
                    span.set_attribute("decision.id", decision_id)
                    span.set_attribute("decision.type", action_type)
                    span.set_attribute("decision.inputs", json.dumps(inputs))
                    span.set_attribute("decision.outputs", json.dumps(outputs))
                    
                    # Simulate agent processing
                    time.sleep(0.001)  # 1ms processing
                
                self.otel_export_count += 1
                otel_success = True
            except Exception as e:
                self.export_failures += 1
                otel_success = False
        
        # EXPORT 2: DPG ledger with Merkle chain
        prev_hash = self.chain[-1]["hash"] if self.chain else self.genesis_hash
        
        node = {
            "id": decision_id,
            "prev_hash": prev_hash,
            "action_type": action_type,
            "inputs": inputs,
            "outputs": outputs,
            "timestamp": time.time(),
            "otel_exported": otel_success
        }
        
        # Hash node
        node_str = json.dumps({k: v for k, v in node.items() if k != 'hash'}, sort_keys=True)
        node["hash"] = self.hash_data(node_str)
        
        self.chain.append(node)
        self.dpg_export_count += 1
        
        # Save to disk
        node_path = self.ledger_path / f"node_{decision_id}.json"
        with open(node_path, 'w') as f:
            json.dump(node, f, indent=2)
        
        elapsed = time.time() - start_time
        
        return {
            "decision_id": decision_id,
            "otel_exported": otel_success,
            "dpg_exported": True,
            "export_time_ms": elapsed * 1000
        }
    
    def verify_chain(self) -> Dict:
        """Verify DPG chain integrity"""
        start_time = time.time()
        
        valid = True
        for i, node in enumerate(self.chain):
            expected_prev = self.genesis_hash if i == 0 else self.chain[i-1]["hash"]
            if node["prev_hash"] != expected_prev:
                valid = False
                break
        
        elapsed = time.time() - start_time
        
        return {
            "valid": valid,
            "chain_length": len(self.chain),
            "verification_time_ms": elapsed * 1000
        }
    
    def get_export_stats(self) -> Dict:
        """Get export statistics"""
        return {
            "otel_exports": self.otel_export_count,
            "dpg_exports": self.dpg_export_count,
            "export_failures": self.export_failures,
            "dual_export_success_rate": (
                (self.otel_export_count / self.dpg_export_count * 100)
                if self.dpg_export_count > 0 else 0
            )
        }

# ============================================================================
# SYNTHETIC AGENT SIMULATOR
# ============================================================================

class SyntheticAgent:
    """Simulate LLM agent workflow"""
    
    @staticmethod
    def generate_decision() -> Dict:
        """Generate synthetic decision data"""
        problem = {
            "query": f"Calculate: {np.random.randint(10, 100)} + {np.random.randint(10, 100)}",
            "context": ["math problem", "addition"]
        }
        
        a = np.random.randint(10, 100)
        b = np.random.randint(10, 100)
        result = a + b
        
        return {
            "inputs": problem,
            "outputs": {"answer": result, "confidence": 0.95}
        }

# ============================================================================
# EXPERIMENT 2A: DUAL EXPORT FUNCTIONALITY
# ============================================================================

def experiment_2a_dual_export(config: OTelExperimentConfig) -> List[Dict]:
    """
    Experiment 2A: Validate dual export to OTel + DPG
    """
    print("\n" + "="*80)
    print("EXPERIMENT 2A: DUAL EXPORT FUNCTIONALITY")
    print("="*80)
    
    results = []
    
    for run_num, seed in enumerate(config.seeds, 1):
        print(f"\n[Run {run_num}/5] Seed: {seed}")
        np.random.seed(seed)
        
        # Create DPG with OTel enabled
        dpg = DPGWithOTel(
            ledger_path=f"{config.dpg_backend}_{run_num}",
            otel_enabled=True,
            otel_endpoint=config.otel_endpoint
        )
        
        # Process decisions
        print(f"  Processing {config.num_decisions} decisions...")
        export_times = []
        
        for i in range(config.num_decisions):
            decision_data = SyntheticAgent.generate_decision()
            
            export_result = dpg.log_decision(
                decision_id=i,
                action_type="DECISION",
                inputs=decision_data["inputs"],
                outputs=decision_data["outputs"]
            )
            
            export_times.append(export_result["export_time_ms"])
        
        # Get statistics
        export_stats = dpg.get_export_stats()
        chain_stats = dpg.verify_chain()
        
        # Calculate metrics
        result = {
            "run_number": run_num,
            "seed": seed,
            "total_decisions": config.num_decisions,
            "otel_exports": export_stats["otel_exports"],
            "dpg_exports": export_stats["dpg_exports"],
            "export_failures": export_stats["export_failures"],
            "export_success_rate_pct": export_stats["dual_export_success_rate"],
            "chain_valid": chain_stats["valid"],
            "avg_export_time_ms": np.mean(export_times),
            "std_export_time_ms": np.std(export_times),
            "timestamp": time.time()
        }
        
        results.append(result)
        
        print(f"  ✓ Export Success Rate: {result['export_success_rate_pct']:.1f}%")
        print(f"  ✓ Avg Export Time: {result['avg_export_time_ms']:.3f}ms")
        print(f"  ✓ Chain Valid: {chain_stats['valid']}")
    
    return results

# ============================================================================
# EXPERIMENT 2B: BACKEND COMPATIBILITY
# ============================================================================

def experiment_2b_backend_compatibility(config: OTelExperimentConfig) -> List[Dict]:
    """
    Experiment 2B: Test compatibility with multiple OTel backends
    
    Note: Requires Docker containers running for each backend
    """
    print("\n" + "="*80)
    print("EXPERIMENT 2B: OTEL BACKEND COMPATIBILITY")
    print("="*80)
    
    backends = [
        {"name": "Jaeger", "endpoint": "http://localhost:4317"},
        {"name": "Console", "endpoint": None},  # Fallback
    ]
    
    results = []
    
    for backend in backends:
        print(f"\n Testing backend: {backend['name']}")
        
        for run_num, seed in enumerate(config.seeds, 1):
            print(f"  [Run {run_num}/5] Seed: {seed}")
            np.random.seed(seed)
            
            dpg = DPGWithOTel(
                ledger_path=f"{config.dpg_backend}_{backend['name']}_{run_num}",
                otel_enabled=True,
                otel_endpoint=backend['endpoint']
            )
            
            # Process sample decisions
            for i in range(100):
                decision_data = SyntheticAgent.generate_decision()
                dpg.log_decision(i, "DECISION", 
                               decision_data["inputs"], 
                               decision_data["outputs"])
            
            export_stats = dpg.get_export_stats()
            
            result = {
                "backend_name": backend['name'],
                "backend_endpoint": backend['endpoint'],
                "run_number": run_num,
                "seed": seed,
                "compatible": export_stats["export_failures"] == 0,
                "export_success_rate_pct": export_stats["dual_export_success_rate"],
                "timestamp": time.time()
            }
            
            results.append(result)
            
            status = "✓ Compatible" if result["compatible"] else "✗ Failed"
            print(f"    {status} ({result['export_success_rate_pct']:.1f}% success)")
    
    return results

# ============================================================================
# EXPERIMENT 2C: SELECTIVE INSTRUMENTATION OVERHEAD
# ============================================================================

def experiment_2c_selective_instrumentation(config: OTelExperimentConfig) -> List[Dict]:
    """
    Experiment 2C: Compare overhead of selective vs. full instrumentation
    """
    print("\n" + "="*80)
    print("EXPERIMENT 2C: SELECTIVE INSTRUMENTATION OVERHEAD")
    print("="*80)
    
    results = []
    
    strategies = [
        {"name": "Baseline (No instrumentation)", "otel": False, "dpg": False},
        {"name": "OTel Only", "otel": True, "dpg": False},
        {"name": "DPG Only", "otel": False, "dpg": True},
        {"name": "Dual Export (OTel + DPG)", "otel": True, "dpg": True},
    ]
    
    for strategy in strategies:
        print(f"\n Testing strategy: {strategy['name']}")
        
        for run_num, seed in enumerate(config.seeds, 1):
            print(f"  [Run {run_num}/5] Seed: {seed}")
            np.random.seed(seed)
            
            # Baseline: No instrumentation
            if not strategy["otel"] and not strategy["dpg"]:
                start = time.time()
                for i in range(1000):
                    decision_data = SyntheticAgent.generate_decision()
                    time.sleep(0.001)  # Simulate processing
                elapsed = time.time() - start
                latency_ms = (elapsed / 1000) * 1000
            
            # OTel only
            elif strategy["otel"] and not strategy["dpg"]:
                dpg = DPGWithOTel(
                    ledger_path=f"{config.dpg_backend}_otel_only_{run_num}",
                    otel_enabled=True,
                    otel_endpoint=config.otel_endpoint
                )
                
                start = time.time()
                for i in range(1000):
                    decision_data = SyntheticAgent.generate_decision()
                    # Only OTel span (no DPG)
                    with dpg.tracer.start_as_current_span(f"decision_{i}") as span:
                        span.set_attribute("decision.id", i)
                        time.sleep(0.001)
                elapsed = time.time() - start
                latency_ms = (elapsed / 1000) * 1000
            
            # DPG only (theoretical - for comparison)
            elif not strategy["otel"] and strategy["dpg"]:
                dpg = DPGWithOTel(
                    ledger_path=f"{config.dpg_backend}_dpg_only_{run_num}",
                    otel_enabled=False
                )
                
                times = []
                for i in range(1000):
                    decision_data = SyntheticAgent.generate_decision()
                    result = dpg.log_decision(i, "DECISION",
                                            decision_data["inputs"],
                                            decision_data["outputs"])
                    times.append(result["export_time_ms"])
                latency_ms = np.mean(times)
            
            # Dual export
            else:
                dpg = DPGWithOTel(
                    ledger_path=f"{config.dpg_backend}_dual_{run_num}",
                    otel_enabled=True,
                    otel_endpoint=config.otel_endpoint
                )
                
                times = []
                for i in range(1000):
                    decision_data = SyntheticAgent.generate_decision()
                    result = dpg.log_decision(i, "DECISION",
                                            decision_data["inputs"],
                                            decision_data["outputs"])
                    times.append(result["export_time_ms"])
                latency_ms = np.mean(times)
            
            result = {
                "strategy": strategy["name"],
                "otel_enabled": strategy["otel"],
                "dpg_enabled": strategy["dpg"],
                "run_number": run_num,
                "seed": seed,
                "latency_per_decision_ms": latency_ms,
                "timestamp": time.time()
            }
            
            results.append(result)
            
            print(f"    Latency: {latency_ms:.3f}ms per decision")
    
    return results

# ============================================================================
# MAIN RUNNER
# ============================================================================

def main():
    """Run all OTel integration experiments"""
    
    config = OTelExperimentConfig()
    
    print("="*80)
    print("DPG OPENTELEMETRY INTEGRATION EXPERIMENTS")
    print("="*80)
    print(f"Configuration:")
    print(f"  - Runs: {config.num_runs}")
    print(f"  - Seeds: {config.seeds}")
    print(f"  - OTel Endpoint: {config.otel_endpoint}")
    print(f"  - Note: Jaeger should be running on port 4317")
    
    # Run experiments
    exp2a_results = experiment_2a_dual_export(config)
    exp2b_results = experiment_2b_backend_compatibility(config)
    exp2c_results = experiment_2c_selective_instrumentation(config)
    
    # Save results
    output_dir = Path("outputs/otel_experiments")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "exp2a_dual_export.json", 'w') as f:
        json.dump(exp2a_results, f, indent=2)
    
    with open(output_dir / "exp2b_backend_compatibility.json", 'w') as f:
        json.dump(exp2b_results, f, indent=2)
    
    with open(output_dir / "exp2c_selective_instrumentation.json", 'w') as f:
        json.dump(exp2c_results, f, indent=2)
    
    print("\n" + "="*80)
    print("✓ ALL OTEL EXPERIMENTS COMPLETE")
    print("="*80)
    print(f"Results saved to: {output_dir}")
    
    # Print summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print("\nExperiment 2A: Dual Export")
    success_rates = [r["export_success_rate_pct"] for r in exp2a_results]
    export_times = [r["avg_export_time_ms"] for r in exp2a_results]
    print(f"  Export Success: {np.mean(success_rates):.1f}% ± {np.std(success_rates):.1f}%")
    print(f"  Avg Export Time: {np.mean(export_times):.3f}ms ± {np.std(export_times):.3f}ms")
    
    print("\nExperiment 2B: Backend Compatibility")
    for backend in ["Jaeger", "Console"]:
        backend_results = [r for r in exp2b_results if r["backend_name"] == backend]
        if backend_results:
            compatibility = sum(r["compatible"] for r in backend_results) / len(backend_results) * 100
            print(f"  {backend}: {compatibility:.0f}% compatible")
    
    print("\nExperiment 2C: Instrumentation Overhead")
    for strategy in ["Baseline (No instrumentation)", "OTel Only", "DPG Only", "Dual Export (OTel + DPG)"]:
        strategy_results = [r for r in exp2c_results if r["strategy"] == strategy]
        if strategy_results:
            latencies = [r["latency_per_decision_ms"] for r in strategy_results]
            print(f"  {strategy}: {np.mean(latencies):.3f}ms ± {np.std(latencies):.3f}ms")

if __name__ == "__main__":
    main()
