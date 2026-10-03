#!/usr/bin/env bash


# =============================================================================
# Project   : Quadcopter Autonomous Inspection (UM6P Internship)
# Author    : Dr. Abdellah TNOURJI
# Website   : https://www.abdellahtnourji.com/
# Date      : [Date, Sep 2026]

# License   : UM6P
# =============================================================================


set -euo pipefail

source "$(dirname "$0")/../config/project.env"

echo "========================================"
echo "UM6P internship system check"
echo "========================================"

if [ "$(lsb_release -rs)" != "22.04" ]; then
    echo "ERROR: Ubuntu 22.04 is required."
    echo "Detected: $(lsb_release -ds)"
    exit 1
fi

if [ "$(uname -m)" != "x86_64" ]; then
    echo "ERROR: This setup expects an x86_64 computer."
    exit 1
fi

if [ ! -f /opt/ros/humble/setup.bash ]; then
    echo "ERROR: ROS 2 Humble is not installed."
    exit 1
fi

source /opt/ros/humble/setup.bash

echo "[OK] Ubuntu: $(lsb_release -ds)"
echo "[OK] Architecture: $(uname -m)"
echo "[OK] ROS distribution: ${ROS_DISTRO}"
echo "[OK] Python: $(python3 --version)"
echo "[OK] Project root: ${INTERNSHIP_ROOT}"
echo "[OK] ROS_DOMAIN_ID: ${ROS_DOMAIN_ID}"

if command -v nvidia-smi >/dev/null 2>&1; then
    echo "[OK] NVIDIA driver detected"
    nvidia-smi --query-gpu=name,driver_version \
        --format=csv,noheader
else
    echo "[INFO] NVIDIA GPU not detected."
    echo "The simulation may still run using another graphics device."
fi

echo
echo "Initial system check passed."
