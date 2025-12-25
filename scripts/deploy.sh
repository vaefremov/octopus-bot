#!/bin/bash -x
# Example long-running script that simulates deployment
# This script demonstrates streaming output via the bot

export PGPASSWORD="qwerty"
export PGUSER=postgres
export PGHOST=localhost

PGDATABASE="testdb2"
export PYTONPATH=/hdd1/DiPreview/DiBack1/

APP_HOME=/hdd1/DiPreview/DiBack1/
WORK_DIR=/hdd5/BACKUPS
REPOSITORY=/hdd1/DiPreview/Repositories/DI_projects/DiBack1/

DI1_DATABASE_URL='postgresql://postgres:qwerty@localhost:5432/testdb2'

. /hdd1/DiPreview/DiBack1/venv/bin/activate

# 0. Stop preview server

$APP_HOME/stop_g.sh -t preview

# 1. Recreate database

cd $WORK_DIR

psql < ./create_testdb2.sql

python /hdd1/DiPreview/DiBack1/create_model.py

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

