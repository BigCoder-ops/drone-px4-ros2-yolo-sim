# PX4 Orbit Inspection

## 1. Project story

A drone acts as an aerial inspector. It climbs smoothly, approaches a virtual asset, flies a cinematic orbit while facing the asset with its camera, displays desired and measured paths, reports live altitude and speed, then lands.

The first classroom run should feel like a complete robotic mission, not only a circle equation:

```text
READY -> CLIMB -> APPROACH -> ORBIT AND INSPECT -> HOLD -> LAND
```

The minimum project is simulation-only. Real-flight use needs a separate safety process, manual takeover and an authorized operator.

## 2. How to re-creat the px4_orbit_inspection package

The package is an `ament_python` package with the standard ROS 2 Python elements:

```text
package.xml
resource/px4_orbit_inspection
setup.cfg
setup.py
px4_orbit_inspection/__init__.py
```

It is created conceptually with:

```bash
cd /home/tnourji/dev/ws_sensor_combined/src
source /opt/ros/humble/setup.bash
ros2 pkg create --build-type ament_python   --license Apache-2.0   --node-name orbit_controller  px4_orbit_inspection  --dependencies rclpy px4_msgs std_srvs geometry_msgs nav_msgs visualization_msgs
```


## 3. Existing environment assumed

- Ubuntu 22.04
- Python 3.10
- ROS 2 Humble at `/opt/ros/humble`
- PX4 SITL and Gazebo already verified
- Micro XRCE-DDS Agent already verified
- workspace `/home/tnourji/dev/ws_sensor_combined`
- virtual environment `/home/tnourji/px4-venv`
- matching `px4_msgs` already present in the workspace


## 4. Build with colcon

```bash
cd /home/tnourji/dev/ws_sensor_combined
source /opt/ros/humble/setup.bash
source /home/tnourji/px4-venv/bin/activate
colcon build --symlink-install --packages-select px4_orbit_inspection
source install/setup.bash
```

Check discovery:

```bash
ros2 pkg list | grep px4_orbit_inspection
ros2 pkg executables px4_orbit_inspection
```

Expected executables:

```text
px4_orbit_inspection mission_monitor
px4_orbit_inspection orbit_controller
```

## 5. Start 

1. PX4 SITL and Gazebo
2. Micro XRCE-DDS Agent

Then verify the bridge:

```bash
ros2 topic echo /fmu/out/vehicle_odometry --once
ros2 topic echo /fmu/out/vehicle_status --once
```

If these commands show nothing, do not launch the mission. Check the Agent, ROS domain, PX4/`px4_msgs` compatibility, and sourced workspaces.

## 6. Demonstration

Launch the two nodes:

```bash
cd /home/tnourji/dev/ws_sensor_combined
source /opt/ros/humble/setup.bash
source /home/tnourji/px4-venv/bin/activate
source install/setup.bash
ros2 launch px4_orbit_inspection orbit_demo.launch.py
```

Start only after everyone sees Gazebo:

```bash
ros2 service call /orbit/start std_srvs/srv/Trigger "{}"
```

Abort and request landing:

```bash
ros2 service call /orbit/abort std_srvs/srv/Trigger "{}"
```

RViz display:

```bash
rviz2
```

Use Fixed Frame `map`, then add:

- Path: `/orbit/desired_path`
- Path: `/orbit/measured_path`
- Marker: `/orbit/inspection_target`

The controller converts NED positions to ENU only for RViz visualization. Commands sent to PX4 remain NED.

## 7. Implemented physics and mathematics

### 7.1 Coordinate frame

PX4 local position uses NED:

```text
x = North
y = East
z = Down
```

Therefore a physical height `h` is commanded as `z = -h`. RViz usually uses ENU. For visualization:

```text
RViz x = PX4 East
RViz y = PX4 North
RViz z = -PX4 Down
```

A frame is not cosmetic. It defines what every number means.

### 7.2 Circular geometry

For center `(cx, cy)`, radius `R`, and angle `theta`:

```text
north = cx + R*cos(theta)
east  = cy + R*sin(theta)
down  = -altitude
```

One complete orbit is `2*pi` radians. If one orbit needs period `T`:

```text
theta(t) = 2*pi*t/T
angular speed omega = 2*pi/T
```

### 7.3 Tangential speed

The distance around one circle is `2*pi*R`. Therefore:

```text
speed v = 2*pi*R/T = R*omega
```

Default values `R=5 m`, `T=24 s` give approximately:

```text
v = 2*pi*5/24 = 1.31 m/s
```

Reducing the period increases speed and normally increases tracking difficulty.

### 7.4 Centripetal acceleration

The vehicle velocity continually changes direction. The required inward acceleration is:

```text
a_c = v^2/R = R*omega^2
```

With the default mission:

```text
a_c = 1.31^2/5 = 0.34 m/s^2
```

A smaller period increases required acceleration quadratically. Halving `T` doubles speed but makes centripetal acceleration four times larger.

### 7.5 Yaw facing the target

To make the orbit visually meaningful, the drone faces the inspection center:

```text
yaw = atan2(center_east - east, center_north - north)
```

The two-argument `atan2` keeps the correct quadrant. This is a simple example of active perception: vehicle orientation is selected to improve observation of a target.

### 7.6 Smooth climb and approach

Instantly jumping from one setpoint to another creates a difficult transient. The function

```text
s(u) = 3*u^2 - 2*u^3,  0 <= u <= 1
```

moves smoothly from 0 to 1 and has zero slope at both endpoints. The node uses it for climb and approach. Students can compare this with a linear interpolation and observe the effect.

This is reference shaping, not full trajectory optimization. PX4's internal controllers still stabilize the vehicle and track the references.

### 7.7 Feedback and tracking error

The node publishes a desired position. PX4 measures/estimates actual position and its controller tries to reduce the error:

```text
position error e = desired position - measured position
```

For a single interpretable number, the package reports Euclidean tracking error:

```text
||e|| = sqrt(ex^2 + ey^2 + ez^2)
```

The node does not replace PX4's control loops. It acts as a reference generator. PX4 remains responsible for low-level stabilization and position tracking.

### 7.8 Discrete-time setpoints

The mathematical curve is continuous, but software publishes samples. At 20 Hz:

```text
sample time dt = 1/20 = 0.05 s
```

Each timer tick evaluates the desired trajectory at the current time. A higher rate creates closer reference points but uses more computation and communication. The package rejects rates below 10 Hz, and PX4 requires a continuing offboard heartbeat.

### 7.9 Why warmup exists

Before requesting offboard mode, the package streams heartbeat and setpoint messages for about one second. This proves to PX4 that an external controller is alive. The stream continues throughout the mission.

### 7.10 What physics is delegated to PX4/Gazebo

This educational node does not calculate motor thrust or attitude commands. The following are delegated:

- rigid-body translation and rotation;
- gravity;
- aerodynamic and motor effects represented by the simulation model;
- state estimation;
- inner attitude and angular-rate control;
- position and velocity control;
- actuator allocation.

This separation is intentional.  First understand mission-level trajectory generation and system integration. Later, you can study lower control layers (optionel)

## 9. ROS 2 concepts

Inspect the graph:

```bash
rqt_graph
ros2 node info /orbit_controller
ros2 topic list | grep orbit
ros2 param list /orbit_controller
```
