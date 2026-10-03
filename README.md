# Drone Simulation: PX4 + ROS 2 + Gazebo + YOLO

A ready-to-run drone simulation that you can set up with **one script** instead of installing every dependency by hand. A virtual drone takes off in Gazebo, flies an orbit around inspection targets (a car, a pickup truck and a person), and a YOLO model detects those objects live from the drone's camera.

## Why this repository exists

Running a PX4 + ROS 2 + Gazebo + YOLO simulation normally means following several long guides: ROS 2 Humble, PX4 v1.15, Gazebo, the Micro XRCE-DDS Agent, a Python environment with exact library versions, and a workspace build. One wrong version and nothing works.

The goal of this repo is to make that **reproducible for everyone**:

- **One command to install** everything with the right pinned versions.
- **One command to run** the whole simulation, with every process started in the right order.
- **Works on WSL2**, so Windows users don't need to dual boot.
- **Works with or without an NVIDIA GPU**: YOLO runs on CPU, or on CUDA if available.

It is meant for students, researchers and hobbyists who want to experiment with autonomous drone inspection and computer vision without spending days on setup.

## What the simulation does

```text
Gazebo (x500_depth drone + camera)
        |  camera image
        v
  ROS 2 image bridge  --->  YOLO detection node  --->  /inspection/detections
        ^                                               /inspection/debug_image
        |
  PX4 SITL autopilot  <--- Micro XRCE-DDS Agent <---> ROS 2 orbit mission node
```

- **PX4 v1.15 SITL** flies the drone (software-in-the-loop, no hardware needed).
- **Gazebo** simulates the world, the drone and its downward-tilted camera.
- **ROS 2 Humble** connects everything; the `px4_orbit_inspection` package flies the orbit mission.
- **YOLOv8** detects objects in the camera stream.
- **MAVSDK keyboard teleop** lets you fly manually.

> Simulation only. This repository is not intended for flying real aircraft.

## Requirements

| Item | Requirement |
| --- | --- |
| OS | Ubuntu **22.04** (native or WSL2) |
| Windows users | Windows 10/11 with **WSL2 + WSLg** (for the Gazebo window) |
| Disk space | about 25 GB free |
| RAM | 16 GB recommended |
| GPU | Optional. NVIDIA GPU with the driver installed on **Windows** (not inside WSL) |
| Internet | Needed during setup (large downloads) |

Ubuntu 24.04 is **not** supported: ROS 2 Humble targets Ubuntu 22.04.

## Quick start

### 1. Install Ubuntu 22.04 on WSL2 (Windows only)

In Windows PowerShell:

```powershell
wsl --update
wsl --install -d Ubuntu-22.04
```

Open the Ubuntu terminal and create your user.

### 2. Clone the repository

The folder name and location matter. Clone it into your home directory with exactly this name:

```bash
sudo apt update && sudo apt install -y git git-lfs
git clone https://github.com/BigCoder-ops/drone-px4-ros2-yolo-sim.git ~/quard_um6p_intership
cd ~/quard_um6p_intership
git lfs pull
```

### 3. Install everything

```bash
chmod +x scripts/*.sh
./scripts/setup_all.sh
```

The script auto-detects an NVIDIA GPU. You can also force a mode:

```bash
./scripts/setup_all.sh --cpu    # CPU-only PyTorch
./scripts/setup_all.sh --gpu    # CUDA PyTorch
```

This takes **1 to 2 hours** (ROS 2, PX4 build, PyTorch). You can safely re-run it if it stops: finished steps are skipped. Progress is saved in `logs/setup_all.log`.

### 4. Run the simulation

Open a **new terminal**, then:

```bash
cd ~/quard_um6p_intership
./scripts/run_sim.sh
```

This opens one `tmux` session with a window for each part:

| Window | What it runs |
| --- | --- |
| `shell` | A ready terminal for your own commands |
| `dds` | Micro XRCE-DDS Agent |
| `px4` | PX4 SITL + Gazebo with the `x500_depth` drone |
| `spawn` | Adds the car, pickup and person to the world |
| `bridge` | Gazebo camera to ROS 2 (`/camera/image_raw`) |
| `orbit` | The orbit mission node |
| `yolo` | YOLO detection on the camera stream |

Switch windows with `Ctrl+b` then `n` (next) or `p` (previous). Detach with `Ctrl+b` then `d`.

### 5. Start the mission

In the `shell` window:

```bash
ros2 service call /orbit/start std_srvs/srv/Trigger "{}"
```

Abort and land:

```bash
ros2 service call /orbit/abort std_srvs/srv/Trigger "{}"
```

### 6. Stop everything

```bash
./scripts/run_sim.sh stop
```

## Useful commands

```bash
# View the camera
ros2 run rqt_image_view rqt_image_view /camera/image_raw

# Check the camera rate
ros2 topic hz /camera/image_raw

# Record an experiment
mkdir -p data/bags
ros2 bag record -o data/bags/run_01 \
  /camera/image_raw /inspection/debug_image /inspection/detections \
  /fmu/out/vehicle_odometry /fmu/out/vehicle_status /fmu/in/trajectory_setpoint
```

## Manual flight with the keyboard

```bash
source ~/px4-venv/bin/activate
cd ~/quard_um6p_intership/tools/mavsdk_teleop
python -u keyboard_mavsdk_control.py
```

| Key | Action |
| --- | --- |
| `r` | Arm |
| `l` | Land |
| `w` / `s` | Throttle up / down |
| `a` / `d` | Yaw left / right |
| Arrow keys | Roll / pitch |
| `i` | Print flight mode |
| `Ctrl+C` | Quit |

## Repository layout

```text
quard_um6p_intership/
├── config/              # project paths and pinned commits (PX4, px4_msgs, DDS Agent)
├── gazebo/              # worlds and inspection models (car, pickup, person)
├── models/yolo/         # YOLO weights
├── perception/yolo/     # YOLO camera detection node
├── ros2_ws/src/         # px4_orbit_inspection package (px4_msgs is downloaded)
├── tools/mavsdk_teleop/ # keyboard flight control
├── scripts/
│   ├── setup_all.sh     # one-command installer
│   ├── run_sim.sh       # starts the whole simulation
│   ├── spawn_objects.sh # adds objects to the Gazebo world
│   └── 02_download_sources.sh  # clones PX4 / px4_msgs / DDS Agent at pinned commits
└── installation_guide/  # detailed step-by-step guides (Phase 0, 1, 2)
```

## What is not stored in this repository

Large or machine-specific parts are recreated by `setup_all.sh`:

| Item | Where it comes from |
| --- | --- |
| PX4-Autopilot, Micro-XRCE-DDS-Agent, `px4_msgs` | Downloaded at pinned commits by `02_download_sources.sh` |
| ROS 2, Gazebo, system packages | Installed with `apt` |
| Python environment `~/px4-venv` | Created with pinned versions (NumPy 1.26.4, PyTorch 2.9.1, Ultralytics 8.3.237) |
| `ros2_ws/build`, `install`, `log` | Built with `colcon` |

The pinned versions keep the setup reproducible: PX4 `release/1.15` and `px4_msgs` `release/1.15` must match.

## Docker (alternative)

```bash
docker compose up --build                                                  # CPU
TORCH=gpu docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build   # NVIDIA GPU
```

The image is very large and slow to build. The script-based install above is the recommended path.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `must live at ~/quard_um6p_intership` | Clone or move the repo to that exact folder |
| No Gazebo window | In Windows PowerShell: `wsl --update`, then `wsl --shutdown`, reopen Ubuntu |
| Black or very slow Gazebo, no GPU | `export LIBGL_ALWAYS_SOFTWARE=1` before `run_sim.sh` |
| GitHub API rate limit during setup | Wait a few minutes and re-run `setup_all.sh` |
| `_ARRAY_API not found` (NumPy error) | Never use `sudo pip`. See `installation_guide/README_PHASE1_PX4_AI_VENV_SETUP.md`, section 19 |
| Setup stops with an error | Read the end of `logs/setup_all.log`, fix the cause, run `setup_all.sh` again |

For deeper details, see the guides in `installation_guide/`.

## Credits

This project is based on the **QUARD UM6P Autonomous Drone Engineering Internship** repository by **abdtnourji**:
https://github.com/abdtnourji/quard_um6p_intership

This repository adds a one-command installer, a one-command launcher, Docker files and a rewritten README so that anyone can reproduce the simulation. It also builds on these open-source projects: [PX4 Autopilot](https://github.com/PX4/PX4-Autopilot), [ROS 2 Humble](https://docs.ros.org/en/humble/), [Gazebo](https://gazebosim.org/), [Micro XRCE-DDS Agent](https://github.com/eProsima/Micro-XRCE-DDS-Agent) and [Ultralytics YOLO](https://github.com/ultralytics/ultralytics).

Check the original repository for its license terms before reusing or redistributing the code.
