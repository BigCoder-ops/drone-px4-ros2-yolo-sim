# UM6P Autonomous Drone Internship

## Phase 1: Create the PX4 and AI Python Virtual Environment

This guide creates the Python virtual environment used by the internship's ROS 2 perception, computer-vision, YOLO and optional MAVSDK tools.

Complete **Phase 0: Ubuntu 22.04 and ROS 2 Humble Installation** before starting this guide.

---

# 1. Target environment

At the end of this phase, the computer should have:

```text
Operating system:        Ubuntu 22.04 LTS
System Python:           Python 3.10
ROS 2:                   Humble under /opt/ros/humble
Project folder:          ${HOME}/quard_um6p_intership
Virtual environment:     ${HOME}/px4-venv
NumPy:                    1.26.4
OpenCV Python:            4.11.0.86
PyTorch:                  2.9.1
Torchvision:              0.24.1
Ultralytics:              8.3.237
Pillow:                    12.0.0
PyYAML:                    6.0.3
```

The same instructions support:

- computers with an NVIDIA GPU;
- computers without an NVIDIA GPU;
- CPU-only inference;
- CUDA-accelerated inference when the NVIDIA driver works.

> The virtual environment is created in `${HOME}/px4-venv`, outside `ros2_ws`. Do not copy the virtual environment to another computer. Each student must recreate it using this guide.

---

# 2. Why this virtual environment is necessary

ROS 2 Humble Python packages such as `rclpy` and `cv_bridge` are installed under `/opt/ros/humble`. AI libraries such as Ultralytics and PyTorch require additional Python packages that should not be installed globally.

The environment is therefore created with:

```text
--system-site-packages
```

This gives the virtual environment access to the Ubuntu and ROS 2 Python packages while allowing project-specific packages to be installed inside `${HOME}/px4-venv`.

The virtual environment's packages take priority over system packages with the same name. This is why the environment can use the project-pinned NumPy version while still importing ROS 2 modules.

---

# 3. Important rules

Follow these rules for the complete internship:

1. Never use `sudo pip install`.
2. Never replace `/usr/bin/python3`.
3. Never globally upgrade NumPy, OpenCV, PyTorch or Ultralytics.
4. Always activate `${HOME}/px4-venv` before installing project Python packages.
5. Always use `python -m pip`, not an unqualified `pip` command.
6. Use NumPy `1.26.4` because the Ubuntu ROS 2 Humble `cv_bridge` binary must not be loaded with NumPy 2.x.
7. Do not copy another student's virtual environment directory.
8. Do not add `source ${HOME}/px4-venv/bin/activate` to `.bashrc`.
9. Do not source another ROS 2 workspace such as `ws_sensor_combined` or `ws_offboard_control` when building the independent internship workspace.

---

# 4. Enter the internship project

Open a new terminal:

```bash
cd "${HOME}/quard_um6p_intership"
```

Confirm the current path:

```bash
pwd
```

Expected form:

```text
/home/<student_username>/quard_um6p_intership
```

Load the project configuration:

```bash
source ./config/project.env
```

Confirm the project variables:

```bash
printf 'INTERNSHIP_ROOT=%s\n' "${INTERNSHIP_ROOT}"
printf 'ROS2_WS=%s\n' "${ROS2_WS}"
printf 'PX4_DIR=%s\n' "${PX4_DIR}"
```

These paths must refer to the current student's home directory. They must not contain `/home/tnourji` on another student's computer.

---

# 5. Check prerequisites

Confirm Ubuntu:

```bash
lsb_release -rs
```

Expected:

```text
22.04
```

Confirm system Python:

```bash
/usr/bin/python3 --version
```

Expected:

```text
Python 3.10.x
```

Confirm ROS 2:

```bash
source /opt/ros/humble/setup.bash

echo "${ROS_DISTRO}"
```

Expected:

```text
humble
```

Confirm the required Ubuntu packages:

```bash
sudo apt update

sudo apt install -y \
    python3-venv \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    python3-numpy \
    python3-opencv \
    ros-humble-rclpy \
    ros-humble-cv-bridge \
    ros-humble-sensor-msgs \
    ros-humble-image-transport
```

---

# 6. Remove an incomplete environment only when necessary

Check whether the environment already exists:

```bash
if [ -d "${HOME}/px4-venv" ]; then
    echo "Existing environment found: ${HOME}/px4-venv"
else
    echo "No existing environment found."
fi
```

If it already exists and works, do not delete it unnecessarily.

If a previous installation was interrupted or the environment is known to be corrupted, recreate it:

```bash
deactivate 2>/dev/null || true

rm -rf "${HOME}/px4-venv"
```

This removes only the virtual environment. It does not remove the internship project or system Python.

---

# 7. Create the environment

Create it using Ubuntu's system Python:

```bash
/usr/bin/python3 -m venv \
    --system-site-packages \
    "${HOME}/px4-venv"
```

Activate it:

```bash
source "${HOME}/px4-venv/bin/activate"
```

The terminal prompt should begin with:

```text
(px4-venv)
```

Confirm the environment:

```bash
which python
python --version
echo "${VIRTUAL_ENV}"
```

Expected form:

```text
/home/<student_username>/px4-venv/bin/python
Python 3.10.x
/home/<student_username>/px4-venv
```

Check the environment configuration:

```bash
cat "${HOME}/px4-venv/pyvenv.cfg"
```

It must contain:

```text
include-system-site-packages = true
```

Prevent Colcon from treating the environment as a workspace directory:

```bash
touch "${HOME}/px4-venv/COLCON_IGNORE"
```

---

# 8. Upgrade the packaging tools safely

Keep Setuptools below version 80 for this pinned environment:

```bash
python -m pip install --upgrade \
    pip \
    wheel \
    "setuptools==79.0.1"
```

Confirm that installation commands target the environment:

```bash
which python
python -m pip --version
```

Both paths must contain:

```text
${HOME}/px4-venv
```

Do not use:

```bash
python -m pip install --upgrade setuptools
```

without the version constraint.

---

# 9. Install NumPy and OpenCV first

Remove potentially conflicting OpenCV and NumPy wheels from the virtual environment:

```bash
python -m pip uninstall -y \
    numpy \
    opencv-python \
    opencv-python-headless \
    opencv-contrib-python \
    opencv-contrib-python-headless
```

An uninstall message saying that a package was not installed is acceptable.

Install the pinned versions:

```bash
python -m pip install --no-cache-dir \
    "numpy==1.26.4" \
    "opencv-python==4.11.0.86"
```

Verify them:

```bash
python - <<'PY'
import sys
import numpy
import cv2

print("Python :", sys.executable)
print("NumPy :", numpy.__version__)
print("OpenCV:", cv2.__version__)
PY
```

Expected key values:

```text
NumPy : 1.26.4
OpenCV: 4.11.0
```

Now test ROS image compatibility:

```bash
source /opt/ros/humble/setup.bash

python - <<'PY'
import numpy
import cv2
from cv_bridge import CvBridge

print("NumPy   :", numpy.__version__)
print("OpenCV  :", cv2.__version__)
print("CvBridge: OK")
PY
```

If this reports `_ARRAY_API not found`, stop. Do not continue with PyTorch. Follow the repair section near the end of this guide.

---

# 10. Choose the PyTorch installation

PyTorch must be installed differently for CPU-only and NVIDIA computers.

## 10.1 Check for an NVIDIA GPU

Run:

```bash
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi
else
    echo "No NVIDIA driver command detected."
fi
```

Use the CPU installation if:

- the computer has no NVIDIA GPU;
- `nvidia-smi` is unavailable;
- `nvidia-smi` reports a driver error;
- the student is unsure.

Use the CUDA installation only if `nvidia-smi` works correctly.

## 10.2 Option A: CPU-only installation

This is the universal and safest option:

```bash
python -m pip install --no-cache-dir \
    "torch==2.9.1" \
    "torchvision==0.24.1" \
    "torchaudio==2.9.1" \
    --index-url https://download.pytorch.org/whl/cpu
```

## 10.3 Option B: NVIDIA CUDA installation

For a working NVIDIA driver, install the official CUDA 12.6 wheel set:

```bash
python -m pip install --no-cache-dir \
    "torch==2.9.1" \
    "torchvision==0.24.1" \
    "torchaudio==2.9.1" \
    --index-url https://download.pytorch.org/whl/cu126
```

A separate CUDA Toolkit installation with `nvcc` is not required for normal PyTorch inference because the PyTorch wheel includes its CUDA runtime components. A compatible, working NVIDIA driver remains required.

> Do not run Gazebo or other memory-intensive applications while PyTorch is being installed.

## 10.4 Verify PyTorch

```bash
python - <<'PY'
import torch
import torchvision

print("PyTorch     :", torch.__version__)
print("Torchvision :", torchvision.__version__)
print("CUDA runtime:", torch.version.cuda)
print("CUDA usable :", torch.cuda.is_available())
print(
    "GPU          :",
    torch.cuda.get_device_name(0)
    if torch.cuda.is_available()
    else "NONE"
)
PY
```

Expected package versions:

```text
PyTorch     : 2.9.1
Torchvision : 0.24.1
```

On a CPU installation:

```text
CUDA usable : False
GPU          : NONE
```

This is a valid result.

On a correctly configured NVIDIA installation:

```text
CUDA usable : True
GPU          : NVIDIA GeForce ...
```

---

# 11. Install Ultralytics and project packages

Install the pinned packages:

```bash
python -m pip install --no-cache-dir \
    "ultralytics==8.3.237" \
    "pillow==12.0.0" \
    "PyYAML==6.0.3"
```

Reapply the NumPy pin because dependency resolution may otherwise select a newer major version:

```bash
python -m pip install --no-cache-dir --force-reinstall \
    "numpy==1.26.4"
```

Reapply the Setuptools pin:

```bash
python -m pip install --no-cache-dir --force-reinstall \
    "setuptools==79.0.1"
```

Check dependency consistency:

```bash
python -m pip check
```

Expected:

```text
No broken requirements found.
```

---

# 12. Install other project packages

```bash
python -m pip install --no-cache-dir \
    "pandas==2.3.3" \
    "scipy==1.15.3" \
    "mavsdk==3.10.2" \
    "pymavlink==2.4.49" \
    "pyserial==3.5"
```

These packages support data analysis, MAVSDK keyboard control, MAVLink utilities and serial communication.

---

# 13. Check the installed package inventory

Use metadata inspection first. This does not import OpenCV or PyTorch:

```bash
python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

packages = [
    "numpy",
    "opencv-python",
    "torch",
    "torchvision",
    "ultralytics",
    "pillow",
    "PyYAML",
    "setuptools",
]

for package in packages:
    try:
        print(f"{package:27s} {version(package)}")
    except PackageNotFoundError:
        print(f"{package:27s} NOT INSTALLED")
PY
```

The inventory should contain only one pip OpenCV variant. Normally:

```text
numpy                       1.26.4
opencv-python               4.11.0.86
torch                       2.9.1
torchvision                 0.24.1
ultralytics                 8.3.237
pillow                      12.0.0
PyYAML                      6.0.3
setuptools                  79.0.1
```

---

# 14. Final Python, ROS 2 and AI validation

Keep the virtual environment active, then source ROS 2:

```bash
source /opt/ros/humble/setup.bash
```

Confirm that sourcing ROS 2 did not change the active Python:

```bash
which python
echo "${VIRTUAL_ENV}"
```

Expected form:

```text
/home/<student_username>/px4-venv/bin/python
/home/<student_username>/px4-venv
```

Run the complete test:

```bash
python - <<'PY'
import sys
import numpy
import cv2
import torch
import torchvision
import ultralytics
import PIL
import yaml
import rclpy
from cv_bridge import CvBridge

print("Python       :", sys.executable)
print("NumPy        :", numpy.__version__)
print("OpenCV       :", cv2.__version__)
print("PyTorch      :", torch.__version__)
print("Torchvision  :", torchvision.__version__)
print("Ultralytics  :", ultralytics.__version__)
print("Pillow       :", PIL.__version__)
print("PyYAML       :", yaml.__version__)
print("rclpy        : OK")
print("CvBridge     : OK")
print("CUDA runtime :", torch.version.cuda)
print("CUDA usable  :", torch.cuda.is_available())
print(
    "GPU          :",
    torch.cuda.get_device_name(0)
    if torch.cuda.is_available()
    else "NONE"
)
PY
```

Expected key results:

```text
Python       : /home/tnourji/px4-venv/bin/python
NumPy        : 1.26.4
OpenCV       : 4.11.0
PyTorch      : 2.9.1+cu128
Torchvision  : 0.24.1+cu128
Ultralytics  : 8.3.237
Pillow       : 12.0.0
PyYAML       : 6.0.3
rclpy        : OK
CvBridge     : OK
CUDA runtime : 12.8
CUDA usable  : True
GPU          : NVIDIA GeForce RTX 4080 SUPER
```

`CUDA usable: False` is acceptable on computers without an NVIDIA GPU or when the CPU PyTorch wheel was intentionally installed.

---

# 15. Test the included YOLO model

Load the project configuration:

```bash
cd "${HOME}/quard_um6p_intership"
source ./config/project.env
```

Locate the model:

```bash
MODEL_PATH="${INTERNSHIP_ROOT}/models/yolo/yolov8m.pt"

test -f "${MODEL_PATH}" \
    && echo "[OK] Model found: ${MODEL_PATH}" \
    || echo "[MISSING] ${MODEL_PATH}"
```

Test model loading without Gazebo or ROS topics:

```bash
python - <<'PY'
import os
from ultralytics import YOLO

project_root = os.environ["INTERNSHIP_ROOT"]
model_path = os.path.join(
    project_root,
    "models",
    "yolo",
    "yolov8m.pt",
)

model = YOLO(model_path)

print("YOLO model loaded successfully:")
print(model_path)
PY
```

This test should not download another model because it uses the supplied absolute path.

---

# 16. Create reproducibility files

Create a directory for Python setup records:

```bash
mkdir -p "${INTERNSHIP_ROOT}/installation_guide/phase1"
```

Save the complete environment inventory:

```bash
python -m pip freeze \
    > "${INTERNSHIP_ROOT}/installation_guide/phase1/px4-venv-freeze.txt"
```

Create a concise direct-dependency file:

```bash
cat > "${INTERNSHIP_ROOT}/installation_guide/phase1/requirements-ai.txt" <<'EOF'
numpy==1.26.4
opencv-python==4.11.0.86
torch==2.9.1
torchvision==0.24.1
torchaudio==2.9.1
ultralytics==8.3.237
pillow==12.0.0
PyYAML==6.0.3
setuptools==79.0.1
EOF
```

The `requirements-ai.txt` file records direct project choices. The freeze file records the complete resolved environment. Do not recreate PyTorch only from the concise file because CPU and CUDA installations require different PyTorch index URLs.

---

# 17. Correct order for every new terminal

For perception or AI execution, use:

```bash
cd "${HOME}/quard_um6p_intership"

source ./config/project.env
source /opt/ros/humble/setup.bash
source "${HOME}/px4-venv/bin/activate"

if [ -f "${ROS2_WS}/install/setup.bash" ]; then
    source "${ROS2_WS}/install/setup.bash"
fi
```

Then verify:

```bash
which python
python -c "import numpy; print(numpy.__version__)"
```

Expected:

```text
/home/<student_username>/px4-venv/bin/python
1.26.4
```

> Do not source an unrelated research workspace. Only source the internship workspace after it has been built.

---

# 18. Important Colcon note for Python ROS 2 packages

For ROS 2 Python packages that import Ultralytics, the installed executable must use the virtual-environment Python.

Before building the internship workspace, verify:

```bash
which python
which colcon
```

If `colcon` points to `/usr/bin/colcon`, install Colcon inside the active environment:

```bash
python -m pip install \
    "colcon-common-extensions"

hash -r
```

Check again:

```bash
which colcon
head -n 1 "$(which colcon)"
```

The path and shebang should refer to `${HOME}/px4-venv`.

When Phase 2 instructs you to build the ROS 2 workspace, build it only after activating this environment. Otherwise a generated ROS 2 Python executable may use `/usr/bin/python3`, fail to find Ultralytics and load a different NumPy version.

Do not build the workspace in this phase unless the Phase 2 guide explicitly instructs you to do so.

---

# 19. Repair procedure

Use this section only when validation fails.

## 19.1 `_ARRAY_API not found` or NumPy 2.x warning

Symptoms:

```text
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x
AttributeError: _ARRAY_API not found
```

Repair:

```bash
source "${HOME}/px4-venv/bin/activate"

python -m pip uninstall -y \
    numpy \
    opencv-python \
    opencv-python-headless \
    opencv-contrib-python \
    opencv-contrib-python-headless

python -m pip install --no-cache-dir \
    "numpy==1.26.4" \
    "opencv-python==4.11.0.86"
```

Test:

```bash
source /opt/ros/humble/setup.bash

python - <<'PY'
import numpy
import cv2
from cv_bridge import CvBridge

print("NumPy   :", numpy.__version__)
print("OpenCV  :", cv2.__version__)
print("CvBridge: OK")
PY
```

## 19.2 `No module named ultralytics`

First verify the active interpreter:

```bash
which python
python -m pip show ultralytics
```

If Ultralytics is missing:

```bash
python -m pip install --no-cache-dir \
    "ultralytics==8.3.237"
```

If it is installed but a ROS 2 executable cannot find it, the executable was probably generated using a different Python interpreter. The ROS 2 workspace must later be cleaned and rebuilt with the virtual environment active and a virtual-environment Colcon installation.

## 19.3 PyTorch installation was interrupted

Inspect package metadata without importing PyTorch:

```bash
python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

for package in ("torch", "torchvision", "torchaudio"):
    try:
        print(package, version(package))
    except PackageNotFoundError:
        print(package, "NOT INSTALLED")
PY
```

Remove incomplete packages:

```bash
python -m pip uninstall -y \
    torch \
    torchvision \
    torchaudio
```

Then reinstall either the CPU or CUDA option from Section 10.

## 19.4 CUDA is unavailable

Check:

```bash
nvidia-smi
```

Then:

```bash
python - <<'PY'
import torch

print("PyTorch build :", torch.__version__)
print("CUDA runtime  :", torch.version.cuda)
print("CUDA available:", torch.cuda.is_available())
PY
```

Interpretation:

- `torch.version.cuda` is `None`: a CPU-only PyTorch wheel is installed.
- `torch.version.cuda` has a version but CUDA is unavailable: inspect the NVIDIA driver.
- no NVIDIA GPU: continue with CPU inference.

Do not install a random CUDA Toolkit as the first troubleshooting step.

## 19.5 `pip check` reports OpenCV requiring NumPy 2.x

Do not upgrade NumPy to 2.x. Confirm that the pinned OpenCV version is installed:

```bash
python -m pip show opencv-python
python -m pip show numpy
```

Then reinstall the pair:

```bash
python -m pip install --no-cache-dir --force-reinstall \
    "numpy==1.26.4" \
    "opencv-python==4.11.0.86"
```

## 19.6 The environment is badly damaged

Virtual environments are disposable. Recreate it rather than repeatedly patching an unknown state:

```bash
deactivate 2>/dev/null || true
rm -rf "${HOME}/px4-venv"
```

Return to Section 7 and follow the guide in order.

---

# 20. Final checklist

Before continuing to PX4 and workspace build phases, confirm:

- [ ] `${HOME}/px4-venv` exists.
- [ ] `pyvenv.cfg` contains `include-system-site-packages = true`.
- [ ] `which python` points to `${HOME}/px4-venv/bin/python`.
- [ ] Python reports version 3.10.x.
- [ ] NumPy reports 1.26.4.
- [ ] OpenCV reports 4.11.0.
- [ ] `from cv_bridge import CvBridge` works.
- [ ] PyTorch reports 2.9.1.
- [ ] Torchvision reports 0.24.1.
- [ ] Ultralytics reports 8.3.237.
- [ ] `import rclpy` works after sourcing ROS 2.
- [ ] The supplied `yolov8m.pt` can be loaded.
- [ ] `python -m pip check` reports no broken requirements.
- [ ] `${HOME}/px4-venv/COLCON_IGNORE` exists.
- [ ] CPU-only students understand that `CUDA usable: False` is valid.
- [ ] No AI package was installed using `sudo pip`.
- [ ] No unrelated ROS 2 workspace is sourced.

---

# 21. Reference links

- Python virtual environments:  
  https://docs.python.org/3/library/venv.html

- Python virtual-environment tutorial:  
  https://docs.python.org/3/tutorial/venv.html

- PyTorch official installation selector:  
  https://pytorch.org/get-started/locally/

- PyTorch previous-version commands for 2.9.1:  
  https://pytorch.org/get-started/previous-versions/

- ROS 2 `cv_bridge`:  
  https://index.ros.org/p/cv_bridge/

---

# Next phase

The next guide will cover:

```text
1. Verifying the independent PX4 and px4_msgs revisions
2. Building PX4 SITL and Gazebo
3. Building Micro XRCE-DDS Agent
4. Building the independent ROS 2 workspace
5. Ensuring ROS 2 Python executables use px4-venv
6. Starting x500_depth and the camera bridge
7. Running YOLO with CPU or NVIDIA acceleration
```
