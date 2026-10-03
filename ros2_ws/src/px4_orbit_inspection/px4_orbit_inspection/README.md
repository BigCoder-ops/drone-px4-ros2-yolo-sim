# Beginner-Annotated PX4 Orbit Scripts

This package contains the three scripts

## Files

- `trajectory.py`: orbit mathematics, smoothstep, yaw, and tracking error.
- `mission_monitor.py`: ROS 2 subscriptions and a readable flight dashboard.
- `orbit_controller.py`: PX4 offboard publishers, services, state machine, trajectory, and RViz paths.

## How topic and service names are discovered

While the system is running, use:

```bash
ros2 node list
ros2 topic list
ros2 topic list | grep /fmu
ros2 topic info /fmu/out/vehicle_odometry --verbose
ros2 interface show px4_msgs/msg/VehicleOdometry
ros2 service list
ros2 service type /orbit/start
ros2 node info /orbit_controller
```

PX4 interface topics use `/fmu/in/...` for data entering PX4 and `/fmu/out/...`
for data leaving PX4. The `/orbit/...` names are application-specific names
chosen by this project.