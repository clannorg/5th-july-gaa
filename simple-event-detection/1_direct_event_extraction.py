#!/usr/bin/env python3
"""
Direct GAA Event Extraction
Skip the commentary layer - go straight from video to structured events
"""

import os
import time
import json
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

def extract_events_from_clip(clip_path, clip_start_seconds):
    """Extract events directly from a 15-second clip"""
    try:
        # Upload video to Gemini
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            return {"error": f"Failed to process {clip_path}"}
        
        # Direct event extraction prompt
        prompt = f"""
        You are analyzing a 15-second GAA match clip starting at {clip_start_seconds} seconds into the match.

        🏐 TEAMS:
        - RED team: red and black jerseys
        - BLUE team: blue and white jerseys
        - Goalkeepers: distinct colored jerseys (often yellow/green/bright colors)

        TASK: Extract ONLY the concrete events you can clearly see. Don't infer or assume.

        🎯 EVENTS TO DETECT:
        1. KICKOUT: Goalkeeper kicks ball from hands (specify exact timing within clip)
        2. SHOT: Player attempts to score (specify outcome: Goal/1Point/2Point/Wide/Saved)
        3. FOUL: Clear foul committed (free kick awarded)
        4. TURNOVER: Ball changes possession clearly
        5. THROW_UP: Ball thrown up to restart play

        📋 OUTPUT FORMAT - JSON ONLY:
        {{
            "clip_start_time": {clip_start_seconds},
            "events": [
                {{
                    "type": "Kickout",
                    "team": "red",
                    "time_in_clip": 4.7,
                    "absolute_time": {clip_start_seconds + 4.7},
                    "description": "Red team goalkeeper kicks ball from hands"
                }},
                {{
                    "type": "Shot",
                    "team": "blue", 
                    "time_in_clip": 12.3,
                    "absolute_time": {clip_start_seconds + 12.3},
                    "outcome": "1Point",
                    "description": "Blue team player scores point"
                }}
            ]
        }}

        🚨 CRITICAL RULES:
        - Only include events you can CLEARLY see
        - Be precise with timing (use decimals: 3.2, 7.8, etc.)
        - If you see nothing significant, return empty events array
        - Don't create events from assumptions or context
        - Focus on the 5 event types above only
        - Team must be "red" or "blue" (not "red team" or "blue team")

        ANALYZE THIS CLIP:
        """
        
        # Generate events
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content([video_file, prompt])
        
        # Clean up
        genai.delete_file(video_file.name)
        
        # Parse JSON response
        try:
            # Clean the response - remove markdown formatting if present
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove ```
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            # Save the raw response for debugging
            debug_file = Path("debug_responses") / f"{Path(clip_path).stem}_debug.txt"
            debug_file.parent.mkdir(exist_ok=True)
            with open(debug_file, 'w') as f:
                f.write(f"JSON Error: {e}\n")
                f.write(f"Raw response:\n{response.text}\n")
            return {"error": "JSON parsing failed", "raw_response": response.text[:200] + "..."}
        
    except Exception as e:
        return {"error": f"Error analyzing {clip_path}: {str(e)}"}

def main():
    print("🎯 DIRECT GAA EVENT EXTRACTION")
    print("=" * 50)
    
    # Configuration
    TIME_LIMIT_MINUTES = 10
    MAX_WORKERS = 12
    
    # Setup paths
    clips_base = Path("../3.5-video-splitting/clips/first_half")
    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not clips_base.exists():
        print(f"❌ Clips directory not found: {clips_base}")
        return
    
    # Find clips for time period
    all_clips = sorted(clips_base.glob("*.mp4"))
    target_clips = []
    
    for clip in all_clips:
        if "clip_" in clip.name:
            parts = clip.stem.replace("clip_", "").split("m")
            if len(parts) >= 1:
                try:
                    minutes = int(parts[0])
                    if minutes < TIME_LIMIT_MINUTES:
                        # Calculate clip start time in seconds
                        seconds_part = parts[1].replace("s", "") if len(parts) > 1 else "0"
                        seconds = int(seconds_part)
                        clip_start_seconds = minutes * 60 + seconds
                        target_clips.append((clip, clip_start_seconds))
                except ValueError:
                    continue
    
    print(f"📊 Found {len(target_clips)} clips in first {TIME_LIMIT_MINUTES} minutes")
    
    if not target_clips:
        print("❌ No clips found!")
        return
    
    # Process clips in parallel
    start_time = time.time()
    all_events = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        
        for clip_path, clip_start_seconds in target_clips:
            future = executor.submit(extract_events_from_clip, str(clip_path), clip_start_seconds)
            futures.append((future, clip_path, clip_start_seconds))
        
        # Collect results
        for future, clip_path, clip_start_seconds in futures:
            try:
                result = future.result()
                
                if "error" in result:
                    print(f"❌ {clip_path.name}: {result['error']}")
                else:
                    # Add events to master list
                    if "events" in result:
                        for event in result["events"]:
                            event["clip_file"] = clip_path.name
                            all_events.append(event)
                
                completed += 1
                progress = (completed / len(futures)) * 100
                print(f"📈 Progress: {completed}/{len(futures)} ({progress:.1f}%)")
                
            except Exception as e:
                print(f"❌ Error processing {clip_path}: {e}")
    
    # Sort events by time
    all_events.sort(key=lambda x: x.get("absolute_time", 0))
    
    # Save results
    output_file = output_dir / "direct_events.json"
    with open(output_file, 'w') as f:
        json.dump({
            "match_info": {
                "title": "GAA Match - Direct Event Extraction",
                "total_events": len(all_events),
                "time_period": f"First {TIME_LIMIT_MINUTES} minutes",
                "method": "Direct VLM to events"
            },
            "events": all_events
        }, f, indent=2)
    
    # Summary
    event_types = {}
    for event in all_events:
        event_type = event.get("type", "Unknown")
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    processing_time = time.time() - start_time
    
    print(f"\n✅ DIRECT EVENT EXTRACTION COMPLETE!")
    print(f"⏱️  Time: {processing_time:.1f}s")
    print(f"📊 Total events: {len(all_events)}")
    print(f"📋 Event breakdown:")
    for event_type, count in event_types.items():
        print(f"   {event_type}: {count}")
    print(f"📁 Results saved to: {output_file}")

if __name__ == "__main__":
    main() 