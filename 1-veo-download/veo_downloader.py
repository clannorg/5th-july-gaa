#!/usr/bin/env python3
"""
🎥 ADVANCED VEO DOWNLOADER
Extracts direct video URLs from Veo platform and downloads GAA matches
Based on proven Veo URL extraction patterns
"""

import os
import sys
import requests
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse
import time
from datetime import datetime

class AdvancedVeoDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        # Add realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def extract_video_url_from_veo(self, veo_url):
        """Extract direct video URL from Veo match page using proven patterns"""
        print(f"🔍 EXTRACTING VIDEO URL FROM VEO")
        print(f"=" * 50)
        print(f"📄 Veo URL: {veo_url}")
        
        try:
            # Get the page content with timeout and retry
            print(f"📥 Fetching Veo page...")
            response = self.session.get(veo_url, timeout=30)
            response.raise_for_status()
            page_content = response.text
            
            print(f"✅ Page loaded ({len(page_content)} characters)")
            
            # Method 1: Look for video ID in Open Graph meta tags (primary method)
            print(f"🎯 Method 1: Extracting video ID from Open Graph meta...")
            og_image_pattern = r'content="https://c\.veocdn\.com/([a-f0-9\-]+)/[^"]*thumbnail\.jpg"'
            match = re.search(og_image_pattern, page_content)
            
            if match:
                video_id = match.group(1)
                print(f"✅ Found video ID: {video_id}")
                
                # Construct video URL using Veo's CDN pattern
                video_url = f"https://c.veocdn.com/{video_id}/standard/human/1cc5edba/video.mp4"
                
                if self.verify_video_url(video_url):
                    return video_url
                else:
                    print(f"❌ Primary video URL not accessible, trying alternatives...")
            
            # Method 2: Alternative video URL patterns
            print(f"🎯 Method 2: Trying alternative video URL patterns...")
            if match:
                video_id = match.group(1)
                alternative_patterns = [
                    f"https://c.veocdn.com/{video_id}/standard/human/video.mp4",
                    f"https://c.veocdn.com/{video_id}/standard/video.mp4",
                    f"https://c.veocdn.com/{video_id}/video.mp4"
                ]
                
                for alt_url in alternative_patterns:
                    print(f"   🔍 Trying: {alt_url}")
                    if self.verify_video_url(alt_url):
                        return alt_url
            
            # Method 3: Look for other video ID patterns in the page
            print(f"🎯 Method 3: Searching for alternative video ID patterns...")
            video_id_patterns = [
                r'"videoId":"([a-f0-9\-]+)"',
                r'"id":"([a-f0-9\-]+)".*?"type":"video"',
                r'veocdn\.com/([a-f0-9\-]+)/',
                r'data-video-id="([a-f0-9\-]+)"'
            ]
            
            for pattern in video_id_patterns:
                matches = re.findall(pattern, page_content)
                for video_id in matches:
                    if len(video_id) > 20:  # Valid Veo video IDs are long
                        video_url = f"https://c.veocdn.com/{video_id}/standard/human/1cc5edba/video.mp4"
                        print(f"   🔍 Testing ID: {video_id}")
                        if self.verify_video_url(video_url):
                            return video_url
            
            print(f"❌ Could not extract video URL from Veo page")
            return None
                
        except Exception as e:
            print(f"❌ Error extracting video URL: {e}")
            return None
    
    def verify_video_url(self, video_url):
        """Verify that the video URL is accessible and contains actual video"""
        try:
            print(f"   ✅ Verifying: {video_url}")
            head_response = self.session.head(video_url, timeout=10)
            
            if head_response.status_code == 200:
                content_length = head_response.headers.get('content-length', '0')
                content_type = head_response.headers.get('content-type', '')
                
                if int(content_length) > 1000000:  # At least 1MB
                    size_gb = int(content_length) / (1024**3)
                    print(f"   ✅ Valid video found!")
                    print(f"   📊 Size: {size_gb:.2f} GB")
                    print(f"   📋 Type: {content_type}")
                    return True
                else:
                    print(f"   ❌ File too small: {content_length} bytes")
                    return False
            else:
                print(f"   ❌ Not accessible: HTTP {head_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Verification failed: {e}")
            return False
    
    def download_video_with_wget(self, video_url, filename=None):
        """Download video using wget for maximum reliability"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gaa_match_{timestamp}.mp4"
        
        # Ensure .mp4 extension
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        
        output_path = self.output_dir / filename
        
        print(f"\n📥 DOWNLOADING VIDEO")
        print(f"=" * 50)
        print(f"🎥 Source: {video_url}")
        print(f"💾 Saving to: {output_path}")
        
        # Check if file already exists
        if output_path.exists():
            print(f"⚠️  File already exists: {output_path}")
            overwrite = input("Overwrite? (y/N): ").lower().strip()
            if overwrite != 'y':
                print("❌ Download cancelled")
                return None
        
        start_time = time.time()
        
        try:
            # Use wget for reliable download with progress and resume capability
            cmd = [
                'wget', video_url,
                '-O', str(output_path),
                '--progress=bar:force:noscroll',
                '--timeout=30',
                '--tries=3',
                '--continue',  # Resume partial downloads
                '--user-agent', self.session.headers['User-Agent']
            ]
            
            print(f"🚀 Starting download with wget...")
            result = subprocess.run(cmd, check=True)
            
            download_time = time.time() - start_time
            file_size = output_path.stat().st_size / (1024**3)  # GB
            
            print(f"\n✅ DOWNLOAD COMPLETE!")
            print(f"📁 File: {output_path}")
            print(f"📊 Size: {file_size:.2f} GB")
            print(f"⏱️  Time: {download_time:.1f} seconds")
            print(f"🚀 Speed: {file_size/download_time*60:.1f} GB/min")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Download failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def download_video_with_requests(self, video_url, filename=None):
        """Fallback: Download video using Python requests with progress"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gaa_match_{timestamp}.mp4"
        
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        
        output_path = self.output_dir / filename
        
        print(f"\n📥 DOWNLOADING VIDEO (Fallback Method)")
        print(f"=" * 50)
        print(f"🎥 Source: {video_url}")
        print(f"💾 Saving to: {output_path}")
        
        try:
            response = self.session.get(video_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            print(f"📊 File size: {total_size / (1024**3):.2f} GB")
            
            downloaded = 0
            start_time = time.time()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress every 10MB
                        if downloaded % (10 * 1024 * 1024) == 0:
                            elapsed = time.time() - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"📈 Progress: {progress:.1f}% ({downloaded/(1024**3):.2f}/{total_size/(1024**3):.2f} GB) - {speed/(1024**2):.1f} MB/s")
                            else:
                                print(f"📈 Downloaded: {downloaded/(1024**3):.2f} GB - {speed/(1024**2):.1f} MB/s")
            
            elapsed = time.time() - start_time
            print(f"\n✅ Download complete!")
            print(f"📁 File: {output_path}")
            print(f"📊 Size: {output_path.stat().st_size/(1024**3):.2f} GB")
            print(f"⏱️  Time: {elapsed:.1f} seconds")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def download_from_veo(self, veo_url, filename=None):
        """Complete Veo download process: extract URL then download"""
        print(f"🎥 ADVANCED VEO DOWNLOADER")
        print(f"=" * 60)
        print(f"🏐 GAA Match Download from Veo Platform")
        print(f"=" * 60)
        
        # Step 1: Extract video URL
        video_url = self.extract_video_url_from_veo(veo_url)
        if not video_url:
            return None
        
        # Step 2: Download video (try wget first, fallback to requests)
        if self.check_wget_available():
            result = self.download_video_with_wget(video_url, filename)
        else:
            print(f"⚠️  wget not available, using Python requests...")
            result = self.download_video_with_requests(video_url, filename)
        
        if result:
            print(f"\n🎉 SUCCESS! GAA match downloaded")
            print(f"📋 Next step: Run video splitting script")
            print(f"   python ../2-splitting/clip_splitter.py {result}")
        
        return result
    
    def check_wget_available(self):
        """Check if wget is available on the system"""
        try:
            subprocess.run(['wget', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def validate_veo_url(self, url):
        """Validate that the URL is a proper Veo match URL"""
        veo_patterns = [
            r'https://app\.veo\.co/matches/',
            r'https://.*\.veo\.co/',
            r'veo\.co'
        ]
        
        return any(re.search(pattern, url) for pattern in veo_patterns)

def main():
    """Main function"""
    print("🎥 ADVANCED VEO DOWNLOADER")
    print("=" * 60)
    
    # Get URL from user or command line
    if len(sys.argv) > 1:
        veo_url = sys.argv[1]
    else:
        veo_url = input("📥 Enter Veo match URL: ").strip()
    
    if not veo_url:
        print("❌ No URL provided")
        sys.exit(1)
    
    # Optional filename
    filename = input("📝 Enter filename (optional, press Enter for auto): ").strip()
    if not filename:
        filename = None
    
    # Create downloader
    downloader = AdvancedVeoDownloader()
    
    # Validate URL
    if not downloader.validate_veo_url(veo_url):
        print("❌ Invalid Veo URL format")
        print("Expected format: https://app.veo.co/matches/...")
        sys.exit(1)
    
    # Download from Veo
    result = downloader.download_from_veo(veo_url, filename)
    
    if result:
        print(f"\n🎉 SUCCESS! Video downloaded to: {result}")
    else:
        print(f"\n❌ FAILED! Could not download video from Veo")
        sys.exit(1)

if __name__ == "__main__":
    main() 