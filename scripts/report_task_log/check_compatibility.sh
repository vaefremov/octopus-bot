#!/usr/bin/env bash

# check_compatibility.sh
# Checks if the system has all required dependencies for report_task_log.sh

echo "=== Checking System Compatibility for report_task_log.sh ==="
echo

# Check bash version
echo "1. Checking Bash version..."
bash_version=$(bash --version | head -n1)
echo "   Found: $bash_version"

bash_major=$(bash --version | head -n1 | grep -oE '[0-9]+\.[0-9]+' | head -n1 | cut -d. -f1)
bash_minor=$(bash --version | head -n1 | grep -oE '[0-9]+\.[0-9]+' | head -n1 | cut -d. -f2)

if [[ $bash_major -ge 3 ]] && [[ $bash_minor -ge 2 ]]; then
    echo "   ✓ Compatible (requires 3.2+)"
else
    echo "   ✗ Incompatible (requires 3.2+, found $bash_major.$bash_minor)"
fi
echo

# Check for required commands
required_commands=("stat" "dd" "cat" "flock")
all_found=true

echo "2. Checking required commands..."
for cmd in "${required_commands[@]}"; do
    if command -v "$cmd" &> /dev/null; then
        echo "   ✓ $cmd found: $(command -v $cmd)"
    else
        echo "   ✗ $cmd NOT FOUND"
        all_found=false
        
        if [[ "$cmd" == "flock" ]] && [[ "$(uname)" == "Darwin" ]]; then
            echo "     Install on macOS: brew install flock"
        fi
    fi
done
echo

# Check OS
echo "3. Checking operating system..."
os=$(uname)
echo "   OS: $os"

if [[ "$os" == "Darwin" ]]; then
    echo "   Platform: macOS"
    echo "   Note: stat command uses BSD syntax (-f %z)"
elif [[ "$os" == "Linux" ]]; then
    echo "   Platform: Linux"
    echo "   Note: stat command uses GNU syntax (-c %s)"
else
    echo "   Platform: Unknown (may have compatibility issues)"
fi
echo

# Summary
echo "=== Summary ==="
if $all_found && [[ $bash_major -ge 3 ]] && [[ $bash_minor -ge 2 ]]; then
    echo "✓ System is compatible with report_task_log.sh"
    exit 0
else
    echo "✗ System has compatibility issues. Please install missing dependencies."
    exit 1
fi
