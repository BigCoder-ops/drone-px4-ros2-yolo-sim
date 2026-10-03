"""
=============================================================================
Project   : Quadcopter Autonomous Inspection (UM6P Internship)
File      : orbit_controller.py
Author    : Dr. Abdellah TNOURJI
Website   : https://www.abdellahtnourji.com/
Date      : [Date, 20, Aug 2026]

Description:
    PX4 offboard mission: climb, approach, inspect by orbiting, hold, and land.
    The code is split into a state machine so each block of software maps to one
    visible phase in Gazebo. It sends PX4 NED position setpoints.
    Run in SITL first. Real flight requires a separate safety review and operator.

License   : UM6P
=============================================================================

"""


# Standard mathematics supplies pi and NaN values used by the trajectory.
import math

# Enum creates a fixed list of named mission states. auto() assigns each state
# an internal unique value, so we do not need to invent numeric codes manually.
from enum import Enum, auto

# rclpy is the Python interface to ROS 2.
import rclpy

# [MEMORY REFRESH] A Node is one focused participant in a ROS 2 system. This node
# is the mission-level trajectory controller. PX4 still performs low-level
# stabilization and motor control.
from rclpy.node import Node

# QoS controls how ROS 2 transports messages. Sensor streams normally prioritize
# fresh information over retrying every old sample.
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

# Trigger is a simple service type with an empty request and a response containing
# success plus a message. It is suitable for commands such as start and abort.
from std_srvs.srv import Trigger

# PoseStamped stores one position together with a coordinate frame and timestamp.
from geometry_msgs.msg import PoseStamped

# Path stores a sequence of PoseStamped values for visualization in RViz.
from nav_msgs.msg import Path

# Marker lets the node draw a simple inspection target in RViz.
from visualization_msgs.msg import Marker

# PX4 message roles:
#   OffboardControlMode tells PX4 which external-control fields are active.
#   TrajectorySetpoint carries the desired position and yaw.
#   VehicleCommand requests mode changes, arming, and landing.
#   VehicleOdometry reports estimated position and velocity back to ROS 2.
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleOdometry

# Import the small mathematical recipes kept in trajectory.py.
# The leading dot means "import from this same Python package".
from .trajectory import smoothstep, orbit_point, inward_yaw, tracking_error


# [MEMORY REFRESH] A state machine is a flowchart implemented in code. At any
# moment the mission is in exactly one named phase. This prevents climb, orbit,
# and landing logic from running at the same time.
class State(Enum):

    # Semicolons separate several Python statements on one physical line.
    WAITING = auto(); WARMUP = auto(); CLIMB = auto(); APPROACH = auto()
    ORBIT = auto(); HOLD = auto(); LANDING = auto(); FINISHED = auto()


# OrbitController inherits all ROS 2 Node capabilities.
class OrbitController(Node):

    # The constructor runs once when this node object is created.
    def __init__(self):

        # Initialize the ROS 2 parent class and choose the node name. Discover it
        # while running with: ros2 node list
        super().__init__('orbit_controller')

        # These defaults are mission parameters rather than hard-coded hidden
        # constants. Their names include units such as _m, _s, and _hz to reduce
        # ambiguity for beginners and engineers.
        defaults = {
            'center_north_m': 0.0, 'center_east_m': 0.0, 'altitude_m': 4.0,
            'radius_m': 5.0, 'orbit_period_s': 24.0, 'number_of_laps': 1.25,
            'climb_time_s': 6.0, 'approach_time_s': 5.0, 'final_hold_s': 3.0,
            'setpoint_rate_hz': 20.0, 'face_center': True, 'auto_start': False,
            'auto_land': True, 'max_radius_m': 12.0, 'max_altitude_m': 10.0}

        # defaults.items() produces (name, value) pairs. For every pair, declare
        # a ROS 2 parameter. Inspect them later with:
        #   ros2 param list /orbit_controller
        for name, value in defaults.items(): self.declare_parameter(name, value)

        # A dictionary comprehension reads every declared parameter and stores it
        # in self.p. Read it as: "for each name, map name to its current value".
        self.p = {name: self.get_parameter(name).value for name in defaults}

        # Reject unsafe or nonsensical settings before sending any flight command.
        self._validate()

        # Configure the subscription used for fast PX4 sensor data. BEST_EFFORT
        # and depth 1 favor the newest estimate instead of building a stale queue.
        sensor_qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST, depth=1)

        # [MEMORY REFRESH] A publisher is a radio transmitter. The variable name
        # heartbeat_pub is local Python naming; the topic name is the shared ROS
        # address. PX4 defines /fmu/in/offboard_control_mode:
        #   /fmu = Flight Management Unit interface
        #   /in  = data entering PX4
        # Find it with: ros2 topic list | grep /fmu/in
        # Inspect it with: ros2 topic info /fmu/in/offboard_control_mode --verbose
        self.heartbeat_pub = self.create_publisher(OffboardControlMode, '/fmu/in/offboard_control_mode', 10)

        # This publisher sends the moving position/yaw reference to PX4. The topic
        # is PX4's standard ROS 2 interface name, not an arbitrary invention.
        self.setpoint_pub = self.create_publisher(TrajectorySetpoint, '/fmu/in/trajectory_setpoint', 10)

        # This publisher sends discrete commands such as arm, mode change, or land.
        self.command_pub = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', 10)

        # [MEMORY REFRESH] A subscriber is a radio receiver. /out means this data
        # leaves PX4. The _odom callback is called whenever odometry arrives.
        # Find and inspect it with:
        #   ros2 topic list | grep vehicle_odometry
        #   ros2 interface show px4_msgs/msg/VehicleOdometry
        self.odom_sub = self.create_subscription(VehicleOdometry, '/fmu/out/vehicle_odometry', self._odom, sensor_qos)

        # These /orbit topics are application-specific names chosen by this project.
        # The naming rule is: /project_namespace/clear_noun. They can be discovered
        # with: ros2 topic list | grep /orbit
        # desired_path is the planned reference shown in RViz.
        self.desired_path_pub = self.create_publisher(Path, '/orbit/desired_path', 10)

        # measured_path is the position actually estimated by PX4 and shown in RViz.
        self.measured_path_pub = self.create_publisher(Path, '/orbit/measured_path', 10)

        # inspection_target publishes a visible RViz marker at the orbit centre.
        self.target_pub = self.create_publisher(Marker, '/orbit/inspection_target', 10)

        # [MEMORY REFRESH] A service is like a doorbell: a client asks once and
        # receives one response. /orbit/start was chosen because it clearly means
        # "start the orbit application". Discover it with: ros2 service list
        # Inspect it with: ros2 service type /orbit/start
        self.start_srv = self.create_service(Trigger, '/orbit/start', self._start)

        # The abort service provides a separate clear request to land.
        self.abort_srv = self.create_service(Trigger, '/orbit/abort', self._abort)

        # Begin in a passive state. No flight sequence starts until requested.
        self.state = State.WAITING

        # Remember when the current state began so elapsed time can be measured.
        self.state_t0 = self._now()

        # Count heartbeat/setpoint cycles before requesting Offboard mode.
        self.warmup_ticks = 0

        # None means no odometry has arrived yet.
        self.measured = None

        # A tuple is an ordered group. This one stores desired NED position.
        self.desired = (0.0, 0.0, 0.0)

        # Create empty paths and label their RViz coordinate frame as map.
        # The semicolon keeps two statements on one source line.
        self.desired_path = Path(); self.desired_path.header.frame_id = 'map'
        self.measured_path = Path(); self.measured_path.header.frame_id = 'map'

        # [MEMORY REFRESH] A timer is a repeating alarm clock. If the rate is
        # 20 Hz, the period is 1/20 = 0.05 seconds. Every tick calls self._tick.
        self.timer = self.create_timer(1.0 / float(self.p['setpoint_rate_hz']), self._tick)

        # Print an operator instruction through the ROS 2 logging system.
        self.get_logger().info('Mission ready. Start: ros2 service call /orbit/start std_srvs/srv/Trigger {}')

    # Validate parameters before flight. Raising ValueError stops initialization
    # with a clear explanation rather than allowing a dangerous command.
    def _validate(self):
        if not 0.5 <= float(self.p['radius_m']) <= float(self.p['max_radius_m']): raise ValueError('radius_m outside safety limits')
        if not 0.5 <= float(self.p['altitude_m']) <= float(self.p['max_altitude_m']): raise ValueError('altitude_m outside safety limits')
        if float(self.p['orbit_period_s']) < 8.0: raise ValueError('orbit_period_s must be at least 8 s')
        if float(self.p['setpoint_rate_hz']) < 10.0: raise ValueError('setpoint_rate_hz must be at least 10 Hz')

    # ROS time is stored in nanoseconds. Dividing by 1e9 converts it to seconds.
    def _now(self): return self.get_clock().now().nanoseconds / 1e9

    # PX4 timestamps use microseconds here. Dividing nanoseconds by 1000 converts
    # ns to us, and int removes any fractional part.
    def _stamp_us(self): return int(self.get_clock().now().nanoseconds / 1000)

    # Time in current state = current time - time when state started.
    def _elapsed(self): return self._now() - self.state_t0

    # Change state and reset its stopwatch in one tuple-assignment statement.
    def _change(self, state):
        self.state, self.state_t0 = state, self._now()
        self.get_logger().info('STATE -> ' + state.name)

    # ROS 2 calls this service callback when a client rings /orbit/start.
    # request is unused because Trigger has no request data; response is filled in.
    def _start(self, request, response):
        del request

        # Permit start only from WAITING or after a previous mission FINISHED.
        if self.state not in (State.WAITING, State.FINISHED):
            response.success=False; response.message='Mission already active'; return response

        # Reset warmup, enter WARMUP, then report success to the service caller.
        self.warmup_ticks=0; self._change(State.WARMUP)
        response.success=True; response.message='Orbit inspection started'; return response

    # The abort callback requests landing and moves the software state accordingly.
    def _abort(self, request, response):
        del request; self._land(); self._change(State.LANDING)
        response.success=True; response.message='Landing requested'; return response

    # Every incoming odometry message updates measured position and RViz history.
    def _odom(self, msg):
        self.measured = tuple(float(v) for v in msg.position)
        self._append_path(self.measured_path, self.measured)
        self.measured_path_pub.publish(self.measured_path)

    # Publish the Offboard heartbeat. This tells PX4 that position is the active
    # external-control level and that the external controller is still alive.
    def _heartbeat(self):
        m=OffboardControlMode(); m.timestamp=self._stamp_us(); m.position=True

        # PX4 message versions may contain optional fields. hasattr asks whether
        # each field exists before setattr writes False, avoiding version errors.
        for field in ('velocity','acceleration','attitude','body_rate','thrust_and_torque','direct_actuator'):
            if hasattr(m, field): setattr(m, field, False)
        self.heartbeat_pub.publish(m)

    # Publish one desired PX4 NED position and yaw.
    def _setpoint(self, n, e, d, yaw):
        self.desired=(float(n),float(e),float(d))
        m=TrajectorySetpoint(); m.timestamp=self._stamp_us(); m.position=list(self.desired)

        # NaN means "this field is intentionally unspecified". Repeating a list
        # with *3 creates three NaN values, one for each spatial axis.
        m.velocity=[math.nan]*3; m.acceleration=[math.nan]*3; m.jerk=[math.nan]*3
        m.yaw=float(yaw); m.yawspeed=math.nan; self.setpoint_pub.publish(m)
        self._append_path(self.desired_path, self.desired); self.desired_path_pub.publish(self.desired_path)

    # Build and publish a generic PX4 VehicleCommand. p1 and p2 are command-
    # specific numeric parameters defined by the MAVLink/PX4 command interface.
    def _command(self, command, p1=0.0, p2=0.0):
        m=VehicleCommand(); m.timestamp=self._stamp_us(); m.command=int(command)
        m.param1=float(p1); m.param2=float(p2); m.target_system=1; m.target_component=1
        m.source_system=1; m.source_component=1; m.from_external=True; self.command_pub.publish(m)

    # Request Offboard mode, then arm. The numeric values 1 and 6 are parameters
    # expected by PX4's DO_SET_MODE command for this mode selection.
    def _offboard_and_arm(self):
        self._command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE,1.0,6.0)
        self._command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,1.0,0.0)

    # A one-line helper that asks PX4 to execute its normal landing command.
    def _land(self): self._command(VehicleCommand.VEHICLE_CMD_NAV_LAND)

    # Add one NED point to an RViz Path.
    def _append_path(self, path, ned):
        # RViz is ENU. For visualization only: ENU=(East, North, Up)=(y,x,-z).

        # PX4 command coordinates remain NED. Only the displayed copy is converted:
        # RViz x = East, RViz y = North, RViz z = Up = -Down.
        pose=PoseStamped(); pose.header.frame_id='map'; pose.header.stamp=self.get_clock().now().to_msg()
        pose.pose.position.x=ned[1]; pose.pose.position.y=ned[0]; pose.pose.position.z=-ned[2]
        path.header.stamp=pose.header.stamp; path.poses.append(pose)

        # Keep at most 2500 poses so memory usage does not grow forever. A negative
        # slice [-2500:] means "keep the last 2500 elements".
        if len(path.poses)>2500: path.poses=path.poses[-2500:]

    # Publish a simple orange cylinder at the inspection centre for RViz.
    def _publish_target(self):
        marker=Marker(); marker.header.frame_id='map'; marker.header.stamp=self.get_clock().now().to_msg()
        marker.ns='inspection'; marker.id=0; marker.type=Marker.CYLINDER; marker.action=Marker.ADD

        # Convert NED centre coordinates to RViz display order: East becomes x,
        # North becomes y.
        marker.pose.position.x=float(self.p['center_east_m']); marker.pose.position.y=float(self.p['center_north_m'])
        marker.pose.position.z=0.5; marker.scale.x=1.2; marker.scale.y=1.2; marker.scale.z=1.0
        marker.color.r=1.0; marker.color.g=0.25; marker.color.b=0.05; marker.color.a=0.9
        self.target_pub.publish(marker)

    # This callback is the mission engine. The timer calls it repeatedly.
    def _tick(self):
        self._publish_target()

        # WAITING and FINISHED are passive states, so return before flight outputs.
        if self.state in (State.WAITING,State.FINISHED): return

        # Every active tick refreshes the heartbeat and reads mission parameters.
        # first is the first orbit point: radius metres north of the centre and at
        # altitude h. In NED, altitude h is represented by Down = -h.
        self._heartbeat(); t=self._elapsed(); cx=float(self.p['center_north_m']); cy=float(self.p['center_east_m'])
        h=float(self.p['altitude_m']); r=float(self.p['radius_m']); first=(cx+r,cy,-h)

        # WARMUP streams valid setpoints before requesting Offboard mode. At 20 Hz,
        # reaching 20 ticks means approximately one second has passed.
        if self.state==State.WARMUP:
            self._setpoint(0.0,0.0,-0.5,0.0); self.warmup_ticks+=1
            if self.warmup_ticks>=int(float(self.p['setpoint_rate_hz'])):
                self._offboard_and_arm(); self._change(State.CLIMB)

        # CLIMB smoothly changes Down from 0 toward -h. u is normalized progress:
        # elapsed/climb_time. smoothstep clamps and gently shapes that progress.
        elif self.state==State.CLIMB:
            u=smoothstep(t/float(self.p['climb_time_s'])); self._setpoint(0.0,0.0,-h*u,0.0)
            if u>=1.0: self._change(State.APPROACH)

        # APPROACH interpolates from the origin toward the first orbit point.
        # Multiplying first coordinates by u moves gradually from 0 to 100 percent.
        elif self.state==State.APPROACH:
            u=smoothstep(t/float(self.p['approach_time_s'])); n=u*first[0]; e=u*first[1]
            self._setpoint(n,e,-h,inward_yaw(n,e,cx,cy))
            if u>=1.0: self._change(State.ORBIT)

        # ORBIT converts time into angle. One complete circle is 2*pi radians, so
        # angle = 2*pi*time/period. orbit_point converts angle into North/East.
        elif self.state==State.ORBIT:
            angle=2.0*math.pi*t/float(self.p['orbit_period_s']); n,e=orbit_point(cx,cy,r,angle)

            # This compact conditional chooses inward-facing yaw when face_center
            # is true; otherwise it chooses tangent yaw, angle + pi/2.
            yaw=inward_yaw(n,e,cx,cy) if bool(self.p['face_center']) else angle+math.pi/2.0
            self._setpoint(n,e,-h,yaw)

            # End orbit after period times number_of_laps seconds.
            if t>=float(self.p['orbit_period_s'])*float(self.p['number_of_laps']): self._change(State.HOLD)

        # HOLD keeps the final/first orbit point stable before landing.
        elif self.state==State.HOLD:

            # *first unpacks the tuple into three positional arguments n, e, d.
            self._setpoint(*first,inward_yaw(first[0],first[1],cx,cy))
            if t>=float(self.p['final_hold_s']):
                if bool(self.p['auto_land']): self._land(); self._change(State.LANDING)
                else: self._change(State.FINISHED)

        # After ten seconds in LANDING, the software marks the mission finished.
        elif self.state==State.LANDING and t>=10.0: self._change(State.FINISHED)

        # If odometry exists, calculate desired-to-measured distance. The modulo
        # expression is true during alternating half-second intervals, while the
        # logger's throttle ultimately limits this message to about once per second.
        if self.measured and int(t*2)%2==0:
            err=tracking_error(self.desired,self.measured)

            # :8s aligns the state in eight spaces; :.2f prints two decimal places.
            # !s explicitly converts the desired tuple to text.
            self.get_logger().info(f'{self.state.name:8s} desired={self.desired!s} tracking_error={err:.2f} m', throttle_duration_sec=1.0)


# Entry point called by the package's ROS 2 console script.
def main(args=None):

    # Initialize ROS 2 and construct the controller node.
    rclpy.init(args=args); node=OrbitController()

    # spin keeps the event loop alive so timers, subscriptions, and services work.
    try: rclpy.spin(node)

    # Ctrl+C ends the loop through KeyboardInterrupt.
    except KeyboardInterrupt: pass

    # Always release the node and shut down rclpy on exit.
    finally: node.destroy_node(); rclpy.shutdown()
