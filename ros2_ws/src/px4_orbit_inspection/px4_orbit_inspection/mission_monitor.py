"""
=============================================================================
Project   : Quadcopter Autonomous Inspection (UM6P Internship)
File      : mission_monitor.py
Author    : Dr. Abdellah TNOURJI
Website   : https://www.abdellahtnourji.com/
Date      : [Date, 25, Aug 2026]

Description:
    Small terminal monitor. It makes the classroom demo easier to follow.

License   : UM6P
=============================================================================

"""

# Python mathematics is used to combine the three velocity components into one
# easy-to-read speed value.
import math

# rclpy is the official Python client library for ROS 2. It lets Python programs
# create nodes, publishers, subscribers, services, timers, and logs.
import rclpy

# [MEMORY REFRESH] A ROS 2 Node is like one specialist in a team. This specialist
# only watches the drone and reports understandable flight information.
from rclpy.node import Node

# QoS means Quality of Service. It describes communication behaviour, such as
# whether every message must arrive and how many old messages should be kept.
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

# These are PX4 message types. A message type is the agreed structure of data
# sent through a topic, similar to a labelled form with predefined fields.
from px4_msgs.msg import VehicleOdometry, VehicleStatus


# Object-oriented programming memory aid: a class is a blueprint. MissionMonitor
# inherits from Node, so every MissionMonitor object also has ROS 2 node tools.
class MissionMonitor(Node):

    # __init__ is the constructor. Python runs it once when the node is created.
    # "self" means "this particular MissionMonitor object".
    def __init__(self):

        # Initialize the parent Node class and register the ROS 2 node name.
        # You can discover this name later with: ros2 node list
        super().__init__('mission_monitor')

        # PX4 sensor topics are fast live streams. BEST_EFFORT means a late or
        # lost sample does not block newer samples. KEEP_LAST with depth=1 means
        # "keep only the newest sample", like replacing an old dashboard value.
        # TRANSIENT_LOCAL allows compatible late subscribers to receive retained
        # data when the publisher supports that behaviour.
        qos=QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST, depth=1)

        # None means "no value has arrived yet". These fields will hold the most
        # recent data received from PX4.
        # The semicolon separates three Python statements written on one line.
        self.position=None; self.velocity=None; self.status=None

        # [MEMORY REFRESH] A subscriber is like a radio receiver. It listens to a
        # topic and runs a callback whenever a matching message arrives.
        #
        # Topic: /fmu/out/vehicle_odometry
        #   /fmu identifies PX4's Flight Management Unit interface.
        #   /out means data travels out of PX4 toward ROS 2.
        #   vehicle_odometry contains estimated position and velocity.
        #
        # These are PX4-defined interface names, not arbitrary names chosen here.
        # Find them with:
        #   ros2 topic list | grep /fmu
        # Inspect the type with:
        #   ros2 topic info /fmu/out/vehicle_odometry --verbose
        #   ros2 interface show px4_msgs/msg/VehicleOdometry
        self.create_subscription(VehicleOdometry,'/fmu/out/vehicle_odometry',self._odom,qos)

        # This second PX4 output reports arming and navigation states. The _status
        # callback runs whenever a VehicleStatus message arrives.
        self.create_subscription(VehicleStatus,'/fmu/out/vehicle_status',self._status,qos)

        # [MEMORY REFRESH] A timer is an alarm clock inside a node. Every 1.0
        # second it calls self._print, producing a readable dashboard without
        # flooding the terminal at the much faster sensor rate.
        self.create_timer(1.0,self._print)

    # A callback is a function that ROS 2 calls because an event happened.
    # Here the event is arrival of a new odometry message named m.
    # tuple(...) stores a fixed snapshot of the message arrays.
    def _odom(self,m): self.position=tuple(m.position); self.velocity=tuple(m.velocity)

    # This callback remembers the newest vehicle-status message.
    def _status(self,m): self.status=m

    # The timer calls this method once each second.
    def _print(self):

        # If position is still None or empty, no useful odometry has arrived.
        # Log a helpful message and return immediately from the function.
        if not self.position: self.get_logger().info('Waiting for PX4 odometry...'); return

        # Total 3-D speed follows the Pythagorean theorem:
        # sqrt(vx^2 + vy^2 + vz^2). The generator loop visits each component v.
        speed=math.sqrt(sum(float(v)**2 for v in self.velocity))

        # PX4 uses NED coordinates: North, East, Down. Positive z means downward,
        # so physical altitude above the origin is the negative of NED z.
        altitude=-float(self.position[2])

        # getattr(object, field, fallback) safely reads a field. If status exists,
        # read nav_state; otherwise show '?'. The final expression is a compact
        # conditional: "value_if_true if condition else value_if_false".
        nav=getattr(self.status,'nav_state','?') if self.status else '?'
        arm=getattr(self.status,'arming_state','?') if self.status else '?'

        # An f-string inserts live values inside braces. The format 5.2f means a
        # width of five characters with two digits after the decimal point.
        self.get_logger().info(f'LIVE | altitude={altitude:5.2f} m | speed={speed:4.2f} m/s | nav={nav} | arm={arm}')


# main is the program entry point called by the ROS 2 console executable.
def main(args=None):

    # Start ROS 2, then create one MissionMonitor object. The semicolon separates
    # two executable statements without changing their order.
    rclpy.init(args=args); n=MissionMonitor()

    # spin keeps the node alive so ROS 2 can execute callbacks and timers.
    try: rclpy.spin(n)

    # Ctrl+C raises KeyboardInterrupt. "pass" means intentionally do nothing.
    except KeyboardInterrupt: pass

    # finally runs during normal exit or interruption. First destroy the node,
    # then shut down the ROS 2 client library.
    finally: n.destroy_node(); rclpy.shutdown()
