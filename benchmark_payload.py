import time
import matplotlib.pyplot as plt
import numpy as np
from src.middleware import track_provenance, audit_log

# Mock Agent that just accepts data
@track_provenance(action_type="LARGE_PAYLOAD_TEST")
def process_large_context(data_string):
    return "Processed"

def run_payload_experiment():
    print("--- 🏋️ Experiment 4: Payload Size vs. Latency ---")
    
    # Sizes: 1KB, 10KB, 100KB, 500KB, 1MB (simulating large RAG contexts)
    kb_sizes = [1, 10, 50, 100, 500, 1000] 
    latencies = []
    
    for kb in kb_sizes:
        # Generate random string of size KB
        payload = "x" * (kb * 1024) 
        
        start = time.time()
        process_large_context(payload)
        duration = (time.time() - start) * 1000 # to ms
        latencies.append(duration)
        print(f"Size: {kb}KB -> Latency: {duration:.4f} ms")

    # Plot
    plt.figure(figsize=(10, 5))
    plt.plot(kb_sizes, latencies, marker='s', color='#8e44ad', linewidth=2)
    plt.title('Impact of Context Window Size on Provenance Overhead', fontsize=12)
    plt.xlabel('Input Payload Size (KB)', fontsize=10)
    plt.ylabel('Overhead (ms)', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Annotation
    plt.text(500, latencies[-1], f"{latencies[-1]:.1f}ms @ 1MB", color='red')
    
    plt.savefig('figure5_payload.png', dpi=300)
    print("✅ Generated figure5_payload.png")

if __name__ == "__main__":
    run_payload_experiment()