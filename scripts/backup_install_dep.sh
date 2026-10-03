# #!/usr/bin/env bash

# set -euo pipefail

# source "$(dirname "$0")/../config/project.env"

# mkdir -p "${INTERNSHIP_ROOT}/dependencies"
# mkdir -p "${ROS2_WS}/src"

# if [ ! -d "${PX4_DIR}/.git" ]; then
#     echo "Cloning PX4 ${PX4_BRANCH}..."

#     git clone \
#         --branch "${PX4_BRANCH}" \
#         --recursive \
#         https://github.com/PX4/PX4-Autopilot.git \
#         "${PX4_DIR}"
# else
#     echo "PX4 already exists. It will not be replaced."
# fi

# cd "${PX4_DIR}"

# git checkout "${PX4_BRANCH}"
# git submodule sync --recursive
# git submodule update --init --recursive

# if [ ! -d "${ROS2_WS}/src/px4_msgs/.git" ]; then
#     echo "Cloning matching px4_msgs..."

#     git clone \
#         --branch "${PX4_MSGS_BRANCH}" \
#         https://github.com/PX4/px4_msgs.git \
#         "${ROS2_WS}/src/px4_msgs"
# else
#     echo "px4_msgs already exists. It will not be replaced."
# fi

# if [ ! -d "${DDS_AGENT_DIR}/.git" ]; then
#     echo "Cloning Micro XRCE-DDS Agent..."

#     git clone \
#         https://github.com/eProsima/Micro-XRCE-DDS-Agent.git \
#         "${DDS_AGENT_DIR}"
# else
#     echo "Micro XRCE-DDS Agent already exists."
# fi

# echo
# echo "Downloaded repositories:"
# echo "PX4:       ${PX4_DIR}"
# echo "px4_msgs:  ${ROS2_WS}/src/px4_msgs"
# echo "DDS Agent: ${DDS_AGENT_DIR}"