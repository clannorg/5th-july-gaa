#!/usr/bin/env python3
"""
Convert Enhanced Kickouts JSON to Website Format
Uses Gemini AI to intelligently transform rich tactical data to simple website format
"""

import json
import argparse
import sys
from pathlib import Path
import google.generativeai as genai
import os

def setup_gemini():
    """Setup Gemini API"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-exp')

def load_enhanced_json(file_path):
    """Load the enhanced kickouts JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        sys.exit(1)

def create_conversion_prompt(enhanced_data):
    """Create prompt for Gemini to convert to website format"""
    
    prompt = f"""
You are converting a detailed GAA kickout analysis to a simple website format.

INPUT DATA:
{json.dumps(enhanced_data, indent=2)}

REQUIRED OUTPUT FORMAT:
{{
  "match_info": {{
    "title": "GAA Match - Goal Kicks (Precise Timing)",
    "description": "Goal kicks detected with exact timing when goalkeeper strikes ball",
    "total_events": [NUMBER],
    "analysis_method": "AI video analysis with precise timing"
  }},
  "events": [
    {{
      "time": [TIME_IN_SECONDS],
      "team": "Team A" or "Team B",
      "action": "Kickout",
      "outcome": "N/A",
      "confidence": [0.0-1.0],
      "validated": false
    }}
  ],
  "summary": {{
    "total_goal_kicks": [NUMBER],
    "by_team": {{
      "Team A": [COUNT],
      "Team B": [COUNT]
    }},
    "time_range": {{
      "first_kick": "[TIME]s",
      "last_kick": "[TIME]s"
    }}
  }}
}}

CONVERSION RULES:
1. Convert each event from enhanced format to simple website format
2. Keep exact time values (don't round)
3. Convert confidence (1-10) to decimal (0.1-1.0): confidence/10
4. Set all outcomes to "N/A" 
5. Set all validated to false
6. Preserve team names exactly ("Team A", "Team B")
7. Count total events and by-team breakdown
8. Find first and last kick times

OUTPUT ONLY THE JSON - NO EXPLANATIONS OR MARKDOWN.
"""
    
    return prompt

def convert_with_gemini(model, enhanced_data):
    """Use Gemini to convert the data"""
    prompt = create_conversion_prompt(enhanced_data)
    
    try:
        print("Converting enhanced JSON to website format...")
        response = model.generate_content(prompt)
        
        # Clean the response (remove markdown code blocks if present)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove ```
        response_text = response_text.strip()
        
        # Parse the JSON response
        website_data = json.loads(response_text)
        return website_data
        
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini response as JSON: {e}")
        print(f"Response: {response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        sys.exit(1)

def save_website_json(data, output_path):
    """Save the website format JSON"""
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Website JSON saved to: {output_path}")
    except Exception as e:
        print(f"Error saving {output_path}: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Convert enhanced kickouts JSON to website format')
    parser.add_argument('--input', '-i', 
                       default='results/enhanced_kickouts.json',
                       help='Input enhanced JSON file')
    parser.add_argument('--output', '-o',
                       default='results/website_kickouts.json', 
                       help='Output website JSON file')
    
    args = parser.parse_args()
    
    # Setup
    model = setup_gemini()
    
    # Load enhanced data
    print(f"Loading enhanced JSON from: {args.input}")
    enhanced_data = load_enhanced_json(args.input)
    print(f"Loaded {enhanced_data['match_info']['total_events']} events")
    
    # Convert using Gemini
    website_data = convert_with_gemini(model, enhanced_data)
    
    # Save result
    save_website_json(website_data, args.output)
    
    # Summary
    print(f"\n📊 CONVERSION SUMMARY:")
    print(f"Enhanced events: {enhanced_data['match_info']['total_events']}")
    print(f"Website events: {website_data['match_info']['total_events']}")
    print(f"Team A: {website_data['summary']['by_team']['Team A']}")
    print(f"Team B: {website_data['summary']['by_team']['Team B']}")
    print(f"Time range: {website_data['summary']['time_range']['first_kick']} - {website_data['summary']['time_range']['last_kick']}")

if __name__ == "__main__":
    main() 