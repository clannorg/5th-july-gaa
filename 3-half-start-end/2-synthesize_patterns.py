#!/usr/bin/env python3
"""
Script 2: Synthesize Patterns from Clip Descriptions
Reads all natural language descriptions and determines halftime start/end
"""

import google.generativeai as genai
import os
import time
from pathlib import Path
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

def read_all_descriptions(input_dir):
    """Read all description files and compile into timeline"""
    descriptions = []
    
    description_files = sorted(Path(input_dir).glob("*.txt"))
    
    for file_path in description_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Extract timestamp from filename (clip_15m30s.txt -> 15:30)
            clip_name = file_path.stem  # removes .txt
            timestamp = clip_name.replace('clip_', '').replace('m', ':').replace('s', '')
            
            descriptions.append({
                'timestamp': timestamp,
                'filename': file_path.name,
                'content': content
            })
            
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    return descriptions

def convert_timestamp_to_seconds(timestamp):
    """Convert MM:SS timestamp to total seconds for sorting"""
    try:
        parts = timestamp.split(':')
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return 0
    except:
        return 0

def synthesize_halftime_patterns(descriptions):
    """Use AI to analyze all descriptions and find halftime patterns"""
    
    print("🧠 Synthesizing patterns from all descriptions...")
    
    # Sort descriptions by timestamp
    descriptions.sort(key=lambda x: convert_timestamp_to_seconds(x['timestamp']))
    
    # Compile all descriptions into one text
    compiled_text = "\n" + "="*80 + "\n"
    compiled_text += "GAA MATCH CLIP DESCRIPTIONS - TIMELINE\n"
    compiled_text += "="*80 + "\n\n"
    
    for desc in descriptions:
        compiled_text += f"TIMESTAMP: {desc['timestamp']}\n"
        compiled_text += f"FILE: {desc['filename']}\n"
        compiled_text += desc['content'] + "\n"
        compiled_text += "-" * 40 + "\n\n"
    
    # Create synthesis prompt
    prompt = f"""
You are analyzing GAA match clips to find EXACTLY 4 events. You have 337 clip descriptions covering timestamps from 00:00 to 84:00.

TASK: Find these 4 timestamps with supporting evidence:
1. FIRST HALF START
2. FIRST HALF END  
3. SECOND HALF START
4. MATCH END

SEARCH STRATEGY:
Step 1: Scan ALL clips for these exact phrases (case-insensitive):
- "THROW-IN CEREMONY" 
- "referee throwing ball up"
- "referee throws ball up"
- "ball up between two players"
- "center circle" + "referee"

Step 2: Scan ALL clips for half-ending phrases:
- "players walking off field"
- "leaving the pitch"
- "final whistle" 
- "end of half"
- "players departing"
- "walking to sidelines"

Step 3: Scan ALL clips for match-ending phrases:
- "match concluded"
- "players leaving permanently"
- "shaking hands"
- "final whistle"
- "end of match"

EVIDENCE RULES:
- ONLY use clips with explicit ceremony language for half starts
- ONLY use clips with explicit departure language for half/match ends
- Ignore vague descriptions like "appears to be" or "possibly"
- If multiple clips describe same event, pick the one with clearest language

LOGICAL CONSTRAINTS:
- First half must start before it ends
- Second half must start after first half ends
- Match must end after second half starts
- Halftime break should be 3-15 minutes
- Each half should be 15-45 minutes

OUTPUT FORMAT (use exact quotes as evidence):

ANALYSIS RESULTS:

FIRST HALF START: [MM:SS]
Evidence: "[exact quote from clip description]"
File: clip_[timestamp].txt

FIRST HALF END: [MM:SS]  
Evidence: "[exact quote from clip description]"
File: clip_[timestamp].txt

SECOND HALF START: [MM:SS]
Evidence: "[exact quote from clip description]"  
File: clip_[timestamp].txt

MATCH END: [MM:SS]
Evidence: "[exact quote from clip description]"
File: clip_[timestamp].txt

TIMELINE SUMMARY:
First Half Duration: [X] minutes
Halftime Break: [X] minutes  
Second Half Duration: [X] minutes

CRITICAL: Do NOT analyze or interpret. Simply FIND the clips with the clearest evidence and report them. Let the evidence speak for itself.

CLIPS TO SEARCH:
{compiled_text}
"""
    
    # Generate synthesis
    model = genai.GenerativeModel("gemini-2.5-pro")
        
    print("🔍 Analyzing patterns across all clips...")
    response = model.generate_content(prompt)
    
    return response.text

def main():
    parser = argparse.ArgumentParser(description='Synthesize halftime patterns from clip descriptions')
    parser.add_argument('--input-dir', type=str, default='results/halftime_detection/clips',
                       help='Directory containing description files')
    parser.add_argument('--output-file', type=str, default='results/halftime_detection/halftime_analysis.txt',
                       help='Output file for synthesis results')
    
    args = parser.parse_args()
    
    print("🧠 HALFTIME DETECTION - PATTERN SYNTHESIS")
    print("=" * 60)
    print("Goal: Analyze all descriptions to find halftime start/end")
    print("=" * 60)
    
    # Setup paths
    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Read all descriptions
    print("📖 Reading all clip descriptions...")
    descriptions = read_all_descriptions(input_dir)
    
    if not descriptions:
        print("❌ No description files found!")
        return
    
    print(f"📊 Found {len(descriptions)} clip descriptions")
    
    # Synthesize patterns
    start_time = time.time()
    
    try:
        synthesis_result = synthesize_halftime_patterns(descriptions)
        
        # Save results
        with open(output_file, 'w') as f:
            f.write(f"HALFTIME DETECTION SYNTHESIS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Input clips: {len(descriptions)}\n")
            f.write(f"Analysis duration: {time.time() - start_time:.1f} seconds\n")
            f.write("\n" + "="*80 + "\n\n")
            f.write(synthesis_result)
        
        processing_time = time.time() - start_time
        
        print(f"\n✅ PATTERN SYNTHESIS COMPLETE!")
        print(f"⏱️  Analysis time: {processing_time:.1f} seconds")
        print(f"📁 Results saved to: {output_file}")
        
        # Display key results
        print(f"\n📋 SYNTHESIS RESULTS:")
        print("-" * 40)
        
        # Try to extract key timestamps from the result
        lines = synthesis_result.split('\n')
        for line in lines:
            if 'FIRST HALF END:' in line or 'SECOND HALF START:' in line or 'MATCH END:' in line:
                print(f"🎯 {line.strip()}")
        
        print(f"\n📖 Full analysis available in: {output_file}")
        
    except Exception as e:
        print(f"❌ Error during synthesis: {e}")

if __name__ == "__main__":
    main() 