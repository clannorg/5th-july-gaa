#!/usr/bin/env python3
"""
Script 1: Analyze Each 15-Second Clip for Halftime Detection
Runs Gemini AI on each clip and outputs natural language descriptions
"""

import google.generativeai as genai
import os
import time
from pathlib import Path
import concurrent.futures
from threading import Lock
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

# Thread safety
results_lock = Lock()
processed_count = 0
error_count = 0

def analyze_clip_for_halftime(clip_path, clip_name, output_dir):
    """Analyze a single clip and write natural language description"""
    global processed_count, error_count
    
    try:
        # Extract timestamp from clip name (clip_15m30s.mp4 -> 15:30)
        timestamp = clip_name.replace('clip_', '').replace('.mp4', '').replace('m', ':').replace('s', '')
        
        print(f"🎬 Analyzing {clip_name} ({timestamp})")
        
        # Upload video to Gemini
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed for {clip_name}")
        
        # Create the model
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Natural language prompt for halftime detection
        prompt = f"""
        Analyze this 15-second GAA football clip (timestamp: {timestamp}) and describe what you observe in natural language, focusing specifically on GAA MATCH TRANSITIONS and HALFTIME INDICATORS.

        Write a detailed description covering:

        1. **Player Movement & Behavior**: Are players actively playing, walking off field, gathering in groups, or positioning for restart?

        2. **Game State**: Is this active play, a break in action, players leaving/entering field, or preparation for restart?

        3. **Team Organization**: Can you identify two distinct teams? Are they organized for play or dispersed/gathering?

        4. **Referee Activity**: Where is the referee positioned? Are they signaling anything? **CRITICAL: Look for referee throwing ball up between players (GAA throw-in ceremony)**

        5. **Field Activity**: Is there a ball in play? Are players spread across the field or concentrated in areas? **CRITICAL: Look for players gathering in center circle for throw-in**

        6. **GAA-Specific Transition Indicators**: 
           - **THROW-IN CEREMONY**: Referee throwing ball up between two players in center circle (indicates half/match start)
           - **CENTER CIRCLE ACTIVITY**: Players positioning for throw-in restart
           - **HALF ENDING**: Players walking to sidelines, leaving field for extended break
           - **HALF STARTING**: Players returning from sidelines, gathering centrally

        7. **GAA Context**: Is this:
           - Active match play (running, tackling, passing under pressure)
           - Practice/warm-up (casual kicking, no pressure, multiple balls)
           - Throw-in ceremony (referee + two players in center)
           - Half-time break (players off field, casual movement)
           - Match end (players leaving permanently, handshakes)

        **CRITICAL GAA ELEMENTS TO IDENTIFY:**
        - "Referee throwing ball up" or "throw-in"
        - "Players in center circle" or "central positioning"
        - "Two players facing off" for throw-in
        - Distinguish between casual practice and organized match play
        - Distinguish between brief stoppages and extended breaks

        Write in clear, descriptive language as if explaining what you see to someone who can't watch the video. Focus on details that would help identify when GAA halves start and end.

        Be specific about what you observe - don't guess or assume. If you see a throw-in ceremony, describe it explicitly.
        """
        
        # Generate description
        response = model.generate_content([video_file, prompt])
        
        # Clean up uploaded file
        genai.delete_file(video_file.name)
        
        # Write description to file
        output_file = output_dir / f"{clip_name.replace('.mp4', '.txt')}"
        
        description = f"TIMESTAMP: {timestamp}\nQUERY: Halftime Detection\n\nDESCRIPTION:\n{response.text}\n"
        
        with open(output_file, 'w') as f:
            f.write(description)
        
        with results_lock:
            global processed_count
            processed_count += 1
            print(f"✅ {clip_name} → {output_file.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing {clip_name}: {e}")
        with results_lock:
            global error_count
            error_count += 1
        return False

def main():
    parser = argparse.ArgumentParser(description='Analyze clips for halftime detection')
    parser.add_argument('--clips-dir', type=str, default='../2-splitting/clips', 
                       help='Directory containing video clips')
    parser.add_argument('--output-dir', type=str, default='results/halftime_detection/clips',
                       help='Directory to save descriptions')
    parser.add_argument('--threads', type=int, default=8, help='Number of parallel threads')
    parser.add_argument('--max-clips', type=int, help='Maximum clips to process (for testing)')
    
    args = parser.parse_args()
    
    print("🕐 HALFTIME DETECTION - CLIP ANALYSIS")
    print("=" * 60)
    print("Goal: Generate natural language descriptions for halftime detection")
    print(f"Threads: {args.threads}")
    print("=" * 60)
    
    # Setup directories
    clips_dir = Path(args.clips_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not clips_dir.exists():
        print(f"❌ Clips directory not found: {clips_dir}")
        return
    
    # Find clips
    clip_files = sorted([f for f in clips_dir.glob("*.mp4") if f.name.startswith("clip_")])
    
    if args.max_clips:
        clip_files = clip_files[:args.max_clips]
    
    if not clip_files:
        print("❌ No clip files found!")
        return
    
    print(f"📊 Found {len(clip_files)} clips to analyze")
    
    start_time = time.time()
    
    # Process clips in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        
        for clip_file in clip_files:
            future = executor.submit(analyze_clip_for_halftime, str(clip_file), clip_file.name, output_dir)
            futures.append(future)
        
        # Wait for completion with progress updates
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 10 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed
                remaining = len(clip_files) - completed
                eta = remaining / rate / 60
                print(f"📈 Progress: {completed}/{len(clip_files)} ({completed/len(clip_files)*100:.1f}%) - ETA: {eta:.1f} min")
    
    # Final summary
    processing_time = time.time() - start_time
    
    print(f"\n✅ CLIP ANALYSIS COMPLETE!")
    print(f"⏱️  Total time: {processing_time/60:.1f} minutes")
    print(f"📊 Processed: {processed_count} clips")
    print(f"❌ Errors: {error_count} clips")
    print(f"⚡ Rate: {processed_count/processing_time:.1f} clips/second")
    print(f"📁 Descriptions saved to: {output_dir}")
    
    print(f"\n🔄 Next step: Run pattern synthesis")
    print(f"Command: python synthesize_patterns.py --input-dir {output_dir}")

if __name__ == "__main__":
    main() 