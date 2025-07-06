#!/usr/bin/env python3
"""
Extract GAA Match Events from Analysis Results
Creates a clean JSON file with all match events and timeline
"""

import json
import re
from pathlib import Path
from datetime import datetime

def parse_synthesis_results(results_file):
    """Parse the synthesis results and extract key events"""
    
    with open(results_file, 'r') as f:
        content = f.read()
    
    # Extract the key transitions section
    key_transitions_match = re.search(r'KEY TRANSITIONS:(.*?)TIMELINE VERIFICATION:', content, re.DOTALL)
    if not key_transitions_match:
        print("❌ Could not find KEY TRANSITIONS section")
        return None
    
    key_transitions_text = key_transitions_match.group(1)
    
    # Parse individual transitions
    events = []
    
    # Parse First Half Start
    first_half_start = re.search(r'FIRST HALF START: (\d+:\d+)', key_transitions_text)
    if first_half_start:
        events.append({
            "event": "first_half_start",
            "timestamp": first_half_start.group(1),
            "description": "First half begins - Official throw-in ceremony",
            "type": "match_transition"
        })
    
    # Parse First Half End
    first_half_end = re.search(r'FIRST HALF END: (\d+:\d+)', key_transitions_text)
    if first_half_end:
        events.append({
            "event": "first_half_end", 
            "timestamp": first_half_end.group(1),
            "description": "First half ends - Transition to halftime break",
            "type": "match_transition"
        })
    
    # Parse Second Half Start
    second_half_start = re.search(r'SECOND HALF START: (\d+:\d+)', key_transitions_text)
    if second_half_start:
        events.append({
            "event": "second_half_start",
            "timestamp": second_half_start.group(1), 
            "description": "Second half begins - Official throw-in ceremony after halftime",
            "type": "match_transition"
        })
    
    # Parse Match End
    match_end = re.search(r'MATCH END: (\d+:\d+)', key_transitions_text)
    if match_end:
        events.append({
            "event": "match_end",
            "timestamp": match_end.group(1),
            "description": "Match ends - Players leave field",
            "type": "match_transition"
        })
    
    # Extract timeline verification
    timeline_match = re.search(r'TIMELINE VERIFICATION:(.*?)$', content, re.DOTALL)
    timeline_info = {}
    
    if timeline_match:
        timeline_text = timeline_match.group(1)
        
        # Parse durations
        first_half_duration = re.search(r'First Half Duration: (\d+) minutes', timeline_text)
        halftime_duration = re.search(r'Halftime Break: (\d+) minutes', timeline_text)
        second_half_duration = re.search(r'Second Half Duration: (\d+) minutes', timeline_text)
        
        if first_half_duration:
            timeline_info['first_half_duration_minutes'] = int(first_half_duration.group(1))
        if halftime_duration:
            timeline_info['halftime_duration_minutes'] = int(halftime_duration.group(1))
        if second_half_duration:
            timeline_info['second_half_duration_minutes'] = int(second_half_duration.group(1))
    
    # Extract block summary
    block_summary_match = re.search(r'BLOCK SUMMARY:(.*?)KEY TRANSITIONS:', content, re.DOTALL)
    blocks = []
    
    if block_summary_match:
        block_text = block_summary_match.group(1)
        block_lines = [line.strip() for line in block_text.split('\n') if line.strip() and line.startswith('Block')]
        
        for line in block_lines:
            # Parse: Block 1: PRE-MATCH (00:00 - 04:44)
            block_match = re.search(r'Block (\d+): ([A-Z\s]+) \((\d+:\d+) - (\d+:\d+)\)(.*)', line)
            if block_match:
                block_num = int(block_match.group(1))
                block_type = block_match.group(2).strip()
                start_time = block_match.group(3)
                end_time = block_match.group(4)
                extra_info = block_match.group(5).strip()
                
                blocks.append({
                    "block_number": block_num,
                    "type": block_type.lower().replace(' ', '_'),
                    "start_time": start_time,
                    "end_time": end_time,
                    "extra_info": extra_info.strip('[]') if extra_info else None
                })
    
    return {
        "events": events,
        "timeline": timeline_info,
        "blocks": blocks
    }

def create_comprehensive_match_json():
    """Create a comprehensive match analysis JSON file"""
    
    # Input file (now relative to 3-half-start-end directory)
    results_file = Path("results/halftime_detection/single_request_analysis.txt")
    
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        return
    
    print("🔍 Parsing synthesis results...")
    match_data = parse_synthesis_results(results_file)
    
    if not match_data:
        print("❌ Failed to parse results")
        return
    
    # Create comprehensive match structure
    match_json = {
        "match_analysis": {
            "generated_at": datetime.now().isoformat(),
            "source": "GAA Video Analysis Pipeline",
            "model": "Gemini 2.5 Flash",
            "video_duration": "84:00",
            "clips_analyzed": 337,
            "analysis_type": "halftime_detection"
        },
        "match_structure": {
            "blocks": match_data["blocks"],
            "timeline_summary": match_data["timeline"]
        },
        "key_events": match_data["events"],
        "match_timeline": {
            "pre_match": {
                "start": "00:00",
                "end": None,
                "description": "Pre-match warm-up and preparation"
            },
            "first_half": {
                "start": None,
                "end": None, 
                "duration_minutes": match_data["timeline"].get("first_half_duration_minutes"),
                "description": "First half competitive play"
            },
            "halftime": {
                "start": None,
                "end": None,
                "duration_minutes": match_data["timeline"].get("halftime_duration_minutes"),
                "description": "Halftime break with casual warm-up"
            },
            "second_half": {
                "start": None,
                "end": None,
                "duration_minutes": match_data["timeline"].get("second_half_duration_minutes"),
                "description": "Second half competitive play"
            },
            "post_match": {
                "start": None,
                "end": "84:00",
                "description": "Post-match conclusion"
            }
        }
    }
    
    # Fill in timeline timestamps from events
    for event in match_data["events"]:
        if event["event"] == "first_half_start":
            match_json["match_timeline"]["first_half"]["start"] = event["timestamp"]
            # Pre-match ends when first half starts
            match_json["match_timeline"]["pre_match"]["end"] = event["timestamp"]
        elif event["event"] == "first_half_end":
            match_json["match_timeline"]["first_half"]["end"] = event["timestamp"]
            match_json["match_timeline"]["halftime"]["start"] = event["timestamp"]
        elif event["event"] == "second_half_start":
            match_json["match_timeline"]["halftime"]["end"] = event["timestamp"]
            match_json["match_timeline"]["second_half"]["start"] = event["timestamp"]
        elif event["event"] == "match_end":
            match_json["match_timeline"]["second_half"]["end"] = event["timestamp"]
            match_json["match_timeline"]["post_match"]["start"] = event["timestamp"]
    
    # Output file (save in results directory)
    output_file = Path("results/halftime_detection/match_events.json")
    
    print(f"💾 Writing comprehensive match data to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(match_json, f, indent=2)
    
    print(f"✅ Match events saved to: {output_file}")
    
    # Print summary
    print(f"\n📊 MATCH ANALYSIS SUMMARY:")
    print(f"=" * 50)
    print(f"🎬 Video Duration: 84:00")
    print(f"📹 Clips Analyzed: 337")
    print(f"🤖 Model: Gemini 2.5 Flash")
    print(f"\n🏈 KEY EVENTS:")
    for event in match_data["events"]:
        print(f"  {event['timestamp']} - {event['description']}")
    
    print(f"\n⏱️  MATCH TIMELINE:")
    for period, info in match_json["match_timeline"].items():
        if info["start"] and info["end"]:
            duration = info.get("duration_minutes", "?")
            print(f"  {period.replace('_', ' ').title()}: {info['start']} - {info['end']} ({duration} min)")
    
    return output_file

def main():
    print("🎯 GAA MATCH EVENTS EXTRACTOR")
    print("=" * 50)
    print("Creating comprehensive match events JSON file...")
    print()
    
    output_file = create_comprehensive_match_json()
    
    if output_file:
        print(f"\n🎉 SUCCESS!")
        print(f"📁 All match events saved to: {output_file}")
        print(f"🔗 This JSON can be consumed by your web application")

if __name__ == "__main__":
    main() 