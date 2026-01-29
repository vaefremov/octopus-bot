# Plan for report_task_log.sh

## Problem Analysis
- Monitor output from an independently running `long_task` process
- Fetch only NEW lines since the last run of the monitoring script
- Output can be run from terminal or programmatically (e.g., Telegram bot)
- Handle burst output patterns with pauses

## Key Challenges
1. **Process independence**: `long_task` runs separately, we need to attach to its output
2. **State tracking**: Must remember which lines we've already reported
3. **Incremental reading**: Only fetch new lines since last run

## Solution Approach

### Option 1: Redirect output to a file (Recommended)
- Start `long_task` with output redirected to a log file
- Track the last read position in the file
- Read from last position to current end

**Pros**: 
- Simple and reliable
- Works with any process
- Easy to implement state tracking

**Cons**: 
- Requires `long_task` to be started with redirection

### Option 2: Attach to process stdout (Complex)
- Use `/proc/<pid>/fd/1` to read stdout
- Requires knowing the PID

**Cons**: 
- Doesn't work reliably for already-buffered output
- Process may not be readable this way

## Chosen Solution: File-based with Position Tracking

### Implementation Details

1. **Configuration**
   - Log file path: where `long_task` writes its output
   - State file: stores the last read byte position
   
2. **State Management**
   - Store last read byte offset in a state file
   - On first run, start from beginning (or end, configurable)
   
3. **Reading Logic**
   - Read state file to get last position
   - Seek to that position in log file
   - Read from position to end
   - Update state file with new position
   
4. **Edge Cases**
   - Log file doesn't exist yet
   - Log file was rotated (smaller than last position)
   - State file doesn't exist (first run)
   - Concurrent access (use flock)

### Script Structure

```
report_task_log.sh
├── Parse arguments (log file path)
├── Define state file location
├── Lock state file (prevent concurrent runs)
├── Read last position from state file
├── Handle log rotation (if file is smaller)
├── Read new content from log file
├── Output new content to stdout
├── Update state file with new position
└── Release lock
```

### Usage Pattern

```bash
# Start long_task with output redirection
long_task > /tmp/long_task.log 2>&1 &

# Run reporting script
./report_task_log.sh /tmp/long_task.log

# Run again later to get only new lines
./report_task_log.sh /tmp/long_task.log
```

### Features to Implement
- ✅ Track last read position
- ✅ Handle missing files gracefully
- ✅ Handle log rotation
- ✅ Prevent concurrent runs with flock
- ✅ Accept log file path as argument
- ✅ Clean, readable output
- ✅ Error handling

## Alternative: Named Pipe Approach (Bonus)
Could also provide a version using named pipes (FIFOs) for real-time streaming, but this adds complexity and doesn't fit the "fetch since last run" requirement as well.