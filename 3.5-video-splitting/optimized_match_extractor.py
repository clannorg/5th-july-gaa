#!/usr/bin/env python3
"""
🚀 OPTIMIZED GAA MATCH EXTRACTOR
Reads timeline JSON and extracts both halves with maximum efficiency
- Parallel processing for multiple operations
- Memory-optimized for large videos
- Uses timeline JSON from halftime detection
- Ultra-fast FFmpeg operations
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
from multiprocessing import cpu_count

class OptimizedMatchExtractor:
    def __init__(self, output_dir="match_videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # VM optimization settings
        self.total_cores = cpu_count()  # 8 cores
        self.max_workers = max(1, self.total_cores - 2)  # Use 6 cores, leave 2 for system
        
        # Default paths
        self.timeline_file = "../3-half-start-end/results/match_timeline_corrected.json"
        self.video_file = "../1-veo-download/downloads/kevy-game.mp4"
        
        print(f"🚀 OPTIMIZED GAA MATCH EXTRACTOR")
        print(f"💻 VM: {self.total_cores} cores, {psutil.virtual_memory().total / (1024**3):.1f}GB RAM")
        print(f"⚙️  Using {self.max_workers} parallel workers")
    
    def load_timeline(self):
        """Load and parse timeline JSON"""
        if not os.path.exists(self.timeline_file):
            print(f"❌ Timeline file not found: {self.timeline_file}")
            return None
        
        with open(self.timeline_file, 'r') as f:
            timeline_data = json.load(f)
        
        # Extract timeline segments
        timeline = timeline_data.get('match_timeline', {})
        
        # Get half timings
        first_half = timeline.get('first_half', {})
        second_half = timeline.get('second_half', {})
        
        if not first_half or not second_half:
            print("❌ Timeline missing first_half or second_half data")
            return None
        
        return {
            'first_half_start': first_half['start'],
            'first_half_end': first_half['end'],
            'second_half_start': second_half['start'],
            'second_half_end': second_half['end']
        }
    
    def timestamp_to_seconds(self, timestamp):
        """Convert MM:SS timestamp to seconds"""
        if isinstance(timestamp, (int, float)):
            return timestamp
        
        parts = timestamp.split(':')
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")
    
    def get_video_duration(self):
        """Get video duration efficiently"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', self.video_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"❌ Error getting video duration: {e}")
            return None
    
    def extract_segment_optimized(self, segment_info):
        """Extract a single video segment with maximum efficiency"""
        start_time, end_time, output_file, description, buffer_seconds = segment_info
        
        # Add buffer margins
        video_duration = self.get_video_duration()
        buffered_start = max(0, start_time - buffer_seconds)
        buffered_end = min(video_duration, end_time + buffer_seconds) if video_duration else end_time + buffer_seconds
        
        duration = buffered_end - buffered_start
        
        print(f"🎬 Extracting {description}")
        print(f"   Time: {buffered_start:.0f}s → {buffered_end:.0f}s ({duration:.0f}s)")
        
        # Ultra-optimized FFmpeg command
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-ss', str(buffered_start),  # Input seeking (fastest)
            '-i', self.video_file,
            '-t', str(duration),
            '-c', 'copy',  # No re-encoding (ultra-fast)
            '-avoid_negative_ts', 'make_zero',
            '-fflags', '+genpts',  # Generate timestamps
            '-movflags', '+faststart',  # Optimize for streaming
            str(output_file)
        ]
        
        start_extract = time.time()
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 minute timeout
                check=True
            )
            
            extract_time = time.time() - start_extract
            file_size = output_file.stat().st_size / (1024*1024)  # MB
            
            print(f"   ✅ {description} complete: {file_size:.1f}MB in {extract_time:.1f}s")
            
            return {
                'success': True,
                'file': output_file,
                'description': description,
                'size_mb': file_size,
                'extract_time': extract_time,
                'duration': duration
            }
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ {description} timed out")
            return {'success': False, 'error': 'timeout'}
        except subprocess.CalledProcessError as e:
            print(f"   ❌ {description} failed: {e.stderr}")
            return {'success': False, 'error': e.stderr}
        except Exception as e:
            print(f"   ❌ {description} unexpected error: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_combined_match_optimized(self, first_half_file, second_half_file):
        """Combine both halves into single match video with maximum efficiency"""
        combined_output = self.output_dir / "full_match_optimized.mp4"
        
        print(f"🔗 Creating combined match video...")
        
        # Create concat file for FFmpeg
        concat_file = self.output_dir / "concat_list.txt"
        with open(concat_file, 'w') as f:
            f.write(f"file '{first_half_file.name}'\n")
            f.write(f"file '{second_half_file.name}'\n")
        
        # Ultra-optimized concat command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',  # No re-encoding
            '-movflags', '+faststart',  # Optimize for streaming
            str(combined_output)
        ]
        
        start_combine = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                check=True,
                cwd=self.output_dir  # Run in output directory
            )
            
            combine_time = time.time() - start_combine
            file_size = combined_output.stat().st_size / (1024*1024)  # MB
            
            print(f"   ✅ Combined match: {file_size:.1f}MB in {combine_time:.1f}s")
            
            # Clean up concat file
            concat_file.unlink()
            
            return {
                'success': True,
                'file': combined_output,
                'size_mb': file_size,
                'combine_time': combine_time
            }
            
        except Exception as e:
            print(f"   ❌ Combine failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def extract_match_optimized(self, buffer_seconds=60):
        """Extract both halves and combined match with maximum efficiency"""
        print(f"🎯 Starting optimized match extraction")
        print(f"=" * 50)
        
        # Load timeline
        timeline = self.load_timeline()
        if not timeline:
            return False
        
        # Check video exists
        if not os.path.exists(self.video_file):
            print(f"❌ Video file not found: {self.video_file}")
            return False
        
        # Convert timestamps to seconds
        first_start = self.timestamp_to_seconds(timeline['first_half_start'])
        first_end = self.timestamp_to_seconds(timeline['first_half_end'])
        second_start = self.timestamp_to_seconds(timeline['second_half_start'])
        second_end = self.timestamp_to_seconds(timeline['second_half_end'])
        
        print(f"📊 Timeline loaded:")
        print(f"   First Half: {timeline['first_half_start']} → {timeline['first_half_end']}")
        print(f"   Second Half: {timeline['second_half_start']} → {timeline['second_half_end']}")
        print(f"   Buffer: {buffer_seconds}s each side")
        
        # Define extraction tasks
        tasks = [
            (first_start, first_end, self.output_dir / "first_half_optimized.mp4", "First Half", buffer_seconds),
            (second_start, second_end, self.output_dir / "second_half_optimized.mp4", "Second Half", buffer_seconds)
        ]
        
        # Start parallel extraction
        start_time = time.time()
        results = []
        
        print(f"\n🚀 Starting parallel extraction using {self.max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit extraction tasks
            future_to_task = {
                executor.submit(self.extract_segment_optimized, task): task[3]
                for task in tasks
            }
            
            # Collect results
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"❌ {task_name} extraction failed: {e}")
                    results.append({'success': False, 'error': str(e)})
        
        # Check if both extractions succeeded
        successful_results = [r for r in results if r.get('success')]
        if len(successful_results) != 2:
            print(f"❌ Extraction failed. Only {len(successful_results)}/2 segments extracted.")
            return False
        
        # Find the files
        first_half_file = None
        second_half_file = None
        for result in successful_results:
            if 'First Half' in result['description']:
                first_half_file = result['file']
            elif 'Second Half' in result['description']:
                second_half_file = result['file']
        
        # Create combined match video
        combined_result = self.create_combined_match_optimized(first_half_file, second_half_file)
        
        # Final statistics
        total_time = time.time() - start_time
        total_size = sum(r['size_mb'] for r in successful_results)
        if combined_result.get('success'):
            total_size += combined_result['size_mb']
        
        print(f"\n✅ OPTIMIZED EXTRACTION COMPLETE!")
        print(f"=" * 50)
        print(f"📊 Results:")
        print(f"   ⏱️  Total time: {total_time:.1f} seconds")
        print(f"   📁 Total size: {total_size:.1f} MB")
        print(f"   🚀 Speed: {total_size/total_time:.1f} MB/s")
        
        print(f"\n📂 Created files:")
        for result in successful_results:
            print(f"   📹 {result['file'].name} - {result['description']} ({result['size_mb']:.1f}MB)")
        
        if combined_result.get('success'):
            print(f"   📹 {combined_result['file'].name} - Combined Match ({combined_result['size_mb']:.1f}MB)")
        
        return True

def main():
    """Main function"""
    print("🚀 OPTIMIZED GAA MATCH EXTRACTOR")
    print("=" * 50)
    
    # Create extractor
    extractor = OptimizedMatchExtractor()
    
    # Extract match with optimization
    success = extractor.extract_match_optimized(buffer_seconds=60)
    
    if success:
        print(f"\n🎉 SUCCESS! Optimized match extraction complete!")
        print(f"📁 Files saved to: {extractor.output_dir}")
        print(f"🎬 Ready to use your GAA match videos!")
    else:
        print(f"\n❌ Extraction failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 