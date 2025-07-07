# 🥅 GAA Kickout Analysis - Clean 2-Script System

Simple, clean approach to GAA kickout detection and analysis.

## 🎯 Overview

**2 Scripts Only:**
1. `1_analyze_clips.py` - Video clips → Text descriptions  
2. `2_synthesize_events.py` - Text descriptions → Timeline JSON

## 🚀 Quick Start

### Step 1: Analyze Video Clips
```bash
python 1_analyze_clips.py
```
- Analyzes first 10 minutes of video clips
- Outputs text descriptions to `results/kickout_analysis/`
- Uses Gemini 2.5 Flash for speed

### Step 2: Create Timeline JSON
```bash
python 2_synthesize_events.py
```
- Synthesizes text descriptions into timeline
- Outputs webapp-ready JSON to `results/webapp_output/kickout_events.json`
- Uses Gemini 2.5 Pro for better synthesis

## 📁 File Structure

```
4-goal-kick-detection/
├── 1_analyze_clips.py          # Video → Text
├── 2_synthesize_events.py      # Text → Timeline
├── results/
│   ├── kickout_analysis/       # Individual text files
│   └── webapp_output/          # Final JSON for webapp
└── README_CLEAN.md             # This file
```

## 🔧 Configuration

Edit these variables in the scripts:
- `TIME_LIMIT_MINUTES = 10` - How many minutes to analyze
- `MAX_WORKERS = 8` - Parallel processing threads

## 📊 Output Format

The final JSON (`kickout_events.json`) contains:
- **events**: List of kickout events with timestamps
- **statistics**: Team performance stats
- **tactical_summary**: AI insights

Perfect for uploading to your webapp!

## 🎯 Next Steps

1. Run both scripts
2. Upload `kickout_events.json` to your webapp
3. View kickout timeline with video sync

Clean, simple, effective! 🚀 