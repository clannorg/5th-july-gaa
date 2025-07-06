#!/usr/bin/env python3
"""
Test script to check Gemini 2.5 context size limits through API
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

def test_context_size():
    """Test different context sizes to find the limit"""
    
    # Read all our description files
    clips_dir = Path("results/halftime_detection/clips")
    description_files = sorted([f for f in clips_dir.glob("*.txt") if f.name.startswith("clip_")])
    
    print(f"🧪 CONTEXT SIZE TEST")
    print(f"=" * 50)
    print(f"Found {len(description_files)} description files")
    print(f"Testing incremental context sizes...")
    print()
    
    model = genai.GenerativeModel("gemini-2.5-pro")
    
    # Test different batch sizes
    test_sizes = [1, 5, 10, 25, 50, 100, 150, 200, 250, 300, 337]
    
    for batch_size in test_sizes:
        if batch_size > len(description_files):
            batch_size = len(description_files)
            
        print(f"📊 Testing {batch_size} files...")
        
        # Compile text for this batch size
        compiled_text = ""
        total_chars = 0
        
        for i, desc_file in enumerate(description_files[:batch_size]):
            try:
                with open(desc_file, 'r') as f:
                    content = f.read()
                    compiled_text += f"\n=== CLIP {i+1}: {desc_file.name} ===\n"
                    compiled_text += content + "\n"
                    total_chars += len(content)
            except Exception as e:
                print(f"❌ Error reading {desc_file}: {e}")
                continue
        
        # Create a simple test prompt
        test_prompt = f"""
        You are analyzing {batch_size} GAA match clip descriptions.
        
        Please respond with:
        1. "SUCCESS" if you can process this
        2. Total number of clips you received
        3. Approximate total text length you processed
        
        Here are the clip descriptions:
        {compiled_text}
        
        END OF CLIPS. Please confirm you received all {batch_size} clips.
        """
        
        try:
            print(f"   📝 Text size: {total_chars:,} characters ({total_chars/1024/1024:.1f} MB)")
            print(f"   🔄 Sending to API...")
            
            start_time = time.time()
            response = model.generate_content(test_prompt)
            processing_time = time.time() - start_time
            
            print(f"   ✅ SUCCESS! Processed in {processing_time:.1f}s")
            print(f"   📤 Response: {response.text[:100]}...")
            print()
            
            # If we successfully processed all files, we're done
            if batch_size == len(description_files):
                print(f"🎉 FULL DATASET PROCESSABLE!")
                print(f"✅ Gemini 2.5 can handle all {len(description_files)} clips")
                print(f"📊 Total size: {total_chars:,} characters ({total_chars/1024/1024:.1f} MB)")
                break
                
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)[:100]}...")
            print()
            
            if "context" in str(e).lower() or "length" in str(e).lower() or "token" in str(e).lower():
                print(f"🚫 CONTEXT LIMIT REACHED!")
                print(f"💡 Maximum processable: {test_sizes[test_sizes.index(batch_size)-1] if batch_size > 1 else 0} clips")
                break
            elif "quota" in str(e).lower() or "rate" in str(e).lower():
                print(f"⏸️  Rate limit hit, waiting 60s...")
                time.sleep(60)
                continue
            else:
                print(f"🔄 Other error, continuing...")
                continue
        
        # Small delay between tests
        time.sleep(2)
    
    print(f"\n🏁 Context size test complete!")

if __name__ == "__main__":
    test_context_size() 