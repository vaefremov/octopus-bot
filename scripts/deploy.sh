#!/bin/bash 
# Example long-running script that simulates deployment
# This script demonstrates streaming output via the bot

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CONFIG="$SCRIPT_DIR/deploy.conf"


if [ -n "${CONFIG:-}" ] && [ -f "$CONFIG" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG"
fi

export PGPASSWORD=${PGPASSWORD:-"password"}
export PGUSER=${PGUSER:-postgres}
export PGHOST=${PGHOST:-localhost}

PGDATABASE=${PGDATABASE:-"testdb_oct"}

APP_HOME=${APP_HOME:-/hdd1/DiPreview/DiBack2/}
WORK_DIR=${WORK_DIR:-/hdd5/BACKUPS}
REPOSITORY=${REPOSITORY:-/hdd1/DiPreview/Repositories/DI_projects/DiBack1/}

export DI1_DATABASE_URL=${DI1_DATABASE_URL:-"postgresql://postgres:${PGPASSWORD}@localhost:5432/testdb_oct"}
export DI1_DATABASE_ECHO=${DI1_DATABASE_ECHO:-false}
export PYTONPATH=$APP_HOME

. $APP_HOME/venv/bin/activate

TAG=${TAG:-"test_run"}
SERVER_PORT=${SERVER_PORT:-9992}
WORKERS=${WORKERS:-3}

# Create a lockfile to indicate deployment in progress so health checks can skip reporting
# Lock contains the PID of this deploy script. Paths can be overridden via
# environment variable DEPLOY_LOCK or deploy_lock in deploy.conf
DEPLOY_LOCK=${DEPLOY_LOCK:-"$SCRIPT_DIR/.deploy.lock"}
DEFAULT_DEPLOY_LOCK="/tmp/octopus_deploy.lock"
if [ -z "${DEPLOY_LOCK:-}" ]; then
  DEPLOY_LOCK="$DEFAULT_DEPLOY_LOCK"
fi

# If lock exists and pid is alive, abort to avoid concurrent deployments
if [ -f "$DEPLOY_LOCK" ]; then
  existing_pid=$(cat "$DEPLOY_LOCK" 2>/dev/null || true)
  if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
    echo "Deploy already in progress (pid $existing_pid). Exiting." >&2
    exit 1
  else
    # Stale lockfile, remove it
    rm -f "$DEPLOY_LOCK"
  fi
fi

# Write our PID into the lockfile
echo "$$" >"$DEPLOY_LOCK"

# Ensure lockfile is removed on exit (normal or error)
cleanup_deploy_lock() {
  rm -f "$DEPLOY_LOCK"
}
trap cleanup_deploy_lock EXIT

# 0. Stop preview server

$APP_HOME/stop_g.sh -t $TAG

# 1. Recreate database

cd $WORK_DIR

psql -q < ./create_testdb_oct.sql

python $APP_HOME/create_model.py

# 2. Transfer data from octopus
cd testdb_to_octopus
rm *.sql
./data_transfer.sh

# 3. Set up alembic
cd $REPOSITORY
VERSION=$(ls -tr1 alembic/versions/ | grep -v __pycache__ | tail -1 | sed 's/_.*$//')
python init_alembic_version.py --version $VERSION   
alembic upgrade head

python import_model_updates.py --clean model_updates.csv

# 3.1 Collect orphaned files in data storage not mentioned in source database.
# TBD!

# 4. Start preview server
cd $APP_HOME
# Start preview server in a new session so it won't be terminated when this script exits.
# Redirect stdout/stderr to a log file and run in background; disown the job so it is not
# tracked by the shell's job table.
setsid "$APP_HOME/start_g.sh" -t $TAG -p $SERVER_PORT -w $WORKERS >"$APP_HOME/nohup.out" 2>&1 &
pid="$!"
# Remove job from shell job table (if supported) so it won't receive SIGHUP from the shell.
disown "$pid" 2>/dev/null || true

echo "Started DI server with pid $pid, tag $TAG and port $SERVER_PORT. Log file: $APP_HOME/nohup.out"
