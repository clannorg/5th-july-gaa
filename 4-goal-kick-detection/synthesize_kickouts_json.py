#!/usr/bin/env python3
"""
AI-Powered GAA Kickout Synthesis
Uses Gemini to intelligently analyze all clip descriptions and create enhanced kickout timeline
"""

import json
import os
import re
from pathlib import Path
import argparse
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

def collect_all_descriptions(clips_dir):
    """Collect all clip descriptions for AI analysis"""
    descriptions = []
    
    analysis_files = sorted(Path(clips_dir).glob("*.txt"))
    
    for file_path in analysis_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract timestamp from filename
            timestamp_match = re.search(r'clip_(\d+)m(\d+)s\.txt', file_path.name)
            if timestamp_match:
                minutes = int(timestamp_match.group(1))
                seconds = int(timestamp_match.group(2))
                clip_start_time = minutes * 60 + seconds
                
                descriptions.append({
                    'file': file_path.name,
                    'clip_start_time': clip_start_time,
                    'timestamp': f"{minutes:02d}:{seconds:02d}",
                    'content': content
                })
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
    
    return descriptions

def ai_synthesize_kickouts(descriptions):
    """Use AI to synthesize all descriptions into enhanced kickout timeline"""
    
    # Prepare massive prompt with all descriptions
    all_descriptions_text = ""
    for desc in descriptions:
        all_descriptions_text += f"\n--- CLIP {desc['timestamp']} (starts at {desc['clip_start_time']}s) ---\n"
        all_descriptions_text += desc['content']
        all_descriptions_text += "\n"
    
    prompt = f"""
You are an expert GAA analyst synthesizing kickout data from {len(descriptions)} video clip analyses.

TASK: Create a comprehensive kickout timeline with enhanced tactical analysis.

ANALYSIS FOCUS:
1. Identify all confirmed official kickouts with precise timing
2. Extract tactical details: possession outcomes, field positions, next actions
3. Identify team performance patterns and momentum shifts
4. Analyze kickout effectiveness and field positioning
5. Detect rapid sequences and pressure periods

CLIP ANALYSES:
{all_descriptions_text}

SYNTHESIS REQUIREMENTS:
For each confirmed kickout, extract:
- Precise absolute timing (clip start time + kick timing within clip)
- Exact contact time (from EXACT_CONTACT_TIME field in descriptions)
- Kicking team (based on goalkeeper jersey colors)
- Trigger event (what caused the kickout)
- Kick quality and direction
- Possession outcome (who won it, where)
- Next action after possession
- Confidence level

ENHANCED OUTPUT FORMAT:
Create a JSON structure with:

{{
  "match_info": {{
    "title": "GAA Match - Enhanced Kickout Analysis",
    "description": "AI-synthesized kickout timeline with tactical insights",
    "total_events": [number],
    "analysis_method": "Enhanced AI video analysis with possession tracking"
  }},
  "events": [
    {{
      "time": [absolute seconds],
      "team": "Team A" or "Team B",
      "action": "Kickout",
      "confidence": [1-10],
      "trigger": "[what caused kickout]",
      "kick_quality": "[Short/Medium/Long]",
      "kick_direction": "[Left/Center/Right]",
      "possession_won_by": "[Team A/Team B/Contested]",
      "possession_location": "[field position]",
      "next_action": "[what happened after]",
      "tactical_context": "[brief tactical description]",
      "exact_contact_time": "[X.X seconds within clip when foot touches ball, or 'N/A' if not visible]"
    }}
  ],
  "tactical_analysis": {{
    "kickout_effectiveness": {{
      "team_a_won_own": [percentage],
      "team_b_won_own": [percentage],
      "contested_kickouts": [count]
    }},
    "field_positioning": {{
      "most_contested_area": "[Left/Center/Right]",
      "average_kickout_distance": "[Short/Medium/Long]"
    }},
    "match_patterns": {{
      "pressure_periods": ["list of time periods with multiple kickouts"],
      "momentum_shifts": ["key kickout sequences that changed possession"],
      "rapid_sequences": ["periods with kickouts within 30 seconds"]
    }},
    "team_performance": {{
      "team_a_kickouts": [count],
      "team_b_kickouts": [count],
      "team_a_possession_rate": "[percentage of kickouts won]",
      "team_b_possession_rate": "[percentage of kickouts won]"
    }}
  }},
  "summary": {{
    "total_goal_kicks": [count],
    "by_team": {{
      "Team A": [count],
      "Team B": [count]
    }},
    "time_range": {{
      "first_kick": "[time]s",
      "last_kick": "[time]s"
    }}
  }}
}}

IMPORTANT NOTES:
- Only include confirmed kickouts (KICKOUT: YES with high confidence)
- Calculate absolute timing precisely (clip start + kick timing)
- Identify teams consistently based on jersey colors described
- Look for patterns across the entire match timeline
- Provide tactical insights based on possession outcomes

Generate the complete JSON analysis:
"""
    
    try:
        print(f"🤖 Sending all {len(descriptions)} descriptions to Gemini for synthesis...")
        print(f"📝 Prompt size: {len(prompt):,} characters")
        
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        
        print(f"✅ AI synthesis complete! Response size: {len(response.text):,} characters")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            return json.loads(json_text)
        else:
            print("❌ Could not extract JSON from AI response")
            return None
            
    except Exception as e:
        print(f"❌ AI synthesis failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='AI-powered synthesis of GAA kickout analysis')
    parser.add_argument('--clips-dir', type=str, required=True, help='Directory containing analyzed clip files')
    parser.add_argument('--output-file', type=str, default='enhanced_kickouts.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    print("🥅 AI-POWERED GAA KICKOUT SYNTHESIS")
    print("=" * 60)
    print("Enhanced tactical analysis with possession tracking")
    print("=" * 60)
    
    clips_dir = Path(args.clips_dir)
    if not clips_dir.exists():
        print(f"❌ Clips directory not found: {clips_dir}")
        return
    
    # Collect all descriptions
    print(f"📋 Collecting descriptions from {clips_dir}...")
    descriptions = collect_all_descriptions(clips_dir)
    
    if not descriptions:
        print(f"❌ No analysis files found in {clips_dir}")
        return
    
    print(f"✅ Collected {len(descriptions)} clip descriptions")
    
    # AI synthesis
    result = ai_synthesize_kickouts(descriptions)
    
    if not result:
        print("❌ Synthesis failed")
        return
    
    # Save results
    output_file = Path(args.output_file)
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Display results
    print(f"\n🎯 SYNTHESIS RESULTS:")
    print(f"📊 Total kickouts: {result.get('match_info', {}).get('total_events', 0)}")
    
    if 'summary' in result:
        summary = result['summary']
        print(f"🔴 Team A: {summary.get('by_team', {}).get('Team A', 0)} kickouts")
        print(f"🔵 Team B: {summary.get('by_team', {}).get('Team B', 0)} kickouts")
    
    if 'tactical_analysis' in result:
        tactical = result['tactical_analysis']
        print(f"\n🎯 TACTICAL INSIGHTS:")
        
        if 'team_performance' in tactical:
            perf = tactical['team_performance']
            print(f"📈 Team A possession rate: {perf.get('team_a_possession_rate', 'N/A')}")
            print(f"📈 Team B possession rate: {perf.get('team_b_possession_rate', 'N/A')}")
        
        if 'match_patterns' in tactical:
            patterns = tactical['match_patterns']
            if patterns.get('pressure_periods'):
                print(f"⚡ Pressure periods: {len(patterns['pressure_periods'])}")
            if patterns.get('rapid_sequences'):
                print(f"🔥 Rapid sequences: {len(patterns['rapid_sequences'])}")
    
    print(f"\n📁 Enhanced analysis saved to: {output_file}")
    print(f"🤖 Powered by Gemini 2.5 Pro tactical analysis!")

if __name__ == "__main__":
    main() 