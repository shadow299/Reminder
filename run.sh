#!/usr/bin/env bash
# Launcher for the Reminder desktop app.
set -e
DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"
exec /usr/bin/python3 main.py "$@"
