#!/usr/bin/env bash
# Starts the full simulation (Phase 3) in one tmux session, one window per
# terminal from the guide:
#   dds -> px4 -> spawn -> bridge -> orbit -> yolo -> shell
#
# Usage:  ./scripts/run_sim.sh          start and attach
#         ./scripts/run_sim.sh stop     stop everything
# tmux basics: Ctrl+b then n/p = next/previous window, Ctrl+b d = detach.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="drone"

if [ "${1:-}" = "stop" ]; then
    tmux kill-session -t "${SESSION}" 2>/dev/null && echo "Stopped." || echo "Not running."
    pkill -f px4_sitl_default/bin/px4 2>/dev/null || true
    pkill -f MicroXRCEAgent 2>/dev/null || true
    pkill -f "gz sim" 2>/dev/null || true
    exit 0
fi

command -v tmux >/dev/null || { echo "tmux missing: sudo apt install tmux"; exit 1; }
[ -x "${HOME}/px4-venv/bin/python" ] || { echo "Run ./scripts/setup_all.sh first."; exit 1; }
[ -f "${ROOT}/ros2_ws/install/setup.bash" ] || { echo "ROS 2 workspace not built. Run ./scripts/setup_all.sh first."; exit 1; }

if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "WARNING: no DISPLAY found - Gazebo GUI cannot open. On WSL you need WSL2 + WSLg (Windows 11 / recent Windows 10)."
fi
# No GPU rendering available -> fall back to software rendering
if ! command -v nvidia-smi >/dev/null 2>&1 && [ ! -e /dev/dri/card0 ] && [ ! -e /dev/dxg ]; then
    export LIBGL_ALWAYS_SOFTWARE=1
fi

ENV_CMD="cd '${ROOT}' && source config/project.env && source /opt/ros/humble/setup.bash \
&& source '${HOME}/px4-venv/bin/activate' && source ros2_ws/install/setup.bash \
&& export GZ_SIM_RESOURCE_PATH='${ROOT}/gazebo/worlds:${ROOT}/gazebo/models:${HOME}/.gz/models'\${GZ_SIM_RESOURCE_PATH:+:\$GZ_SIM_RESOURCE_PATH}"

tmux kill-session -t "${SESSION}" 2>/dev/null || true
tmux new-session -d -s "${SESSION}" -n shell
tmux send-keys -t "${SESSION}:shell" "${ENV_CMD}" C-m
tmux send-keys -t "${SESSION}:shell" "echo 'Start mission: ros2 service call /orbit/start std_srvs/srv/Trigger \"{}\"'; echo 'Abort+land:    ros2 service call /orbit/abort std_srvs/srv/Trigger \"{}\"'" C-m

launch() {  # window-name  command
    tmux new-window -t "${SESSION}" -n "$1"
    tmux send-keys -t "${SESSION}:$1" "${ENV_CMD} && $2" C-m
}

launch dds    'MicroXRCEAgent udp4 -p 8888'
launch px4    'cd "${PX4_DIR}" && PX4_SYS_AUTOSTART=4002 PX4_GZ_MODEL=x500_depth ./build/px4_sitl_default/bin/px4'
launch spawn  './scripts/spawn_objects.sh'
launch bridge 'until gz topic -l 2>/dev/null | grep -qx /camera; do echo "waiting for /camera..."; sleep 3; done; ros2 run ros_gz_image image_bridge /camera --ros-args -r /camera:=/camera/image_raw -p qos:=sensor_data'
launch orbit  'sleep 30; ros2 launch px4_orbit_inspection orbit_demo.launch.py'
if [ -f "${ROOT}/perception/yolo/uav_camera_det.py" ]; then
    launch yolo 'until ros2 topic list 2>/dev/null | grep -qx /camera/image_raw; do sleep 3; done; cd perception/yolo && python -u uav_camera_det.py'
fi

tmux select-window -t "${SESSION}:shell"
echo "Session '${SESSION}' started. Attaching... (stop everything later with: ./scripts/run_sim.sh stop)"
tmux attach -t "${SESSION}"
