#!/usr/bin/env python3
"""
1_analyze_clips.py - GAA Turnover Detection
Video clips → Text descriptions of turnovers/possession changes
"""

import os
import time
import google.generativeai as genai
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

def analyze_clip_for_turnovers(clip_path, timestamp, half_name):
    """Analyze a single clip for GAA turnovers/possession changes"""
    try:
        # Upload video to Gemini
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            return f"❌ Failed to process {clip_path}"
        
        # GAA turnover analysis prompt
        prompt = f"""
        You are an expert GAA analyst watching a 15-second clip from the {half_name} at {timestamp}.

        GOAL: Detect GAA TURNOVERS (possession changes) with precise timing.

        GAA TURNOVER DEFINITION:
        A turnover occurs when possession of the ball changes from one team to the other during active play.

        COMMON GAA TURNOVER SCENARIOS:
        1. INTERCEPTION: Player intercepts a pass intended for opponent
        2. TACKLE: Player dispossesses opponent carrying the ball
        3. FUMBLE/DROP: Player drops ball, opponent picks it up
        4. BLOCK DOWN: Player blocks a kick/shot, opponent recovers
        5. CONTESTED CATCH: High ball contested, opposite team wins it
        6. LOOSE BALL: Ball becomes loose, opposite team gains control
        7. STEAL: Player steals ball from opponent's possession

        TURNOVER CRITERIA:
        ✓ Clear change of possession from Team A to Team B (or vice versa)
        ✓ Ball control transfers from one team to another
        ✓ Moment of possession change is visible in the clip
        ✓ This is active match play (not restarts like kickouts)
        ✓ New team has clear control of the ball

        DO NOT DETECT:
        - Kickouts, throw-ins, or other official restarts
        - Shots or passes that go out of play
        - Fouls where play stops
        - When possession doesn't clearly change
        - Warm-up or training activities

        **OUTPUT FORMAT:**
        TURNOVER: [YES/NO]
        CONFIDENCE: [1-10]
        HALF: {half_name}
        CLIP_TIME: {timestamp}
        
        IF TURNOVER = YES:
        TURNOVER_TYPE: [Interception/Tackle/Fumble/Block/Contest/Loose Ball/Steal]
        EXACT_MOMENT: [X.X seconds when possession changes]
        TEAM_LOST_POSSESSION: [Team A/Team B based on jersey colors]
        TEAM_GAINED_POSSESSION: [Team A/Team B based on jersey colors]
        
        TURNOVER_DETAILS:
        LOCATION: [Field position where turnover occurred]
        METHOD: [How the turnover happened - detailed description]
        PLAYER_INVOLVED: [Key players involved if visible]
        
        BEFORE_TURNOVER:
        TEAM_IN_POSSESSION: [Team A/Team B]
        ACTIVITY: [What they were doing - passing/running/shooting]
        
        AFTER_TURNOVER:
        TEAM_IN_POSSESSION: [Team A/Team B]
        IMMEDIATE_ACTION: [What they did after gaining possession]
        
        JERSEY_COLORS:
        TEAM_A_COLORS: [Describe colors]
        TEAM_B_COLORS: [Describe colors]
        
        TACTICAL_CONTEXT: [Brief description of the turnover sequence]

        IF TURNOVER = NO:
        REASONING: [Why no turnover occurred]

        REMEMBER: 
        - Turnovers are common in GAA - expect 10-20 per 10 minutes
        - Focus on clear possession changes during active play
        - Be specific about the exact moment possession changes
        - Distinguish between teams consistently by jersey colors
        """
        
        # Generate analysis
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([video_file, prompt])
        
        # Clean up
        genai.delete_file(video_file.name)
        
        return response.text
        
    except Exception as e:
        return f"❌ Error analyzing {clip_path}: {str(e)}"

def main():
    print("🔄 GAA TURNOVER ANALYSIS - STEP 1: VIDEO → TEXT")
    print("=" * 60)
    
    # Configuration
    TIME_LIMIT_MINUTES = 10  # Analyze first 10 minutes
    MAX_WORKERS = 8
    
    # Setup paths
    clips_base = Path("../3.5-video-splitting/clips/first_half")
    output_dir = Path("results/turnover_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not clips_base.exists():
        print(f"❌ Clips directory not found: {clips_base}")
        return
    
    # Find clips for specified time period
    all_clips = sorted(clips_base.glob("*.mp4"))
    target_clips = []
    
    for clip in all_clips:
        if "clip_" in clip.name:
            parts = clip.stem.replace("clip_", "").split("m")
            if len(parts) >= 1:
                try:
                    minutes = int(parts[0])
                    if minutes < TIME_LIMIT_MINUTES:
                        target_clips.append(clip)
                except ValueError:
                    continue
    
    print(f"📊 Found {len(target_clips)} clips in first {TIME_LIMIT_MINUTES} minutes")
    print(f"🧵 Using {MAX_WORKERS} threads for processing")
    
    # Process clips in parallel
    start_time = time.time()
    completed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        
        for video_file in target_clips:
            # Skip if already processed
            output_file = output_dir / f"{video_file.stem}.txt"
            if output_file.exists():
                print(f"⏭️  Skipping {video_file.name} (already processed)")
                continue
            
            # Extract timestamp from filename
            timestamp = video_file.stem.replace('clip_', '').replace('m', ':').replace('s', '')
            
            future = executor.submit(analyze_clip_for_turnovers, str(video_file), timestamp, "first_half")
            futures.append((future, video_file, timestamp))
        
        # Collect results with progress
        for future, video_file, timestamp in futures:
            try:
                result = future.result()
                
                # Save result
                output_file = output_dir / f"{video_file.stem}.txt"
                with open(output_file, 'w') as f:
                    f.write(f"HALF: first_half\n")
                    f.write(f"TIMESTAMP: {timestamp}\n")
                    f.write(f"CLIP_FILE: {video_file.name}\n")
                    f.write(f"ANALYSIS:\n{result}\n")
                
                completed += 1
                progress = (completed / len(futures)) * 100 if futures else 0
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                
                print(f"📈 Progress: {completed}/{len(futures)} ({progress:.1f}%) | "
                      f"Rate: {rate:.1f} clips/s")
                
            except Exception as e:
                print(f"❌ Error processing {video_file}: {e}")
    
    processing_time = time.time() - start_time
    
    print(f"\n✅ TURNOVER ANALYSIS COMPLETE!")
    print(f"⏱️  Time: {processing_time:.1f}s")
    print(f"📁 Results saved to: {output_dir}")
    print(f"\n🔄 Next step: Run '2_synthesize_events.py' to create timeline")

if __name__ == "__main__":
    main() 