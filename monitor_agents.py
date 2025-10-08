#!/usr/bin/env python3
"""Monitor agent progress and documentation sync."""

import subprocess
from pathlib import Path

def get_agent_status(agent: str):
    """Get status for specific agent."""
    workspace = f"../basis-strategy-v1-agent-{agent}"
    progress_file = f"{workspace}/agent-{agent}-progress.txt"
    
    print(f"\n🤖 Agent {agent.upper()} Status:")
    print("=" * 40)
    
    # Check progress file
    if Path(progress_file).exists():
        with open(progress_file, 'r') as f:
            print("📋 Progress:")
            for line in f:
                print(f"  {line.strip()}")
    else:
        print("❌ No progress file found")
    
    # Check recent commits
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=workspace,
            capture_output=True, text=True
        )
        print("\n📝 Recent Commits:")
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
    except Exception as e:
        print(f"❌ Error checking commits: {e}")
    
    # Check documentation sync
    try:
        result = subprocess.run(
            ["python", "validate_docs.py"],
            cwd=workspace,
            capture_output=True, text=True
        )
        print(f"\n📚 Documentation: {'✅ Synced' if result.returncode == 0 else '❌ Issues'}")
    except Exception as e:
        print(f"❌ Error checking docs: {e}")

if __name__ == "__main__":
    get_agent_status("a")
    get_agent_status("b")
