#!/usr/bin/env python3
"""
🎯 GAA ANALYSIS PIPELINE
Master script to run the complete 5th July GAA analysis pipeline
"""

import os
import sys
import subprocess
from pathlib import Path
import time

def run_step(step_name, script_path, description):
    """Run a pipeline step"""
    print(f"\n{'='*60}")
    print(f"🚀 STEP: {step_name}")
    print(f"📋 {description}")
    print(f"{'='*60}")
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # Run the script
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=script_path.parent,
                              check=True)
        
        print(f"✅ {step_name} completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {step_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running {step_name}: {e}")
        return False

def main():
    """Main pipeline function"""
    print("🎯 GAA ANALYSIS PIPELINE")
    print("=" * 60)
    print("🏐 5th July GAA Match Analysis")
    print("📋 Complete pipeline: Download → Split → Analyze → Detect")
    print("=" * 60)
    
    # Define pipeline steps
    steps = [
        {
            'name': '1. VEO DOWNLOAD',
            'script': Path('1-veo-download/veo_downloader.py'),
            'description': 'Download GAA match video from Veo URL'
        },
        {
            'name': '2. VIDEO SPLITTING',
            'script': Path('2-splitting/clip_splitter.py'),
            'description': 'Split video into 15-second clips for analysis'
        },
        {
            'name': '3A. CLIP ANALYSIS',
            'script': Path('3-half-start-end/analyze_all_clips.py'),
            'description': 'Analyze all clips with Gemini AI'
        },
        {
            'name': '3B. THROW-IN DETECTION',
            'script': Path('3-half-start-end/detect_throw_ins.py'),
            'description': 'Detect throw-ins from clip descriptions'
        }
    ]
    
    # Ask user which steps to run
    print("\n📋 Pipeline Steps:")
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step['name']}")
    
    choice = input("\nRun all steps? (y/n) or enter step numbers (e.g., 1,3,4): ").strip().lower()
    
    if choice == 'y' or choice == 'yes':
        steps_to_run = list(range(len(steps)))
    elif choice == 'n' or choice == 'no':
        print("Pipeline cancelled.")
        return
    else:
        try:
            steps_to_run = [int(x.strip()) - 1 for x in choice.split(',')]
            steps_to_run = [i for i in steps_to_run if 0 <= i < len(steps)]
        except ValueError:
            print("❌ Invalid input. Running all steps.")
            steps_to_run = list(range(len(steps)))
    
    if not steps_to_run:
        print("❌ No valid steps selected.")
        return
    
    # Run selected steps
    start_time = time.time()
    completed_steps = 0
    
    for step_index in steps_to_run:
        step = steps[step_index]
        
        success = run_step(step['name'], step['script'], step['description'])
        
        if success:
            completed_steps += 1
        else:
            print(f"\n❌ Pipeline failed at step: {step['name']}")
            break
    
    # Summary
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"🎯 PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Completed steps: {completed_steps}/{len(steps_to_run)}")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    
    if completed_steps == len(steps_to_run):
        print(f"🎉 SUCCESS! All selected steps completed!")
        print(f"📁 Check the output directories for results:")
        print(f"   📥 Downloads: 1-veo-download/downloads/")
        print(f"   ✂️ Clips: 2-splitting/clips/")
        print(f"   🔍 Analysis: 3-half-start-end/analysis/")
        print(f"   🏐 Throw-ins: 3-half-start-end/throw_ins/")
    else:
        print(f"❌ Pipeline incomplete. Check errors above.")

if __name__ == "__main__":
    main() 