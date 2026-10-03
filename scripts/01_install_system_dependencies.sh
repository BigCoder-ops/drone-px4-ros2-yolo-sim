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

sudo apt update

sudo apt install -y \
    git \
    git-lfs \
    curl \
    wget \
    unzip \
    zip \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    python3-argcomplete \
    python3-pytest \
    python3-numpy \
    python3-yaml \
    python3-lark \
    python3-jinja2 \
    ros-humble-rclpy \
    ros-humble-std-srvs \
    ros-humble-geometry-msgs \
    ros-humble-nav-msgs \
    ros-humble-visualization-msgs \
    ros-humble-rviz2 \
    ros-humble-rqt \
    ros-humble-rqt-graph

if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init
fi

rosdep update

git lfs install

echo
echo "System dependencies installed."
