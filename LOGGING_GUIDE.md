# Enhanced Logging Guide

The DateSpot Aggregator now includes comprehensive step-by-step logging to help you debug and monitor the workflow execution.

## What You'll See

### Main Workflow Structure
```
================================================================================
🚀 STARTING DATESPOT AGGREGATOR WORKFLOW
🕐 Start Time: 2024-01-15 14:30:00
================================================================================

🔵 STEP 1/8: FETCHING EVENTS FROM BLOGTO
   ⏰ Step started at: 14:30:00
   📋 Fetching events for the next 7 days with rate limiting...
   📅 Processing date 1/7: 2024-01-15
   ✓ Completed 2024-01-15: 45 events fetched
   📅 Processing date 2/7: 2024-01-16
   ⏳ Waiting 5 seconds for rate limiting...
   ✓ Completed 2024-01-16: 38 events fetched
   ✅ STEP 1 COMPLETED in 42.3s
   📊 Result: 315 events across 7 dates
------------------------------------------------------------

🔵 STEP 2/8: VALIDATING AND CLEANING DATA
   ⏰ Step started at: 14:30:42
   📋 Filtering events with required fields and adding numerical time...
   📅 Validating 45 events for 2024-01-15
   ✓ 2024-01-15: 42 valid, 3 invalid events
   📅 Validating 38 events for 2024-01-16
   ✓ 2024-01-16: 35 valid, 3 invalid events
   ✅ STEP 2 COMPLETED in 2.1s
   📊 Result: 298/315 events passed validation
------------------------------------------------------------

🔵 STEP 3/8: ADDING LOCATION COORDINATES
   ⏰ Step started at: 14:30:45
   📋 Geocoding venue addresses using Google Maps API...
   📅 Processing 42 venues for 2024-01-15
   🏢 Geocoding venue 1/42: "CN Tower"
   ✓ Success: CN Tower → 43.6426, -79.3871
   🏢 Geocoding venue 2/42: "Royal Ontario Museum"
   ✓ Success: Royal Ontario Museum → 43.6677, -79.3948
   ✗ Failed: Unknown Venue
   ✓ Completed 2024-01-15: 40/42 venues geocoded
   ✅ STEP 3 COMPLETED in 125.7s
   📊 Result: 285/298 venues geocoded successfully
------------------------------------------------------------

🔵 STEP 4/8: ENRICHING WITH WEATHER DATA
   ⏰ Step started at: 14:32:51
   📋 Fetching weather data from Visual Crossing API...
   🌐 Fetching weather data for 7 dates concurrently...
   ✓ Weather for 2024-01-15: 12°C max, Partly cloudy
   ✓ Weather for 2024-01-16: 8°C max, Rain
   📊 Weather summary: 7/7 dates successful
   ✅ STEP 4 COMPLETED in 3.2s
   📊 Result: Weather data fetched for 7/7 dates
------------------------------------------------------------

🔵 STEP 5/8: CATEGORIZING EVENTS WITH AI
   ⏰ Step started at: 14:32:54
   📋 Using Claude AI to categorize events into predefined categories...
   🤖 Sending categorization request to Claude AI...
   📊 Request size: 15234 characters
   ✓ Successfully received categorization from Claude AI
   📊 Response size: 8456 characters
   ✓ Successfully parsed AI categorization response
   📊 AI categorized 285 events
   ✅ STEP 5 COMPLETED in 8.7s
   📊 Result: 285 events categorized by AI
------------------------------------------------------------

🔵 STEP 6/8: MERGING EVENT DATA WITH CATEGORIES
   ⏰ Step started at: 14:33:03
   📋 Combining event data with AI-generated categories...
   ✅ STEP 6 COMPLETED in 0.3s
   📊 Result: 275/285 events successfully categorized
------------------------------------------------------------

🔵 STEP 7/8: FILTERING UNWANTED CATEGORIES
   ⏰ Step started at: 14:33:03
   📋 Removing events in excluded categories: ['Camps & Kids Programs', 'Seniors Programs']
   ✅ STEP 7 COMPLETED in 0.1s
   📊 Result: 268/275 events after filtering
------------------------------------------------------------

🔵 STEP 8/8: PUBLISHING TO GITHUB
   ⏰ Step started at: 14:33:04
   📋 Publishing schema to gregmckenzie88/DateSpot-Schema/api/schema.js
   🔍 Checking for existing file...
   ✓ Found existing file with SHA: a1b2c3d4...
   📝 Preparing JavaScript function code...
   📊 Function code size: 45673 characters
   🚀 Publishing to gregmckenzie88/DateSpot-Schema/api/schema.js...
   ✓ Successfully published to GitHub
   📊 Commit SHA: e5f6g7h8
   ✅ STEP 8 COMPLETED in 2.1s
   📊 Result: Schema successfully published to GitHub

================================================================================
🎉 WORKFLOW COMPLETED SUCCESSFULLY
🕐 Total Duration: 182.2 seconds (3.0 minutes)
📊 Final Result: 268 events across 7 dates
================================================================================
```

## Emoji Legend

### Step Status
- 🔵 **Step in progress**
- ✅ **Step completed successfully**
- ⚠️ **Step completed with warnings**
- ❌ **Step failed**

### Activities
- 📅 **Date processing**
- 🏢 **Venue geocoding**
- 🌐 **API requests**
- 🤖 **AI processing**
- 📝 **File operations**
- 🔍 **Checking/validation**
- 🚀 **Publishing/deployment**

### Results
- ✓ **Success**
- ✗ **Failure**
- ⏳ **Waiting/delay**
- ⏰ **Timing information**
- 📊 **Statistics/metrics**

## Error Scenarios

### API Failures
```
🔵 STEP 1/8: FETCHING EVENTS FROM BLOGTO
   ⏰ Step started at: 14:30:00
   📅 Processing date 1/7: 2024-01-15
   ❌ STEP 1 FAILED: No events fetched from BlogTO API

================================================================================
💥 WORKFLOW FAILED
❌ Error: HTTP 500 from BlogTO API
🕐 Failed after: 15.3 seconds
================================================================================
```

### Geocoding Issues
```
🔵 STEP 3/8: ADDING LOCATION COORDINATES
   🏢 Geocoding venue 1/42: "Invalid Venue Name"
   ✗ Failed: Invalid Venue Name
   🏢 Geocoding venue 2/42: "CN Tower"
   ✓ Success: CN Tower → 43.6426, -79.3871
```

### AI Processing Problems
```
🔵 STEP 5/8: CATEGORIZING EVENTS WITH AI
   🤖 Sending categorization request to Claude AI...
   ❌ Failed to parse AI response as JSON: Expecting ',' delimiter
   📄 AI response: {"results_by_date": {"2024-01-15": [incomplete...
```

## Viewing Logs

### Real-time in Docker
```bash
./docker-run.sh logs
```

### Real-time locally
```bash
python main.py
```

### Scheduled runs
```bash
./docker-run.sh schedule
./docker-run.sh logs
```

## Debugging Tips

1. **Step Failures**: Look for the ❌ emoji to identify which step failed
2. **Timing Issues**: Check ⏰ timestamps to identify slow operations
3. **Data Flow**: Follow 📊 statistics to see data transformation at each step
4. **API Problems**: Look for ✗ symbols in API call logs
5. **Rate Limiting**: Watch for ⏳ delay messages

## Log Levels

The application uses these log levels:
- **INFO**: Step progress, success messages
- **WARNING**: Non-critical issues (⚠️)
- **ERROR**: Failures and exceptions (❌)
- **DEBUG**: Detailed debugging information (enable with DEBUG=1)

## Customizing Logging

To enable debug logging:
```bash
export DEBUG=1
python main.py
```

Or in Docker:
```yaml
environment:
  - DEBUG=1
```
