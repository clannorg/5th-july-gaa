#!/usr/bin/env python3
"""
✂️ VIDEO CLIP SPLITTER
Splits GAA match videos into 15-second clips for analysis
"""

import os
import sys
import subprocess
from pathlib import Path
import time
from datetime import datetime, timedelta
import json

class VideoSplitter:
    def __init__(self, output_dir="clips"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.clip_duration = 15  # seconds
        self.clips_created = []
        
    def get_video_duration(self, video_path):
        """Get video duration using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                print(f"❌ Could not get video duration: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ Error getting video duration: {e}")
            return None
    
    def format_time(self, seconds):
        """Format seconds into MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def split_video(self, video_path, start_time=0, end_time=None):
        """Split video into 15-second clips"""
        video_path = Path(video_path)
        
        if not video_path.exists():
            print(f"❌ Video file not found: {video_path}")
            return False
        
        print(f"✂️ VIDEO CLIP SPLITTER")
        print(f"=" * 50)
        print(f"📁 Input video: {video_path}")
        print(f"⏱️  Clip duration: {self.clip_duration} seconds")
        
        # Get video duration
        total_duration = self.get_video_duration(video_path)
        if total_duration is None:
            return False
        
        # Set end time if not provided
        if end_time is None:
            end_time = total_duration
        
        # Validate times
        start_time = max(0, start_time)
        end_time = min(total_duration, end_time)
        
        if start_time >= end_time:
            print(f"❌ Invalid time range: {start_time} to {end_time}")
            return False
        
        print(f"🎬 Total duration: {self.format_time(total_duration)} ({total_duration:.1f}s)")
        print(f"📊 Processing range: {self.format_time(start_time)} to {self.format_time(end_time)}")
        
        # Calculate number of clips
        duration_to_process = end_time - start_time
        num_clips = int(duration_to_process / self.clip_duration)
        
        print(f"✂️ Will create {num_clips} clips")
        print(f"💾 Output directory: {self.output_dir}")
        
        # Create clips
        clips_created = 0
        failed_clips = 0
        
        for i in range(num_clips):
            clip_start = start_time + (i * self.clip_duration)
            clip_end = min(clip_start + self.clip_duration, end_time)
            
            # Skip if clip would be too short
            if clip_end - clip_start < 5:  # Skip clips shorter than 5 seconds
                continue
            
            # Generate clip filename
            clip_filename = f"clip_{i+1:03d}_{self.format_time(clip_start).replace(':', '')}.mp4"
            clip_path = self.output_dir / clip_filename
            
            # FFmpeg command
            cmd = [
                'ffmpeg', '-y',  # Overwrite output files
                '-i', str(video_path),
                '-ss', str(clip_start),
                '-t', str(clip_end - clip_start),
                '-c', 'copy',  # Copy streams without re-encoding (faster)
                '-avoid_negative_ts', 'make_zero',
                str(clip_path)
            ]
            
            try:
                # Run FFmpeg
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    clips_created += 1
                    clip_info = {
                        'clip_number': i + 1,
                        'filename': clip_filename,
                        'start_time': clip_start,
                        'end_time': clip_end,
                        'duration': clip_end - clip_start,
                        'timestamp': self.format_time(clip_start),
                        'file_path': str(clip_path)
                    }
                    self.clips_created.append(clip_info)
                    
                    # Progress indicator
                    if clips_created % 10 == 0:
                        progress = (clips_created / num_clips) * 100
                        print(f"📈 Progress: {clips_created}/{num_clips} clips ({progress:.1f}%)")
                else:
                    failed_clips += 1
                    print(f"❌ Failed to create clip {i+1}: {result.stderr}")
                    
            except Exception as e:
                failed_clips += 1
                print(f"❌ Error creating clip {i+1}: {e}")
        
        print(f"\n✅ SPLITTING COMPLETE!")
        print(f"📊 Results:")
        print(f"   ✅ Clips created: {clips_created}")
        print(f"   ❌ Failed: {failed_clips}")
        print(f"   📁 Output directory: {self.output_dir}")
        
        # Save clip metadata
        metadata = {
            'source_video': str(video_path),
            'total_duration': total_duration,
            'processed_range': {
                'start': start_time,
                'end': end_time,
                'duration': duration_to_process
            },
            'clip_settings': {
                'duration': self.clip_duration,
                'total_clips': clips_created
            },
            'clips': self.clips_created,
            'created_at': datetime.now().isoformat()
        }
        
        metadata_file = self.output_dir / 'clips_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📋 Metadata saved to: {metadata_file}")
        
        return clips_created > 0
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return True
        except FileNotFoundError:
            print("❌ FFmpeg not found! Please install FFmpeg:")
            print("   Ubuntu: sudo apt install ffmpeg")
            print("   macOS: brew install ffmpeg")
            return False

def main():
    """Main function"""
    print("✂️ VIDEO CLIP SPLITTER")
    print("=" * 50)
    
    # Check for FFmpeg
    splitter = VideoSplitter()
    if not splitter.check_ffmpeg():
        sys.exit(1)
    
    # Get video file
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
    else:
        video_file = input("📁 Enter video file path: ").strip()
    
    if not video_file:
        print("❌ No video file provided")
        sys.exit(1)
    
    # Optional time range
    start_time = 0
    end_time = None
    
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
    
    # Split the video
    success = splitter.split_video(video_file, start_time, end_time)
    
    if success:
        print(f"\n🎉 SUCCESS! Video split into clips")
        print(f"📋 Next step: Run analysis on the clips")
    else:
        print(f"\n❌ FAILED! Could not split video")
        sys.exit(1)

if __name__ == "__main__":
    main() 