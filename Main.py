import os, sys, json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(__file__))
from data.data_generator import load_real_ehr_dataset, preprocess, partition_hospitals
from hospitals.hospital_node import HospitalNode
from aggregator.aggregator import FederatedAggregator
from causal.causal_engine import CausalDiscovery, CausalEffectEstimator, CounterfactualEngine
from .visualization.visualizer import plot_federated_rounds, plot_causal_dag, plot_counterfactual, plot_model_comparison, plot_privacy_audit, plot_ate_summary

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_federated_learning(hospitals, n_rounds=5, dp_noise=0.0):
    aggregator = FederatedAggregator(dp_noise_scale=dp_noise)
    nodes = [HospitalNode(i, h, model_type="logistic") for i, h in enumerate(hospitals)]
    global_weights = None
    global_intercept = None
    round_metrics = {i: [] for i in range(len(nodes))}
    print(f"\n{'='*60}")
    print(f"  FEDERATED LEARNING  ({n_rounds} rounds, {len(nodes)} hospitals)")
    print(f"{'='*60}")
    for r in range(1, n_rounds + 1):
        updates = []
        for node in nodes:
            w, b, n = node.train(global_weights, global_intercept)
            updates.append((w, b, n))
            round_metrics[node.hospital_id].append(node.metrics.copy())
        global_weights, global_intercept = aggregator.aggregate(updates, round_num=r)
        for node in nodes:
            node.apply_global_model(global_weights, global_intercept)
        avg_auc = np.mean([node.metrics["auc"] for node in nodes])
        print(f"  Round {r:2d} | Avg AUC: {avg_auc:.4f}")
    audit = aggregator.privacy_audit(updates)
    print(f"\n  Privacy Audit -> {audit}")
    return aggregator, round_metrics, global_weights, global_intercept, nodes, audit

def build_centralised_baseline(df_full):
    X, y, feature_names, scaler = preprocess(df_full)
    X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = LogisticRegression(max_iter=500, solver="lbfgs", C=1.0, random_state=42)
    clf.fit(X_tr, y_tr)
    y_pred = clf.predict(X_val)
    y_prob = clf.predict_proba(X_val)[:, 1]
    return {
        "accuracy":  round(accuracy_score(y_val, y_pred), 4),
        "auc":       round(roc_auc_score(y_val, y_prob), 4),
        "precision": round(precision_score(y_val, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_val, y_pred, zero_division=0), 4),
    }, clf, scaler, feature_names

def main():
    print("\n" + "="*60)
    print("  PRIVACY-PRESERVING HEALTHCARE ANALYTICS FRAMEWORK")
    print("="*60)
    print("\n[1] Loading real EHR dataset ...")
    df_full = load_real_ehr_dataset("real_patient_data.csv")
    hospitals_data = partition_hospitals(df_full, n_hospitals=4)
    print(f"    Total patients : {len(df_full)}")
    print(f"    Readmission    : {df_full['readmission'].mean():.2%}")
    for i, h in enumerate(hospitals_data):
        print(f"    Hospital {i+1}     : {len(h)} patients")
    aggregator, round_metrics, global_w, global_b, nodes, audit = run_federated_learning(hospitals_data, n_rounds=6, dp_noise=0.0)
    fed_metrics = {
        "accuracy":  round(np.mean([n.metrics["accuracy"] for n in nodes]), 4),
        "auc":       round(np.mean([n.metrics["auc"]      for n in nodes]), 4),
        "precision": round(np.mean([n.metrics["precision"] for n in nodes]), 4),
        "recall":    round(np.mean([n.metrics["recall"]   for n in nodes]), 4),
    }
    print(f"\n  Final Federated Metrics: {fed_metrics}")
    print("\n[3] Building centralised baseline ...")
    central_metrics, central_clf, central_scaler, feat_names = build_centralised_baseline(df_full)
    print(f"    Centralised AUC: {central_metrics['auc']:.4f}")
    single_node = HospitalNode(0, hospitals_data[0])
    single_node.train()
    local_metrics = single_node.metrics
    comparison = {
        "Federated (ours)": fed_metrics,
        "Centralised":      central_metrics,
        "Local only":       local_metrics,
    }
    print("\n[4] Running causal discovery ...")
    causal_disc = CausalDiscovery(alpha=0.05)
    dag = causal_disc.fit(df_full)
    summary = causal_disc.summary()
    print(f"    DAG: {len(dag.nodes)} nodes, {len(dag.edges)} edges")
    print(f"    Direct causes of readmission: {summary['readmission_parents']}")
    print("\n[5] Estimating Average Treatment Effect ...")
    effect_est = CausalEffectEstimator()
    ate_result = effect_est.estimate_ate(df_full)
    print(f"    ATE (IPW): {ate_result['ate_ipw']:+.4f}")
    print(f"    -> {ate_result['interpretation']}")
    print("\n[6] Running counterfactual analysis ...")
    cf_engine = CounterfactualEngine(central_clf, central_scaler, feat_names)
    cf_df = cf_engine.batch_counterfactual(df_full, intervention={"treatment_type": 1}, n_patients=300)
    mean_delta = cf_df["delta"].mean()
    print(f"    Mean Delta prob (surgery intervention): {mean_delta:+.4f}")
    print("\n[7] Generating visualisations ...")
    plot_federated_rounds(round_metrics)
    plot_causal_dag(dag)
    plot_counterfactual(cf_df)
    plot_model_comparison(comparison)
    plot_privacy_audit(audit)
    plot_ate_summary(ate_result)
    report = {
        "dataset": {
            "total_patients": len(df_full),
            "n_hospitals": 4,
            "readmission_rate": round(float(df_full["readmission"].mean()), 4),
        },
        "federated_learning": {
            "rounds": 6,
            "final_metrics": fed_metrics,
        },
        "centralised_baseline": central_metrics,
        "local_only": local_metrics,
        "causal_discovery": {
            "n_nodes": len(dag.nodes),
            "n_edges": len(dag.edges),
            "readmission_parents": summary["readmission_parents"],
        },
        "ate": ate_result,
        "counterfactual_summary": {
            "n_patients_analysed": len(cf_df),
            "mean_delta": round(float(mean_delta), 4),
            "patients_benefiting": int((cf_df["delta"] < 0).sum()),
        },
        "privacy_audit": audit,
    }
    report_path = os.path.join(RESULTS_DIR, "summary_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Summary report saved -> {report_path}")
    print("\n" + "="*60)
    print("  RESULTS SUMMARY")
    print("="*60)
    print(f"  Federated AUC   : {fed_metrics['auc']:.4f}")
    print(f"  Centralised AUC : {central_metrics['auc']:.4f}")
    print(f"  Local-only AUC  : {local_metrics['auc']:.4f}")
    print(f"  ATE (surgery)   : {ate_result['ate_ipw']:+.4f}  -> {ate_result['interpretation']}")
    print(f"  Privacy Audit   : {audit['status']}")
    print(f"\n  All outputs in: {RESULTS_DIR}/")
    print("="*60 + "\n")
    return report

if __name__ == "__main__":
    main()