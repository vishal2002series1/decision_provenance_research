#!/usr/bin/env python3
"""
Analysis and Visualization for GDPR + OTel Experiments
Generates tables and figures for paper
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 300

# ============================================================================
# STATISTICAL ANALYSIS UTILITIES
# ============================================================================

def calculate_stats(values):
    """Calculate mean, std, CI, CV"""
    mean = np.mean(values)
    std = np.std(values, ddof=1)
    ci_95 = 1.96 * (std / np.sqrt(len(values)))
    cv = (std / mean * 100) if mean != 0 else 0
    
    return {
        "mean": mean,
        "std": std,
        "ci_95": [mean - ci_95, mean + ci_95],
        "cv": cv
    }

def perform_ttest(group1, group2):
    """Perform independent t-test"""
    t_stat, p_value = stats.ttest_ind(group1, group2)
    cohens_d = (np.mean(group1) - np.mean(group2)) / np.sqrt(
        (np.std(group1, ddof=1)**2 + np.std(group2, ddof=1)**2) / 2
    )
    return {
        "t_statistic": t_stat,
        "p_value": p_value,
        "cohens_d": cohens_d
    }

# ============================================================================
# TABLE GENERATION
# ============================================================================

def generate_table_gdpr_erasure(exp1a_file, exp1b_file, exp1c_file):
    """Generate Table 5: GDPR Erasure Performance"""
    
    with open(exp1a_file) as f:
        exp1a = json.load(f)
    with open(exp1b_file) as f:
        exp1b = json.load(f)
    with open(exp1c_file) as f:
        exp1c = json.load(f)
    
    print("\n" + "="*80)
    print("TABLE 5: GDPR CRYPTOGRAPHIC ERASURE PERFORMANCE")
    print("="*80)
    
    # Experiment 1A statistics
    erasure_rates = [r["erasure_success_rate_pct"] for r in exp1a]
    recovery_rates = [r["recovery_failure_rate_pct"] for r in exp1a]
    chain_valid = [r["chain_valid"] for r in exp1a]
    
    stats_1a = {
        "erasure_success": calculate_stats(erasure_rates),
        "recovery_failure": calculate_stats(recovery_rates),
        "chain_integrity": sum(chain_valid) / len(chain_valid) * 100
    }
    
    # Experiment 1B statistics (batch 1000)
    batch_1000 = [r for r in exp1b if r["batch_size"] == 1000]
    storage_overhead = [r["storage_overhead_ms"] for r in batch_1000]
    erasure_latency = [r["erasure_latency_ms"] for r in batch_1000]
    
    stats_1b = {
        "storage_overhead": calculate_stats(storage_overhead),
        "erasure_latency": calculate_stats(erasure_latency)
    }
    
    # Experiment 1C statistics
    compliance_scores = [r["compliance_score_pct"] for r in exp1c]
    stats_1c = calculate_stats(compliance_scores)
    
    # Generate LaTeX table (Note: LaTeX braces are doubled {{ }})
    latex = r"""
\begin{{table}}[t]
\centering
\caption{{GDPR Cryptographic Erasure Performance}}
\label{{tab:gdpr_erasure}}
\begin{{tabular}}{{lccc}}
\toprule
Metric & Mean $\pm$ Std & 95\% CI & CV (\%) \\
\midrule
Erasure Success Rate (\%) & {erasure_mean:.1f} $\pm$ {erasure_std:.1f} & [{erasure_ci_low:.1f}, {erasure_ci_high:.1f}] & {erasure_cv:.1f} \\
Recovery Failure Rate (\%) & {recovery_mean:.1f} $\pm$ {recovery_std:.1f} & [{recovery_ci_low:.1f}, {recovery_ci_high:.1f}] & {recovery_cv:.1f} \\
Chain Integrity (\%) & {chain:.0f} & --- & --- \\
Storage Overhead (ms) & {storage_mean:.3f} $\pm$ {storage_std:.3f} & [{storage_ci_low:.3f}, {storage_ci_high:.3f}] & {storage_cv:.1f} \\
Erasure Latency (ms) & {erasure_lat_mean:.3f} $\pm$ {erasure_lat_std:.3f} & [{erasure_lat_ci_low:.3f}, {erasure_lat_ci_high:.3f}] & {erasure_lat_cv:.1f} \\
GDPR Compliance Score (\%) & {compliance_mean:.0f} $\pm$ {compliance_std:.0f} & [{compliance_ci_low:.0f}, {compliance_ci_high:.0f}] & {compliance_cv:.1f} \\
\bottomrule
\end{{tabular}}
\end{{table}}
""".format(
        erasure_mean=stats_1a["erasure_success"]["mean"],
        erasure_std=stats_1a["erasure_success"]["std"],
        erasure_ci_low=stats_1a["erasure_success"]["ci_95"][0],
        erasure_ci_high=stats_1a["erasure_success"]["ci_95"][1],
        erasure_cv=stats_1a["erasure_success"]["cv"],
        recovery_mean=stats_1a["recovery_failure"]["mean"],
        recovery_std=stats_1a["recovery_failure"]["std"],
        recovery_ci_low=stats_1a["recovery_failure"]["ci_95"][0],
        recovery_ci_high=stats_1a["recovery_failure"]["ci_95"][1],
        recovery_cv=stats_1a["recovery_failure"]["cv"],
        chain=stats_1a["chain_integrity"],
        storage_mean=stats_1b["storage_overhead"]["mean"],
        storage_std=stats_1b["storage_overhead"]["std"],
        storage_ci_low=stats_1b["storage_overhead"]["ci_95"][0],
        storage_ci_high=stats_1b["storage_overhead"]["ci_95"][1],
        storage_cv=stats_1b["storage_overhead"]["cv"],
        erasure_lat_mean=stats_1b["erasure_latency"]["mean"],
        erasure_lat_std=stats_1b["erasure_latency"]["std"],
        erasure_lat_ci_low=stats_1b["erasure_latency"]["ci_95"][0],
        erasure_lat_ci_high=stats_1b["erasure_latency"]["ci_95"][1],
        erasure_lat_cv=stats_1b["erasure_latency"]["cv"],
        compliance_mean=stats_1c["mean"],
        compliance_std=stats_1c["std"],
        compliance_ci_low=stats_1c["ci_95"][0],
        compliance_ci_high=stats_1c["ci_95"][1],
        compliance_cv=stats_1c["cv"]
    )
    
    print(latex)
    return latex

def generate_table_otel_integration(exp2a_file, exp2c_file):
    """Generate Table 6: OpenTelemetry Integration Overhead"""
    
    with open(exp2a_file) as f:
        exp2a = json.load(f)
    with open(exp2c_file) as f:
        exp2c = json.load(f)
    
    print("\n" + "="*80)
    print("TABLE 6: OPENTELEMETRY INTEGRATION OVERHEAD")
    print("="*80)
    
    # Export success from 2A
    success_rates = [r["export_success_rate_pct"] for r in exp2a]
    export_times = [r["avg_export_time_ms"] for r in exp2a]
    
    stats_2a = {
        "success_rate": calculate_stats(success_rates),
        "export_time": calculate_stats(export_times)
    }
    
    # Instrumentation strategies from 2C
    strategies = {}
    for strategy_name in ["Baseline (No instrumentation)", "OTel Only", 
                         "DPG Only", "Dual Export (OTel + DPG)"]:
        strategy_results = [r for r in exp2c if r["strategy"] == strategy_name]
        latencies = [r["latency_per_decision_ms"] for r in strategy_results]
        strategies[strategy_name] = calculate_stats(latencies)
    
    # Calculate overhead relative to baseline
    baseline_mean = strategies["Baseline (No instrumentation)"]["mean"]
    
    # Corrected LaTeX string with doubled braces {{ }}
    latex = r"""
\begin{{table}}[t]
\centering
\caption{{OpenTelemetry Integration Overhead}}
\label{{tab:otel_overhead}}
\begin{{tabular}}{{lcccc}}
\toprule
Strategy & Latency (ms) & Overhead (ms) & Overhead (\%) & CV (\%) \\
\midrule
Baseline & {baseline_mean:.3f} $\pm$ {baseline_std:.3f} & --- & --- & {baseline_cv:.1f} \\
OTel Only & {otel_mean:.3f} $\pm$ {otel_std:.3f} & {otel_oh:.3f} & {otel_oh_pct:.1f}\% & {otel_cv:.1f} \\
DPG Only & {dpg_mean:.3f} $\pm$ {dpg_std:.3f} & {dpg_oh:.3f} & {dpg_oh_pct:.1f}\% & {dpg_cv:.1f} \\
\textbf{{Dual Export}} & \textbf{{{dual_mean:.3f} $\pm$ {dual_std:.3f}}} & \textbf{{{dual_oh:.3f}}} & \textbf{{{dual_oh_pct:.1f}\%}} & \textbf{{{dual_cv:.1f}}} \\
\midrule
Export Success (\%) & \multicolumn{{4}}{{c}}{{{success_mean:.1f} $\pm$ {success_std:.1f}}} \\
\bottomrule
\end{{tabular}}
\end{{table}}
""".format(
        baseline_mean=strategies["Baseline (No instrumentation)"]["mean"],
        baseline_std=strategies["Baseline (No instrumentation)"]["std"],
        baseline_cv=strategies["Baseline (No instrumentation)"]["cv"],
        otel_mean=strategies["OTel Only"]["mean"],
        otel_std=strategies["OTel Only"]["std"],
        otel_oh=strategies["OTel Only"]["mean"] - baseline_mean,
        otel_oh_pct=(strategies["OTel Only"]["mean"] - baseline_mean) / baseline_mean * 100,
        otel_cv=strategies["OTel Only"]["cv"],
        dpg_mean=strategies["DPG Only"]["mean"],
        dpg_std=strategies["DPG Only"]["std"],
        dpg_oh=strategies["DPG Only"]["mean"] - baseline_mean,
        dpg_oh_pct=(strategies["DPG Only"]["mean"] - baseline_mean) / baseline_mean * 100,
        dpg_cv=strategies["DPG Only"]["cv"],
        dual_mean=strategies["Dual Export (OTel + DPG)"]["mean"],
        dual_std=strategies["Dual Export (OTel + DPG)"]["std"],
        dual_oh=strategies["Dual Export (OTel + DPG)"]["mean"] - baseline_mean,
        dual_oh_pct=(strategies["Dual Export (OTel + DPG)"]["mean"] - baseline_mean) / baseline_mean * 100,
        dual_cv=strategies["Dual Export (OTel + DPG)"]["cv"],
        success_mean=stats_2a["success_rate"]["mean"],
        success_std=stats_2a["success_rate"]["std"]
    )
    
    print(latex)
    return latex

# ============================================================================
# FIGURE GENERATION
# ============================================================================

def generate_figure_gdpr_erasure(exp1a_file, output_path):
    """Generate Figure 7: GDPR Erasure Effectiveness"""
    
    with open(exp1a_file) as f:
        exp1a = json.load(f)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Subplot 1: Erasure success vs recovery attempts
    erasure_rates = [r["erasure_success_rate_pct"] for r in exp1a]
    recovery_rates = [r["recovery_failure_rate_pct"] for r in exp1a]
    
    x = np.arange(len(exp1a))
    width = 0.35
    
    ax1.bar(x - width/2, erasure_rates, width, label='Erasure Success', 
            color='#2ecc71', alpha=0.8)
    ax1.bar(x + width/2, recovery_rates, width, label='Recovery Failure',
            color='#e74c3c', alpha=0.8)
    
    ax1.set_xlabel('Run Number')
    ax1.set_ylabel('Success Rate (%)')
    ax1.set_title('(a) Erasure Effectiveness Across 5 Runs')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'Run {i+1}' for i in range(len(exp1a))])
    ax1.legend()
    ax1.set_ylim([95, 101])
    ax1.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Subplot 2: Chain integrity preservation
    chain_valid = [100 if r["chain_valid"] else 0 for r in exp1a]
    
    ax2.bar(x, chain_valid, color='#3498db', alpha=0.8)
    ax2.set_xlabel('Run Number')
    ax2.set_ylabel('Chain Integrity (%)')
    ax2.set_title('(b) Chain Integrity After Erasure')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'Run {i+1}' for i in range(len(exp1a))])
    ax2.set_ylim([95, 105])
    ax2.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Add annotation
    ax2.text(2, 102, '100% Integrity\nPreserved', ha='center', 
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: {output_path}")
    plt.close()

def generate_figure_otel_overhead(exp2c_file, output_path):
    """Generate Figure 8: OTel Integration Overhead Comparison"""
    
    with open(exp2c_file) as f:
        exp2c = json.load(f)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    strategies = ["Baseline (No instrumentation)", "OTel Only", 
                 "DPG Only", "Dual Export (OTel + DPG)"]
    
    data = {strategy: [] for strategy in strategies}
    for r in exp2c:
        if r["strategy"] in strategies:
            data[r["strategy"]].append(r["latency_per_decision_ms"])
    
    # Box plot
    positions = np.arange(len(strategies))
    bp = ax.boxplot([data[s] for s in strategies], positions=positions,
                     widths=0.6, patch_artist=True,
                     boxprops=dict(facecolor='lightblue', alpha=0.7),
                     medianprops=dict(color='red', linewidth=2))
    
    # Add means as points
    means = [np.mean(data[s]) for s in strategies]
    ax.scatter(positions, means, color='darkblue', s=100, zorder=3, 
              label='Mean', marker='D')
    
    # Add overhead annotations
    baseline_mean = np.mean(data["Baseline (No instrumentation)"])
    for i, strategy in enumerate(strategies[1:], 1):
        mean = np.mean(data[strategy])
        overhead = mean - baseline_mean
        overhead_pct = (overhead / baseline_mean) * 100
        ax.text(i, mean + 0.05, f'+{overhead:.3f}ms\n({overhead_pct:.1f}%)',
               ha='center', fontsize=9, 
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    ax.set_xticks(positions)
    ax.set_xticklabels(strategies, rotation=15, ha='right')
    ax.set_ylabel('Latency per Decision (ms)')
    ax.set_title('OpenTelemetry Integration Overhead Comparison\n(5 runs, 95% CI)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: {output_path}")
    plt.close()

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Generate all tables and figures"""
    
    print("="*80)
    print("GENERATING TABLES AND FIGURES FOR NEW EXPERIMENTS")
    print("="*80)
    
    # Directories
    gdpr_dir = Path("outputs/gdpr_experiments")
    otel_dir = Path("outputs/otel_experiments")
    output_dir = Path("outputs/new_experiments_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if experiment results exist
    exp1a = gdpr_dir / "exp1a_erasure_effectiveness.json"
    exp1b = gdpr_dir / "exp1b_erasure_performance.json"
    exp1c = gdpr_dir / "exp1c_gdpr_compliance.json"
    exp2a = otel_dir / "exp2a_dual_export.json"
    exp2c = otel_dir / "exp2c_selective_instrumentation.json"
    
    if not all([exp1a.exists(), exp1b.exists(), exp1c.exists()]):
        print("  [ERROR] GDPR experiment results not found. Run experiment_gdpr_erasure.py first")
        return
    
    if not all([exp2a.exists(), exp2c.exists()]):
        print("  [ERROR] OTel experiment results not found. Run experiment_otel_integration.py first")
        return
    
    # Generate tables
    print("\n" + "="*80)
    print("GENERATING TABLES")
    print("="*80)
    
    table5 = generate_table_gdpr_erasure(exp1a, exp1b, exp1c)
    with open(output_dir / "table5_gdpr_erasure.tex", 'w') as f:
        f.write(table5)
    
    table6 = generate_table_otel_integration(exp2a, exp2c)
    with open(output_dir / "table6_otel_overhead.tex", 'w') as f:
        f.write(table6)
    
    # Generate figures
    print("\n" + "="*80)
    print("GENERATING FIGURES")
    print("="*80)
    
    generate_figure_gdpr_erasure(exp1a, output_dir / "figure7_gdpr_erasure.pdf")
    generate_figure_otel_overhead(exp2c, output_dir / "figure8_otel_overhead.pdf")
    
    print("\n" + "="*80)
    print("✓ ALL ANALYSIS COMPLETE")
    print("="*80)
    print(f"Output directory: {output_dir}")
    print("  - table5_gdpr_erasure.tex")
    print("  - table6_otel_overhead.tex")
    print("  - figure7_gdpr_erasure.pdf")
    print("  - figure8_otel_overhead.pdf")

if __name__ == "__main__":
    main()
