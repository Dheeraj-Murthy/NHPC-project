#!/Users/dheerajmurthy/miniforge3/envs/ns3/bin/python
"""
Convenience script to run all baseline models and generate comparison.
This is the main entry point for the baseline model workflow.
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from train_model import run_baseline_benchmarking

def main():
    """Run complete baseline workflow."""
    print("="*60)
    print("BASELINE ROUTING MODELS - COMPLETE WORKFLOW")
    print("="*60)
    
    # Run comprehensive benchmarking
    results, comparison = run_baseline_benchmarking(
        models=None,  # Run all models
        output_dir="ml/results",
        generate_training=True
    )
    
    print("\n" + "="*60)
    print("WORKFLOW COMPLETED SUCCESSFULLY")
    print("="*60)
    print("\nNext steps:")
    print("1. Review results in ml/results/ directory")
    print("2. Check comparison_report_*.json for detailed analysis")
    print("3. Use training_data.json for ML model development")
    print("4. Run individual models with:")
    print("   python ml/infer_routes.py --model <model_name>")
    print("5. Generate new comparisons with:")
    print("   python ml/infer_routes.py --model all --compare")

if __name__ == "__main__":
    main()