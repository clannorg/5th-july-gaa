// GAA Match Timeline - Ready for Web Integration
const gaaMatchTimeline = {
  matchId: "gaa_match_001",
  analysisDate: "2025-07-06",
  totalDuration: "84:00",
  
  // Main timeline phases
  timeline: {
    preMatch: {
      start: "00:00",
      end: "00:15", 
      durationMinutes: 0.25,
      description: "Pre-match setup and preparation"
    },
    firstHalf: {
      start: "00:15",
      end: "33:00",
      durationMinutes: 32.75,
      description: "First half of GAA match",
      keyEvents: {
        throwInCeremony: "00:15",
        activePlayStart: "02:15"
      }
    },
    halftimeBreak: {
      start: "33:00", 
      end: "48:45",
      durationMinutes: 15.75,
      description: "Halftime break - practice/warm-up session"
    },
    secondHalf: {
      start: "48:45",
      end: "83:00", 
      durationMinutes: 34.25,
      description: "Second half of GAA match",
      keyEvents: {
        throwInCeremony: "48:45"
      }
    },
    postMatch: {
      start: "83:00",
      end: "84:00",
      durationMinutes: 1.0,
      description: "Post-match - players leaving field"
    }
  },

  // Key transition points
  keyTransitions: [
    {
      timestamp: "00:15",
      event: "match_start", 
      description: "First half throw-in ceremony"
    },
    {
      timestamp: "33:00",
      event: "first_half_end",
      description: "End of active play, start of halftime"
    },
    {
      timestamp: "48:45", 
      event: "second_half_start",
      description: "Second half throw-in ceremony"
    },
    {
      timestamp: "83:00",
      event: "match_end",
      description: "End of organized play"
    }
  ],

  // Utility functions for web apps
  utils: {
    // Convert timestamp to seconds
    timestampToSeconds: (timestamp) => {
      const [minutes, seconds] = timestamp.split(':').map(Number);
      return minutes * 60 + seconds;
    },
    
    // Convert seconds to timestamp
    secondsToTimestamp: (seconds) => {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },
    
    // Get phase for any timestamp
    getPhaseAtTime: (timestamp) => {
      const seconds = gaaMatchTimeline.utils.timestampToSeconds(timestamp);
      
      if (seconds < 15) return 'preMatch';
      if (seconds < 33 * 60) return 'firstHalf';
      if (seconds < 48 * 60 + 45) return 'halftimeBreak';
      if (seconds < 83 * 60) return 'secondHalf';
      return 'postMatch';
    },
    
    // Get progress percentage for timeline scrubber
    getProgressPercentage: (timestamp) => {
      const seconds = gaaMatchTimeline.utils.timestampToSeconds(timestamp);
      const totalSeconds = gaaMatchTimeline.utils.timestampToSeconds("84:00");
      return (seconds / totalSeconds) * 100;
    }
  },

  // Statistics
  statistics: {
    firstHalfDuration: "32:45",
    halftimeDuration: "15:45",
    secondHalfDuration: "34:15", 
    totalMatchTime: "67:00",
    coveragePercentage: 79.8
  },

  // Metadata
  metadata: {
    analysisMethod: "manual_correction",
    clipsAnalyzed: 337,
    clipInterval: "15_seconds",
    sport: "GAA_football",
    aiModelUsed: "gemini_2.5_flash",
    aiAccuracy: "poor_requires_manual_correction"
  }
};

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = gaaMatchTimeline;
}

if (typeof window !== 'undefined') {
  window.gaaMatchTimeline = gaaMatchTimeline;
} 