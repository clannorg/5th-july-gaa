# GAA Match Video Splitter

Splits full GAA match videos into separate segments based on timeline analysis.

## Features

- **Automatic video splitting** based on timeline JSON
- **Buffer margins** added to each segment (default 30 seconds)
- **Multiple output formats**:
  - First half video
  - Halftime break video
  - Second half video
  - Combined match video (no halftime)
- **Fast processing** using ffmpeg copy (no re-encoding)

## Requirements

- Python 3.6+
- ffmpeg installed and in PATH
- Timeline JSON file from halftime detection

## Usage

### Super Simple (Recommended)
```bash
python run_split.py
```
That's it! The script will:
- ✅ Auto-find your video file
- ✅ Use the timeline from halftime detection
- ✅ Apply 60-second buffer margins
- ✅ Create all output videos

### Manual Usage
```bash
python split_match_video.py                    # Auto-detect video
python split_match_video.py your_video.mp4     # Specify video only
python split_match_video.py timeline.json video.mp4  # Specify both
```

### Examples

**Super simple (just works):**
```bash
python run_split.py
```

**Manual with specific video:**
```bash
python split_match_video.py match.mp4
```

## Output Files

The script creates these files in the `output/` directory:

1. **`01_first_half.mp4`** - First half with buffer margins
2. **`02_halftime_break.mp4`** - Halftime break with buffer margins  
3. **`03_second_half.mp4`** - Second half with buffer margins
4. **`04_combined_match.mp4`** - First + Second half combined (no halftime)

## Timeline Format

The script accepts two JSON formats:

### Format 1: Timeline Object
```json
{
  "timeline": {
    "firstHalf": {
      "start": "00:15",
      "end": "33:00"
    },
    "halftimeBreak": {
      "start": "33:00", 
      "end": "48:45"
    },
    "secondHalf": {
      "start": "48:45",
      "end": "83:00"
    }
  }
}
```

### Format 2: Events Array
```json
{
  "events": [
    {
      "time": 135.0,
      "action": "First Half Start"
    },
    {
      "time": 1980.0,
      "action": "First Half End"
    },
    {
      "time": 2925.0,
      "action": "Second Half Start"
    },
    {
      "time": 4980.0,
      "action": "Second Half End"
    }
  ]
}
```

## Buffer Margins

- **Default**: 60 seconds before and after each segment
- **Purpose**: Ensures no important action is cut off
- **Automatic clipping**: Won't go below 0 or beyond video duration

## Example Timeline

For a GAA match with these timings:
- First Half: 02:15 - 33:00
- Halftime: 33:00 - 48:45  
- Second Half: 48:45 - 83:00

With 60s buffer, the output videos will be:
- First Half: 01:15 - 34:00 (32m 45s)
- Halftime: 32:00 - 49:45 (17m 45s)
- Second Half: 47:45 - 84:00 (36m 15s)

## Troubleshooting

**Video not found:**
- Check the path to your input video file
- Use absolute paths if needed

**Timeline not found:**
- Ensure you've run the halftime detection first
- Check the JSON file path

**ffmpeg errors:**
- Ensure ffmpeg is installed: `ffmpeg -version`
- Check video format compatibility

**No segments extracted:**
- Verify your timeline JSON has the correct format
- Check that timeline events are found in the JSON 