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
DB_NAMES=${DB_NAMES:-octopus testdb_oct}

export PGPASSWORD=${PGPASSWORD:-"password_should_be_secret"}
export PGUSER=${PGUSER:-postgres}
export PGHOST=${PGHOST:-localhost}

decimate_backups() {
  local db_name="$1"
  local cutoff_week cutoff_month
  cutoff_week=$(date -d "7 days ago" +%Y-%m-%d)
  cutoff_month=$(date -d "1 month ago" +%Y-%m-%d)

  local file base date_part local_date dow month keep
  declare -A kept_months

  while IFS= read -r file; do
    base=$(basename "$file")
    date_part="${base#${db_name}_}"
    local_date="${date_part%%_*}"

    # Newer than a week: keep everything
    if [[ "$local_date" > "$cutoff_week" || "$local_date" == "$cutoff_week" ]]; then
      continue
    fi

    dow=$(date -d "$local_date" +%u)

    # Between a week and a month: keep weekly (weekend) backups only
    if [[ "$local_date" > "$cutoff_month" || "$local_date" == "$cutoff_month" ]]; then
      if [[ "$dow" == "6" || "$dow" == "7" ]]; then
        continue
      fi
    else
      # Older than a month: keep one weekend backup per calendar month
      month="${local_date%-*}"
      keep=0
      if [[ "$dow" == "6" || "$dow" == "7" ]]; then
        if [[ -z "${kept_months[$month]:-}" ]]; then
          kept_months[$month]=1
          keep=1
        fi
      fi
      if (( ! keep )); then
        rm -f "$file"
        echo "Removed old backup: $file"
      fi
    fi
  done < <(find "$WHERE_BACKUP" -maxdepth 1 -type f -name "${db_name}_*.sql.gz" | sort -r)
}

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

  echo "Applying retention policy for $DB_NAME backups..."
  decimate_backups "$DB_NAME"
done
