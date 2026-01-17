# compare_ids.sh

This script compares a database object ID with a file-based ID and warns when the difference is less than a given threshold.

## Usage

```bash
./compare_ids.sh
```

The script will:
1. Obtain the next value from the `object_id_seq` database sequence
2. Read an ID from the `start_id.txt` file
3. Compare the difference between these values with a threshold
4. Print a warning if the difference is less than the threshold
5. Produce no output if the difference is greater than or equal to the threshold

## Configuration

The script can be configured using a configuration file. By default, it looks for `compare_ids.conf` in the same directory as the script.

You can also specify a configuration file using the `COMPARE_IDS_CONFIG` environment variable:

```bash
COMPARE_IDS_CONFIG=/path/to/config ./compare_ids.sh
```

### Configuration Options

- `THRESHOLD`: The threshold for warning (default: 1000)
- `START_ID_FILE`: Path to the file containing the ID (default: start_id.txt in current directory)
- Database connection parameters:
  - `PGPASSWORD`: Database password
  - `PGUSER`: Database user (default: postgres)
  - `PGHOST`: Database host (default: localhost)
  - `PGDATABASE`: Database name (default: octopus)

## Example Configuration File

```bash
# Threshold for warning
THRESHOLD=500

# Path to start_id.txt file
START_ID_FILE=/path/to/start_id.txt

# Database connection parameters
PGPASSWORD="your_password"
PGUSER=postgres
PGHOST=localhost
PGDATABASE=octopus
```

## Exit Codes

- 0: Success (no warning or warning printed)
- 1: Error (invalid configuration, database connection failed, etc.)