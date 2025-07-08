#!/usr/bin/env python3
"""
Test Commentary System
Find available clips and test the simple commentary approach
"""

import os
from pathlib import Path

def find_available_clips():
    """Find any available video clips in the system"""
    
    print("🔍 SEARCHING FOR AVAILABLE VIDEO CLIPS")
    print("=" * 50)
    
    # Check multiple possible locations
    search_paths = [
        "3.5-video-splitting/clips/first_half",
        "3.5-video-splitting/clips/second_half", 
        "clips",
        "2-splitting/clips",
        "../clips"
    ]
    
    all_clips = []
    
    for search_path in search_paths:
        path = Path(search_path)
        if path.exists():
            clips = list(path.glob("*.mp4"))
            if clips:
                print(f"📁 Found {len(clips)} clips in {search_path}")
                all_clips.extend(clips)
            else:
                print(f"📁 Directory exists but no clips: {search_path}")
        else:
            print(f"📁 Directory not found: {search_path}")
    
    return all_clips

def check_system_readiness():
    """Check if the system is ready to run commentary analysis"""
    
    print("\n🔧 SYSTEM READINESS CHECK")
    print("=" * 50)
    
    # Check API key
    if os.getenv('GEMINI_API_KEY'):
        print("✅ Gemini API key found")
    else:
        print("❌ Gemini API key not found - set GEMINI_API_KEY environment variable")
    
    # Check video files
    clips = find_available_clips()
    if clips:
        print(f"✅ Found {len(clips)} video clips ready for analysis")
        print("📋 Sample clips:")
        for i, clip in enumerate(clips[:5]):
            print(f"   {i+1}. {clip.name}")
        if len(clips) > 5:
            print(f"   ... and {len(clips) - 5} more")
    else:
        print("❌ No video clips found")
        print("💡 You need to generate video clips first:")
        print("   1. Make sure you have the full match video")
        print("   2. Run the video splitting script to create 15-second clips")
        print("   3. Then run the commentary analysis")
    
    return len(clips) > 0

def create_demo_workflow():
    """Show the workflow for the new commentary system"""
    
    print("\n🎙️  NEW COMMENTARY WORKFLOW")
    print("=" * 50)
    
    print("STEP 1: Generate Simple Commentary")
    print("   python simple_commentary.py")
    print("   → Creates natural descriptions of each 15-second clip")
    print("   → No complex detection logic, just 'what's happening'")
    print("   → Saves to results/simple_commentary/")
    print()
    
    print("STEP 2: Create Match Narrative")
    print("   python narrative_synthesis.py")
    print("   → Weaves individual clips into flowing commentary")
    print("   → Creates continuous match story")
    print("   → Saves to results/match_narrative/")
    print()
    
    print("BENEFITS:")
    print("✅ Much simpler than complex kickout detection")
    print("✅ Natural commentary style")
    print("✅ Forced continuity through narrative synthesis")
    print("✅ No rigid JSON schemas or event categories")
    print("✅ Easy to read and understand output")

def main():
    print("🎙️  GAA COMMENTARY SYSTEM TEST")
    print("=" * 50)
    
    # Check system readiness
    ready = check_system_readiness()
    
    # Show workflow
    create_demo_workflow()
    
    if ready:
        print(f"\n✅ SYSTEM READY!")
        print("🚀 You can now run the commentary analysis:")
        print("   cd 4-goal-kick-detection/")
        print("   python simple_commentary.py")
    else:
        print(f"\n❌ SYSTEM NOT READY")
        print("🔧 Fix the issues above first, then run the commentary analysis")
    
    print(f"\n💡 This approach should work much better than the rigid kickout detection!")

if __name__ == "__main__":
    main() 