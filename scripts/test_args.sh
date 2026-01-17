#!/bin/bash

echo "Script executed with arguments: $@"

# Print each argument on a separate line
for arg in "$@"; do
    echo "Argument: $arg"
done

echo "Test script completed."