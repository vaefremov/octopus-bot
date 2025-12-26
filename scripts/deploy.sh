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

PGDATABASE=${PGDATABASE:-"testdb2"}
export PYTONPATH=/hdd1/DiPreview/DiBack1/

APP_HOME=${APP_HOME:-/hdd1/DiPreview/DiBack1/}
WORK_DIR=${WORK_DIR:-/hdd5/BACKUPS}
REPOSITORY=${REPOSITORY:-/hdd1/DiPreview/Repositories/DI_projects/DiBack1/}

export DI1_DATABASE_URL=${DI1_DATABASE_URL:-"postgresql://postgres:${PGPASSWORD}@localhost:5432/testdb2"}
export DI1_DATABASE_ECHO=${DI1_DATABASE_ECHO:-false}

. $APP_HOME/venv/bin/activate

# 0. Stop preview server

$APP_HOME/stop_g.sh -t preview

# 1. Recreate database

cd $WORK_DIR

psql < ./create_testdb2.sql

python $APP_HOME/create_model.py

# 2. Transfer data from octopus
cd testdb_to_octopus
rm *.sql
./data_transfer_testdb2.sh

# 3. Set up alembic
cd $REPOSITORY
VERSION=$(ls -tr1 alembic/versions/ | grep -v __pycache__ | tail -1 | sed 's/_.*$//')
python init_alembic_version.py --version $VERSION   
alembic upgrade head

# 4. Start preview server
cd $APP_HOME
nohup $APP_HOME/start_g.sh -t preview -p 9991 -w 3 &

