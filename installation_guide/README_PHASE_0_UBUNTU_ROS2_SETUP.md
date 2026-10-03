# UM6P Autonomous Drone Internship

## Phase 0: Ubuntu 22.04 and ROS 2 Humble Installation

This guide prepares the **base operating-system and ROS 2 environment**.

---

# 1. Target system

The rest of the internship assumes:

```text
Operating system:       Ubuntu 22.04 LTS, 64-bit
System Python:          Python 3.10
ROS 2 distribution:    Humble Hawksbill
ROS 2 installation:    /opt/ros/humble
Project directory:      ${HOME}/quard_um6p_intership
Future AI environment: ${HOME}/px4-venv
GPU:                    NVIDIA GeForce RTX series, if available
```

An NVIDIA GPU is **optional**. The core PX4, Gazebo and ROS 2 activities will also support computers without NVIDIA hardware.

> **Important:** use Ubuntu **22.04**, not Ubuntu 24.04, for this course environment. ROS 2 Humble Debian packages officially target Ubuntu Jammy 22.04.

---

# 2. Before installing Ubuntu

## 2.1 Back up important files

Before changing disk partitions or installing a second operating system:

1. Back up all important Windows files to an external disk or trusted cloud location.
2. Confirm that the backup can be opened.
3. Save the Windows BitLocker recovery key if BitLocker or device encryption is enabled.
4. Ensure that the computer is connected to power.
5. Do not resize or delete partitions unless you understand which partition contains Windows.

Disk partitioning can cause data loss if performed incorrectly. Ask a supervisor for help when uncertain.

## 2.2 Windows 11 dual boot

Students who need to keep Windows 11 can use the following visual guide:

- Video: https://www.youtube.com/watch?v=mXyN1aJYefc&t=308s

The video demonstrates a Windows 11 and Ubuntu dual-boot process. It is a useful visual reference, but the exact disk layout can differ between computers.

Official Ubuntu download:

- https://releases.ubuntu.com/jammy/

Recommended system:

```text
Ubuntu Desktop 22.04 LTS, 64-bit
```

Do not continue to ROS 2 installation until Ubuntu starts normally and internet access works.

---

# 3. First startup after installing Ubuntu

**Before you open the terminal and start typing commands**, we highly recommend getting comfortable with how Linux works. Unlike Windows, in robotics (especially with ROS/ROS 2), the terminal is where you will spend 90% of your time.

- **[Linux Journey](https://linuxbasecamp.com/tutorials/command-line):** The best bite-sized, interactive guide to understanding the Linux file system, basic commands, and permissions. Start with the "Getting Started" and "Command Line" modules.

---

Once you are comfortable with the basics, you can open the standard Ubuntu terminal with:

```text
Ctrl + Alt + T

```

## 3.1 Confirm the operating system

```bash
lsb_release -a
```

Expected information must include:

```text
No LSB modules are available.
Distributor ID:	Ubuntu
Description:	Ubuntu 22.04.5 LTS
Release:	22.04
Codename:	jammy
```

Confirm the architecture:

```bash
uname -m
```

Expected result:

```text
x86_64
```

## 3.2 Confirm the system Python version

```bash
python3 --version
```

Expected result:

```text
Python 3.10.x
```

Do not replace `/usr/bin/python3`, and do not use sudo pip install to modify the system Python environment. If you get a Python not available error, don't worry—we will install it in the following section.

---

# 4. Update the fresh Ubuntu installation

A fresh Ubuntu 22.04 installation must be updated **before installing ROS 2**. This step is important because installing ROS 2 dependencies on an outdated fresh system can cause package conflicts involving core system components.

Run:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt autoremove -y
```

Restart the computer:

```bash
sudo reboot
```

After restarting, open a terminal and confirm that there are no pending upgrades:

```bash
sudo apt update
```

---

# 5. Install the basic development environment

Install the common command-line, build and Python tools:

```bash
sudo apt install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    git-lfs \
    curl \
    wget \
    unzip \
    zip \
    tree \
    terminator \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    locales \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-setuptools \
    python3-wheel
```

Initialize Git LFS:

```bash
git lfs install
```

Verify the main tools:

```bash
git --version
cmake --version
python3 --version
pip3 --version
tree --version
```

## 5.1 Terminator

Terminator is a terminal application that makes it easy to split one window into several terminals. It is useful because later the project will run PX4, Gazebo, the DDS Agent and ROS 2 nodes in separate terminals.

Start it with:

```bash
terminator
```

---

# 6. Configure a UTF-8 locale

ROS 2 requires a UTF-8-capable locale. Check the current locale:

```bash
locale
```

Install and configure the English UTF-8 locale:

```bash
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

Verify:

```bash
locale
```

The output should contain UTF-8 values, such as:

```text
LANG=en_US.UTF-8
```

---

# 7. Install ROS 2 Humble from Debian packages

Follow the official ROS 2 Humble Ubuntu installation guide:

- https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html

Use the **Ubuntu deb packages** installation, not the source-build alternative.

## Important warning about the official page

The official page contains an **Uninstall** section near the end. **Do not execute the Uninstall commands.** They remove ROS 2. Follow only these sections:

1. Set locale
2. Setup Sources
3. Install ROS 2 packages
4. Environment setup
5. Try some examples (Optionel)

## 7.1 Enable Ubuntu Universe

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
```

## 7.2 Install the ROS 2 repository configuration

Run the commands from the current official documentation:

```bash
sudo apt update
sudo apt install -y curl

export ROS_APT_SOURCE_VERSION="$({ \
    curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
    | grep -F 'tag_name' \
    | awk -F '"' '{print $4}'; \
})"

curl -L \
    -o /tmp/ros2-apt-source.deb \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb
```

Update Ubuntu again before installing ROS 2:

```bash
sudo apt update
sudo apt upgrade -y
```

## 7.3 Install ROS 2 Desktop and development tools

Install the desktop version because the internship uses RViz and graphical ROS tools:

```bash
sudo apt install -y \
    ros-humble-desktop \
    ros-dev-tools
```

This installation provides the ROS 2 core, command-line tools, RViz, demos, tutorials, compilers and common workspace-development utilities.

---

# 8. Configure ROS 2 in Bash

Test the ROS 2 environment in the current terminal:

```bash
source /opt/ros/humble/setup.bash
```

Verify:

```bash
echo "$ROS_DISTRO"
```

Expected result:

```text
humble
```

Add the ROS 2 setup command to `.bashrc`, but only if it is not already present:

```bash
grep -qxF 'source /opt/ros/humble/setup.bash' ~/.bashrc \
    || echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
```

Reload the Bash configuration:

```bash
source ~/.bashrc
```

Verify again:

```bash
echo "$ROS_DISTRO"
which ros2
```

Expected results:

```text
humble
/opt/ros/humble/bin/ros2
```

> This `.bashrc` line sources only the system ROS 2 installation. Do not add a personal ROS workspace or the future `px4-venv` to `.bashrc`.

---

# 9. Install the ROS 2 packages required for the internship

Install the packages needed for ROS 2 development, Gazebo integration, image transport, OpenCV bridging, transforms, visualization and basic control exercises:

```bash
sudo apt update
sudo apt-get install ros-humble-ros2-control
sudo apt-get install ros-humble-ros2-controllers
sudo apt-get install ros-humble-xacro
sudo apt-get install ros-humble-ros-gz-*
sudo apt-get install ros-humble-*-ros2-control
sudo apt-get install ros-humble-joint-state-publisher-gui
sudo apt-get install ros-humble-turtlesim
sudo apt-get install ros-humble-robot-localization
sudo apt-get install ros-humble-joy
sudo apt-get install ros-humble-joy-teleop
sudo apt-get install ros-humble-tf-transformations
```

Open a clean terminal and run:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev \
    ros-humble-cv-bridge ros-humble-rclpy \
    ros-humble-sensor-msgs ros-humble-image-transport
```

---

# 10. Initialize rosdep

`rosdep` installs system dependencies declared by ROS packages.

Check whether it is already initialized:

```bash
if [ -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    echo "rosdep is already initialized."
else
    sudo rosdep init
fi
```

Update its database:

```bash
rosdep update
```

Do not repeat `sudo rosdep init` after it has already succeeded.

---

# 11. Keep the system Python clean

At this stage, do not install AI libraries globally.

Do not run:

```bash
sudo pip install ...
pip3 install ultralytics
pip3 install numpy --upgrade
```

Why?

ROS 2 packages such as `cv_bridge` are installed for the system Python and are compiled against compatible system libraries. Replacing the system NumPy with another major version can create errors such as:

```text
A module compiled using NumPy 1.x cannot be run with NumPy 2.x
AttributeError: _ARRAY_API not found
```

For the base system, use Ubuntu packages:

```bash
sudo apt install python3-numpy python3-opencv python3-transforms3d
```

---

# 12. Validate the base installation

## 12.1 System validation

```bash
lsb_release -rs
python3 --version
echo "$ROS_DISTRO"
which ros2
```

Expected values:

```text
22.04
Python 3.10.x
humble
/opt/ros/humble/bin/ros2
```

## 12.2 Check main ROS packages

```bash
for package in \
    cv_bridge \
    image_transport \
    ros_gz_bridge \
    ros_gz_image \
    rqt_image_view \
    robot_localization \
    turtlesim
do
    if ros2 pkg prefix "$package" >/dev/null 2>&1; then
        echo "[OK] $package"
    else
        echo "[MISSING] $package"
    fi
done
```

All packages should report `[OK]`.

## 12.3 Test ROS 2 with talker and listener

Open Terminal 1:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```

Open Terminal 2:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_py listener
```

The talker should publish messages and the listener should receive them.

Stop both with:

```text
Ctrl + C
```

## 12.4 Test the graphical installation

Run:

```bash
rviz2
```

RViz should open without crashing. Close it before continuing.

Test Turtlesim:

```bash
ros2 run turtlesim turtlesim_node
```

A small graphical window should appear.

---

# 13. Optional NVIDIA hardware check

Students with an NVIDIA GPU can check whether the operating system recognizes it:

```bash
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi
else
    echo "No NVIDIA driver command was detected."
    echo "This is not a blocker for the core internship."
fi
```

Do not install a CUDA Toolkit or PyTorch in this phase. GPU setup will be handled with the AI virtual environment later.

---

# 14. Final checklist

Confirm all items:

- [ ] Ubuntu 22.04 starts normally.
- [ ] Windows still starts normally if dual boot is used.
- [ ] Important files and recovery keys are backed up.
- [ ] `python3 --version` reports Python 3.10.x.
- [ ] ROS 2 Humble is installed under `/opt/ros/humble`.
- [ ] `echo $ROS_DISTRO` reports `humble`.
- [ ] ROS talker and listener communicate.
- [ ] RViz opens.
- [ ] Turtlesim opens.
- [ ] `cv_bridge`, `ros_gz_bridge` and `ros_gz_image` are discoverable.
- [ ] `rosdep update` completes successfully.
- [ ] `${HOME}/quard_um6p_intership` exists.

---

# 16. Troubleshooting

## `ROS_DISTRO` is empty

Run:

```bash
source /opt/ros/humble/setup.bash
echo "$ROS_DISTRO"
```

If this works, verify the `.bashrc` entry:

```bash
grep -n "source /opt/ros/humble/setup.bash" ~/.bashrc
```

## `ros2: command not found`

Check that ROS 2 exists:

```bash
ls /opt/ros/humble/setup.bash
```

Then source it:

```bash
source /opt/ros/humble/setup.bash
```

## `sudo rosdep init` says the file already exists

This is not an error requiring repair. Run only:

```bash
rosdep update
```

## An APT package cannot be located

Update package lists:

```bash
sudo apt update
```

Then verify that the ROS 2 repository setup from Section 7 completed successfully.

## Python package conflicts appear

Check whether packages were installed globally with `pip`:

```bash
python3 -m pip list
```

Do not upgrade NumPy globally. The future AI dependencies will be isolated in `${HOME}/px4-venv`.

---

# 17. Official references

- ROS 2 Humble installation using Ubuntu deb packages:  
  https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html

- ROS 2 Humble beginner tutorials:  
  https://docs.ros.org/en/humble/Tutorials.html

- Ubuntu Desktop download:  
  https://ubuntu.com/download/desktop

- Windows 11 and Ubuntu dual-boot video supplied for this course:  
  https://www.youtube.com/watch?v=mXyN1aJYefc&t=308s

---

# Next phase

The next guide will cover:

```text
1. Creating ${HOME}/px4-venv
2. Pinning NumPy to a ROS-compatible version
3. Installing Ultralytics and optional CUDA-enabled PyTorch
4. Cloning and building PX4-Autopilot
5. Building Micro XRCE-DDS Agent
6. Creating the independent ROS 2 workspace
7. Running PX4, Gazebo and the x500_depth camera model
```
