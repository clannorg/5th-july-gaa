# 🥅 Goal Kick Detection System

AI-powered detection of goal kicks and scoring attempts in GAA football matches.

## 📋 Overview

This system analyzes 15-second video clips to identify:
- **Official Kickouts**: Ball going wide/over goal, goalkeeper restarts
- **Scoring Attempts**: Shots at goal (successful/unsuccessful)
- **Goalkeeper Activity**: Saves, clearances, goal kicks
- **Team Performance**: Which team has more goal kicks against them

## 🚀 Quick Start

### 1. Analyze Video Clips
```bash
python analyze_clips.py --clips-dir ../clips --output-dir results/descriptions
```

### 2. Synthesize Goal Kick Patterns
```bash
python synthesize_kickouts_json.py --input-dir results/descriptions --output-file results/goal_kicks.json
```

### 3. Generate Web Export
```bash
python export_web_json.py --input-file results/goal_kicks.json --output-dir web_exports
```

## 📁 Directory Structure

```
4-goal-kick-detection/
├── analyze_clips.py              # Step 1: Analyze individual clips
├── synthesize_kickouts_json.py   # Step 2: Find goal kick patterns
├── filter_true_kickouts.py       # Step 3: Filter official kickouts
├── export_web_json.py            # Step 4: Export for web visualization
├── analyze_halftime.py           # Halftime analysis integration
├── run_complete_analysis.py      # Complete pipeline runner
├── results/
│   ├── descriptions/             # Individual clip descriptions
│   ├── goal_kicks.json          # Detected goal kicks
│   ├── true_kickouts.json       # Filtered official kickouts
│   └── web_exports/             # Web visualization files
└── README.md                     # This file
```

## 🎯 Detection Criteria

### Official Kickouts
- Ball has gone **OUT OF PLAY** (wide shot, over goal line, or saved)
- Play has **STOPPED** completely
- Goalkeeper places ball on **GROUND** in goal area
- All outfield players are **POSITIONED AWAY** from goal area
- Players are **SPREAD OUT** across field waiting for restart
- Goalkeeper kicks ball from **STATIONARY** position on ground

### NOT Detected
- Goalkeeper clearances during active play
- Goalkeeper kicks from hands during play
- Quick kicks or punts during active play
- Any kick when play hasn't stopped
- Kicks when players are still near goal area

## 🏐 GAA-Specific Features

### Team Identification
- **Cork Team**: Yellow/amber jersey goalkeeper
- **Kerry Team**: White/grey jersey goalkeeper

### Event Categories
- **MISSED SHOTS**: Ball goes wide/over from scoring attempt
- **GOALKEEPER CLEARANCES**: Goalkeeper kicks ball out from goal area
- **DEFENSIVE CLEARANCES**: Ball kicked out by defenders near goal
- **RESTART SITUATIONS**: Goal kicks following stoppages

## 📊 Output Formats

### JSON Results
- **goal_kicks.json**: All detected goal kick events
- **true_kickouts.json**: Filtered official kickouts only
- **web_timeline.json**: Timeline format for web visualization
- **web_stats.json**: Statistics and team performance

### Analysis Files
- **Individual descriptions**: Natural language analysis per clip
- **Pattern synthesis**: Comprehensive goal kick timeline
- **Halftime analysis**: Integration with match periods

## 🔧 Configuration

### Environment Setup
```bash
export GEMINI_API_KEY='your_api_key_here'
```

### Performance Tuning
- **Threads**: Adjust parallel processing (default: 200)
- **Clip Range**: Process specific time ranges
- **Confidence Filtering**: Adjust detection sensitivity

## 📈 Performance Metrics

- **Processing Speed**: ~5.5 clips/second with 200 threads
- **Analysis Time**: ~1-2 minutes for full match (337 clips)
- **AI Model**: Gemini 2.5 Pro for superior sports understanding
- **Accuracy**: Temporal logic validation prevents false positives

## 🔄 Integration

This system integrates with:
- **Match Timeline**: Uses periods from `../3-half-start-end/`
- **Video Clips**: Processes clips from `../clips/`
- **Web Visualization**: Exports data for web dashboards

## 🎯 Use Cases

- **Match Analysis**: Identify scoring opportunities and defensive performance
- **Goalkeeper Stats**: Track saves, clearances, and goal kicks
- **Team Performance**: Compare goal kick frequency between teams
- **Tactical Analysis**: Understand when teams are under pressure

Perfect for detailed GAA match analysis and performance tracking! 🏐 