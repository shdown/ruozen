#!/usr/bin/env bash

set -e

cd -- "$(dirname "$(readlink "$0" || printf '%s\n' "$0")")"

srv_pid=0

terminate_server() {
    if (( srv_pid )); then
        kill $srv_pid || true
        wait $srv_pid || true
        srv_pid=0
    fi
}

trap terminate_server EXIT

$PYTHON3 ./main.py &
srv_pid=$!

echo >&2 "Waiting for server..."

is_ok=1
while ! curl -s http://localhost:8999/api/ping -o /dev/null; do
    if ! kill -0 $srv_pid; then
        is_ok=0
        break
    fi
    echo >&2 "..."
    sleep 0.1
done

if (( is_ok )); then
    echo >&2 "OK, running quick_runner"
    $PYTHON3 ./quick_runner.py || true
    echo >&2 "OK, quick_runner exited"
    exit 0
else
    echo >&2 "Server failed"
    exit 1
fi
