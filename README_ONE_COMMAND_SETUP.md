# One-command setup (WSL2 Ubuntu 22.04)

This automates Phase 0, Phase 1 and the build steps of Phase 3.
The step-by-step guides in this folder stay valid; the script just runs them in order.

## Requirements

- Windows 10/11 with **WSL2** and **WSLg** (needed for the Gazebo window)
- **Ubuntu 22.04** distro: `wsl --install -d Ubuntu-22.04`
- About 25 GB free disk space and a stable internet connection
- Optional NVIDIA GPU: install the NVIDIA driver on **Windows** (not inside WSL). `nvidia-smi` must work inside Ubuntu. Without a GPU, everything still runs on CPU.

## Install

```bash
cd ~
git clone https://github.com/<your-user>/quard_um6p_intership.git
cd quard_um6p_intership
git lfs pull                      # only needed if weights are stored with Git LFS
chmod +x scripts/*.sh
./scripts/setup_all.sh            # auto-detects GPU; or add --cpu / --gpu
```

The project **must** be at `~/quard_um6p_intership` (the guides rely on this path).
Expect 1-2 hours. The script is safe to re-run: finished steps are skipped
(state is kept in `.setup_state/`, log in `logs/setup_all.log`).

## Run

```bash
./scripts/run_sim.sh              # opens a tmux session with every terminal of Phase 3
./scripts/run_sim.sh stop         # stops everything
```

Windows in the tmux session: `shell`, `dds`, `px4`, `spawn`, `bridge`, `orbit`, `yolo`
(switch with `Ctrl+b` then `n`/`p`, detach with `Ctrl+b d`).
Start the mission from the `shell` window:

```bash
ros2 service call /orbit/start std_srvs/srv/Trigger "{}"
```

## Docker alternative

```bash
docker compose up --build                                                    # CPU
TORCH=gpu docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build   # NVIDIA
```

The image is large and slow to build. Use the script above unless you specifically need a container.

## What is NOT in the repository (and why)

| Item | How it is recreated |
| --- | --- |
| `dependencies/` (PX4, DDS Agent) | `scripts/02_download_sources.sh`, pinned by `config/*_COMMIT.txt` |
| `ros2_ws/src/px4_msgs` | same script |
| `ros2_ws/build, install, log` | `colcon build` in `setup_all.sh` |
| `~/px4-venv` | created by `setup_all.sh` with the pinned versions |
| ROS 2, Gazebo, system packages | `apt`, run by `setup_all.sh` |

The `x500_depth` camera tilt is applied automatically, because that file lives inside `dependencies/` and is never pushed.

## Troubleshooting

- **No Gazebo window**: run `wsl --update` in Windows PowerShell, then `wsl --shutdown` and reopen Ubuntu.
- **Slow or black Gazebo without a GPU**: `export LIBGL_ALWAYS_SOFTWARE=1` before `run_sim.sh`.
- **`ERROR: ... must live at ~/quard_um6p_intership`**: move or re-clone the repo to your home directory.
- **GitHub API rate limit during ROS setup**: wait a few minutes and re-run.
- Anything else: see the failing phase's own guide in this folder.
