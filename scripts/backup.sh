#!/bin/bash
#  Backup script
# This script is a one-time script that performs backups

WHERE_BACKUP=/hdd5/BACKUPS

echo "Starting backup process..."
echo "Backup will be created here: $WHERE_BACKUP"
sleep 1
DB_NAME1=octopus
BACKUP_NAME="${DB_NAME1}_"$(date +%Y-%m-%d_%H-%M-%S).sql.gz
BACKUP_TO=$WHERE_BACKUP/$BACKUP_NAME
echo "Backing up PostgreSQL database to $BACKUP_TO"

pg_dump -U postgres -h localhost --file=$BACKUP_TO --create --clean --verbose $DB_NAME1
gzip $BACKUP_TO

echo "$DB_NAME1 Backup completed successfully!"

echo "Backup size: $(du -h $BACKUP_TO | awk '{print $1}')"
