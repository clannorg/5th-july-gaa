import urllib.request
import urllib.error
import os
import sys

def upload_video_with_presigned_url():
    # Presigned URL (you can replace this with your actual URL)
    presigned_url = "https://clannaicdkappstack-assetbucket4e280c9d-ileugds4qae9.s3.eu-west-1.amazonaws.com/public/6ff42b36-a71f-47eb-a95e-416c7dbddbad/videos/0940079e-c361-49ec-9fd0-7cb892dc56ce/original/Shaker.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=AKIAVIJ7GITJTHN3NITU%2F20250707%2Feu-west-1%2Fs3%2Faws4_request&X-Amz-Date=20250707T185200Z&X-Amz-Expires=3600&X-Amz-Signature=05bdeb7468da0e9bc8e63d99d758479933e430acad8c9c937028c2304cfdd1e1&X-Amz-SignedHeaders=host&x-amz-checksum-crc32=AAAAAA%3D%3D&x-amz-meta-file-type=video&x-amz-meta-upload-timestamp=2025-07-07T18%3A52%3A00.955Z&x-amz-sdk-checksum-algorithm=CRC32&x-id=PutObject"
    
    # Video file path
    video_path = "/home/ubuntu/5th-july-gaa/3.5-video-splitting/match_videos/full_match_optimized.mp4"
    
    try:
        print(f"🔍 Reading video file from: {video_path}")
        
        # Check if file exists
        if not os.path.exists(video_path):
            print(f"❌ Video file not found at: {video_path}")
            sys.exit(1)
        
        # Get file stats
        stats = os.stat(video_path)
        file_size_in_mb = round(stats.st_size / (1024 * 1024), 2)
        
        print(f"📁 File size: {file_size_in_mb} MB")
        print(f"📤 Uploading video to S3...")
        
        # Read the file
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        
        # Create request with headers
        req = urllib.request.Request(
            presigned_url,
            data=video_data,
            method='PUT',
            headers={
                'Content-Type': 'video/mp4',
                'Content-Length': str(stats.st_size)
            }
        )
        
        # Upload using urllib
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            
            if status_code == 200:
                print(f"✅ Video uploaded successfully!")
                print(f"📊 Response status: {status_code}")
                print(f"🔗 File uploaded to: public/6ff42b36-a71f-47eb-a95e-416c7dbddbad/videos/0940079e-c361-49ec-9fd0-7cb892dc56ce/original/Shaker.mp4")
            else:
                print(f"❌ Upload failed with status: {status_code}")
                sys.exit(1)
        
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print(f"📝 Response text: {e.read().decode()}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        sys.exit(1)
    except Exception as error:
        print(f"❌ Error uploading video: {error}")
        sys.exit(1)

if __name__ == "__main__":
    upload_video_with_presigned_url() 