#!/usr/bin/env bash


# =============================================================================
# Project   : Quadcopter Autonomous Inspection (UM6P Internship)
# Author    : Dr. Abdellah TNOURJI
# Website   : https://www.abdellahtnourji.com/
# Date      : [Date, Aug 2026]

# License   : UM6P
# =============================================================================



set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/config/project.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: Missing ${ENV_FILE}" >&2
  exit 1
fi

source "${ENV_FILE}"

: "${INTERNSHIP_ROOT:?Missing INTERNSHIP_ROOT in project.env}"
: "${ROS2_WS:?Missing ROS2_WS in project.env}"
: "${PX4_DIR:?Missing PX4_DIR in project.env}"
: "${DDS_AGENT_DIR:?Missing DDS_AGENT_DIR in project.env}"
: "${PX4_BRANCH:?Missing PX4_BRANCH in project.env}"
: "${PX4_MSGS_BRANCH:?Missing PX4_MSGS_BRANCH in project.env}"

PX4_MSGS_DIR="${ROS2_WS}/src/px4_msgs"
DDS_AGENT_REVISION="${DDS_AGENT_REVISION:-2.4.2}"


export GIT_TERMINAL_PROMPT=0

mkdir -p "${INTERNSHIP_ROOT}/dependencies" "${ROS2_WS}/src" "${INTERNSHIP_ROOT}/config"

check_public_repository() {
  local url="$1"
  echo "Checking anonymous access: ${url}"
  if ! git ls-remote "${url}" HEAD >/dev/null 2>&1; then
    echo "ERROR: Anonymous GitHub access failed for ${url}" >&2
    echo "These repositories are public and do not need a password or PAT." >&2
    echo "Check network, proxy, Git URL rewrites, or cached credentials." >&2
    exit 1
  fi
}

clone_or_update_branch() {
  local name="$1" url="$2" directory="$3" branch="$4" recursive="$5"

  if [[ ! -d "${directory}/.git" ]]; then
    echo "Cloning ${name} (${branch})..."
    if [[ "${recursive}" == "yes" ]]; then
      git clone --branch "${branch}" --recursive "${url}" "${directory}"
    else
      git clone --branch "${branch}" "${url}" "${directory}"
    fi
  else
    echo "${name} already exists. Updating metadata without deleting local files..."
    git -C "${directory}" fetch --tags --prune
    git -C "${directory}" checkout "${branch}"
  fi
}

check_public_repository "https://github.com/PX4/PX4-Autopilot.git"
check_public_repository "https://github.com/PX4/px4_msgs.git"
check_public_repository "https://github.com/eProsima/Micro-XRCE-DDS-Agent.git"

clone_or_update_branch \
  "PX4-Autopilot" \
  "https://github.com/PX4/PX4-Autopilot.git" \
  "${PX4_DIR}" \
  "${PX4_BRANCH}" \
  "yes"

git -C "${PX4_DIR}" submodule sync --recursive
git -C "${PX4_DIR}" submodule update --init --recursive

clone_or_update_branch \
  "px4_msgs" \
  "https://github.com/PX4/px4_msgs.git" \
  "${PX4_MSGS_DIR}" \
  "${PX4_MSGS_BRANCH}" \
  "no"

if [[ ! -d "${DDS_AGENT_DIR}/.git" ]]; then
  echo "Cloning Micro-XRCE-DDS-Agent (${DDS_AGENT_REVISION})..."
  git clone --branch "${DDS_AGENT_REVISION}" \
    https://github.com/eProsima/Micro-XRCE-DDS-Agent.git \
    "${DDS_AGENT_DIR}"
else
  echo "Micro-XRCE-DDS-Agent already exists. Selecting ${DDS_AGENT_REVISION}..."
  git -C "${DDS_AGENT_DIR}" fetch --tags --prune
  git -C "${DDS_AGENT_DIR}" checkout "${DDS_AGENT_REVISION}"
fi

PX4_CURRENT_BRANCH="$(git -C "${PX4_DIR}" branch --show-current)"
PX4_MSGS_CURRENT_BRANCH="$(git -C "${PX4_MSGS_DIR}" branch --show-current)"
DDS_CURRENT_REVISION="$(git -C "${DDS_AGENT_DIR}" describe --tags --always --exact-match 2>/dev/null || git -C "${DDS_AGENT_DIR}" rev-parse --short HEAD)"

if [[ "${PX4_CURRENT_BRANCH}" != "${PX4_BRANCH}" ]]; then
  echo "ERROR: PX4 is ${PX4_CURRENT_BRANCH}; expected ${PX4_BRANCH}." >&2
  exit 1
fi

if [[ "${PX4_MSGS_CURRENT_BRANCH}" != "${PX4_MSGS_BRANCH}" ]]; then
  echo "ERROR: px4_msgs is ${PX4_MSGS_CURRENT_BRANCH}; expected ${PX4_MSGS_BRANCH}." >&2
  exit 1
fi

PX4_COMMIT="$(git -C "${PX4_DIR}" rev-parse HEAD)"
PX4_MSGS_COMMIT="$(git -C "${PX4_MSGS_DIR}" rev-parse HEAD)"
DDS_AGENT_COMMIT="$(git -C "${DDS_AGENT_DIR}" rev-parse HEAD)"

printf '%s\n' "${PX4_COMMIT}" > "${INTERNSHIP_ROOT}/config/PX4_COMMIT.txt"
printf '%s\n' "${PX4_MSGS_COMMIT}" > "${INTERNSHIP_ROOT}/config/PX4_MSGS_COMMIT.txt"
printf '%s\n' "${DDS_AGENT_COMMIT}" > "${INTERNSHIP_ROOT}/config/DDS_AGENT_COMMIT.txt"

cat <<EOF

Source stack downloaded and verified.

PX4-Autopilot
  path:    ${PX4_DIR}
  branch:  ${PX4_CURRENT_BRANCH}
  commit:  ${PX4_COMMIT}

px4_msgs
  path:    ${PX4_MSGS_DIR}
  branch:  ${PX4_MSGS_CURRENT_BRANCH}
  commit:  ${PX4_MSGS_COMMIT}

Micro-XRCE-DDS-Agent
  path:    ${DDS_AGENT_DIR}
  revision:${DDS_CURRENT_REVISION}
  commit:  ${DDS_AGENT_COMMIT}

Compatibility result: PASS
PX4 ${PX4_BRANCH} matches px4_msgs ${PX4_MSGS_BRANCH}.
EOF
