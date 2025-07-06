#!/usr/bin/env python3
"""
🚀 QUICK RUNNER FOR HALVES TO CLIPS SPLITTING
Simple script to run the optimized halves-to-clips splitter
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from split_halves_to_clips import OptimizedHalvesToClipsSplitter

def main():
    print("🚀 RUNNING OPTIMIZED HALVES TO CLIPS SPLITTER")
    print("=" * 60)
    
    # Create and run splitter
    splitter = OptimizedHalvesToClipsSplitter()
    success = splitter.split_both_halves()
    
    if success:
        print("\n🎉 ALL DONE! Ready for analysis")
        print("📁 Check the 'clips/' directory for your split videos")
    else:
        print("\n❌ Splitting failed - check the logs above")
        sys.exit(1)

if __name__ == "__main__":
    main() 