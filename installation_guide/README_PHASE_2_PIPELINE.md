# UM6P Autonomous Drone Internship

# Phase 3 - Run the Autonomous AI Drone Inspection Pipeline

This guide explains how to run the complete internship demonstration in separate Terminator terminals:

1. verify the fixed software versions;
2. start the Micro XRCE-DDS Agent;
3. start PX4 v1.15 with the `x500_depth` model in Gazebo;
4. add inspection objects to the empty world;
5. discover and bridge the RGB camera into ROS 2;
6. run the `px4_orbit_inspection` package or fly manually;
7. run YOLO on the camera stream;
8. visualize and record the results.

The tutorial assumes that Phase 1 and Phase 2 are complete. Do not reinstall the complete platform if the checks below succeed.

---

## 1. Expected environment

| Component            | Required version or location             |
| -------------------- | ---------------------------------------- |
| Operating system     | Ubuntu 22.04                             |
| ROS 2                | Humble, `/opt/ros/humble`                |
| Python               | Python 3.10                              |
| Python environment   | `/home/<user_name>/px4-venv`             |
| NumPy                | 1.26.4                                   |
| PX4                  | `release/1.15`                           |
| `px4_msgs`           | `release/1.15`                           |
| Micro XRCE-DDS Agent | `master`, using the already tested build |
| PX4 model            | `x500_depth`, airframe ID `4002`         |
| ROS 2 workspace      | `${ROS2_WS}` from `config/project.env`   |

The matching PX4 and `px4_msgs` branches are important because ROS 2 applications must use message definitions compatible with the uXRCE-DDS client built into PX4.

---

## 2. Project layout

The project structure OJECTIVE is:

```text
quard_um6p_intership/
├── config/
│   ├── project.env
│   ├── DDS_AGENT_COMMIT.txt
│   ├── PX4_COMMIT.txt
│   └── PX4_MSGS_COMMIT.txt
├── data/
├── dependencies/
│   ├── Micro-XRCE-DDS-Agent/
│   └── PX4-Autopilot/
├── gazebo/
│   ├── models/
│   │   ├── inspection_car/
│   │   ├── inspection_person_marker/
│   │   └── inspection_stop_sign/
│   └── worlds/
├── logs/
├── ros2_ws/
│   └── src/
│       ├── px4_msgs/
│       ├── px4_orbit_inspection/
├── scripts/
│   ├── 00_check_ubuntu.sh
│   ├── 01_install_system_dependencies.sh
│   └── 02_download_sources.sh
└── student_logs/
```

# 3. Install and Verify the Project Dependencies

This phase prepares a coherent PX4 v1.15, ROS 2 Humble and Gazebo development environment for the internship.

## 3.1 Required source stack

```text
PX4-Autopilot:         release/1.15
px4_msgs:              release/1.15
Micro-XRCE-DDS-Agent:  2.4.2 pinned revision
Ubuntu:                 22.04
ROS 2:                  Humble
Python:                 3.10
```

PX4 and `px4_msgs` must use matching release branches because the ROS 2 message definitions must match those used to build the PX4 uXRCE-DDS client.

The repositories are stored inside the project:

```text
${HOME}/quard_um6p_intership/
├── config/
│   ├── project.env
│   ├── PX4_COMMIT.txt
│   ├── PX4_MSGS_COMMIT.txt
│   └── DDS_AGENT_COMMIT.txt
├── dependencies/
│   ├── PX4-Autopilot/
│   └── Micro-XRCE-DDS-Agent/
└── ros2_ws/
    └── src/
        └── px4_msgs/
```

## 3.2 Download and verify the source stack

Run:

```bash
cd ~/quard_um6p_intership
chmod +x scripts/02_download_sources.sh
./scripts/02_download_sources.sh
```

Expected final output:

```text
Compatibility result: PASS
PX4 release/1.15 matches px4_msgs release/1.15.
```

Verify manually:

```bash
cd ~/quard_um6p_intership
source config/project.env

git -C "${PX4_DIR}" branch --show-current
git -C "${ROS2_WS}/src/px4_msgs" branch --show-current
git -C "${DDS_AGENT_DIR}" describe --tags --always
```

Expected:

```text
release/1.15
release/1.15
2.4.2
```

Verify recorded commits:

```bash
test "$(git -C "${PX4_DIR}" rev-parse HEAD)" = "$(cat config/PX4_COMMIT.txt)" \
  && echo "PX4 commit: MATCH"

test "$(git -C "${ROS2_WS}/src/px4_msgs" rev-parse HEAD)" = "$(cat config/PX4_MSGS_COMMIT.txt)" \
  && echo "px4_msgs commit: MATCH"

test "$(git -C "${DDS_AGENT_DIR}" rev-parse HEAD)" = "$(cat config/DDS_AGENT_COMMIT.txt)" \
  && echo "DDS Agent commit: MATCH"
```

Do not continue if one comparison does not print `MATCH`.

## 3.3 Install the PX4 and Gazebo development toolchain

Run the setup tool from the checked-out PX4 v1.15 source:

```bash
cd ~/quard_um6p_intership
source config/project.env
cd "${PX4_DIR}"

bash Tools/setup/ubuntu.sh
```

Restart Ubuntu after installation:

```bash
sudo reboot
```

Build PX4 SITL:

```bash
cd ~/quard_um6p_intership
source config/project.env
cd "${PX4_DIR}"

make px4_sitl
```

Verify:

```bash
test -x "${PX4_DIR}/build/px4_sitl_default/bin/px4" \
  && echo "PX4 SITL: READY"
```

## 3.4 Build and install the DDS Agent

```bash
cd ~/quard_um6p_intership
source config/project.env
cd "${DDS_AGENT_DIR}"

mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig /usr/local/lib/
```

Verify:

```bash
command -v MicroXRCEAgent
MicroXRCEAgent --help | head
```

## 3.5 Build the ROS 2 workspace

```bash
cd ~/quard_um6p_intership
source config/project.env
source /opt/ros/humble/setup.bash
cd "${ROS2_WS}"

rosdep install \
  --from-paths src \
  --ignore-src \
  --rosdistro humble \
  -r -y

colcon build --symlink-install
source install/setup.bash
```

Verify `px4_msgs`:

```bash
ros2 pkg prefix px4_msgs
ros2 interface show px4_msgs/msg/VehicleOdometry | head -n 20
```

## 7. Configure `.bashrc`

Run this command once.

```bash
python3 - <<'PY'
from pathlib import Path

bashrc = Path.home() / ".bashrc"
start = "# >>> UM6P DRONE INTERNSHIP >>>"
end = "# <<< UM6P DRONE INTERNSHIP <<<"

block = r'''# >>> UM6P DRONE INTERNSHIP >>>
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
# <<< UM6P DRONE INTERNSHIP <<<'''

text = bashrc.read_text() if bashrc.exists() else ""
if start in text and end in text:
    before = text.split(start, 1)[0].rstrip()
    after = text.split(end, 1)[1].lstrip()
    text = before + "\n\n" + block + "\n\n" + after
else:
    text = text.rstrip() + "\n\n" + block + "\n"

bashrc.write_text(text)
print(f"Updated {bashrc}")
PY
```

Reload:

```bash
source ~/.bashrc
```

## 3.5 Verify paths after opening a new terminal

Close the current terminal, open a new one and run:

```bash
printf "INTERNSHIP_ROOT=%s\n" "${INTERNSHIP_ROOT}"
printf "PX4_DIR=%s\n" "${PX4_DIR}"
printf "ROS2_WS=%s\n" "${ROS2_WS}"
printf "DDS_AGENT_DIR=%s\n" "${DDS_AGENT_DIR}"
printf "GZ_SIM_RESOURCE_PATH=%s\n" "${GZ_SIM_RESOURCE_PATH}"
```

Verify ROS 2 and Gazebo resources:

```bash
ros2 pkg prefix px4_msgs

test -d "${INTERNSHIP_ROOT}/gazebo/models" \
  && echo "Project Gazebo models: READY"

test -d "${INTERNSHIP_ROOT}/gazebo/worlds" \
  && echo "Project Gazebo worlds: READY"
```

A project-owned world can now be referenced directly by path:

```bash
gz sim "${INTERNSHIP_ROOT}/gazebo/worlds/default.sdf"
```

A model can be referenced directly by path:

```bash
MODEL_SDF="${INTERNSHIP_ROOT}/gazebo/models/inspection_car/model.sdf"
test -f "${MODEL_SDF}" && echo "Inspection model: READY"
```

# 4. Run the full pipeline in Terminator

Open a Terminator window and split it into at least six terminals. Run the terminals in the order below.

---

## Terminal 1 - Micro XRCE-DDS Agent

```bash
cd ~/quard_um6p_intership
source config/project.env
cd "${DDS_AGENT_DIR}"

MicroXRCEAgent udp4 -p 8888
```

Keep this terminal running. The agent connects PX4's uXRCE-DDS client to ROS 2 over UDP.

---

## Terminal 2 - PX4 v1.15 and Gazebo with `x500_depth`

```bash
cd ~/quard_um6p_intership
source config/project.env
cd "${PX4_DIR}"

PX4_SYS_AUTOSTART=4002 \
PX4_GZ_MODEL=x500_depth \
./build/px4_sitl_default/bin/px4
```

The empty world is expected. It confirms that PX4 and the `x500_depth` model started before the inspection objects are added.

## Open VsCode - Camera orientation: Down

Change the angle of Drone's camera; The PX4 v1.15 `x500_depth` model is documented as having a front-facing depth camera.

# Go to PX4-Autopilot/Tools/simulation/gz/models/x500_depth/model.sdf then change <pose> tag in line 9 from:

The suggested change:

```xml
<pose>.12 .03 .242 0 0 0</pose>
```

to:

```xml
<pose>.15 .029 .21 0 0.7854 0</pose>
```

---

## Terminal 3 - Add inspection objects

First discover the running world name:

```bash
cd ~/quard_um6p_intership
source config/project.env

gz service -l | grep '/world/.*/create'
```

Normally:

```text
/world/default/create
```

The local demonstration layout is:

```text
                         Person marker
                            (0, 6)
                               ●

                               ↑ Gazebo +X or chosen map direction

       Stop-sign marker       DRONE/HOME          Car marker
          (-5, 2.5)             (0, 0)              (8, 0)
               ●                   ✈                   ●
```

Set shared variables:

```bash
cd ~/quard_um6p_intership
source config/project.env

WORLD_NAME="default"
MODEL_DIR="$(pwd)/gazebo/models"
```

### Spawn the car marker

```bash
# OBJECT_SDF="${MODEL_DIR}/inspection_car/model.sdf"
OBJECT_SDF="${MODEL_DIR}/inspection_hatchback/model.sdf"

gz service \
  -s "/world/${WORLD_NAME}/create" \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 3000 \
  --req "
    name: 'inspection_car_instance',
    sdf_filename: '${OBJECT_SDF}',
    pose: {
      position: {x: 8.0, y: 0.0, z: 0.0},
      orientation: {w: 1.0, x: 0.0, y: 0.0, z: 0.0}
    }
  "
```

### Spawn the stop-sign marker

```bash
# OBJECT_SDF="${MODEL_DIR}/inspection_stop_sign/model.sdf"
OBJECT_SDF="${MODEL_DIR}/inspection_pickup/model.sdf"


gz service \
  -s "/world/${WORLD_NAME}/create" \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 3000 \
  --req "
    # name: 'inspection_stop_sign_instance',
    name: 'inspection_pickup',
    sdf_filename: '${OBJECT_SDF}',
    pose: {
      position: {x: -5.0, y: 2.5, z: 0.0},
      orientation: {w: 1.0, x: 0.0, y: 0.0, z: 0.0}
    }
  "
```

### Spawn the person marker

```bash
# OBJECT_SDF="${MODEL_DIR}/inspection_person_marker/model.sdf"
OBJECT_SDF="${MODEL_DIR}/inspection_person/model.sdf"

gz service \
  -s "/world/${WORLD_NAME}/create" \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 3000 \
  --req "
    # name: 'inspection_person_marker_instance',
    name: 'inspection_person',
    sdf_filename: '${OBJECT_SDF}',
    pose: {
      position: {x: 0.0, y: 6.0, z: 0.0},
      orientation: {w: 1.0, x: 0.0, y: 0.0, z: 0.0}
    }
  "
```

A successful response should include:

```text
data: true
```

## If the world name differs, replace `default`. If a model already exists, use a new entity name or remove the old entity before spawning it again.

## Terminal 4 - Discover and bridge the RGB camera

Do not guess the camera topic. Discover it:

```bash
gz topic -l | grep -Ei 'camera|image|rgb|depth|points'
```

For the standard `x500_depth` model, the RGB image is commonly `/camera` and depth data is commonly `/depth_camera`, but use the names printed by the running simulation.

Inspect the candidate RGB topic:

```bash
gz topic -i -t /camera
```

Confirm that Gazebo is publishing messages:

```bash
gz topic -e -t /camera
```

Stop the binary-looking image output with `Ctrl+C`.

Now bridge the RGB topic to ROS 2:

```bash
source /opt/ros/humble/setup.bash

ros2 run ros_gz_image image_bridge /camera \
  --ros-args \
  -r /camera:=/camera/image_raw \
  -p qos:=sensor_data
```

or

```bash
source /opt/ros/humble/setup.bash
ros2 run ros_gz_image image_bridge /camera
```

An apparently silent bridge terminal is normal. Leave it running and verify from another terminal:

```bash
source /opt/ros/humble/setup.bash
ros2 topic list | grep camera
ros2 topic info /camera/image_raw --verbose
ros2 topic hz /camera/image_raw
```

Display the raw camera image before starting YOLO:

```bash
ros2 run rqt_image_view rqt_image_view /camera/image_raw
```

Do not proceed until an image is visible. If the camera sees only sky, ground, or empty space, change drone pose, camera angle, or object placement.

---

## Terminal 5 - Run the orbit mission

```bash
cd ~/quard_um6p_intership
source config/project.env
source /opt/ros/humble/setup.bash
source /home/<user_name>/px4-venv/bin/activate
source "${ROS2_WS}/install/setup.bash"

ros2 launch px4_orbit_inspection orbit_demo.launch.py
```

Start explicitly from another sourced ROS 2 terminal:

```bash
ros2 service call /orbit/start std_srvs/srv/Trigger "{}"
```

Abort and request landing:

```bash
ros2 service call /orbit/abort std_srvs/srv/Trigger "{}"
```

Inspect the package while it runs:

```bash
ros2 node info /orbit_controller
ros2 topic hz /fmu/in/trajectory_setpoint
ros2 topic echo /fmu/out/vehicle_odometry --once
```

---

## Terminal 6 - Run YOLO

```bash
source /opt/ros/humble/setup.bash
source /home/<user_name>/px4-venv/bin/activate
source ~/quard_um6p_intership/ros2_ws/install/setup.bash
cd ~/quard_um6p_intership/perception/yolo

python -u uav_camera_det.py
```

---

## Terminal 7 - Visualization and evidence

Node graph:

```bash
rqt_graph
```

Record a complete experiment:

```bash
cd ~/quard_um6p_intership
mkdir -p data/bags

ros2 bag record \
  -o data/bags/orbit_inspection_run_01 \
  /camera/image_raw \
  /inspection/debug_image \
  /inspection/detections \
  /fmu/out/vehicle_odometry \
  /fmu/out/vehicle_status \
  /fmu/in/trajectory_setpoint
```

Stop recording with `Ctrl+C` and confirm that the bag closes successfully.

---

## Terminal 8 - Manual keyboard flight before autonomous flight

Keyboard flight is useful for camera exploration,
First inspect available executables:

```bash
source /opt/ros/humble/setup.bash
source /home/<user_name>/px4-venv/bin/activate
source ~/quard_um6p_intership/ros2_ws/install/setup.bash
cd ~/quard_um6p_intership/tools/mavsdk_teleop

python -u keyboard_mavsdk_control.py

```

## Flight Controls

| Key          | Action             |
| ------------ | ------------------ |
| `r`          | Arm the drone      |
| `l`          | Land               |
| `w` / `s`    | Throttle up / down |
| `a` / `d`    | Yaw left / right   |
| `Arrow keys` | Roll / Pitch       |
| `i`          | Print flight mode  |
| `Ctrl+C`     | Quit               |

---

# Clean shutdown

Preferred shutdown:

1. abort or land the drone;
2. stop YOLO with `Ctrl+C`;
3. stop rosbag cleanly with `Ctrl+C`;
4. stop the camera bridge;
5. stop PX4/Gazebo;
6. stop the DDS Agent.
