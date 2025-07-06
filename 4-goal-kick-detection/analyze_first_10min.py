#!/usr/bin/env python3
"""
analyze_first_10min.py - GAA Kickout Detection for First 10 Minutes
Quick analysis of first 10 minutes (40 clips) for faster testing
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
    """Analyze a single clip for GAA kickouts with strict criteria"""
    try:
        # Upload video to Gemini
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            return f"❌ Failed to process {clip_path}"
        
        # Enhanced GAA kickout analysis prompt (same strict criteria)
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
        
        CRITICAL: If you cannot see the COMPLETE SEQUENCE (ball going out → players clearing → positioning → kick → contest), then it is NOT a kickout. Be extremely conservative - only detect obvious, structured kickout sequences.

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

        Focus on the structured tactical behavior that defines GAA kickouts.
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
    print("🥅 GAA KICKOUT DETECTION - FIRST 10 MINUTES")
    print("=" * 60)
    print("Quick analysis of first 10 minutes for faster testing")
    print("=" * 60)
    
    # Setup paths
    clips_base = Path("3.5-video-splitting/clips/first_half")
    output_dir = Path("results/kickout_first_10min")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not clips_base.exists():
        print(f"❌ Clips directory not found: {clips_base}")
        return
    
    # Find clips for first 10 minutes (00m00s to 09m59s)
    all_clips = sorted(clips_base.glob("*.mp4"))
    first_10min_clips = []
    
    for clip in all_clips:
        # Extract minutes from filename (clip_05m30s.mp4 -> 5)
        if "clip_" in clip.name:
            parts = clip.stem.replace("clip_", "").split("m")
            if len(parts) >= 1:
                try:
                    minutes = int(parts[0])
                    if minutes < 10:  # First 10 minutes
                        first_10min_clips.append(clip)
                except ValueError:
                    continue
    
    print(f"📊 Found {len(first_10min_clips)} clips in first 10 minutes")
    print(f"🧵 Using 10 threads for faster processing")
    
    # Process clips in parallel
    start_time = time.time()
    completed = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        
        for video_file in first_10min_clips:
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
                    f.write(f"QUERY: GAA Kickout Detection\n\n")
                    f.write(f"ANALYSIS:\n{result}\n")
                
                completed += 1
                progress = (completed / len(first_10min_clips)) * 100
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                
                print(f"📈 Progress: {completed}/{len(first_10min_clips)} ({progress:.1f}%) | "
                      f"Rate: {rate:.1f} clips/s")
                
            except Exception as e:
                print(f"❌ Error processing {video_file}: {e}")
    
    processing_time = time.time() - start_time
    
    print(f"\n✅ FIRST 10 MINUTES ANALYSIS COMPLETE!")
    print(f"⏱️  Time: {processing_time:.1f}s")
    print(f"🚀 Rate: {len(first_10min_clips)/processing_time:.1f} clips/second")
    print(f"📁 Results: {output_dir}")
    
    # Quick summary of kickouts found
    kickout_count = 0
    kickout_times = []
    
    for result_file in output_dir.glob("*.txt"):
        try:
            with open(result_file, 'r') as f:
                content = f.read()
                if "KICKOUT: YES" in content:
                    kickout_count += 1
                    # Extract timestamp
                    timestamp_line = [line for line in content.split('\n') if 'TIMESTAMP:' in line]
                    if timestamp_line:
                        timestamp = timestamp_line[0].split('TIMESTAMP:')[1].strip()
                        kickout_times.append(timestamp)
        except Exception as e:
            continue
    
    print(f"\n🥅 KICKOUT SUMMARY:")
    print(f"✅ Total kickouts detected: {kickout_count}")
    if kickout_times:
        print(f"📍 Kickout timestamps:")
        for time_stamp in sorted(kickout_times):
            print(f"   - {time_stamp}")
    else:
        print(f"📍 No kickouts detected in first 10 minutes")

if __name__ == "__main__":
    main() 