#!/usr/bin/env python3
"""
🚀 OPTIMIZED MATCH HALVES TO CLIPS SPLITTER
Takes extracted match videos and splits them into 15-second clips for analysis
- Uses ultra-efficient parallel processing from 2-splitting approach
- Optimized for 8-core VM with 15GB RAM
- Timestamp-named clips for easy analysis
- Separate folders for first_half and second_half clips
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
from multiprocessing import cpu_count
import psutil

class OptimizedHalvesToClipsSplitter:
    def __init__(self, output_base_dir="clips"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)
        
        # VM optimization settings
        self.total_cores = cpu_count()  # 8 cores
        self.max_workers = max(1, self.total_cores - 1)  # Use 7 cores, leave 1 for system
        
        # Input video paths
        self.match_videos_dir = Path("match_videos")
        self.first_half_video = self.match_videos_dir / "first_half_optimized.mp4"
        self.second_half_video = self.match_videos_dir / "second_half_optimized.mp4"
        
        print(f"🚀 OPTIMIZED HALVES TO CLIPS SPLITTER")
        print(f"💻 VM: {self.total_cores} cores, {psutil.virtual_memory().total / (1024**3):.1f}GB RAM")
        print(f"⚙️  Using {self.max_workers} parallel workers")
    
    def get_video_info(self, video_path):
        """Get video information using ffprobe"""
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
                'fps': eval(video_stream['r_frame_rate']),
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
    
    def calculate_optimal_batch_size(self, total_clips, video_info):
        """Calculate optimal batch size based on VM resources"""
        base_batch_size = 50
        
        # Adjust for video complexity
        if video_info['size_gb'] > 1.5:  # Large video
            batch_size = max(20, base_batch_size // 2)
        elif video_info['bitrate'] > 10000000:  # High bitrate
            batch_size = max(30, base_batch_size // 1.5)
        else:
            batch_size = base_batch_size
        
        # Ensure efficient processing with available workers
        optimal_batch = min(batch_size, max(10, total_clips // self.max_workers))
        
        return int(optimal_batch)
    
    def create_clip_batch(self, video_path, clip_batch, output_dir, clip_duration=15):
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
            clip_path = output_dir / clip_filename
            
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
                        'file_path': str(clip_path),
                        'file_size': clip_path.stat().st_size,
                        'success': True
                    }
                    batch_results.append(clip_info_result)
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Clip {clip_index + 1} timed out")
            except subprocess.CalledProcessError as e:
                print(f"❌ Clip {clip_index + 1} failed")
            except Exception as e:
                print(f"❌ Unexpected error for clip {clip_index + 1}: {e}")
        
        return batch_results
    
    def split_video_to_clips(self, video_path, output_dir, half_name, clip_duration=15):
        """Split a single video into clips with ultra efficiency"""
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        
        if not video_path.exists():
            print(f"❌ Video file not found: {video_path}")
            return False
        
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n🎬 SPLITTING {half_name.upper()}")
        print(f"=" * 50)
        print(f"📁 Input: {video_path}")
        print(f"📁 Output: {output_dir}")
        
        # Get video information
        video_info = self.get_video_info(video_path)
        if not video_info:
            return False
        
        total_duration = video_info['duration']
        total_clips = math.ceil(total_duration / clip_duration)
        
        print(f"🎥 Video Info:")
        print(f"   Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        print(f"   Size: {video_info['size_gb']:.2f} GB")
        print(f"   Expected clips: {total_clips}")
        
        # Calculate optimal batch size
        batch_size = self.calculate_optimal_batch_size(total_clips, video_info)
        print(f"   Batch size: {batch_size} clips/batch")
        
        # Clear existing clips
        existing_clips = list(output_dir.glob("clip_*.mp4"))
        if existing_clips:
            print(f"🧹 Removing {len(existing_clips)} existing clips...")
            for clip in existing_clips:
                clip.unlink()
        
        # Create clip batches for parallel processing
        clip_batches = []
        for i in range(0, total_clips, batch_size):
            batch = []
            for j in range(i, min(i + batch_size, total_clips)):
                clip_start = j * clip_duration
                if clip_start < total_duration:
                    batch.append((clip_start, j, total_clips))
            if batch:
                clip_batches.append(batch)
        
        print(f"📦 Created {len(clip_batches)} batches for parallel processing")
        
        # Start processing
        start_time = time.time()
        completed_clips = []
        
        print(f"🚀 Starting ultra-efficient parallel processing...")
        
        # Process batches in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(self.create_clip_batch, video_path, batch, output_dir, clip_duration): batch_idx
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
                    elapsed = time.time() - start_time
                    clips_per_sec = completed / elapsed if elapsed > 0 else 0
                    eta = (total_clips - completed) / clips_per_sec if clips_per_sec > 0 else 0
                    
                    print(f"📈 {half_name} Progress: {completed}/{total_clips} ({progress:.1f}%) | "
                          f"Speed: {clips_per_sec:.1f} clips/s | ETA: {eta:.0f}s")
                    
                except Exception as e:
                    print(f"❌ Batch {batch_idx} failed: {e}")
        
        # Final statistics
        total_time = time.time() - start_time
        success_count = len(completed_clips)
        
        print(f"\n✅ {half_name.upper()} SPLITTING COMPLETE!")
        print(f"📊 Results:")
        print(f"   ✅ Clips created: {success_count}")
        print(f"   ⏱️  Total time: {total_time:.1f} seconds")
        print(f"   🚀 Speed: {success_count/total_time:.1f} clips/second")
        
        # Save metadata
        self.save_metadata(video_path, completed_clips, video_info, total_time, half_name, output_dir)
        
        return success_count > 0
    
    def save_metadata(self, video_path, clips_data, video_info, processing_time, half_name, output_dir):
        """Save metadata about the splitting process"""
        metadata = {
            'source_video': {
                'path': str(video_path),
                'half_name': half_name,
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
            'clips': clips_data
        }
        
        metadata_file = output_dir / f'{half_name}_clips_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Metadata saved to: {metadata_file}")
    
    def split_both_halves(self):
        """Split both first and second half videos into clips"""
        print(f"🚀 SPLITTING BOTH MATCH HALVES TO CLIPS")
        print(f"=" * 60)
        
        # Check input videos exist
        if not self.first_half_video.exists():
            print(f"❌ First half video not found: {self.first_half_video}")
            return False
        
        if not self.second_half_video.exists():
            print(f"❌ Second half video not found: {self.second_half_video}")
            return False
        
        # Create output directories
        first_half_clips_dir = self.output_base_dir / "first_half"
        second_half_clips_dir = self.output_base_dir / "second_half"
        
        total_start_time = time.time()
        
        # Split first half
        print(f"🥅 Starting First Half Splitting...")
        first_success = self.split_video_to_clips(
            self.first_half_video, 
            first_half_clips_dir, 
            "first_half"
        )
        
        # Split second half
        print(f"\n🥅 Starting Second Half Splitting...")
        second_success = self.split_video_to_clips(
            self.second_half_video, 
            second_half_clips_dir, 
            "second_half"
        )
        
        # Final summary
        total_time = time.time() - total_start_time
        
        print(f"\n🎉 COMPLETE MATCH SPLITTING FINISHED!")
        print(f"=" * 60)
        print(f"⏱️  Total processing time: {total_time:.1f} seconds")
        print(f"📂 Output structure:")
        print(f"   📁 {first_half_clips_dir}/ - First half clips")
        print(f"   📁 {second_half_clips_dir}/ - Second half clips")
        
        if first_success and second_success:
            print(f"\n✅ SUCCESS! Both halves split into clips")
            print(f"🔄 Next step: Run analysis on clips")
            print(f"   python ../3-half-start-end/1-analyze_clips.py {self.output_base_dir}/first_half/")
            print(f"   python ../3-half-start-end/1-analyze_clips.py {self.output_base_dir}/second_half/")
            return True
        else:
            print(f"\n❌ Some splits failed")
            return False

def main():
    """Main function"""
    # Create splitter
    splitter = OptimizedHalvesToClipsSplitter()
    
    # Split both halves
    success = splitter.split_both_halves()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 