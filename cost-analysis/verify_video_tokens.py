#!/usr/bin/env python3
"""
Verify Video Token Calculation Formula
Tests the official formula: 263 tokens/second for video + 32 tokens/second for audio
"""

import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

def verify_video_token_formula(clip_path, model_name="gemini-2.5-flash"):
    """Verify the official video token calculation formula"""
    
    print(f"🧪 VERIFYING VIDEO TOKEN FORMULA")
    print(f"Model: {model_name}")
    print(f"Clip: {clip_path}")
    print("=" * 60)
    
    # Official formula from Google documentation
    clip_duration_seconds = 15
    expected_video_tokens = clip_duration_seconds * 263  # 263 tokens/second
    expected_audio_tokens = clip_duration_seconds * 32   # 32 tokens/second
    expected_media_tokens = expected_video_tokens + expected_audio_tokens
    
    print(f"📐 EXPECTED TOKEN CALCULATION:")
    print(f"Video: {clip_duration_seconds}s × 263 tokens/s = {expected_video_tokens:,} tokens")
    print(f"Audio: {clip_duration_seconds}s × 32 tokens/s = {expected_audio_tokens:,} tokens")
    print(f"Total media: {expected_media_tokens:,} tokens")
    print()
    
    try:
        # Upload the video clip
        print(f"📹 Uploading clip...")
        video_file = genai.upload_file(path=clip_path)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            print("⏳ Processing video...")
            time.sleep(1)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed")
        
        # Simple prompt to minimize text token variation
        prompt = "Describe what you see in this video clip in one sentence."
        
        # Generate analysis and capture usage metadata
        model = genai.GenerativeModel(model_name)
        print("🤖 Generating analysis...")
        
        response = model.generate_content([video_file, prompt])
        
        # Get actual token usage from API
        usage = response.usage_metadata
        actual_input_tokens = usage.prompt_token_count
        actual_output_tokens = usage.candidates_token_count
        actual_total_tokens = usage.total_token_count
        
        print(f"📊 ACTUAL API USAGE:")
        print(f"Input tokens: {actual_input_tokens:,}")
        print(f"Output tokens: {actual_output_tokens:,}")
        print(f"Total tokens: {actual_total_tokens:,}")
        print()
        
        # Calculate text tokens (prompt only)
        text_tokens = model.count_tokens(prompt).total_tokens
        estimated_media_tokens = actual_input_tokens - text_tokens
        
        print(f"🔍 TOKEN BREAKDOWN:")
        print(f"Text prompt: {text_tokens:,} tokens")
        print(f"Media (video+audio): {estimated_media_tokens:,} tokens")
        print(f"Output: {actual_output_tokens:,} tokens")
        print()
        
        # Compare with formula
        print(f"📐 FORMULA VERIFICATION:")
        print(f"Expected media tokens: {expected_media_tokens:,}")
        print(f"Actual media tokens: {estimated_media_tokens:,}")
        
        if abs(expected_media_tokens - estimated_media_tokens) <= 10:  # Allow small variance
            print(f"✅ FORMULA CONFIRMED! Difference: {abs(expected_media_tokens - estimated_media_tokens)} tokens")
        else:
            print(f"❌ Formula mismatch. Difference: {abs(expected_media_tokens - estimated_media_tokens)} tokens")
        
        print()
        
        # Calculate real costs with all models
        models_pricing = {
            "gemini-2.5-flash": {"input": 0.0003, "output": 0.0025, "name": "Gemini 2.5 Flash"},
            "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004, "name": "Gemini 2.0 Flash"},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003, "name": "Gemini 1.5 Flash"}
        }
        
        print(f"💰 REAL COST CALCULATION (per 15s clip):")
        print("-" * 50)
        
        for model_key, pricing in models_pricing.items():
            input_cost = (actual_input_tokens * pricing["input"]) / 1000000
            output_cost = (actual_output_tokens * pricing["output"]) / 1000000
            total_cost = input_cost + output_cost
            
            print(f"{pricing['name']:20} | ${total_cost:.8f}")
        
        print()
        
        # Full match calculation
        total_clips = 336  # 84 minutes × 4 clips/minute
        
        print(f"🏈 FULL MATCH COSTS (84 min = {total_clips} clips):")
        print("-" * 50)
        
        for model_key, pricing in models_pricing.items():
            clip_input_cost = (actual_input_tokens * pricing["input"]) / 1000000
            clip_output_cost = (actual_output_tokens * pricing["output"]) / 1000000
            clip_total_cost = clip_input_cost + clip_output_cost
            
            match_clip_cost = clip_total_cost * total_clips
            
            # Add synthesis cost (estimated)
            synthesis_input = 250000
            synthesis_output = 1000
            synthesis_cost = ((synthesis_input * pricing["input"]) + (synthesis_output * pricing["output"])) / 1000000
            
            total_match_cost = match_clip_cost + synthesis_cost
            
            print(f"{pricing['name']:20} | ${total_match_cost:.6f}")
        
        # Show sample analysis
        print(f"\n📝 Analysis sample:")
        print(f'"{response.text}"')
        
        # Cleanup
        genai.delete_file(video_file.name)
        
        return {
            "expected_media_tokens": expected_media_tokens,
            "actual_media_tokens": estimated_media_tokens,
            "actual_input_tokens": actual_input_tokens,
            "actual_output_tokens": actual_output_tokens,
            "formula_verified": abs(expected_media_tokens - estimated_media_tokens) <= 10
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🎯 VIDEO TOKEN FORMULA VERIFICATION")
    print("=" * 60)
    print("Testing: 263 tokens/second video + 32 tokens/second audio")
    print("Official source: Google AI Developers Forum")
    print()
    
    # Test clip
    clip_path = "/home/ubuntu/5th-july-gaa/clips/clip_00m00s.mp4"
    
    if not os.path.exists(clip_path):
        print(f"❌ Clip not found: {clip_path}")
        return
    
    # Test with Gemini 2.5 Flash (most detailed usage metadata)
    result = verify_video_token_formula(clip_path, "gemini-2.5-flash")
    
    if result and result["formula_verified"]:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Video token formula confirmed: 263 tokens/second")
        print(f"✅ Audio token formula confirmed: 32 tokens/second")
        print(f"✅ Total media tokens: {result['expected_media_tokens']:,}")
        print(f"✅ GAA analysis costs are now completely predictable!")
    else:
        print(f"\n❌ Formula verification failed or error occurred")

if __name__ == "__main__":
    main() 