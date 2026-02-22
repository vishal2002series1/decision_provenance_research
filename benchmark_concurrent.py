import time
import threading
import random
import matplotlib.pyplot as plt
from src.middleware import track_provenance, audit_log

# Simulate a shared log (simplified for demo)
# In reality, this would be a DB with a lock or CAS operation
SHARED_LOG_LOCK = threading.Lock()

def concurrent_agent_task(agent_id, steps):
    """Simulates an agent working in parallel."""
    for i in range(steps):
        # Simulate work
        time.sleep(random.uniform(0.001, 0.005)) 
        
        # Write to shared log with locking (simulating DB concurrency)
        with SHARED_LOG_LOCK:
            audit_log.add_step(f"AGENT_{agent_id}_ACTION", {"step": i}, {"result": "ok"})

def run_concurrency_test():
    print("--- ⚔️ Experiment: Multi-Agent Concurrency ---")
    
    agent_counts = [1, 5, 10, 20, 50]
    throughputs = []
    
    for n_agents in agent_counts:
        audit_log.chain = [] # Reset
        threads = []
        steps_per_agent = 100
        
        start_time = time.time()
        
        # Launch agents
        for i in range(n_agents):
            t = threading.Thread(target=concurrent_agent_task, args=(i, steps_per_agent))
            threads.append(t)
            t.start()
            
        # Wait for all to finish
        for t in threads:
            t.join()
            
        duration = time.time() - start_time
        total_ops = n_agents * steps_per_agent
        ops_per_sec = total_ops / duration
        throughputs.append(ops_per_sec)
        
        print(f"Agents: {n_agents} | Total Ops: {total_ops} | Time: {duration:.2f}s | TPS: {ops_per_sec:.0f}")

    # Plot
    plt.figure(figsize=(10, 5))
    plt.plot(agent_counts, throughputs, marker='o', color='#d35400', linewidth=2)
    plt.title('System Throughput vs. Concurrent Agents', fontsize=12)
    plt.xlabel('Number of Concurrent Agents', fontsize=10)
    plt.ylabel('Transactions Per Second (TPS)', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.savefig('figure6_concurrency.png', dpi=300)
    print("✅ Generated figure6_concurrency.png")

if __name__ == "__main__":
    run_concurrency_test()