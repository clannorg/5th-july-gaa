# Commentator Method - Experimental Approach

## Overview
This directory contains an experimental approach to GAA match analysis using natural language commentary to detect all events simultaneously.

## The Approach
Instead of rigid event detection, this method:
1. **Natural Commentary**: AI describes what's happening in each 15-second clip
2. **Flowing Narrative**: Weaves individual clips into continuous match commentary  
3. **Event Extraction**: Extracts all events (kickouts, shots, turnovers, etc.) from the narrative

## Processing Pipeline
1. **`1_simple_commentary.py`** - Generates natural commentary for each 15-second clip
2. **`2_narrative_synthesis.py`** - Weaves clips into flowing match narrative
3. **`3_extract_events.py`** - Extracts events from narrative into GAA Events Schema JSON

## Advantages
- **Natural flow**: Reads like real sports commentary
- **Contextual understanding**: Events understood in match context
- **Precise timing**: Captures exact moments (especially goalkeeper actions)
- **Multiple events**: Detects all event types simultaneously

## Current Issues
- **Over-detection**: Too many kickouts (25 in 10 minutes vs realistic 2-4)
- **Classification**: Needs stricter event definitions
- **Context**: May miss that some actions aren't official restarts

## Next Steps
- Experiment with stricter event classification
- Add context checking for realistic event frequency
- Balance natural commentary with accurate event detection 