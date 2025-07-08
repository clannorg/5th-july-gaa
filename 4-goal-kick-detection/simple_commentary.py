#!/usr/bin/env python3
"""
Simple GAA Match Commentary Generator
Just describe what's happening - no complex detection logic
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

def create_simple_commentary(clip_path, timestamp, half_name):
    """Generate simple commentary for a 15-second clip"""
    try:
        # Upload video to Gemini
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            return f"❌ Failed to process {clip_path}"
        
        # Simple commentary prompt
        prompt = f"""
        You are a GAA match commentator watching a 15-second clip at {timestamp} in the {half_name}.

        🏐 MATCH CONTEXT - RED vs BLUE TEAMS:
        - RED team wears RED and BLACK jerseys (goalkeeper in different colored jersey)
        - BLUE team wears BLUE and WHITE jerseys (goalkeeper in different colored jersey)
        - Goalkeepers typically wear distinct colored jerseys (often yellow, green, or other bright colors)
        - Be specific about which team's goalkeeper is taking kickouts

        TASK: Provide natural, flowing commentary describing what's happening in this clip.

        🎯 SPECIAL FOCUS - GOALKEEPER KICKOUTS:
        If you see a goalkeeper taking a kickout (goalkeeper kicking the ball from their hands):
        1. IDENTIFY THE EXACT MOMENT the goalkeeper's foot makes contact with the ball
        2. STATE THE PRECISE TIME within the 15-second clip (e.g., "at 3.2 seconds", "at 7.8 seconds")
        3. Describe it naturally: "The red team goalkeeper strikes the ball at [X.X seconds] sending it long..."
        4. BE SPECIFIC about which team's goalkeeper (red team or blue team)

        STYLE: 
        - Write like a sports commentator
        - Be descriptive but concise
        - Focus on the action, players, and ball movement
        - Mention key events naturally (kickouts, scores, tackles, etc.)
        - Don't force structure - just describe what you see
        - For kickouts, be PRECISE about the exact contact timing

        WHAT TO INCLUDE:
        - What's happening with the ball
        - Player movements and actions
        - Team identification: "red team players in red and black jerseys" vs "blue team players in blue and white jerseys"
        - Goalkeeper actions: "red team goalkeeper" or "blue team goalkeeper" (not just "goalkeeper in blue")
        - Any significant events (goals, saves, tackles, restarts)
        - Pace and intensity of play
        - Field position and movement
        - EXACT timing of goalkeeper foot-to-ball contact (if visible)

        WHAT TO AVOID:
        - Complex analysis or tactical breakdowns
        - Forcing specific event categories
        - Rigid formatting requirements
        - Over-analyzing minor details

        OUTPUT FORMAT:
        Just write 2-3 sentences of natural commentary describing the 15 seconds of action.

        Example style:
        "The ball is worked across the field by the team in blue jerseys. A player in red intercepts the pass and immediately kicks it long towards the goal area. The goalkeeper comes out to collect the ball as players from both teams converge."

        Example with kickout timing:
        "The goalkeeper in blue receives the ball and prepares for the kickout. At 4.7 seconds, he strikes the ball with his right foot, sending it high towards the center of the field where players from both teams are positioned to contest."

        Your commentary for this {timestamp} clip:
        """
        
        # Generate commentary
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([video_file, prompt])
        
        # Clean up
        genai.delete_file(video_file.name)
        
        return response.text.strip()
        
    except Exception as e:
        return f"❌ Error analyzing {clip_path}: {str(e)}"

def main():
    print("🎙️  GAA MATCH COMMENTARY GENERATOR")
    print("=" * 50)
    
    # Configuration
    TIME_LIMIT_MINUTES = 10  # Analyze first 10 minutes
    MAX_WORKERS = 6  # Reasonable for Flash model
    
    # Setup paths
    clips_base = Path("../3.5-video-splitting/clips/first_half")
    output_dir = Path("results/simple_commentary")
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
    
    if not target_clips:
        print("❌ No clips found! Make sure video clips exist in the clips directory.")
        return
    
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
            
            future = executor.submit(create_simple_commentary, str(video_file), timestamp, "first_half")
            futures.append((future, video_file, timestamp))
        
        # Collect results with progress
        for future, video_file, timestamp in futures:
            try:
                result = future.result()
                
                # Save result
                output_file = output_dir / f"{video_file.stem}.txt"
                with open(output_file, 'w') as f:
                    f.write(f"TIME: {timestamp}\n")
                    f.write(f"CLIP: {video_file.name}\n")
                    f.write(f"COMMENTARY:\n{result}\n")
                
                completed += 1
                progress = (completed / len(futures)) * 100 if futures else 0
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                
                print(f"📈 Progress: {completed}/{len(futures)} ({progress:.1f}%) | "
                      f"Rate: {rate:.1f} clips/s | Latest: {timestamp}")
                
            except Exception as e:
                print(f"❌ Error processing {video_file}: {e}")
    
    processing_time = time.time() - start_time
    
    print(f"\n✅ COMMENTARY GENERATION COMPLETE!")
    print(f"⏱️  Time: {processing_time:.1f}s")
    print(f"📁 Results saved to: {output_dir}")
    print(f"\n🔄 Next: Run the narrative synthesis script to create flowing match commentary")

if __name__ == "__main__":
    main() 