# Simple Direct Event Extraction

This directory contains a simplified approach to GAA event detection that cuts out the intermediate steps and goes directly from video clips to structured events.

## The Problem with the Commentator Method

The commentator method had a "telephone game" effect:
1. VLM sees video → describes what happened
2. AI creates commentary from description 
3. AI synthesizes commentary into narrative
4. AI extracts events from narrative

Each step introduced potential errors and hallucinations.

## The Simple Approach

This method goes directly:
**VLM sees video → AI extracts structured events**

## Files

- `1_direct_event_extraction.py` - Direct video-to-events extraction
- `results/direct_events.json` - Raw event output

## Key Differences

1. **No commentary layer** - Skip the narrative generation
2. **JSON output only** - Force structured responses
3. **Conservative detection** - Only report what you clearly see
4. **Precise timing** - Use decimal seconds for exact timing
5. **5 event types only** - Focus on core GAA events

## Event Types Detected

1. **Kickout** - Goalkeeper kicks ball from hands
2. **Shot** - Player attempts to score (with outcome)
3. **Foul** - Clear foul committed
4. **Turnover** - Ball changes possession
5. **Throw_up** - Ball thrown up to restart play

## Usage

```bash
cd simple-event-detection
python 1_direct_event_extraction.py
```

This should produce more accurate, less hallucinated events by removing the narrative interpretation layers. 