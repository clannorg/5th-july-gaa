# 🏐 5th July GAA Analysis Pipeline

Complete pipeline for analyzing GAA (Gaelic Football) matches with AI-powered video analysis.

## 🎯 Pipeline Overview

```
📥 1. VEO DOWNLOAD  →  ✂️ 2. VIDEO SPLITTING  →  🕐 3. HALF DETECTION  →  🥅 4. GOAL KICK DETECTION
   Download video      Split into 15s clips     Find match periods     Detect goal kicks
```

## 📁 Directory Structure

```
5th-july-gaa/
├── 1-veo-download/
│   ├── veo_downloader.py      # Download videos from Veo URLs
│   └── downloads/             # Downloaded videos
├── 2-splitting/
│   ├── clip_splitter.py       # Split videos into 15s clips
│   └── clips/                 # Generated video clips
├── 3-half-start-end/
│   ├── analyze_clips.py       # Analyze clips for match periods
│   ├── synthesize_patterns.py # Find halftime patterns
│   └── results/               # Timeline analysis results
├── 4-goal-kick-detection/
│   ├── analyze_clips.py       # Analyze clips for goal kicks
│   ├── synthesize_kickouts_json.py # Find goal kick patterns
│   ├── filter_true_kickouts.py # Filter official kickouts
│   ├── export_web_json.py     # Export for web visualization
│   └── results/               # Goal kick analysis results
└── run_pipeline.py            # Master pipeline script
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with required packages:
   ```bash
   pip install requests google-generativeai pathlib
   ```

2. **FFmpeg** for video processing:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

3. **Gemini API Key**:
   ```bash
   export GEMINI_API_KEY='your_api_key_here'
   ```

### Run Complete Pipeline

```bash
cd 5th-july-gaa
python run_pipeline.py
```

### Run Individual Steps

```bash
# Step 1: Download video
python 1-veo-download/veo_downloader.py

# Step 2: Split into clips
python 2-splitting/clip_splitter.py path/to/video.mp4

# Step 3A: Analyze clips
python 3-half-start-end/analyze_all_clips.py clips/

# Step 3B: Detect throw-ins
python 3-half-start-end/detect_throw_ins.py analysis/clip_descriptions.json
```

## 📋 Detailed Usage

### 1. VEO Download (`veo_downloader.py`)

Downloads GAA match videos from Veo platform URLs.

**Features:**
- Progress tracking with speed indicators
- Automatic filename generation
- Overwrite protection
- Error handling and retry logic

**Usage:**
```bash
python veo_downloader.py [URL]
# or run interactively
python veo_downloader.py
```

### 2. Video Splitting (`clip_splitter.py`)

Splits videos into 15-second clips for analysis.

**Features:**
- Configurable clip duration (default: 15 seconds)
- Time range selection
- Progress tracking
- Metadata generation
- Fast copy mode (no re-encoding)

**Usage:**
```bash
python clip_splitter.py video.mp4
# or with time range
python clip_splitter.py video.mp4
# Then enter: 0-1800 (first 30 minutes)
```

### 3A. Clip Analysis (`analyze_all_clips.py`)

Analyzes video clips using Gemini AI to generate detailed descriptions.

**Features:**
- Parallel processing (configurable workers)
- Comprehensive GAA-specific analysis
- Progress tracking
- Error handling and retry
- Detailed JSON output

**Analysis Focus:**
- Key events (goals, points, fouls, restarts)
- Player actions and movements
- Ball trajectory and possession
- Team identification by jersey colors
- Specific moments (throw-ins, kickouts, scores)

### 3B. Throw-in Detection (`detect_throw_ins.py`)

Analyzes clip descriptions to detect exactly when throw-ins occur.

**Features:**
- AI-powered pattern recognition
- Confidence scoring
- Team identification
- Validation and enhancement
- Timeline generation

**Detection Criteria:**
- Ball going out of bounds
- Sideline restarts
- Player throwing ball back into play
- Team positioning for throw-ins

## 📊 Output Files

### Downloads
- `downloads/gaa_match_YYYYMMDD_HHMMSS.mp4` - Downloaded video

### Clips
- `clips/clip_001_0000.mp4` - Individual 15-second clips
- `clips/clips_metadata.json` - Clip information and timestamps

### Analysis
- `analysis/clip_analysis_results.json` - Complete analysis results
- `analysis/clip_descriptions.json` - Simplified descriptions for throw-in detection

### Throw-in Detection
- `throw_ins/throw_in_detections.json` - Detailed throw-in events
- `throw_ins/throw_in_timeline.txt` - Human-readable timeline

## 🔧 Configuration

### Environment Variables
```bash
export GEMINI_API_KEY='your_api_key'        # Required for AI analysis
export MAX_WORKERS=3                        # Parallel processing (optional)
```

### Customization
- Modify clip duration in `clip_splitter.py`
- Adjust analysis prompts in `analyze_all_clips.py`
- Change throw-in detection criteria in `detect_throw_ins.py`

## 🏐 GAA-Specific Features

### Team Identification
- Automatic jersey color recognition
- Cork vs Kerry identification
- Team-specific statistics

### Event Detection
- **Throw-ins**: Sideline restarts
- **Kickouts**: Goalkeeper restarts
- **Scores**: Points and goals
- **Fouls**: Free kicks and cards

### Analysis Depth
- Player positioning and movement
- Ball trajectory analysis
- Game context understanding
- Tactical situation recognition

## 🚨 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   sudo apt install ffmpeg  # Ubuntu
   brew install ffmpeg      # macOS
   ```

2. **Gemini API errors**
   ```bash
   export GEMINI_API_KEY='your_key'
   ```

3. **Memory issues with large videos**
   - Process in smaller time ranges
   - Reduce parallel workers
   - Use faster storage

4. **Slow analysis**
   - Reduce clip count
   - Increase worker count
   - Use faster internet connection

## 📈 Performance Tips

- Use SSD storage for faster video processing
- Set appropriate worker count (3-5 for most systems)
- Process videos in chunks for very long matches
- Use time ranges to focus on specific periods

## 🎯 Use Cases

- **Match Analysis**: Detailed breakdown of game events
- **Coaching**: Identify tactical patterns and player performance
- **Statistics**: Generate throw-in, kickout, and scoring statistics
- **Research**: Study GAA gameplay patterns and trends

## 📝 Example Output

```json
{
  "throw_ins": [
    {
      "timestamp": "15:30",
      "team": "Cork (red/black)",
      "confidence": "high",
      "evidence": "ball goes out over sideline, player throws back",
      "description": "Cork throw-in from right sideline"
    }
  ]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**🏐 Ready to analyze your GAA matches!** 

Run `python run_pipeline.py` to get started. 