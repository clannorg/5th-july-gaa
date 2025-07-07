#!/usr/bin/env python3
"""
1_analyze_clips.py - Clean GAA Kickout Analysis
Video clips → Text descriptions of kickouts
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

def analyze_clip_for_kickouts(clip_path, timestamp, half_name):
    """Analyze a single clip for GAA kickouts"""
    try:
        # Upload video to Gemini
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            return f"❌ Failed to process {clip_path}"
        
        # GAA kickout analysis prompt
        prompt = f"""
        You are an expert GAA analyst watching a 15-second clip from the {half_name} at {timestamp}.

        GOAL: Detect OFFICIAL GAA KICKOUTS with precise timing and tactical analysis.

        GAA KICKOUT SEQUENCE:
        1. TRIGGER: Ball goes out of play (wide/over/save)
        2. SETUP: Players clear goal area and spread across field  
        3. KICKOUT: Goalkeeper places ball on ground, kicks from stationary position
        4. CONTEST: Players run toward ball to contest possession
        5. OUTCOME: Who wins possession and what happens next

        STRICT OFFICIAL KICKOUT CRITERIA (ALL MUST BE PRESENT):
        ✓ Complete play stoppage after ball goes out of play
        ✓ Players deliberately CLEAR the goal area (crucial GAA behavior)
        ✓ ALL outfield players SPREAD across field in anticipation
        ✓ Goalkeeper places ball on GROUND (never from hands during active play)
        ✓ Clear PAUSE before kick (not immediate clearance)
        ✓ Players contest for possession after the kick
        ✓ STRUCTURED RESTART SEQUENCE visible (not just any goalkeeper kick)

        ABSOLUTELY DO NOT DETECT:
        - Goalkeeper clearances during active play
        - Kicks from hands without play stoppage
        - Quick kicks without proper player positioning
        - Any kick when players haven't cleared the area
        - Free kicks or any other restarts
        - Goalkeeper saves or clearances during ongoing play
        
        **OUTPUT FORMAT:**
        KICKOUT: [YES/NO]
        CONFIDENCE: [1-10]
        HALF: {half_name}
        CLIP_TIME: {timestamp}
        
        IF KICKOUT = YES:
        TRIGGER_EVENT: [What caused it]
        EXACT_CONTACT_TIME: [X.X seconds when foot touches ball]
        KICKING_TEAM: [Team A/Team B based on goalkeeper jersey]
        PLAYER_POSITIONING: [Did players clear and spread? YES/NO]
        
        KICK_ANALYSIS:
        KICK_DISTANCE: [Short/Medium/Long]
        KICK_DIRECTION: [Left/Center/Right]
        KICK_ACCURACY: [On target/Off target/Contested]
        
        POSSESSION_OUTCOME:
        POSSESSION_WON_BY: [Team A/Team B/Contested/Unclear]
        POSSESSION_LOCATION: [Field position where caught]
        NEXT_ACTION: [What happened after possession]
        
        JERSEY_COLORS:
        TEAM_A_COLORS: [Describe colors]
        TEAM_B_COLORS: [Describe colors]
        GOALKEEPER_JERSEY: [Color of kicking goalkeeper]
        
        TACTICAL_CONTEXT: [Full sequence description]

        IF KICKOUT = NO:
        REASONING: [Why not an official kickout]
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
    print("🥅 GAA KICKOUT ANALYSIS - STEP 1: VIDEO → TEXT")
    print("=" * 60)
    
    # Configuration
    TIME_LIMIT_MINUTES = 10  # Analyze first 10 minutes
    MAX_WORKERS = 8
    
    # Setup paths
    clips_base = Path("../3.5-video-splitting/clips/first_half")
    output_dir = Path("results/kickout_analysis")
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
            
            future = executor.submit(analyze_clip_for_kickouts, str(video_file), timestamp, "first_half")
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
    
    print(f"\n✅ CLIP ANALYSIS COMPLETE!")
    print(f"⏱️  Time: {processing_time:.1f}s")
    print(f"📁 Results saved to: {output_dir}")
    print(f"\n🔄 Next step: Run '2_synthesize_events.py' to create timeline")

if __name__ == "__main__":
    main() 