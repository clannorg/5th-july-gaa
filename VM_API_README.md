# GAA Analysis VM - Input/Output API Documentation

## 🎯 **VM Purpose**
This VM serves as the backend analysis engine for the GAA match analysis web application. It receives match URLs, processes videos through AI analysis, and returns structured JSON data for the interactive viewer.

## 📥 **Input Interface**

### **Primary Input: Match URL**
```
Input: Video URL (YouTube, Vimeo, direct MP4, etc.)
Format: String URL
Example: "https://app.veo.co/matches/20250608-8-jun-2025-122805-27ca4c57/"
```

### **Expected Video Specifications**
- **Duration**: 60-120 minutes (typical GAA match length)
- **Format**: MP4, AVI, MOV, MKV (auto-converted)
- **Quality**: 720p minimum, 1080p preferred
- **Content**: Single-camera GAA football match footage

### **Processing Trigger**
The VM expects to receive match URLs through the web application's backend API and processes them automatically.

## 🔄 **Processing Pipeline**

### **Stage 1: Video Download & Preparation**
```
Input:  Match URL
Output: Local video file (downloads/match_video.mp4)
Time:   ~2-5 minutes (depending on video size)
```

### **Stage 2: Video Splitting**
```
Input:  Full match video
Output: 336 x 15-second clips (clips/clip_XXmXXs.mp4)
Time:   ~1-2 minutes
Size:   ~3GB total clips
```

### **Stage 3: AI Analysis**
```
Input:  337 video clips
Output: Individual clip descriptions (text files)
Time:   ~5-10 minutes (rate limited)
Cost:   ~$0.0005 per match
```

### **Stage 4: Timeline Synthesis**
```
Input:  All clip descriptions (1MB text)
Output: Match timeline with key timestamps
Time:   ~30 seconds
Method: Temporal block analysis
```

## 📤 **Output Interface**

### **Primary Output: Analysis JSON**
```json
{
  "match_id": "generated_uuid",
  "video_url": "original_input_url",
  "processing_time": "2024-01-15T14:30:00Z",
  "duration_minutes": 84,
  "analysis_version": "v2.1",
  "costs": {
    "gemini_api_calls": 337,
    "total_cost_usd": 0.000548,
    "model_used": "gemini-2.5-flash"
  },
  "timeline": {
    "pre_match": {
      "start": "00:00",
      "end": "02:15",
      "description": "Pre-match warm-up and preparation"
    },
    "first_half": {
      "start": "02:15",
      "end": "32:00",
      "duration_minutes": 30,
      "description": "First half active play"
    },
    "halftime": {
      "start": "32:00",
      "end": "46:45",
      "duration_minutes": 15,
      "description": "Halftime break"
    },
    "second_half": {
      "start": "46:45",
      "end": "81:45",
      "duration_minutes": 35,
      "description": "Second half active play"
    },
    "post_match": {
      "start": "81:45",
      "end": "84:00",
      "description": "Post-match activities"
    }
  },
  "confidence_scores": {
    "overall": 0.98,
    "first_half_start": 0.99,
    "first_half_end": 0.97,
    "second_half_start": 0.99,
    "match_end": 0.95
  },
  "key_events": [
    {
      "timestamp": "02:15",
      "type": "throw_in_ceremony",
      "description": "Match start with official throw-in ceremony"
    },
    {
      "timestamp": "32:00",
      "type": "half_end",
      "description": "First half ends, players leave field"
    },
    {
      "timestamp": "46:45",
      "type": "throw_in_ceremony",
      "description": "Second half start with throw-in ceremony"
    }
  ],
  "processing_metadata": {
    "clips_processed": 337,
    "clips_successful": 337,
    "clips_failed": 0,
    "total_tokens_used": 1486800,
    "average_clip_confidence": 0.94
  }
}
```

### **Error Output Format**
```json
{
  "error": true,
  "error_type": "video_download_failed",
  "error_message": "Unable to download video from provided URL",
  "timestamp": "2024-01-15T14:30:00Z",
  "match_id": "generated_uuid",
  "video_url": "original_input_url",
  "retry_possible": true,
  "suggested_action": "Check URL validity and try again"
}
```

## 📊 **Performance Specifications**

### **Processing Times**
- **Total Processing**: 8-15 minutes per match
- **Video Download**: 2-5 minutes
- **Video Splitting**: 1-2 minutes  
- **AI Analysis**: 5-10 minutes (rate limited)
- **Timeline Synthesis**: 30 seconds

### **Resource Usage**
- **Storage**: ~3GB per match (temporary, cleaned after processing)
- **Memory**: ~2GB peak usage
- **CPU**: Moderate usage during video processing
- **Network**: ~1GB download per match

### **Cost Structure**
- **Gemini API**: $0.000134 - $0.000548 per match
- **Compute**: ~$0.01 per match (VM time)
- **Storage**: Negligible (temporary files)
- **Total**: <$0.02 per match

## 🔧 **API Integration**

### **Status Monitoring**
The VM can provide real-time status updates:
```json
{
  "status": "processing",
  "stage": "ai_analysis",
  "progress": 0.65,
  "clips_processed": 220,
  "clips_remaining": 117,
  "estimated_completion": "2024-01-15T14:45:00Z"
}
```

### **Webhook Integration**
Configure webhooks to receive completion notifications:
```json
{
  "event": "analysis_complete",
  "match_id": "uuid",
  "status": "success",
  "results_url": "path/to/results.json",
  "processing_time_seconds": 847
}
```

## 🚨 **Error Handling**

### **Common Error Types**
1. **video_download_failed**: Invalid URL or network issues
2. **video_format_unsupported**: Unsupported video format
3. **api_rate_limit_exceeded**: Gemini API rate limits hit
4. **insufficient_storage**: Disk space issues
5. **analysis_failed**: AI analysis errors

### **Retry Logic**
- **Automatic Retry**: 3 attempts with exponential backoff
- **Rate Limit Handling**: Intelligent delay and retry
- **Partial Recovery**: Resume from failed stage when possible

## 🔒 **Security & Configuration**

### **Required Environment Variables**
```bash
GEMINI_API_KEY=your_gemini_api_key
WEBHOOK_URL=https://your-app.com/webhook (optional)
MAX_CONCURRENT_JOBS=3 (optional)
```

### **File Structure**
```
/home/ubuntu/5th-july-gaa/
├── downloads/           # Temporary video downloads
├── clips/              # Temporary 15-second clips  
├── 3-half-start-end/   # Analysis results
├── results/            # Final JSON outputs
└── logs/               # Processing logs
```

## 📈 **Scaling Considerations**

### **Current Limitations**
- **Rate Limits**: 15 requests/minute (Gemini API)
- **Storage**: 3GB per match (temporary)
- **Concurrency**: 1 match at a time recommended

### **Scaling Options**
- **Multi-API Keys**: Rotate keys for higher throughput
- **Parallel Processing**: Multiple VM instances
- **Queue System**: Redis/RabbitMQ for job management
- **Storage Optimization**: Automatic cleanup and compression

## 🎯 **Integration Example**

### **Web App → VM Flow**
1. User uploads match URL in web app
2. Web app sends URL to VM via API/queue
3. VM processes match and generates JSON
4. VM sends completion webhook to web app
5. Web app loads JSON into interactive viewer
6. User sees timeline visualization

### **Expected SLA**
- **Processing Time**: <15 minutes per match
- **Success Rate**: >95% for valid URLs
- **Availability**: 99%+ uptime
- **Cost**: <$0.02 per match

---

**This VM serves as a reliable, cost-effective backend for GAA match analysis, providing structured timeline data for interactive visualization.** 