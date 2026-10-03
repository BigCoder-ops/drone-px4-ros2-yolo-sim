#!/usr/bin/env bash
# Spawns the car, pickup and person inspection models into the running
# Gazebo world (Phase 3, Terminal 3). Waits until the world is up.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${ROOT}/gazebo/models"

echo "Waiting for the Gazebo world (up to 4 minutes)..."
WORLD_NAME=""
for _ in $(seq 1 120); do
    WORLD_NAME="$(gz service -l 2>/dev/null | grep -oP '(?<=/world/)[^/]+(?=/create)' | head -n 1 || true)"
    [ -n "${WORLD_NAME}" ] && break
    sleep 2
done
[ -n "${WORLD_NAME}" ] || { echo "Gazebo world not found. Is PX4 running?"; exit 1; }
echo "World: ${WORLD_NAME}"

spawn() {  # name  model_dir_name  x  y
    local sdf="${MODEL_DIR}/$2/model.sdf"
    if [ ! -f "${sdf}" ]; then
        echo "WARNING: ${sdf} not found, skipping $1"
        return 0
    fi
    gz service -s "/world/${WORLD_NAME}/create" \
        --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
        --req "name: '$1', sdf_filename: '${sdf}', pose: {position: {x: $3, y: $4, z: 0.0}, orientation: {w: 1.0, x: 0.0, y: 0.0, z: 0.0}}" \
        || echo "WARNING: spawning $1 failed"
}

spawn inspection_car     inspection_hatchback  8.0  0.0
spawn inspection_pickup  inspection_pickup    -5.0  2.5
spawn inspection_person  inspection_person     0.0  6.0
echo "Objects spawned."
