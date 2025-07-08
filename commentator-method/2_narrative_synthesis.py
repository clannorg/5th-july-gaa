#!/usr/bin/env python3
"""
GAA Match Narrative Synthesis
Takes individual clip commentaries and creates a flowing match story
"""

import os
import re
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

def collect_commentary_clips(commentary_dir):
    """Collect all commentary clips in chronological order"""
    results = []
    
    commentary_dir = Path(commentary_dir)
    if not commentary_dir.exists():
        print(f"❌ Commentary directory not found: {commentary_dir}")
        return results
    
    commentary_files = sorted(commentary_dir.glob("*.txt"))
    print(f"📋 Found {len(commentary_files)} commentary files")
    
    for file_path in commentary_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract timestamp and commentary
            time_match = re.search(r'TIME: (\d+:\d+)', content)
            commentary_match = re.search(r'COMMENTARY:\n(.*)', content, re.DOTALL)
            
            if time_match and commentary_match:
                timestamp = time_match.group(1)
                minutes, seconds = map(int, timestamp.split(':'))
                clip_start_time = minutes * 60 + seconds
                
                commentary = commentary_match.group(1).strip()
                
                results.append({
                    'timestamp': timestamp,
                    'clip_start_time': clip_start_time,
                    'commentary': commentary,
                    'file': file_path.name
                })
                
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
    
    # Sort by time
    results.sort(key=lambda x: x['clip_start_time'])
    
    return results

def create_match_narrative(commentary_clips):
    """Use AI to weave individual commentaries into a flowing match narrative"""
    
    # Prepare all commentary clips for AI
    all_commentary = ""
    for clip in commentary_clips:
        all_commentary += f"\n[{clip['timestamp']}] {clip['commentary']}"
    
    prompt = f"""
    You are a professional GAA match commentator creating a flowing narrative from individual 15-second clip descriptions.

    🏐 MATCH CONTEXT - RED vs BLUE TEAMS:
    - RED team wears RED and BLACK jerseys
    - BLUE team wears BLUE and WHITE jerseys
    - Maintain consistent team identification throughout the narrative
    - Goalkeepers should be identified as "red team goalkeeper" or "blue team goalkeeper"

    TASK: Take these individual clip commentaries and weave them into a natural, flowing match narrative.

    🎯 SPECIAL FOCUS - GOALKEEPER KICKOUT TIMING:
    Look for any mentions of exact goalkeeper kickout timing (e.g., "at 3.2 seconds", "at 7.8 seconds").
    PRESERVE these precise timings in your narrative as they are crucial for event detection.
    Convert them to absolute match time by adding to the clip start time.

    INDIVIDUAL CLIP COMMENTARIES:
    {all_commentary}

    INSTRUCTIONS:
    1. Create a natural, flowing commentary that tells the story of the match
    2. Connect the clips smoothly - don't just list them
    3. Identify key moments and build narrative tension
    4. Use natural transitions between clips
    5. Maintain the energy and excitement of live commentary
    6. Point out patterns, momentum shifts, and key events
    7. Keep team colors consistent throughout
    8. Make it feel like one continuous commentary, not separate clips
    9. PRESERVE exact kickout timing details when mentioned

    STYLE:
    - Write like a professional sports commentator
    - Use present tense and active voice
    - Build excitement around key moments
    - Provide context and continuity
    - Make natural transitions between time periods
    - Maintain precise kickout timing information

    OUTPUT FORMAT:
    Write a flowing match narrative that reads like continuous live commentary. Include timestamps naturally within the narrative (e.g., "At 3:45, the ball is worked across the field...").

    For kickouts with precise timing, convert to absolute match time:
    - If a clip starts at [2:30] and mentions "at 4.7 seconds", write "At 2:34.7, the goalkeeper strikes the ball..."

    Create the flowing match narrative:
    """
    
    try:
        print(f"🎙️  Creating match narrative from {len(commentary_clips)} clips...")
        
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        print(f"❌ Narrative synthesis failed: {e}")
        return None

def save_match_narrative(narrative, output_dir):
    """Save the complete match narrative"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main narrative
    narrative_file = output_dir / "match_narrative.txt"
    with open(narrative_file, 'w') as f:
        f.write("GAA MATCH NARRATIVE - FIRST 10 MINUTES\n")
        f.write("=" * 50 + "\n\n")
        f.write(narrative)
    
    print(f"📄 Match narrative saved: {narrative_file}")
    
    # Also save as markdown for better readability
    markdown_file = output_dir / "match_narrative.md"
    with open(markdown_file, 'w') as f:
        f.write("# GAA Match Narrative - First 10 Minutes\n\n")
        f.write(narrative)
    
    print(f"📄 Markdown version saved: {markdown_file}")
    
    return narrative_file

def main():
    print("🎙️  GAA MATCH NARRATIVE SYNTHESIS")
    print("=" * 50)
    
    # Setup paths
    commentary_dir = Path("results/simple_commentary")
    output_dir = Path("results/match_narrative")
    
    # Collect commentary clips
    print("📋 Collecting commentary clips...")
    commentary_clips = collect_commentary_clips(commentary_dir)
    
    if not commentary_clips:
        print("❌ No commentary clips found!")
        print(f"   Make sure to run 'simple_commentary.py' first")
        return
    
    print(f"✅ Found {len(commentary_clips)} commentary clips")
    print(f"⏱️  Time range: {commentary_clips[0]['timestamp']} → {commentary_clips[-1]['timestamp']}")
    
    # Create narrative
    print("🎙️  Synthesizing match narrative...")
    narrative = create_match_narrative(commentary_clips)
    
    if not narrative:
        print("❌ Narrative synthesis failed!")
        return
    
    # Save narrative
    print("💾 Saving match narrative...")
    narrative_file = save_match_narrative(narrative, output_dir)
    
    print(f"\n✅ MATCH NARRATIVE COMPLETE!")
    print(f"📁 Narrative saved to: {narrative_file}")
    print(f"🎙️  You now have a flowing match commentary!")
    
    # Show preview
    print(f"\n📖 PREVIEW:")
    print("=" * 50)
    preview = narrative[:500] + "..." if len(narrative) > 500 else narrative
    print(preview)

if __name__ == "__main__":
    main() 