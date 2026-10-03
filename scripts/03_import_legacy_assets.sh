#!/usr/bin/env bash


# =============================================================================
# Project   : Quadcopter Autonomous Inspection (UM6P Internship)
# Author    : Dr. Abdellah TNOURJI
# Website   : https://www.abdellahtnourji.com/
# Date      : [Date, Aug 2026]

# License   : UM6P
# =============================================================================


set -euo pipefail


SCRIPT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")"
    pwd
)"

PROJECT_ROOT="$(
    cd "${SCRIPT_DIR}/.."
    pwd
)"


SOURCE_PROJECT="${1:-/home/tnourji/dev/PX4-ROS2-Gazebo-YOLOv8}"


echo "============================================"
echo "Importing existing inspection resources"
echo "============================================"
echo "Source:      ${SOURCE_PROJECT}"
echo "Destination: ${PROJECT_ROOT}"
echo "============================================"


if [ ! -d "${SOURCE_PROJECT}" ]; then

    echo "[ERROR] The source project does not exist:"

    echo "        ${SOURCE_PROJECT}"

    echo

    echo "Usage:"

    echo "  $0 /absolute/path/to/PX4-ROS2-Gazebo-YOLOv8"

    exit 1

fi


copy_required()
{
    local source_path="$1"
    local destination_path="$2"

    if [ ! -e "${source_path}" ]; then

        echo "[ERROR] Required resource is missing:"

        echo "        ${source_path}"

        return 1

    fi

    mkdir -p "$(dirname "${destination_path}")"

    cp -a "${source_path}" "${destination_path}"

    echo "[COPIED] ${source_path}"

    echo "      -> ${destination_path}"
}


copy_optional()
{
    local source_path="$1"
    local destination_path="$2"

    if [ ! -e "${source_path}" ]; then

        echo "[SKIP] Optional resource not found:"

        echo "       ${source_path}"

        return 0

    fi

    mkdir -p "$(dirname "${destination_path}")"

    cp -a "${source_path}" "${destination_path}"

    echo "[COPIED] ${source_path}"

    echo "      -> ${destination_path}"
}


echo
echo "1. Importing native Gazebo worlds"
echo

copy_required \
    "${SOURCE_PROJECT}/worlds/default.sdf" \
    "${PROJECT_ROOT}/gazebo/worlds/legacy_inspection.sdf"


echo
echo "2. Importing native Gazebo models"
echo

copy_required \
    "${SOURCE_PROJECT}/models/casual_female" \
    "${PROJECT_ROOT}/gazebo/models/inspection_person"

copy_required \
    "${SOURCE_PROJECT}/models/hatchback" \
    "${PROJECT_ROOT}/gazebo/models/inspection_hatchback"

copy_required \
    "${SOURCE_PROJECT}/models/hatchback_blue" \
    "${PROJECT_ROOT}/gazebo/models/inspection_hatchback_blue"

copy_required \
    "${SOURCE_PROJECT}/models/pickup" \
    "${PROJECT_ROOT}/gazebo/models/inspection_pickup"

copy_optional \
    "${SOURCE_PROJECT}/models/sonoma_raceway" \
    "${PROJECT_ROOT}/gazebo/models/sonoma_raceway"


echo
echo "3. Importing the YOLO weight"
echo

copy_required \
    "${SOURCE_PROJECT}/yolov8m.pt" \
    "${PROJECT_ROOT}/models/yolo/yolov8m.pt"


echo
echo "4. Importing MAVSDK keyboard-control tools"
echo

copy_required \
    "${SOURCE_PROJECT}/keyboard-mavsdk-test.py" \
    "${PROJECT_ROOT}/tools/mavsdk_teleop/keyboard_mavsdk_control.py"

copy_required \
    "${SOURCE_PROJECT}/KeyPressModule.py" \
    "${PROJECT_ROOT}/tools/mavsdk_teleop/key_press.py"


echo
echo "5. Archiving the old standalone detector"
echo

copy_optional \
    "${SOURCE_PROJECT}/uav_camera_det.py" \
    "${PROJECT_ROOT}/archive/legacy_perception/uav_camera_detection.py"


echo
echo "6. Importing Docker resources"
echo

copy_optional \
    "${SOURCE_PROJECT}/Dockerfile" \
    "${PROJECT_ROOT}/deployment/docker/Dockerfile"

copy_optional \
    "${SOURCE_PROJECT}/px4_ros2_gazebo.yml" \
    "${PROJECT_ROOT}/deployment/docker/compose.yaml"

copy_optional \
    "${SOURCE_PROJECT}/worlds/default_docker.sdf" \
    "${PROJECT_ROOT}/deployment/docker/worlds/inspection_docker.sdf"

if [ -d "${SOURCE_PROJECT}/models_docker" ]; then

    rm -rf "${PROJECT_ROOT}/deployment/docker/models"

    cp -a \
        "${SOURCE_PROJECT}/models_docker" \
        "${PROJECT_ROOT}/deployment/docker/models"

    echo "[COPIED] Docker models"

fi


echo
echo "7. Importing the reference rosbag"
echo

REFERENCE_BAG="$(
    find "${SOURCE_PROJECT}" \
        -maxdepth 1 \
        -type d \
        -name "rosbag2_*" \
        | sort \
        | head -n 1
)"

if [ -n "${REFERENCE_BAG}" ]; then

    rm -rf \
        "${PROJECT_ROOT}/data/rosbags/reference_inspection_run"

    cp -a \
        "${REFERENCE_BAG}" \
        "${PROJECT_ROOT}/data/rosbags/reference_inspection_run"

    echo "[COPIED] ${REFERENCE_BAG}"

else

    echo "[SKIP] No reference rosbag was found."

fi


echo
echo "8. Preserving the original README"
echo

copy_optional \
    "${SOURCE_PROJECT}/README.md" \
    "${PROJECT_ROOT}/archive/legacy_README.md"


echo
echo "9. Removing generated Python caches"
echo

find "${PROJECT_ROOT}" \
    -type d \
    -name "__pycache__" \
    -prune \
    -exec rm -rf {} +

find "${PROJECT_ROOT}" \
    -type f \
    -name "*.pyc" \
    -delete


echo
echo "============================================"
echo "Resource import completed successfully"
echo "============================================"
