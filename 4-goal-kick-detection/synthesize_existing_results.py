#!/usr/bin/env python3
"""
Quick script to synthesize existing kickout results from descriptions directory
"""

import json
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

def collect_existing_results():
    """Collect all existing kickout results from descriptions directory"""
    results = []
    
    descriptions_dir = Path("4-goal-kick-detection/results/descriptions")
    analysis_files = sorted(descriptions_dir.glob("*.txt"))
    
    print(f"📋 Found {len(analysis_files)} analysis files")
    
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
                
                # Determine half (assuming first half is 0-35 minutes, second half is 35+ minutes)
                half = "first_half" if clip_start_time < 35 * 60 else "second_half"
                
                results.append({
                    'file': file_path.name,
                    'half': half,
                    'clip_start_time': clip_start_time,
                    'timestamp': f"{minutes:02d}:{seconds:02d}",
                    'content': content
                })
                
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
    
    # Sort by time
    results.sort(key=lambda x: x['clip_start_time'])
    
    return results

def synthesize_with_ai(analysis_results):
    """Use AI to synthesize existing results"""
    
    # Filter only successful kickouts
    kickout_results = []
    for result in analysis_results:
        if "KICKOUT: YES" in result['content']:
            kickout_results.append(result)
    
    print(f"🥅 Found {len(kickout_results)} successful kickout detections")
    
    if not kickout_results:
        print("❌ No successful kickouts found")
        return None
    
    # Prepare prompt with kickout results
    all_analyses = ""
    for result in kickout_results:
        all_analyses += f"\n--- {result['half'].upper()} - {result['timestamp']} (starts at {result['clip_start_time']}s) ---\n"
        all_analyses += result['content']
        all_analyses += "\n"
    
    prompt = f"""
You are an expert GAA analyst synthesizing {len(kickout_results)} confirmed kickout detections.

TASK: Create a comprehensive GAA kickout timeline with tactical analysis.

CONFIRMED KICKOUT DATA:
{all_analyses}

OUTPUT FORMAT (JSON):
{{
  "match_info": {{
    "title": "GAA Match - Kickout Analysis",
    "description": "AI-synthesized kickout timeline from confirmed detections",
    "total_kickouts": {len(kickout_results)},
    "analysis_method": "Enhanced AI video analysis",
    "halves_analyzed": ["first_half", "second_half"]
  }},
  "kickouts": [
    {{
      "time": [absolute seconds from match start],
      "half": "first_half" or "second_half",
      "team": "Team A" or "Team B",
      "confidence": [1-10],
      "trigger": "[what caused kickout]",
      "kick_distance": "[Short/Medium/Long]",
      "kick_direction": "[Left/Center/Right]",
      "possession_won_by": "[Team A/Team B/Contested]",
      "possession_location": "[field position]",
      "next_action": "[what happened after]",
      "tactical_context": "[brief description]",
      "exact_contact_time": "[precise timing or N/A]",
      "goalkeeper_jersey": "[color description]"
    }}
  ],
  "statistics": {{
    "total_kickouts": {len(kickout_results)},
    "by_half": {{
      "first_half": [count],
      "second_half": [count]
    }},
    "by_team": {{
      "Team A": [count],
      "Team B": [count]
    }},
    "possession_success": {{
      "team_a_won_own": [count and percentage],
      "team_b_won_own": [count and percentage],
      "contested": [count]
    }}
  }},
  "tactical_insights": {{
    "pressure_periods": ["time periods with multiple kickouts"],
    "most_contested_area": "[field position]",
    "team_strategies": {{
      "Team A": "[tactical approach]",
      "Team B": "[tactical approach]"
    }}
  }}
}}

Extract all kickout data precisely and create comprehensive statistics.
"""
    
    try:
        print(f"🤖 Sending {len(kickout_results)} kickouts to Gemini Flash for synthesis...")
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        print(f"✅ AI synthesis complete!")
        
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

def save_results(kickout_data, output_dir="results/existing_kickout_synthesis"):
    """Save synthesis results"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main JSON
    json_file = output_dir / "kickouts_analysis.json"
    with open(json_file, 'w') as f:
        json.dump(kickout_data, f, indent=2)
    print(f"💾 Main analysis saved: {json_file}")
    
    # Save timeline JSON
    if 'kickouts' in kickout_data:
        timeline_data = {
            "title": "GAA Match - Kickout Timeline",
            "events": kickout_data['kickouts'],
            "statistics": kickout_data.get('statistics', {})
        }
        
        timeline_file = output_dir / "kickout_timeline.json"
        with open(timeline_file, 'w') as f:
            json.dump(timeline_data, f, indent=2)
        print(f"💾 Timeline saved: {timeline_file}")
    
    # Save summary
    summary_file = output_dir / "kickout_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("GAA KICKOUT ANALYSIS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        if 'match_info' in kickout_data:
            f.write(f"Total Kickouts: {kickout_data['match_info'].get('total_kickouts', 0)}\n")
        
        if 'statistics' in kickout_data:
            stats = kickout_data['statistics']
            f.write(f"\nBy Half:\n")
            if 'by_half' in stats:
                f.write(f"  First Half: {stats['by_half'].get('first_half', 0)}\n")
                f.write(f"  Second Half: {stats['by_half'].get('second_half', 0)}\n")
            
            f.write(f"\nBy Team:\n")
            if 'by_team' in stats:
                f.write(f"  Team A: {stats['by_team'].get('Team A', 0)}\n")
                f.write(f"  Team B: {stats['by_team'].get('Team B', 0)}\n")
        
        if 'kickouts' in kickout_data:
            f.write(f"\nKickout Timeline:\n")
            for kickout in kickout_data['kickouts']:
                time_str = f"{kickout['time']//60:02d}:{kickout['time']%60:02d}"
                f.write(f"  {time_str} - {kickout['team']} ({kickout['half']})\n")
    
    print(f"💾 Summary saved: {summary_file}")

def main():
    print("🥅 GAA KICKOUT SYNTHESIS - EXISTING RESULTS")
    print("=" * 60)
    print("Synthesizing existing successful kickout detections")
    print("=" * 60)
    
    # Collect existing results
    print(f"📋 Collecting existing analysis results...")
    analysis_results = collect_existing_results()
    
    if not analysis_results:
        print(f"❌ No analysis results found")
        return
    
    # Synthesize with AI
    print(f"🤖 Starting AI synthesis...")
    kickout_data = synthesize_with_ai(analysis_results)
    
    if not kickout_data:
        print(f"❌ Synthesis failed")
        return
    
    # Save results
    print(f"💾 Saving synthesis results...")
    save_results(kickout_data)
    
    # Summary
    total_kickouts = kickout_data.get('match_info', {}).get('total_kickouts', 0)
    
    print(f"\n🎉 EXISTING KICKOUT SYNTHESIS COMPLETE!")
    print(f"=" * 60)
    print(f"✅ Total kickouts synthesized: {total_kickouts}")
    print(f"📁 Results saved to: results/existing_kickout_synthesis")
    print(f"📊 Ready for visualization!")

if __name__ == "__main__":
    main() 