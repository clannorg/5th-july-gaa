#!/usr/bin/env python3
"""
Script 1.5: Compress Agent - Convert Detailed Descriptions to Concise Timeline Summaries
Processes all detailed clip descriptions and creates focused summaries for halftime detection
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

def compress_clip_description(input_file, output_dir):
    """Compress a single detailed description into a concise timeline summary"""
    global processed_count, error_count
    
    try:
        # Read the detailed description
        with open(input_file, 'r') as f:
            detailed_content = f.read()
        
        # Extract clip name and timestamp
        clip_name = input_file.stem  # removes .txt
        timestamp = clip_name.replace('clip_', '').replace('m', ':').replace('s', '')
        
        print(f"🔄 Compressing {clip_name} ({timestamp})")
        
        # Create compression prompt
        compression_prompt = f"""
Analyze this detailed GAA match clip description and classify it into ONE of these categories with supporting evidence.

CATEGORIES:
1. GAME_START - Throw-in ceremony marking start of first/second half
2. HALFTIME - Warm-up, practice, casual play during break period  
3. ACTIVE_PLAY - Competitive match action with organized teams
4. GAME_END - Final whistle, players permanently leaving field

DETAILED DESCRIPTION TO ANALYZE:
{detailed_content}

RESPOND IN THIS EXACT FORMAT:

TIMESTAMP: {timestamp}
CATEGORY: [GAME_START/HALFTIME/ACTIVE_PLAY/GAME_END]
CONFIDENCE: [1-10]

KEY_INDICATORS:
- [Specific detail 1 that led to classification]
- [Specific detail 2 that led to classification] 
- [Specific detail 3 that led to classification]

TIMELINE_RELEVANCE:
[One sentence explaining why this matters for half-time detection]

CRITICAL_PHRASES:
[Any exact phrases related to: "throw-in ceremony", "referee throwing ball up", "center circle", "players leaving field", "final whistle", "warm-up", "practice"]

REQUIREMENTS:
- Be precise and specific
- Quote exact phrases from the description
- Focus ONLY on timeline detection relevance
- Keep response under 150 words
- If you see throw-in ceremony language, mark as GAME_START
- If you see players leaving field permanently, mark as GAME_END
- If you see casual/practice activity, mark as HALFTIME
- If you see competitive organized play, mark as ACTIVE_PLAY
"""
        
        # Generate compression
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(compression_prompt)
        
        # Save compressed description
        output_file = output_dir / f"{clip_name}_compressed.txt"
        
        with open(output_file, 'w') as f:
            f.write(response.text)
        
        with results_lock:
            processed_count += 1
            print(f"✅ {clip_name} → {output_file.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error compressing {input_file.name}: {e}")
        with results_lock:
            error_count += 1
        return False

def main():
    parser = argparse.ArgumentParser(description='Compress detailed clip descriptions for timeline detection')
    parser.add_argument('--input-dir', type=str, default='results/halftime_detection/clips',
                       help='Directory containing detailed description files')
    parser.add_argument('--output-dir', type=str, default='results/halftime_detection/compressed',
                       help='Directory to save compressed descriptions')
    parser.add_argument('--threads', type=int, default=12, help='Number of parallel threads')
    parser.add_argument('--max-clips', type=int, help='Maximum clips to process (for testing)')
    
    args = parser.parse_args()
    
    print("🗜️  COMPRESSION AGENT - CLIP DESCRIPTION COMPRESSION")
    print("=" * 70)
    print("Goal: Convert detailed descriptions to concise timeline summaries")
    print(f"Threads: {args.threads}")
    print("=" * 70)
    
    # Setup directories
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Find description files
    description_files = sorted([f for f in input_dir.glob("*.txt") if f.name.startswith("clip_")])
    
    if args.max_clips:
        description_files = description_files[:args.max_clips]
    
    if not description_files:
        print("❌ No description files found!")
        return
    
    print(f"📊 Found {len(description_files)} descriptions to compress")
    
    start_time = time.time()
    
    # Process descriptions in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        
        for desc_file in description_files:
            future = executor.submit(compress_clip_description, desc_file, output_dir)
            futures.append(future)
        
        # Wait for completion with progress updates
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 20 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed
                remaining = len(description_files) - completed
                eta = remaining / rate / 60
                print(f"📈 Progress: {completed}/{len(description_files)} ({completed/len(description_files)*100:.1f}%) - ETA: {eta:.1f} min")
    
    # Final summary
    processing_time = time.time() - start_time
    
    print(f"\n✅ COMPRESSION COMPLETE!")
    print(f"⏱️  Total time: {processing_time/60:.1f} minutes")
    print(f"📊 Processed: {processed_count} descriptions")
    print(f"❌ Errors: {error_count} descriptions")
    print(f"⚡ Rate: {processed_count/processing_time:.1f} descriptions/second")
    print(f"📁 Compressed summaries saved to: {output_dir}")
    
    # Show size comparison
    try:
        input_size = sum(f.stat().st_size for f in input_dir.glob("*.txt")) / 1024 / 1024
        output_size = sum(f.stat().st_size for f in output_dir.glob("*.txt")) / 1024 / 1024
        compression_ratio = (1 - output_size/input_size) * 100
        
        print(f"\n📊 COMPRESSION STATS:")
        print(f"Input size: {input_size:.1f} MB")
        print(f"Output size: {output_size:.1f} MB") 
        print(f"Compression: {compression_ratio:.1f}% reduction")
    except:
        pass
    
    print(f"\n🔄 Next step: Run pattern synthesis on compressed data")
    print(f"Command: python 2-synthesize_patterns.py --input-dir {output_dir}")

if __name__ == "__main__":
    main() 