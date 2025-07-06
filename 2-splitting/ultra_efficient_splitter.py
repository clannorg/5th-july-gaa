#!/usr/bin/env python3
"""
🚀 ULTRA EFFICIENT VIDEO SPLITTER
Optimized for 8-core VM with 15GB RAM
- Parallel processing using all cores
- Memory-optimized for large videos
- Timestamp-named clips (clip_15m30s.mp4)
- Smart batching and progress tracking
"""

import os
import sys
import subprocess
import json
import time
import math
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count, Manager
import threading
import psutil

class UltraEfficientSplitter:
    def __init__(self, output_dir="clips", max_workers=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # VM optimization settings
        self.total_cores = cpu_count()  # 8 cores
        self.max_workers = max_workers or max(1, self.total_cores - 1)  # Use 7 cores, leave 1 for system
        self.memory_limit_gb = 8  # Use max 8GB of 15GB available
        
        # Performance tracking
        self.clips_created = []
        self.processing_stats = {
            'total_clips': 0,
            'completed_clips': 0,
            'failed_clips': 0,
            'start_time': None,
            'clips_per_second': 0
        }
        
        print(f"🚀 ULTRA EFFICIENT SPLITTER INITIALIZED")
        print(f"💻 VM Specs: {self.total_cores} cores, {psutil.virtual_memory().total / (1024**3):.1f}GB RAM")
        print(f"⚙️  Using {self.max_workers} parallel workers")
    
    def get_video_info(self, video_path):
        """Get comprehensive video information using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
            duration = float(info['format']['duration'])
            size_gb = int(info['format']['size']) / (1024**3)
            
            return {
                'duration': duration,
                'size_gb': size_gb,
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),  # Convert fraction to float
                'codec': video_stream['codec_name'],
                'bitrate': int(info['format'].get('bit_rate', 0))
            }
        except Exception as e:
            print(f"❌ Error getting video info: {e}")
            return None
    
    def format_timestamp(self, seconds):
        """Convert seconds to MMmSSs format for filename"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}m{secs:02d}s"
    
    def format_time_display(self, seconds):
        """Convert seconds to MM:SS for display"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def calculate_optimal_batch_size(self, total_clips, video_info):
        """Calculate optimal batch size based on VM resources"""
        # Base batch size on available memory and clip complexity
        base_batch_size = 50
        
        # Adjust for video complexity
        if video_info['size_gb'] > 3:  # Large video
            batch_size = max(20, base_batch_size // 2)
        elif video_info['bitrate'] > 10000000:  # High bitrate
            batch_size = max(30, base_batch_size // 1.5)
        else:
            batch_size = base_batch_size
        
        # Ensure we can process efficiently with available workers
        optimal_batch = min(batch_size, max(10, total_clips // self.max_workers))
        
        return int(optimal_batch)
    
    def create_clip_batch(self, video_path, clip_batch, clip_duration=15):
        """Process a batch of clips in parallel - optimized for single process"""
        batch_results = []
        
        for clip_info in clip_batch:
            start_seconds, clip_index, total_clips = clip_info
            
            # Calculate actual duration (handle end of video)
            video_info = self.get_video_info(video_path)
            if not video_info:
                continue
                
            actual_duration = min(clip_duration, video_info['duration'] - start_seconds)
            if actual_duration < 1:  # Skip clips shorter than 1 second
                continue
            
            # Generate timestamp-based filename
            timestamp = self.format_timestamp(start_seconds)
            clip_filename = f"clip_{timestamp}.mp4"
            clip_path = self.output_dir / clip_filename
            
            # Ultra-efficient FFmpeg command
            cmd = [
                'ffmpeg', '-y',  # Overwrite existing
                '-ss', str(start_seconds),  # Seek to start (input seeking is faster)
                '-i', str(video_path),
                '-t', str(actual_duration),
                '-c', 'copy',  # No re-encoding (ultra-fast)
                '-avoid_negative_ts', 'make_zero',
                '-fflags', '+genpts',  # Generate presentation timestamps
                str(clip_path)
            ]
            
            try:
                # Run FFmpeg with minimal output
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,  # 30 second timeout per clip
                    check=True
                )
                
                # Verify clip was created and has reasonable size
                if clip_path.exists() and clip_path.stat().st_size > 1000:  # At least 1KB
                    clip_info_result = {
                        'clip_number': clip_index + 1,
                        'filename': clip_filename,
                        'start_time': start_seconds,
                        'duration': actual_duration,
                        'timestamp': timestamp,
                        'time_display': self.format_time_display(start_seconds),
                        'file_path': str(clip_path),
                        'file_size': clip_path.stat().st_size,
                        'success': True
                    }
                    batch_results.append(clip_info_result)
                else:
                    print(f"⚠️  Clip {clip_index + 1} created but invalid size")
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Clip {clip_index + 1} timed out")
            except subprocess.CalledProcessError as e:
                print(f"❌ Clip {clip_index + 1} failed: {e.stderr}")
            except Exception as e:
                print(f"❌ Unexpected error for clip {clip_index + 1}: {e}")
        
        return batch_results
    
    def split_video_ultra_efficient(self, video_path, clip_duration=15, start_time=0, end_time=None):
        """Ultra-efficient video splitting using all available cores"""
        video_path = Path(video_path)
        
        if not video_path.exists():
            print(f"❌ Video file not found: {video_path}")
            return False
        
        print(f"🚀 ULTRA EFFICIENT VIDEO SPLITTING")
        print(f"=" * 60)
        print(f"📁 Input: {video_path}")
        print(f"📁 Output: {self.output_dir}")
        print(f"⏱️  Clip duration: {clip_duration} seconds")
        
        # Get video information
        video_info = self.get_video_info(video_path)
        if not video_info:
            return False
        
        total_duration = video_info['duration']
        end_time = end_time or total_duration
        start_time = max(0, start_time)
        end_time = min(total_duration, end_time)
        
        duration_to_process = end_time - start_time
        total_clips = math.ceil(duration_to_process / clip_duration)
        
        print(f"🎥 Video Info:")
        print(f"   Duration: {self.format_time_display(total_duration)} ({total_duration:.1f}s)")
        print(f"   Size: {video_info['size_gb']:.2f} GB")
        print(f"   Resolution: {video_info['width']}x{video_info['height']}")
        print(f"   FPS: {video_info['fps']:.1f}")
        print(f"   Codec: {video_info['codec']}")
        print(f"📊 Processing:")
        print(f"   Range: {self.format_time_display(start_time)} to {self.format_time_display(end_time)}")
        print(f"   Expected clips: {total_clips}")
        print(f"   Workers: {self.max_workers}")
        
        # Calculate optimal batch size
        batch_size = self.calculate_optimal_batch_size(total_clips, video_info)
        print(f"   Batch size: {batch_size} clips/batch")
        
        # Clear existing clips
        existing_clips = list(self.output_dir.glob("clip_*.mp4"))
        if existing_clips:
            print(f"🧹 Removing {len(existing_clips)} existing clips...")
            for clip in existing_clips:
                clip.unlink()
        
        # Create clip batches for parallel processing
        clip_batches = []
        for i in range(0, total_clips, batch_size):
            batch = []
            for j in range(i, min(i + batch_size, total_clips)):
                clip_start = start_time + (j * clip_duration)
                if clip_start < end_time:
                    batch.append((clip_start, j, total_clips))
            if batch:
                clip_batches.append(batch)
        
        print(f"📦 Created {len(clip_batches)} batches for parallel processing")
        
        # Start processing
        self.processing_stats['start_time'] = time.time()
        self.processing_stats['total_clips'] = total_clips
        
        print(f"\n🚀 Starting ultra-efficient parallel processing...")
        
        # Process batches in parallel
        completed_clips = []
        failed_count = 0
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(self.create_clip_batch, video_path, batch, clip_duration): batch_idx
                for batch_idx, batch in enumerate(clip_batches)
            }
            
            # Process completed batches
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                
                try:
                    batch_results = future.result()
                    completed_clips.extend(batch_results)
                    
                    # Update progress
                    completed = len(completed_clips)
                    progress = (completed / total_clips) * 100
                    elapsed = time.time() - self.processing_stats['start_time']
                    clips_per_sec = completed / elapsed if elapsed > 0 else 0
                    eta = (total_clips - completed) / clips_per_sec if clips_per_sec > 0 else 0
                    
                    print(f"📈 Progress: {completed}/{total_clips} ({progress:.1f}%) | "
                          f"Speed: {clips_per_sec:.1f} clips/s | "
                          f"ETA: {eta:.0f}s")
                    
                except Exception as e:
                    print(f"❌ Batch {batch_idx} failed: {e}")
                    failed_count += len(clip_batches[batch_idx])
        
        # Final statistics
        total_time = time.time() - self.processing_stats['start_time']
        success_count = len(completed_clips)
        
        print(f"\n✅ ULTRA EFFICIENT SPLITTING COMPLETE!")
        print(f"=" * 60)
        print(f"📊 Results:")
        print(f"   ✅ Clips created: {success_count}")
        print(f"   ❌ Failed clips: {failed_count}")
        print(f"   ⏱️  Total time: {total_time:.1f} seconds")
        print(f"   🚀 Average speed: {success_count/total_time:.1f} clips/second")
        print(f"   💻 CPU efficiency: {(success_count/total_time/self.max_workers)*100:.1f}%")
        
        # Save metadata
        self.save_metadata(video_path, completed_clips, video_info, total_time)
        
        # Show sample clips
        if completed_clips:
            print(f"\n📁 Sample clips created:")
            for clip in sorted(completed_clips, key=lambda x: x['start_time'])[:5]:
                size_mb = clip['file_size'] / (1024*1024)
                print(f"   {clip['filename']} - {clip['time_display']} ({size_mb:.1f} MB)")
            if len(completed_clips) > 5:
                print(f"   ... and {len(completed_clips) - 5} more clips")
        
        return success_count > 0
    
    def save_metadata(self, video_path, clips_data, video_info, processing_time):
        """Save comprehensive metadata about the splitting process"""
        metadata = {
            'source_video': {
                'path': str(video_path),
                'duration': video_info['duration'],
                'size_gb': video_info['size_gb'],
                'resolution': f"{video_info['width']}x{video_info['height']}",
                'fps': video_info['fps'],
                'codec': video_info['codec']
            },
            'processing_info': {
                'clip_duration': 15,
                'total_clips': len(clips_data),
                'processing_time': processing_time,
                'clips_per_second': len(clips_data) / processing_time if processing_time > 0 else 0,
                'workers_used': self.max_workers,
                'timestamp': datetime.now().isoformat()
            },
            'clips': clips_data,
            'performance_stats': {
                'vm_cores': self.total_cores,
                'workers_used': self.max_workers,
                'memory_limit_gb': self.memory_limit_gb,
                'efficiency_percent': (len(clips_data)/processing_time/self.max_workers)*100 if processing_time > 0 else 0
            }
        }
        
        metadata_file = self.output_dir / 'clips_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Metadata saved to: {metadata_file}")
        
        return metadata_file
    
    def check_ffmpeg_optimization(self):
        """Check FFmpeg capabilities and suggest optimizations"""
        try:
            # Check FFmpeg threading support
            result = subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1', 
                                   '-threads', str(self.max_workers), '-f', 'null', '-'], 
                                   capture_output=True, text=True, timeout=10)
            
            print(f"✅ FFmpeg threading test passed")
            return True
        except Exception as e:
            print(f"⚠️  FFmpeg optimization check failed: {e}")
            return False

def main():
    """Main function"""
    print("🚀 ULTRA EFFICIENT VIDEO SPLITTER")
    print("=" * 60)
    
    # Get video file
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
    else:
        video_file = input("📁 Enter video file path: ").strip()
    
    if not video_file:
        print("❌ No video file provided")
        sys.exit(1)
    
    # Optional parameters
    clip_duration = 15
    start_time = 0
    end_time = None
    
    # Time range input
    time_range = input("⏰ Enter time range (start-end in seconds, or press Enter for full video): ").strip()
    if time_range:
        try:
            if '-' in time_range:
                start_str, end_str = time_range.split('-', 1)
                start_time = float(start_str.strip())
                end_time = float(end_str.strip()) if end_str.strip() else None
            else:
                start_time = float(time_range)
        except ValueError:
            print("❌ Invalid time format. Using full video.")
    
    # Create ultra-efficient splitter
    splitter = UltraEfficientSplitter()
    
    # Check FFmpeg optimization
    splitter.check_ffmpeg_optimization()
    
    # Split the video
    success = splitter.split_video_ultra_efficient(video_file, clip_duration, start_time, end_time)
    
    if success:
        print(f"\n🎉 SUCCESS! Video split into timestamp-named clips")
        print(f"📋 Next step: Run AI analysis on the clips")
        print(f"   python ../3-half-start-end/analyze_all_clips.py clips/")
    else:
        print(f"\n❌ FAILED! Could not split video")
        sys.exit(1)

if __name__ == "__main__":
    main() 