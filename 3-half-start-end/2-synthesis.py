#!/usr/bin/env python3
"""
Simple Single Request Synthesis - Just like the web app approach
Read all 337 txt files, combine into one big string, send ONE request to Gemini 2.5
"""

import google.generativeai as genai
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

def main():
    print("🎯 SINGLE REQUEST SYNTHESIS")
    print("=" * 50)
    print("Goal: Send all clip descriptions in ONE request")
    print("Model: Gemini 2.5 Pro (better reasoning for complex analysis)")
    print()
    
    # Read all 337 txt files
    clips_dir = Path("results/halftime_detection/clips")
    description_files = sorted([f for f in clips_dir.glob("*.txt") if f.name.startswith("clip_")])
    
    print(f"📁 Found {len(description_files)} description files")
    
    # Combine into one big string
    print("🔄 Combining all descriptions...")
    combined_text = ""
    total_chars = 0
    
    for desc_file in description_files:
        try:
            with open(desc_file, 'r') as f:
                content = f.read()
                # Extract timestamp from filename
                timestamp = desc_file.stem.replace('clip_', '').replace('m', ':').replace('s', '')
                combined_text += f"\n{'='*80}\n"
                combined_text += f"CLIP: {timestamp}\n"
                combined_text += f"{'='*80}\n"
                combined_text += content + "\n"
                total_chars += len(content)
        except Exception as e:
            print(f"❌ Error reading {desc_file}: {e}")
            continue
    
    print(f"📊 Combined text size: {total_chars:,} characters ({total_chars/1024/1024:.1f} MB)")
    
    # Create the synthesis prompt (temporal block analysis like web app)
    prompt = f"""
You are analyzing a GAA (Gaelic Athletic Association) football match from video clips. GAA matches have a specific structure:

GAA MATCH STRUCTURE:
- Pre-match warm-up (casual practice)
- FIRST HALF: 35+ minutes of competitive play
- HALFTIME BREAK: 10-15 minutes of casual warm-up/rest
- SECOND HALF: 35+ minutes of competitive play
- Post-match conclusion

Each half starts with an OFFICIAL THROW-IN CEREMONY by the referee in the center circle.

TASK: Analyze {len(description_files)} clips (00:00 to 84:00) to find the 4 key transition points.

STEP 1 - CATEGORIZE EVERY CLIP:
Go through each clip and categorize it as:

A) "PRE-MATCH" - Casual warm-up, loose practice, players gathering
B) "ACTIVE PLAY" - Competitive, fast-paced, tackles, scores, intense gameplay  
C) "HALFTIME BREAK" - Casual warm-up, players walking, practice kicks, relaxed
D) "THROW-IN CEREMONY" - Referee throws ball up between two players in center
E) "POST-MATCH" - Players leaving permanently, match concluded

STEP 2 - FIND CONTINUOUS BLOCKS:
Look for these temporal patterns:

1. PRE-MATCH block (casual)
2. Long ACTIVE PLAY block (30+ minutes of competitive play)
3. HALFTIME BREAK block (10-15 minutes of casual activity)
4. Long ACTIVE PLAY block (30+ minutes of competitive play)  
5. POST-MATCH conclusion

STEP 3 - IDENTIFY TRANSITIONS:
The 4 key moments are the TRANSITIONS between blocks:

1. FIRST HALF START = Last THROW-IN CEREMONY before long ACTIVE PLAY block
2. FIRST HALF END = When long ACTIVE PLAY transitions to HALFTIME BREAK
3. SECOND HALF START = THROW-IN CEREMONY that ends HALFTIME BREAK
4. MATCH END = When final ACTIVE PLAY block ends

ANALYSIS STRATEGY:
- Focus on DURATION and CONTINUITY of blocks
- A real half = 30+ minutes of continuous competitive play
- Halftime = 10-15 minutes of casual activity between competitive blocks
- Ignore isolated throw-ins during active play (these are just restarts)
- Look for the BIG PICTURE timeline, not individual moments

OUTPUT FORMAT:

TEMPORAL BLOCK ANALYSIS:

[List each clip with its category, like:]
00:00 - PRE-MATCH
00:15 - PRE-MATCH  
02:00 - THROW-IN CEREMONY
02:15 - ACTIVE PLAY
[continue for all clips...]

BLOCK SUMMARY:
Block 1: PRE-MATCH (00:00 - XX:XX)
Block 2: ACTIVE PLAY (XX:XX - XX:XX) [First Half]
Block 3: HALFTIME BREAK (XX:XX - XX:XX)
Block 4: ACTIVE PLAY (XX:XX - XX:XX) [Second Half]
Block 5: POST-MATCH (XX:XX - XX:XX)

KEY TRANSITIONS:

FIRST HALF START: [MM:SS]
Evidence: "[exact quote showing throw-in ceremony before sustained active play]"
Reasoning: "This throw-in ceremony is immediately followed by X minutes of continuous competitive play"

FIRST HALF END: [MM:SS]
Evidence: "[exact quote showing transition from active play to casual break]"
Reasoning: "After X minutes of continuous active play, players transition to casual halftime activities"

SECOND HALF START: [MM:SS]
Evidence: "[exact quote showing throw-in ceremony after halftime break]"
Reasoning: "This throw-in ceremony ends the halftime break and starts X minutes of continuous competitive play"

MATCH END: [MM:SS]
Evidence: "[exact quote showing definitive end of match]"
Reasoning: "After X minutes of second half play, the match concludes with players leaving permanently"

TIMELINE VERIFICATION:
First Half Duration: [X] minutes (should be 30+ minutes)
Halftime Break: [X] minutes (should be 10-15 minutes)
Second Half Duration: [X] minutes (should be 30+ minutes)

CRITICAL: Think like the web app - look for CONTINUOUS BLOCKS of activity, not individual moments. The GAA match structure is predictable: long competitive periods separated by a clear halftime break.

CLIPS TO ANALYZE:
{combined_text}
"""
    
    print(f"📝 Prompt size: {len(prompt):,} characters")
    print(f"🔄 Sending ONE request to Gemini 2.5 Flash...")
    
    try:
        # Send ONE request to Gemini 2.5 Pro (better reasoning for complex analysis)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        start_time = time.time()
        response = model.generate_content(prompt)
        processing_time = time.time() - start_time
        
        print(f"✅ SUCCESS! Processed in {processing_time:.1f} seconds")
        print()
        
        # Save results
        output_file = Path("results/halftime_detection/single_request_analysis.txt")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(f"SINGLE REQUEST SYNTHESIS RESULTS\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: Gemini 2.5 Pro\n")
            f.write(f"Input clips: {len(description_files)}\n")
            f.write(f"Text size: {total_chars:,} characters ({total_chars/1024/1024:.1f} MB)\n")
            f.write(f"Processing time: {processing_time:.1f} seconds\n")
            f.write("\n" + "="*80 + "\n\n")
            f.write(response.text)
        
        print(f"📁 Results saved to: {output_file}")
        print()
        print("🎯 ANALYSIS RESULTS:")
        print("=" * 50)
        print(response.text)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            print("💡 Hit rate limit - try again tomorrow or upgrade to paid tier")
        elif "context" in str(e).lower() or "length" in str(e).lower():
            print("💡 Context too large - need to split the data")
        else:
            print("💡 Other error - check the details above")

if __name__ == "__main__":
    main() 