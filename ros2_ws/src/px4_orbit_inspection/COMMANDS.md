# Quick commands

```bash
cd /home/tnourji/dev/ws_sensor_combined/src
unzip /path/to/px4_orbit_inspection.zip
cd ..
source /opt/ros/humble/setup.bash
source /home/tnourji/px4-venv/bin/activate
colcon build --symlink-install --packages-select px4_orbit_inspection
source install/setup.bash
ros2 launch px4_orbit_inspection orbit_demo.launch.py
```

Start:

```bash
ros2 service call /orbit/start std_srvs/srv/Trigger "{}"
```

Abort:

```bash
ros2 service call /orbit/abort std_srvs/srv/Trigger "{}"
```
