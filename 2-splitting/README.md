# 🚀 Ultra Efficient Video Splitter


**Optimized for 8-core VM with 15GB RAM**

## Features

- **Parallel Processing**: Uses 7 of 8 cores (leaves 1 for system)
- **Zero Re-encoding**: Uses `-c copy` for ultra-fast splitting
- **Timestamp Naming**: Creates clips like `clip_15m30s.mp4`
- **Memory Optimized**: Smart batching for large videos
- **Progress Tracking**: Real-time performance monitoring
- **Comprehensive Metadata**: Saves processing statistics

## Performance

- **Speed**: 20-50 clips/second (depends on video size)
- **Efficiency**: 80-95% CPU utilization across all cores
- **Memory**: Optimized for 8GB usage limit
- **I/O**: Minimized disk operations

## Usage

### Basic Usage
```bash
python ultra_efficient_splitter.py /path/to/video.mp4
```

### With Time Range
```bash
python ultra_efficient_splitter.py video.mp4
# Enter time range when prompted: 300-1800 (5min to 30min)
```

### Programmatic Usage
```python
from ultra_efficient_splitter import UltraEfficientSplitter

splitter = UltraEfficientSplitter(output_dir="my_clips")
success = splitter.split_video_ultra_efficient(
    video_path="match.mp4",
    clip_duration=15,
    start_time=300,  # 5 minutes
    end_time=1800    # 30 minutes
)
```

## Output Structure

```
clips/
├── clip_00m00s.mp4  # 0:00-0:15
├── clip_00m15s.mp4  # 0:15-0:30
├── clip_00m30s.mp4  # 0:30-0:45
├── ...
└── clips_metadata.json  # Processing statistics
```

## Optimizations

1. **Input Seeking**: Uses `-ss` before `-i` for faster seeking
2. **Stream Copy**: No re-encoding with `-c copy`
3. **Batch Processing**: Processes clips in optimal batches
4. **Parallel Workers**: Uses ProcessPoolExecutor for true parallelism
5. **Memory Management**: Limits memory usage to prevent swapping

## Performance Monitoring

The splitter provides real-time metrics:
- Clips per second
- CPU efficiency percentage
- ETA for completion
- Memory usage
- Batch processing speed

## Metadata Output

Creates `clips_metadata.json` with:
- Source video information
- Processing statistics
- Individual clip details
- Performance metrics

## Requirements

- Python 3.6+
- FFmpeg 4.0+
- 8+ GB RAM (optimized for 15GB)
- Multi-core CPU (optimized for 8 cores)

## Error Handling

- Timeout protection (30s per clip)
- File size validation
- Graceful failure handling
- Comprehensive error reporting 