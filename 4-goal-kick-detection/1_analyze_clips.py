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
        
        # GAA kickout analysis prompt - ULTRA STRICT
        prompt = f"""
        You are an expert GAA analyst watching a 15-second clip from the {half_name} at {timestamp}.

        CRITICAL: GAA KICKOUTS ARE EXTREMELY RARE EVENTS. In a typical GAA match, there are only 15-25 kickouts in the ENTIRE 70+ minute game. In the first 10 minutes, expect 0-3 maximum.

        GOAL: Detect ONLY GENUINE OFFICIAL GAA KICKOUTS. When in doubt, always say NO.

        MANDATORY KICKOUT SEQUENCE (ALL MUST BE CLEARLY VISIBLE):
        1. TRIGGER: You must SEE the ball going out of play (shot wide/over/saved)
        2. COMPLETE STOPPAGE: All play stops, referee signals
        3. AREA CLEARANCE: All outfield players deliberately exit the 20m area
        4. FIELD SPREAD: Players spread to midfield/opposition half
        5. GROUND PLACEMENT: Goalkeeper places ball on ground at 20m line
        6. STRUCTURED KICK: Goalkeeper takes run-up, kicks from stationary ball
        7. AERIAL CONTEST: Multiple players contest high ball

        ULTRA-STRICT CRITERIA (MISSING ANY = NO KICKOUT):
        ✓ You can SEE the trigger event (ball going out) in THIS clip
        ✓ COMPLETE play stoppage visible (not during active play)
        ✓ ALL players have CLEARED the 20-meter area completely
        ✓ Players are SPREAD across the entire field (not bunched up)
        ✓ Ball is placed on GROUND (not kicked from hands)
        ✓ Clear PAUSE and setup time (not immediate clearance)
        ✓ Goalkeeper takes PROPER run-up from behind ball
        ✓ Multiple players contest the HIGH aerial ball
        ✓ This is MATCH PLAY not warm-up/training

        ABSOLUTELY NEVER DETECT:
        - Warm-up kicks or training drills
        - Goalkeeper clearances during active play
        - Any kick from hands
        - Quick clearances without setup
        - Free kicks, sideline kicks, or other restarts
        - Shots or passes during active play
        - Any kick when players haven't fully cleared area
        - Throw-ins or any other restart
        - If you can't see the trigger event that caused it
        
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

        REMEMBER: 
        - GAA kickouts are EXTREMELY RARE - only 2-3 in first 10 minutes maximum
        - When in doubt, ALWAYS say NO
        - Must see COMPLETE sequence from trigger to aerial contest
        - This is MATCH PLAY not training/warm-up
        - Be ULTRA-CONSERVATIVE in detection
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
    print("🥅 GAA KICKOUT ANALYSIS - STEP 1: VIDEO → TEXT (GEMINI 2.5 PRO)")
    print("=" * 60)
    
    # Configuration
    TIME_LIMIT_MINUTES = 10  # Analyze first 10 minutes
    MAX_WORKERS = 4  # Reduced for Pro model (slower but higher quality)
    
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