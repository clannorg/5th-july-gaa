#!/usr/bin/env python3
"""
Script 1: Analyze Each 15-Second Clip for Goal Kick Detection
Runs Gemini AI on each clip and outputs natural language descriptions
"""

import google.generativeai as genai
import os
import time
from pathlib import Path
import concurrent.futures
from threading import Lock
import argparse
from concurrent.futures import ThreadPoolExecutor

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

# Thread safety
results_lock = Lock()
processed_count = 0
error_count = 0

def analyze_clip_for_goal_kicks(clip_path, timestamp):
    """Analyze a single clip for goal kick indicators"""
    
    try:
        # Upload video to Gemini
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            return f"❌ Failed to process {clip_path}"
        
        # Create enhanced GAA kickout analysis prompt
        prompt = f"""
        You are an expert GAA analyst watching a 15-second clip starting at {timestamp}.

        GOAL: Detect OFFICIAL KICKOUTS and analyze the complete tactical sequence.

        GAA KICKOUT SEQUENCE ANALYSIS:
        1. TRIGGER: What caused the kickout (ball goes out of play)
        2. SETUP: Players clearing goal area and spreading across field  
        3. KICKOUT: Goalkeeper places ball on ground, kicks from stationary position
        4. CONTEST: Players running toward ball to win possession
        5. OUTCOME: Who wins possession, where, and what happens next

        OFFICIAL KICKOUT CRITERIA:
        ✓ Complete play stoppage after ball goes out of play
        ✓ Players deliberately CLEAR the goal area (crucial GAA behavior)
        ✓ All outfield players SPREAD across field in anticipation
        ✓ Goalkeeper places ball on GROUND (never from hands during active play)
        ✓ Clear PAUSE before kick (not immediate clearance)
        ✓ Players contest for possession after the kick

        DO NOT DETECT:
        - Goalkeeper clearances during active play
        - Kicks from hands without play stoppage
        - Quick kicks without proper player positioning
        - Any kick when players haven't cleared the area

        TEAM IDENTIFICATION (by jersey colors):
        - Goalkeeper and outfield players wear different colored jerseys
        - Note specific colors you observe for each team
        - Team A (Cork): Often yellow/amber/red combinations
        - Team B (Kerry): Often green/gold/white combinations

        **ENHANCED OUTPUT FORMAT:**
        KICKOUT: [YES/NO]
        CONFIDENCE: [1-10] (how certain are you this is an official kickout?)
        
        IF KICKOUT = YES, provide:
        TRIGGER_EVENT: [What caused it - shot wide/shot over/goalkeeper save/defensive clearance]
        EXACT_CONTACT_TIME: [X.X seconds into clip when goalkeeper's foot touches ball - be precise to 0.1s]
        KICKING_TEAM: [Team A/Team B based on goalkeeper jersey]
        PLAYER_POSITIONING: [Did players clear area and spread out? YES/NO]
        
        KICK_ANALYSIS:
        KICK_DISTANCE: [Short/Medium/Long - how far did it travel?]
        KICK_DIRECTION: [Left/Center/Right of field]
        KICK_ACCURACY: [On target to players/Off target/Contested]
        
        POSSESSION_OUTCOME:
        POSSESSION_WON_BY: [Team A/Team B/Contested/Unclear]
        POSSESSION_LOCATION: [Where caught - Left/Center/Right, Near/Middle/Far field]
        NEXT_ACTION: [What happened after catch - Shot/Pass/Retained/Lost possession/Unclear]
        
        JERSEY_DETAILS:
        TEAM_A_COLORS: [Describe jersey colors you see]
        TEAM_B_COLORS: [Describe jersey colors you see]
        GOALKEEPER_JERSEY: [Color of kicking goalkeeper]
        
        TACTICAL_CONTEXT: [Describe the full sequence - what led to kickout, how players positioned, who won possession, immediate outcome]

        IF KICKOUT = NO, provide:
        REASONING: [Why this is not an official kickout - active play/no positioning/etc.]

        REMEMBER: GAA kickouts are highly structured events where players must clear the area and position for the contest. Look for this specific tactical behavior.
        """
        
        # Generate analysis
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content([video_file, prompt])
        
        # Clean up
        genai.delete_file(video_file.name)
        
        return response.text
        
    except Exception as e:
        return f"❌ Error analyzing {clip_path}: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Analyze clips for goal kick detection')
    parser.add_argument('--clips-dir', type=str, required=True, help='Directory containing video clips')
    parser.add_argument('--output-dir', type=str, default='results/goal_kick_detection/clips', help='Output directory for descriptions')
    parser.add_argument('--threads', type=int, default=30, help='Number of threads for parallel processing')
    
    args = parser.parse_args()
    
    print("🥅 GOAL KICK DETECTION - PRECISE TIMING ANALYSIS")
    print("=" * 60)
    print("Goal: Detect exact moment goalkeeper kicks ball from goal area")
    print(f"Threads: {args.threads}")
    print("=" * 60)
    
    # Setup paths
    clips_dir = Path(args.clips_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not clips_dir.exists():
        print(f"❌ Clips directory not found: {clips_dir}")
        return
    
    # Find all video clips
    video_files = sorted(clips_dir.glob("*.mp4"))
    
    if not video_files:
        print(f"❌ No video files found in {clips_dir}")
        return
    
    print(f"📊 Found {len(video_files)} clips to analyze")
    
    # Process clips in parallel
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        
        for video_file in video_files:
            # Extract timestamp from filename
            timestamp = video_file.stem.replace('clip_', '').replace('m', ':').replace('s', '')
            
            print(f"🥅 Analyzing {video_file.name} ({timestamp})")
            
            future = executor.submit(analyze_clip_for_goal_kicks, str(video_file), timestamp)
            futures.append((future, video_file, timestamp))
        
        # Collect results
        for future, video_file, timestamp in futures:
            try:
                result = future.result()
                
                # Save result
                output_file = output_dir / f"{video_file.stem}.txt"
                with open(output_file, 'w') as f:
                    f.write(f"TIMESTAMP: {timestamp}\n")
                    f.write(f"QUERY: Goal Kick Detection\n\n")
                    f.write(f"DESCRIPTION:\n{result}\n")
                
            except Exception as e:
                print(f"❌ Error processing {video_file}: {e}")
    
    processing_time = time.time() - start_time
    
    print(f"\n✅ GOAL KICK ANALYSIS COMPLETE!")
    print(f"⏱️  Processing time: {processing_time:.1f} seconds")
    print(f"📁 Results saved to: {output_dir}")
    print(f"🚀 Processing rate: {len(video_files)/processing_time:.1f} clips/second")

if __name__ == "__main__":
    main() 