#!/usr/bin/env python3
"""
Decision script for SPS-CE workflow: Determine if second attempt is needed.
Adapted from SIP workflow decision script patterns for SPS-CE workflow integration.

This script presents a decision point to the user after the second FA output analysis
to determine whether to proceed with final analysis or perform additional rework.

Author: Laboratory Automation Team
Version: 1.0 (Initial implementation for workflow manager integration)
"""

import datetime
import json
import sys
from pathlib import Path


def create_success_marker():
    """Create success marker file for workflow manager integration."""
    script_name = Path(__file__).stem
    status_dir = Path(".workflow_status")
    status_dir.mkdir(exist_ok=True)
    success_file = status_dir / f"{script_name}.success"
    
    try:
        with open(success_file, "w") as f:
            f.write(f"SUCCESS: {script_name} completed at {datetime.datetime.now()}\n")
        print(f"✅ Success marker created: {success_file}")
    except Exception as e:
        print(f"❌ ERROR: Could not create success marker: {e}")
        print("Script failed - workflow manager integration requires success marker")
        sys.exit()


def update_workflow_state(choice):
    """Update workflow_state.json based on user choice."""
    state_file = Path("workflow_state.json")
    
    # Load current state
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
    else:
        state = {}
    
    if choice == "yes":
        # Enable rework steps
        state["rework_first_attempt"] = "pending"
        state["second_fa_analysis"] = "pending"
        # conclude_fa_analysis remains pending (will be set after step 5)
        
    else:  # choice == "no"
        # Skip rework steps, go directly to conclusion
        state["rework_first_attempt"] = "skipped"
        state["second_fa_analysis"] = "skipped"
        state["conclude_fa_analysis"] = "pending"
    
    # Save updated state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def main():
    """Main decision logic for second attempt determination."""
    print("\n" + "="*60)
    print("SPS-CE WORKFLOW DECISION POINT")
    print("="*60)
    print("\nBased on the second FA output analysis results,")
    print("do you need to perform a second rework attempt?")
    print("\nOptions:")
    print("  YES - Perform second rework attempt")
    print("  NO  - Proceed to final analysis and ESP file generation")
    
    choice = None
    while True:
        user_input = input("\nEnter your choice (YES/NO): ").strip().upper()
        
        if user_input in ['YES', 'Y']:
            print("\n✅ Decision recorded: Second rework attempt will be performed")
            print("   → The workflow will loop back for additional rework")
            choice = "yes"
            break
        elif user_input in ['NO', 'N']:
            print("\n✅ Decision recorded: Proceeding to final analysis")
            print("   → The workflow will continue to ESP file generation")
            choice = "no"
            break
        else:
            print("❌ Invalid choice. Please enter YES or NO.")
    
    # Update workflow state based on choice
    update_workflow_state(choice)
    
    # Create success marker for workflow manager
    create_success_marker()
    
    print(f"\n🎯 Decision complete. Workflow will continue based on your choice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())