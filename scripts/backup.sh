#!/bin/bash
# Example backup script
# This script demonstrates a one-time script that could perform backups

echo "Starting backup process..."
echo "Backup would be created here"
sleep 1

echo "Backing up to /tmp/backup.tar.gz"
echo "Progress: 25%"
sleep 1

echo "Progress: 50%"
sleep 1

echo "Progress: 75%"
sleep 1

echo "Backup completed successfully!"
echo "Backup size: $(du -h /tmp 2>/dev/null | tail -1 || echo 'N/A')"
