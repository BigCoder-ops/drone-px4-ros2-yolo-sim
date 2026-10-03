# QUARD UM6P Autonomous Drone Engineering Internship

Welcome to the **QUARD UM6P Autonomous Drone Engineering Internship**. In this project, you will learn how a modern autonomous drone system is organized by working with **Ubuntu 22.04, ROS 2 Humble, PX4, Gazebo, Python, computer vision, and object detection**.

The internship follows a practical engineering approach:

```text
Mission -> Requirements -> Architecture -> Design -> Simulation
        -> Programming -> Integration -> Testing -> Demonstration
```

You are **not expected to know GitHub, Linux, ROS 2, PX4, Gazebo, or artificial intelligence before starting**. The installation guides are written to be followed in order, one command at a time. Do not skip a phase, even if a later activity appears more interesting.

> **Safety scope:** This repository is designed primarily for PX4 SITL and Gazebo simulation. Do not use the autonomous-control code on a physical drone unless the activity is explicitly authorized and supervised.

---

## 1. What You Will Build

By the end of the internship, your team will work toward an autonomous aerial-inspection demonstration in which a simulated drone can:

1. take off in Gazebo;
2. receive flight commands through PX4 and ROS 2;
3. follow a planned trajectory;
4. observe objects using its camera;
5. detect selected objects using computer vision or YOLO;
6. associate detections with mission information;
7. record experimental evidence;
8. explain what worked, what failed, and what should be improved.

The goal is not only to make the drone move. The goal is to understand how the complete system works and how engineering decisions are validated with evidence.

---

## 2. Project Repository

The official project repository is:

```text
https://github.com/abdtnourji/quard_um6p_intership
```

A GitHub repository is an online project folder. It stores source code, documentation, configuration files, scripts, and the history of project changes.

### Important GitHub words

- **Repository:** the complete online project folder.
- **Clone:** download a working copy using Git so it can later be updated.
- **ZIP:** download a simple compressed copy without Git history.
- **Commit:** a recorded version of the project.
- **Branch:** one line of project development. This internship normally uses `main`.
- **README:** the main instruction page of a repository.

For this internship, **cloning with Git is recommended** because it preserves the project structure and makes future updates easier.

---

## 3. Download the Project from GitHub

### Method A: Clone with Git, recommended

#### Step 1: Open the repository page

Open a web browser and visit:

```text
https://github.com/abdtnourji/quard_um6p_intership
```

You do not need to understand every button on the page. The files shown there belong to the internship project.

#### Step 2: Open a terminal

On Ubuntu, press:

```text
Ctrl + Alt + T
```

#### Step 3: Confirm that Git is installed

```bash
git --version
```

If Git is missing, install it:

```bash
sudo apt update
sudo apt install -y git git-lfs

git lfs install
```

#### Step 4: Move to your home directory

```bash
cd "${HOME}"
```

`cd` means **change directory**. `${HOME}` means your personal Ubuntu home folder, for example `/home/student`.

#### Step 5: Clone the repository

```bash
git clone \
    https://github.com/abdtnourji/quard_um6p_intership.git
```

Git will create:

```text
${HOME}/quard_um6p_intership
```

#### Step 6: Enter the project

```bash
cd "${HOME}/quard_um6p_intership"
```

#### Step 7: Verify the project

```bash
pwd
tree -L 2
```

The `pwd` command prints your current location. It should end with:

```text
/quard_um6p_intership
```

If `tree` is missing, install it:

```bash
sudo apt install -y tree
```

### Method B: Download a ZIP, only when Git cannot be used

1. Open the repository page in a browser.
2. Select the green **Code** button.
3. Select **Download ZIP**.
4. Open the Ubuntu **Downloads** folder.
5. Right-click the downloaded ZIP and select **Extract Here**.
6. Rename the extracted folder to exactly:

```text
quard_um6p_intership
```

7. Move it into your home directory.

The final location must be:

```text
${HOME}/quard_um6p_intership
```

The ZIP method does not preserve Git history and cannot be updated with `git pull`. Use Method A whenever possible.

---

## 4. Do Not Rename or Move Internal Folders

Several scripts calculate paths from the project structure. Keep these main folders and names unchanged:

```text
quard_um6p_intership/
├── config/
├── data/
├── dependencies/
├── gazebo/
├── installation_guide/
├── models/
├── perception/
├── ros2_ws/
├── scripts/
├── student_logs/
└── tools/
```

You may place the complete `quard_um6p_intership` folder in your home directory, but do not independently move folders such as `config`, `gazebo`, `models`, `ros2_ws`, or `scripts`.

Do not run project commands with `sudo` unless an installation guide explicitly includes `sudo` for an Ubuntu package-management command.

---

# Download and install Microsoft’s VS-Code

```bash
sudo apt update
sudo apt install -y wget gpg apt-transport-https
```

```bash
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /usr/share/keyrings/packages.microsoft.gpg > /dev/null
```

# Add Microsoft’s official VS Code repository

```bash
echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
```

# Install VS Code

```bash
sudo apt update
sudo apt install -y code
```

# Install Recommended Extensions

Install the essential tools for Python, ROS 2 (C++/XML), Git, and Markdown by running this block:

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-vscode.cpptools
code --install-extension redhat.vscode-yaml
code --install-extension yzhang.markdown-all-in-one
code --install-extension eamodio.gitlens
code --install-extension ms-azuretools.vscode-docker
```

# Set VS Code as the Default Editor (Optional but Recommended)

```bash
sudo update-alternatives --install /usr/bin/editor editor "$(which code)" 10
sudo update-alternatives --set editor "$(which code)"
```

# Working in VS Code

Opening the Complete Project
Always open the root directory of the project rather than individual files so VS Code can map the complete workspace:

```bash
cd ~/quard_um6p_intership
code .
```

Note: If prompted with a workspace-trust question, select Yes, I trust the authors.

## 5. Read the Installation Guides in Order

All primary setup instructions are located in:

```text
installation_guide/
```

Enter that directory and inspect its files:

```bash
cd "${HOME}/quard_um6p_intership/installation_guide"

ls
```

You should find:

```text
README_PHASE0_UBUNTU_ROS2_SETUP.md
README_PHASE_1_PX4_AI_VENV_SETUP.md
README_PHASE_2_PIPELINE.md
```

Follow them in the exact order below.

### Phase 0: Ubuntu 22.04 and ROS 2 Humble

Read:

```text
installation_guide/README_PHASE0_UBUNTU_ROS2_SETUP.md
```

This phase prepares the base computer:

- Ubuntu 22.04;
- system updates;
- development tools;
- ROS 2 Humble;
- ROS-Gazebo packages;
- ROS 2 validation.

Do not continue until every Phase 0 validation check passes.

### Phase 1: PX4 and AI Python Virtual Environment

Read:

```text
installation_guide/README_PHASE1_PX4_AI_VENV_SETUP.md
```

This phase creates:

```text
${HOME}/px4-venv
```

It installs and validates the Python packages required for:

- NumPy;
- OpenCV;
- ROS 2 `cv_bridge`;
- PyTorch;
- Ultralytics YOLO;
- CPU or optional NVIDIA execution.

Do not continue if the final Python, ROS 2, `cv_bridge`, and YOLO import tests fail.

### Pipeline Phase: Run the Complete Project

Read:

```text
installation_guide/README_PHASE_3_PIPELINE.md
```

This phase explains the complete startup order and integration pipeline, including the required terminals, PX4 SITL, Gazebo, communication, camera data, perception, mission execution, and output evidence.

Follow the terminal order exactly. Do not launch all components randomly.

> **Numbering note:** The file is currently named `README_PHASE_3_PIPELINE.md`. Always follow the filenames present in the repository and any instructions announced by the supervisor.

---

## 6. The Correct Learning and Setup Rule

For every phase:

```text
Read the objective
      ↓
Run one command or block
      ↓
Read the complete output
      ↓
Perform the validation check
      ↓
Record errors before modifying anything
      ↓
Continue only after the check passes
```

Do not copy the entire guide into a terminal. Run commands block by block.

When an error occurs:

1. stop at the failing step;
2. copy the complete command that was executed;
3. copy the complete error output;
4. record the current phase and section number;
5. record the result of `pwd`;
6. do not install random packages from forums;
7. ask a supervisor if you are not able to repair youself.

A useful support report looks like:

```text
Guide: README_PHASE1_PX4_AI_VENV_SETUP.md
Section: 14, Final validation
Current directory: /home/student/quard_um6p_intership
Command: python ...
Expected result: CvBridge: OK
Actual result: <complete error copied here>
```

This is much more useful than writing only “it does not work.”

---

## 7. Commands Used in Every New Terminal

The exact commands depend on the activity, but most project terminals begin from the project root:

```bash
cd "${HOME}/quard_um6p_intership"
```

Load project paths when requested:

```bash
source ./config/project.env
```

Load ROS 2 when requested:

```bash
source /opt/ros/humble/setup.bash
```

Activate the AI environment **when requested**:

```bash
source "${HOME}/px4-venv/bin/activate"
```

Load the built internship workspace only after it exists:

```bash
source "${HOME}/quard_um6p_intership/ros2_ws/install/setup.bash"
```

Do not source unrelated personal workspaces. Mixing workspaces can cause ROS 2 to load a different `px4_msgs`, Python package, launch file, or executable.

---

## 8. Student Responsibilities

Each student is responsible for:

- following installation instructions in order;
- keeping the project structure unchanged;
- maintaining an individual engineering logbook;
- recording commands, observations, errors, tests, and conclusions;
- understanding the code assigned to them;
- contributing identifiable work to the team;
- saving experimental evidence;
- respecting simulation and flight-safety rules;
- explaining what worked, what failed, and why.

**A successful internship is not defined only by a perfect demonstration. A well-observed and well-explained failure can be a valuable engineering result**.

---

## 9. Engineering Logbook

Use the folder:

```text
student_logs/
```

Your logbook should include, for each work session:

```text
Date:
Objective:
What I studied:
What I changed:
Command or code tested:
Expected result:
Observed result:
Evidence location:
Problem or failure:
Possible explanation:
Decision taken:
Next action:
```

Do not wait until the final day to reconstruct your work from memory.

---

## 10. Video Tutorials

[Watch the Drone Demo Video](docs/videodemo/Screencast%20from%2009-09-2026%2012:17:54%20PM.webm)

---

## 11. Internship Tasks and Required Deliverables

> **The final task specification PDF will be added here by the supervisor.**

Expected location:

```text
tasks/QUARD_UM6P_INTERNSHIP_TASKS.pdf
```

---

## 12. Quick Start Checklist

Before beginning technical work, confirm:

- [ ] I am using Ubuntu 22.04.
- [ ] I downloaded or cloned `quard_um6p_intership`.
- [ ] The project is located at `${HOME}/quard_um6p_intership`.
- [ ] I did not rename the internal project folders.
- [ ] I found the `installation_guide` directory.
- [ ] I will complete Phase 0 before Phase 1.
- [ ] I will complete Phase 1 before running the pipeline.
- [ ] I will run commands one block at a time.
- [ ] I will read command outputs instead of ignoring them.
- [ ] I will not install random packages when an error occurs.
- [ ] I will maintain my engineering logbook.
- [ ] I understand that the core project is simulation-first.
- [ ] I will read the task PDF when it is published.

---

## 13. Project Support

When asking for technical support, provide:

```bash
pwd
lsb_release -rs
python3 --version
echo "${ROS_DISTRO:-NOT_SOURCED}"
git -C "${HOME}/quard_um6p_intership" status --short
```

Also provide:

- the installation-guide filename;
- the current section number;
- the exact command;
- the complete error message;
- a short description of what you expected.

Never share passwords, GitHub tokens, private keys, or personal credentials in screenshots, logs, or support messages.

---

## 14. Supervisor and Project Information

```text
Project:      QUARD UM6P Autonomous Drone Engineering Internship
Institution:  Mohammed VI Polytechnic University, UM6P
Supervisor:   Abdellah TNOURJI
Repository:   https://github.com/abdtnourji/quard_um6p_intership
```

```text
Learn -> Build -> Test -> Fail -> Understand -> Improve -> Demonstrate
```
