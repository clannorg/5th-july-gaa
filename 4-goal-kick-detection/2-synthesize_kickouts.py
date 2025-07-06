#!/usr/bin/env python3
"""
2-synthesize_kickouts.py - Synthesize GAA Kickout Analysis Results
Processes analysis results from 1-analyze_clips.py into comprehensive JSON
"""

import json
import os
import re
from pathlib import Path
import argparse
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

def collect_analysis_results(analysis_dir):
    """Collect all analysis results from both halves"""
    results = []
    
    # Process both halves
    for half_name in ['first_half', 'second_half']:
        half_dir = Path(analysis_dir) / half_name
        if not half_dir.exists():
            print(f"⚠️  {half_name} directory not found: {half_dir}")
            continue
        
        analysis_files = sorted(half_dir.glob("*.txt"))
        print(f"📋 Found {len(analysis_files)} analysis files in {half_name}")
        
        for file_path in analysis_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Extract metadata from content
                half_match = re.search(r'HALF: (\w+)', content)
                timestamp_match = re.search(r'TIMESTAMP: (\d+:\d+)', content)
                clip_file_match = re.search(r'CLIP_FILE: (clip_\d+m\d+s\.mp4)', content)
                
                if timestamp_match and clip_file_match:
                    timestamp = timestamp_match.group(1)
                    minutes, seconds = map(int, timestamp.split(':'))
                    clip_start_time = minutes * 60 + seconds
                    
                    results.append({
                        'file': file_path.name,
                        'half': half_name,
                        'clip_start_time': clip_start_time,
                        'timestamp': timestamp,
                        'clip_file': clip_file_match.group(1),
                        'content': content
                    })
                    
            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")
    
    # Sort by time
    results.sort(key=lambda x: x['clip_start_time'])
    
    return results

def synthesize_kickouts_with_ai(analysis_results):
    """Use AI to synthesize all analysis results into comprehensive kickout data"""
    
    # Prepare comprehensive prompt
    all_analyses = ""
    for result in analysis_results:
        all_analyses += f"\n--- {result['half'].upper()} - {result['timestamp']} (starts at {result['clip_start_time']}s) ---\n"
        all_analyses += result['content']
        all_analyses += "\n"
    
    prompt = f"""
You are an expert GAA analyst synthesizing kickout data from {len(analysis_results)} clip analyses across both match halves.

TASK: Create a comprehensive GAA kickout timeline with enhanced tactical analysis.

SYNTHESIS GOALS:
1. Identify all confirmed official kickouts with precise timing
2. Track possession outcomes and field positioning
3. Analyze team performance and tactical patterns
4. Identify momentum shifts and pressure periods
5. Calculate kickout effectiveness statistics

ANALYSIS DATA:
{all_analyses}

SYNTHESIS REQUIREMENTS:
- Only include confirmed kickouts (KICKOUT: YES with confidence ≥7)
- Calculate absolute timing precisely (clip start time + exact contact time)
- Maintain team consistency based on jersey colors
- Track tactical patterns across both halves
- Provide comprehensive match statistics

OUTPUT FORMAT (JSON):
{{
  "match_info": {{
    "title": "GAA Match - Kickout Analysis",
    "description": "AI-synthesized kickout timeline with tactical insights",
    "total_kickouts": [number],
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
    "total_kickouts": [count],
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
    }},
    "kick_analysis": {{
      "short_kicks": [count],
      "medium_kicks": [count],
      "long_kicks": [count],
      "left_direction": [count],
      "center_direction": [count],
      "right_direction": [count]
    }}
  }},
  "tactical_insights": {{
    "pressure_periods": ["time periods with multiple kickouts"],
    "momentum_shifts": ["key sequences that changed possession"],
    "most_contested_area": "[field position]",
    "team_strategies": {{
      "Team A": "[tactical approach description]",
      "Team B": "[tactical approach description]"
    }}
  }},
  "timeline_summary": {{
    "first_kickout": "[time]s",
    "last_kickout": "[time]s",
    "peak_activity_period": "[time range with most kickouts]",
    "average_time_between_kickouts": "[seconds]"
  }}
}}

IMPORTANT:
- Be precise with timing calculations
- Only include high-confidence kickouts (≥7)
- Maintain team identification consistency
- Provide meaningful tactical insights
- Calculate accurate statistics

Generate the complete JSON analysis:
"""
    
    try:
        print(f"🤖 Sending {len(analysis_results)} analyses to Gemini for synthesis...")
        print(f"📝 Prompt size: {len(prompt):,} characters")
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        print(f"✅ AI synthesis complete! Response size: {len(response.text):,} characters")
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            return json.loads(json_text)
        else:
            print("❌ Could not extract JSON from AI response")
            print("Raw response:", response.text[:500] + "...")
            return None
            
    except Exception as e:
        print(f"❌ AI synthesis failed: {e}")
        return None

def save_results(kickout_data, output_dir):
    """Save synthesis results in multiple formats"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main JSON
    json_file = output_dir / "kickouts_analysis.json"
    with open(json_file, 'w') as f:
        json.dump(kickout_data, f, indent=2)
    print(f"💾 Main analysis saved: {json_file}")
    
    # Save timeline-only JSON (for web display)
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
    
    # Save summary report
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
    parser = argparse.ArgumentParser(description='Synthesize GAA kickout analysis results')
    parser.add_argument('--analysis-dir', type=str, default='results/kickout_analysis',
                       help='Directory containing analysis results from 1-analyze_clips.py')
    parser.add_argument('--output-dir', type=str, default='results/kickout_synthesis',
                       help='Output directory for synthesis results')
    
    args = parser.parse_args()
    
    print("🥅 GAA KICKOUT SYNTHESIS")
    print("=" * 60)
    print("Synthesizing kickout analysis into comprehensive timeline")
    print(f"Analysis directory: {args.analysis_dir}")
    print("=" * 60)
    
    analysis_dir = Path(args.analysis_dir)
    if not analysis_dir.exists():
        print(f"❌ Analysis directory not found: {analysis_dir}")
        return
    
    # Collect all analysis results
    print(f"📋 Collecting analysis results...")
    analysis_results = collect_analysis_results(analysis_dir)
    
    if not analysis_results:
        print(f"❌ No analysis results found in {analysis_dir}")
        return
    
    print(f"📊 Found {len(analysis_results)} analysis files")
    
    # Synthesize with AI
    print(f"🤖 Starting AI synthesis...")
    kickout_data = synthesize_kickouts_with_ai(analysis_results)
    
    if not kickout_data:
        print(f"❌ Synthesis failed")
        return
    
    # Save results
    print(f"💾 Saving synthesis results...")
    save_results(kickout_data, args.output_dir)
    
    # Summary
    total_kickouts = kickout_data.get('match_info', {}).get('total_kickouts', 0)
    
    print(f"\n🎉 KICKOUT SYNTHESIS COMPLETE!")
    print(f"=" * 60)
    print(f"✅ Total kickouts identified: {total_kickouts}")
    print(f"📁 Results saved to: {args.output_dir}")
    print(f"📊 Ready for visualization and analysis!")

if __name__ == "__main__":
    main() 