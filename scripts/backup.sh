#!/bin/bash
#  Backup script
# This script is a one-time script that performs backups

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CONFIG="$SCRIPT_DIR/backup.conf"


if [ -n "${CONFIG:-}" ] && [ -f "$CONFIG" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG"
fi

WHERE_BACKUP=${WHERE_BACKUP:-/hdd5/BACKUPS}
DB_NAMES=${DB_NAMES:-octopus octopus_test}

export PGPASSWORD=${PGPASSWORD:-"password_should_be_secret"}
export PGUSER=${PGUSER:-postgres}
export PGHOST=${PGHOST:-localhost}

echo "Starting backup process..."
echo "Backup will be created here: $WHERE_BACKUP"
sleep 1

for DB_NAME in $DB_NAMES; do
  BACKUP_NAME="${DB_NAME}_"$(date +%Y-%m-%d_%H-%M-%S).sql
  BACKUP_TO=$WHERE_BACKUP/$BACKUP_NAME
  echo "Backing up PostgreSQL database to $BACKUP_TO"

  if pg_dump --file=$BACKUP_TO --create --clean "$DB_NAME"; then
    gzip "$BACKUP_TO"
    echo "$DB_NAME Backup completed successfully!"
    echo "Backup size: $(du -h ${BACKUP_TO}.gz | awk '{print $1}')"
  else
    echo "$DB_NAME Backup FAILED!"
  fi
done
