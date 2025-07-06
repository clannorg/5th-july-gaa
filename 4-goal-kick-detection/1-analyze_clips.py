#!/usr/bin/env python3
"""
1-analyze_clips.py - Analyze Match Clips for Goal Kick Detection
Analyzes clips from 3.5-video-splitting for GAA kickouts
"""

import google.generativeai as genai
import os
import time
from pathlib import Path
import concurrent.futures
from threading import Lock
import argparse
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
        
        # Enhanced GAA kickout analysis prompt
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

def analyze_half_clips(clips_dir, half_name, output_dir, max_threads=20):
    """Analyze all clips from one half"""
    
    clips_path = Path(clips_dir)
    if not clips_path.exists():
        print(f"❌ {half_name} clips directory not found: {clips_path}")
        return False
    
    # Find all video clips
    video_files = sorted(clips_path.glob("*.mp4"))
    
    if not video_files:
        print(f"❌ No clips found in {clips_path}")
        return False
    
    print(f"\n🥅 ANALYZING {half_name.upper()} CLIPS")
    print(f"=" * 50)
    print(f"📁 Input: {clips_path}")
    print(f"📊 Clips: {len(video_files)}")
    print(f"🧵 Threads: {max_threads}")
    
    # Create output directory
    half_output_dir = output_dir / half_name
    half_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process clips in parallel
    start_time = time.time()
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        
        for video_file in video_files:
            # Extract timestamp from filename (clip_00m15s.mp4 -> 00:15)
            timestamp = video_file.stem.replace('clip_', '').replace('m', ':').replace('s', '')
            
            future = executor.submit(analyze_clip_for_kickouts, str(video_file), timestamp, half_name)
            futures.append((future, video_file, timestamp))
        
        # Collect results with progress
        for future, video_file, timestamp in futures:
            try:
                result = future.result()
                
                # Save result
                output_file = half_output_dir / f"{video_file.stem}.txt"
                with open(output_file, 'w') as f:
                    f.write(f"HALF: {half_name}\n")
                    f.write(f"TIMESTAMP: {timestamp}\n")
                    f.write(f"CLIP_FILE: {video_file.name}\n")
                    f.write(f"QUERY: GAA Kickout Detection\n\n")
                    f.write(f"ANALYSIS:\n{result}\n")
                
                completed += 1
                progress = (completed / len(video_files)) * 100
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                
                print(f"📈 {half_name} Progress: {completed}/{len(video_files)} ({progress:.1f}%) | "
                      f"Rate: {rate:.1f} clips/s")
                
            except Exception as e:
                print(f"❌ Error processing {video_file}: {e}")
    
    processing_time = time.time() - start_time
    
    print(f"\n✅ {half_name.upper()} ANALYSIS COMPLETE!")
    print(f"⏱️  Time: {processing_time:.1f}s")
    print(f"🚀 Rate: {len(video_files)/processing_time:.1f} clips/second")
    print(f"📁 Results: {half_output_dir}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Analyze match clips for GAA kickout detection')
    parser.add_argument('--clips-base', type=str, default='../3.5-video-splitting/clips', 
                       help='Base clips directory (contains first_half/ and second_half/)')
    parser.add_argument('--output-dir', type=str, default='results/kickout_analysis', 
                       help='Output directory for analysis results')
    parser.add_argument('--threads', type=int, default=20, 
                       help='Number of threads for parallel processing')
    parser.add_argument('--half', type=str, choices=['first_half', 'second_half', 'both'], 
                       default='both', help='Which half to analyze')
    
    args = parser.parse_args()
    
    print("🥅 GAA KICKOUT DETECTION - MATCH ANALYSIS")
    print("=" * 60)
    print("Analyzing clips from 3.5-video-splitting for GAA kickouts")
    print(f"Base directory: {args.clips_base}")
    print(f"Threads: {args.threads}")
    print("=" * 60)
    
    # Setup paths
    clips_base = Path(args.clips_base)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not clips_base.exists():
        print(f"❌ Clips base directory not found: {clips_base}")
        return
    
    total_start_time = time.time()
    success_count = 0
    
    # Analyze requested halves
    if args.half in ['first_half', 'both']:
        first_half_dir = clips_base / 'first_half'
        if analyze_half_clips(first_half_dir, 'first_half', output_dir, args.threads):
            success_count += 1
    
    if args.half in ['second_half', 'both']:
        second_half_dir = clips_base / 'second_half'
        if analyze_half_clips(second_half_dir, 'second_half', output_dir, args.threads):
            success_count += 1
    
    total_time = time.time() - total_start_time
    
    print(f"\n🎉 COMPLETE KICKOUT ANALYSIS FINISHED!")
    print(f"=" * 60)
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(f"✅ Halves analyzed: {success_count}")
    print(f"📁 Results saved to: {output_dir}")
    
    if success_count > 0:
        print(f"\n🔄 Next step: Synthesize results")
        print(f"   python 2-synthesize_kickouts.py --analysis-dir {output_dir}")
    
    print(f"\n📊 Analysis complete! Ready for synthesis.")

if __name__ == "__main__":
    main() 