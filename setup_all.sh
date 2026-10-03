#!/usr/bin/env bash
# =============================================================================
# setup_all.sh - one-command setup for the UM6P drone internship simulation
#
# Automates, in order (exactly as written in the installation guides):
#   Phase 0 : Ubuntu 22.04 base tools, locale, ROS 2 Humble, rosdep
#   Phase 1 : ~/px4-venv with pinned NumPy/OpenCV/PyTorch/Ultralytics/MAVSDK
#   Phase 3 : PX4 release/1.15 + px4_msgs + Micro XRCE-DDS Agent (pinned
#             commits via scripts/02_download_sources.sh), PX4 SITL build,
#             DDS Agent build, ROS 2 workspace build, .bashrc block,
#             x500_depth downward-camera patch.
#
# Usage:   ./scripts/setup_all.sh [--cpu | --gpu]
#   --cpu  force CPU-only PyTorch
#   --gpu  force CUDA 12.6 PyTorch (needs a working nvidia-smi)
#   (default: auto-detect with nvidia-smi)
#
# Safe to re-run: finished steps are skipped (state in .setup_state/).
# To force a step again, delete its file in .setup_state/.
# =============================================================================
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_ROOT="${HOME}/quard_um6p_intership"
TORCH_MODE="auto"

for arg in "$@"; do
    case "$arg" in
        --cpu) TORCH_MODE="cpu" ;;
        --gpu) TORCH_MODE="gpu" ;;
        -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "Unknown option: $arg (use --cpu, --gpu or --help)"; exit 1 ;;
    esac
done

STATE="${ROOT}/.setup_state"
mkdir -p "${STATE}" "${ROOT}/logs"
exec > >(tee -a "${ROOT}/logs/setup_all.log") 2>&1

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33mWARNING: %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
is_done() { [ -f "${STATE}/$1" ]; }
mark()    { touch "${STATE}/$1"; }

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
APT_GET="sudo -E apt-get"

# -----------------------------------------------------------------------------
# 0. Pre-flight checks
# -----------------------------------------------------------------------------
preflight() {
    log "Pre-flight checks"
    [ "$(id -u)" -ne 0 ] || die "Do not run as root. Run as a normal user; the script calls sudo itself."
    command -v sudo >/dev/null || die "sudo is required."
    [ "$(uname -m)" = "x86_64" ] || die "x86_64 required (found $(uname -m))."

    . /etc/os-release
    [ "${VERSION_ID:-}" = "22.04" ] || die "Ubuntu 22.04 is required (found ${PRETTY_NAME:-unknown}). In WSL: wsl --install -d Ubuntu-22.04"

    if [ "${ROOT}" != "${EXPECTED_ROOT}" ]; then
        die "The project must live at ${EXPECTED_ROOT} (it is at ${ROOT}). Move/clone it there and re-run."
    fi

    if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "Running inside WSL."
        grep -qi 'WSL2' /proc/version 2>/dev/null || warn "Could not confirm WSL2. Gazebo needs WSL2 + WSLg."
    fi

    local free_gb
    free_gb=$(df -BG --output=avail "${HOME}" | tail -1 | tr -dc '0-9')
    [ "${free_gb:-0}" -ge 25 ] || warn "Only ${free_gb} GB free in ${HOME}. PX4 + Gazebo + PyTorch need roughly 20-25 GB."

    sudo -v
    # keep sudo alive during long builds
    ( while true; do sudo -n true; sleep 50; kill -0 "$$" 2>/dev/null || exit; done ) 2>/dev/null &

    if [ "${TORCH_MODE}" = "auto" ]; then
        if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
            TORCH_MODE="gpu"
        else
            TORCH_MODE="cpu"
        fi
    fi
    echo "PyTorch mode: ${TORCH_MODE}"
}

# -----------------------------------------------------------------------------
# Phase 0 - Ubuntu base + ROS 2 Humble
# -----------------------------------------------------------------------------
phase0_base() {
    is_done phase0_base && { log "Phase 0 (base + ROS 2): already done"; return; }

    log "Phase 0: update Ubuntu"
    ${APT_GET} update
    ${APT_GET} full-upgrade -y
    ${APT_GET} autoremove -y

    log "Phase 0: base development tools"
    ${APT_GET} install -y \
        build-essential cmake ninja-build git git-lfs curl wget unzip zip tree \
        tmux terminator software-properties-common ca-certificates gnupg \
        lsb-release locales python3 python3-pip python3-dev python3-venv \
        python3-setuptools python3-wheel
    git lfs install

    log "Phase 0: UTF-8 locale"
    sudo locale-gen en_US en_US.UTF-8
    sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
    export LANG=en_US.UTF-8

    log "Phase 0: ROS 2 apt source"
    if ! dpkg -s ros2-apt-source >/dev/null 2>&1; then
        sudo add-apt-repository -y universe
        local ver codename
        ver="$(curl -fsS https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
               | grep -F 'tag_name' | awk -F '"' '{print $4}')"
        [ -n "${ver}" ] || die "Could not read the latest ros-apt-source version from GitHub (rate limit?). Retry in a few minutes."
        codename="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}")"
        curl -fL -o /tmp/ros2-apt-source.deb \
            "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ver}/ros2-apt-source_${ver}.${codename}_all.deb"
        sudo dpkg -i /tmp/ros2-apt-source.deb
    fi
    ${APT_GET} update
    ${APT_GET} upgrade -y

    log "Phase 0: ROS 2 Humble desktop + dev tools (large download)"
    ${APT_GET} install -y ros-humble-desktop ros-dev-tools

    log "Phase 0: ROS 2 packages required by the internship"
    ${APT_GET} install -y \
        ros-humble-ros2-control \
        ros-humble-ros2-controllers \
        ros-humble-xacro \
        'ros-humble-ros-gz-*' \
        'ros-humble-*-ros2-control' \
        ros-humble-joint-state-publisher-gui \
        ros-humble-turtlesim \
        ros-humble-robot-localization \
        ros-humble-joy \
        ros-humble-joy-teleop \
        ros-humble-tf-transformations \
        ros-humble-cv-bridge ros-humble-rclpy \
        ros-humble-sensor-msgs ros-humble-image-transport \
        ros-humble-rqt-image-view

    log "Phase 0: system Python helpers (apt, never pip)"
    ${APT_GET} install -y python3-numpy python3-opencv python3-transforms3d

    log "Phase 0: rosdep"
    if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
        sudo rosdep init
    fi
    rosdep update

    mark phase0_base
}

# -----------------------------------------------------------------------------
# Project config + pinned source download (uses the repo's own script)
# -----------------------------------------------------------------------------
load_project_env() {
    [ -f "${ROOT}/config/project.env" ] || die "config/project.env is missing - is this the full repository?"
    set +u
    # shellcheck disable=SC1091
    source "${ROOT}/config/project.env"
    set -u
    : "${PX4_DIR:?PX4_DIR not set by config/project.env}"
    : "${ROS2_WS:?ROS2_WS not set by config/project.env}"
    : "${DDS_AGENT_DIR:?DDS_AGENT_DIR not set by config/project.env}"
    case "${PX4_DIR}${ROS2_WS}${DDS_AGENT_DIR}" in
        *"${HOME}"*) ;;
        *) die "config/project.env contains paths outside ${HOME} (e.g. another user's /home/...). Fix it first." ;;
    esac
}

download_sources() {
    is_done sources && { log "Sources: already downloaded"; return; }
    log "Download PX4 / px4_msgs / Micro-XRCE-DDS-Agent at the pinned commits"
    # Git LFS objects of this repo (YOLO weights etc.), if any
    git -C "${ROOT}" lfs pull 2>/dev/null || true
    chmod +x "${ROOT}/scripts/02_download_sources.sh"
    "${ROOT}/scripts/02_download_sources.sh"

    test "$(git -C "${PX4_DIR}" rev-parse HEAD)" = "$(cat "${ROOT}/config/PX4_COMMIT.txt")" \
        || die "PX4 commit does not match config/PX4_COMMIT.txt"
    test "$(git -C "${ROS2_WS}/src/px4_msgs" rev-parse HEAD)" = "$(cat "${ROOT}/config/PX4_MSGS_COMMIT.txt")" \
        || die "px4_msgs commit does not match config/PX4_MSGS_COMMIT.txt"
    test "$(git -C "${DDS_AGENT_DIR}" rev-parse HEAD)" = "$(cat "${ROOT}/config/DDS_AGENT_COMMIT.txt")" \
        || die "DDS Agent commit does not match config/DDS_AGENT_COMMIT.txt"
    echo "Pinned commits: MATCH"
    mark sources
}

patch_camera() {
    # Phase 3: tilt the x500_depth camera downward by 45 degrees
    local sdf="${PX4_DIR}/Tools/simulation/gz/models/x500_depth/model.sdf"
    local new='<pose>.15 .029 .21 0 0.7854 0</pose>'
    [ -f "${sdf}" ] || { warn "x500_depth model.sdf not found, camera patch skipped"; return; }
    if grep -qF "${new}" "${sdf}"; then
        echo "Camera patch already applied."
    elif grep -qE '<pose>\.12 \.03 \.242 0 0 0</pose>' "${sdf}"; then
        sed -i "s|<pose>\.12 \.03 \.242 0 0 0</pose>|${new}|" "${sdf}"
        echo "Camera patch applied (camera now looks down)."
    else
        warn "Expected camera <pose> line not found in ${sdf}; patch skipped."
    fi
}

# -----------------------------------------------------------------------------
# Phase 1 - px4-venv with pinned AI stack
# -----------------------------------------------------------------------------
phase1_venv() {
    is_done phase1_venv && { log "Phase 1 (px4-venv): already done"; return; }
    local venv="${HOME}/px4-venv"

    log "Phase 1: create ${venv} (system Python, --system-site-packages)"
    if [ ! -x "${venv}/bin/python" ]; then
        /usr/bin/python3 -m venv --system-site-packages "${venv}"
    fi
    touch "${venv}/COLCON_IGNORE"
    # shellcheck disable=SC1091
    source "${venv}/bin/activate"

    python -m pip install --upgrade pip wheel "setuptools==79.0.1"

    log "Phase 1: NumPy + OpenCV (pinned)"
    python -m pip uninstall -y numpy opencv-python opencv-python-headless \
        opencv-contrib-python opencv-contrib-python-headless || true
    python -m pip install --no-cache-dir "numpy==1.26.4" "opencv-python==4.11.0.86"

    log "Phase 1: PyTorch (${TORCH_MODE})"
    local index
    if [ "${TORCH_MODE}" = "gpu" ]; then
        index="https://download.pytorch.org/whl/cu126"
    else
        index="https://download.pytorch.org/whl/cpu"
    fi
    python -m pip install --no-cache-dir \
        "torch==2.9.1" "torchvision==0.24.1" "torchaudio==2.9.1" \
        --index-url "${index}"

    log "Phase 1: Ultralytics + project packages"
    python -m pip install --no-cache-dir \
        "ultralytics==8.3.237" "pillow==12.0.0" "PyYAML==6.0.3"
    python -m pip install --no-cache-dir --force-reinstall "numpy==1.26.4"
    python -m pip install --no-cache-dir --force-reinstall "setuptools==79.0.1"
    python -m pip install --no-cache-dir \
        "pandas==2.3.3" "scipy==1.15.3" "mavsdk==3.10.2" \
        "pymavlink==2.4.49" "pyserial==3.5"

    log "Phase 1: colcon inside the venv (so ROS 2 Python nodes use px4-venv)"
    python -m pip install "colcon-common-extensions"
    hash -r

    log "Phase 1: validation"
    python -m pip check || warn "pip check reported issues (see above)."
    # shellcheck disable=SC1091
    source /opt/ros/humble/setup.bash
    python - <<'PY'
import numpy, cv2, torch, torchvision, ultralytics, rclpy
from cv_bridge import CvBridge
print("NumPy       :", numpy.__version__)
print("OpenCV      :", cv2.__version__)
print("PyTorch     :", torch.__version__)
print("CUDA usable :", torch.cuda.is_available())
print("Ultralytics :", ultralytics.__version__)
print("rclpy / cv_bridge: OK")
PY
    deactivate || true
    mark phase1_venv
}

# -----------------------------------------------------------------------------
# Phase 3 - PX4 SITL, DDS agent, ROS 2 workspace
# -----------------------------------------------------------------------------
build_px4() {
    if ! is_done px4_toolchain; then
        log "PX4: install toolchain + Gazebo (Tools/setup/ubuntu.sh)"
        ( cd "${PX4_DIR}" && bash Tools/setup/ubuntu.sh )
        mark px4_toolchain
    fi
    if [ ! -x "${PX4_DIR}/build/px4_sitl_default/bin/px4" ]; then
        log "PX4: build SITL (15-40 minutes)"
        ( cd "${PX4_DIR}" && make px4_sitl )
    fi
    test -x "${PX4_DIR}/build/px4_sitl_default/bin/px4" || die "PX4 SITL build failed."
    echo "PX4 SITL: READY"
}

build_dds_agent() {
    if command -v MicroXRCEAgent >/dev/null 2>&1; then
        log "Micro XRCE-DDS Agent: already installed"
        return
    fi
    log "Micro XRCE-DDS Agent: build and install"
    mkdir -p "${DDS_AGENT_DIR}/build"
    ( cd "${DDS_AGENT_DIR}/build" && cmake .. && make -j"$(nproc)" && sudo make install )
    sudo ldconfig /usr/local/lib/
    command -v MicroXRCEAgent >/dev/null || die "MicroXRCEAgent not found after install."
}

build_workspace() {
    log "ROS 2 workspace: rosdep + colcon build (venv active)"
    # shellcheck disable=SC1091
    source /opt/ros/humble/setup.bash
    # shellcheck disable=SC1091
    source "${HOME}/px4-venv/bin/activate"
    ( cd "${ROS2_WS}" \
        && rosdep install --from-paths src --ignore-src --rosdistro humble -r -y \
        && colcon build --symlink-install )
    # shellcheck disable=SC1091
    source "${ROS2_WS}/install/setup.bash"
    ros2 pkg prefix px4_msgs >/dev/null && echo "px4_msgs: OK"
    deactivate || true
}

configure_bashrc() {
    log ".bashrc block"
    local start="# >>> UM6P DRONE INTERNSHIP >>>" end="# <<< UM6P DRONE INTERNSHIP <<<"
    touch "${HOME}/.bashrc"
    sed -i "/${start//\//\\/}/,/${end//\//\\/}/d" "${HOME}/.bashrc"
    cat >> "${HOME}/.bashrc" <<'EOF'
# >>> UM6P DRONE INTERNSHIP >>>
# ROS 2 Humble base environment
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
fi

# Project root and fixed dependency paths
export INTERNSHIP_ROOT="$HOME/quard_um6p_intership"
if [ -f "$INTERNSHIP_ROOT/config/project.env" ]; then
    source "$INTERNSHIP_ROOT/config/project.env"
fi

# Project-owned Gazebo worlds and models, plus the user model cache
export GZ_SIM_RESOURCE_PATH="$INTERNSHIP_ROOT/gazebo/worlds:$INTERNSHIP_ROOT/gazebo/models:$HOME/.gz/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"

# Project ROS 2 overlay, loaded only after it has been built
if [ -f "$INTERNSHIP_ROOT/ros2_ws/install/setup.bash" ]; then
    source "$INTERNSHIP_ROOT/ros2_ws/install/setup.bash"
fi
# <<< UM6P DRONE INTERNSHIP <<<
EOF
}

# -----------------------------------------------------------------------------
main() {
    preflight
    phase0_base
    load_project_env
    download_sources
    patch_camera
    phase1_venv
    build_px4
    build_dds_agent
    build_workspace
    configure_bashrc

    log "SETUP COMPLETE"
    cat <<EOF

Next steps:
  1. Open a NEW terminal (or run: source ~/.bashrc)
  2. Start the whole simulation:   ${ROOT}/scripts/run_sim.sh
  3. Full log of this setup:       ${ROOT}/logs/setup_all.log
EOF
}

main "$@"
