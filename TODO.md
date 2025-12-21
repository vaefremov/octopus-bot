# What to implement and fix (as of 21 Dec 2025)

## 1. Health check script for periodic run
Implement it so that only errors and dangerous conditions are reported.
If no dangerous conditions were met, then the script should exit with status 0 without any output.
Implementation should be a separate script placed in the `scripts` directory.

### List of filesystems and corresponding conditions on free space

List of filesystems and corresponding conditions on free space should be specified in the script
like:
```
filesystems=(/ 10 /tmp 5 /hdd1 5 /var 5)
```
This means that there should be not less than 10% free space on /, not less than 5% free space on /tmp,
not less than 5% free space on /hdd1, etc.

### Presence of specific processes and its number
Presence of specific processes and its number should be specified in the script
like:
```
processes=(nginx 1 mysql 2)
```

That is, there should be not less than 1 nginx process and not less than 2 mysql processes.
Report if any of the conditions is not met.

### Swap usage
Significant swap usage should be reported. If swap usage is greater than the specified threshold, 
then this condition should be reported.


## 2. Logs rotation
Logs should be rotated daily.

## 3. Start scripts at a specified time
Some of periodic scripts should be run at a specified time.
