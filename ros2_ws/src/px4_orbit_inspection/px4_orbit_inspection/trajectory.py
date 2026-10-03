"""
=============================================================================
Project   : Quadcopter Autonomous Inspection (UM6P Internship)
File      : trajectory.py
Author    : Dr. Abdellah TNOURJI
Website   : https://www.abdellahtnourji.com/
Date      : [Date, 20, Aug 2026]

Description:
    Mathematical functions for trajectory generation.

License   : UM6P
=============================================================================

"""

# [MEMORY REFRESH] A module is one Python file that groups related tools.
# This module contains only mathematics. Keeping mathematics separate makes it
# easier to understand, reuse, and test without starting ROS 2 or Gazebo.

# Import Python's standard mathematics toolbox. We need pi, sine, cosine,
# atan2, and square root later in this file.
import math


# A function is a named reusable recipe. The value after the arrow, "float",
# documents that this function returns a decimal number.
def smoothstep(u: float) -> float:
    """Smoothly move from 0 to 1 with zero slope at both ends."""

    # First, clamp u to the interval [0, 1].
    #
    # Read the expression from the inside outward:
    #   min(1.0, u) prevents u from becoming larger than 1.
    #   max(0.0, ...) prevents the result from becoming smaller than 0.
    #
    # Physical intuition: u is mission progress. A value of 0 means "not
    # started" and 1 means "finished". Values outside that range make no sense.
    u = max(0.0, min(1.0, u))

    # This polynomial is called smoothstep:
    #
    #     s(u) = u^2 (3 - 2u)
    #
    # Unlike a sudden jump, it begins and ends gently. In the mission it shapes
    # climb and approach references so PX4 does not receive an abrupt command.
    # The * symbol means multiplication.
    return u * u * (3.0 - 2.0 * u)


# cx and cy are the circle-centre coordinates. radius is the distance from the
# centre, and angle tells us where we are around the circle in radians.
def orbit_point(cx: float, cy: float, radius: float, angle: float):
    """Return North and East coordinates on a horizontal circle."""

    # Circle memory aid:
    #
    #     horizontal coordinate = centre + radius * cos(angle)
    #     vertical coordinate   = centre + radius * sin(angle)
    #
    # Here those coordinates are PX4 North and East. Python returns both values
    # as one tuple: (north, east).
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


# This function computes the drone heading needed to look at the orbit centre.
# "yaw" means rotation around the vertical axis, like turning left or right.
def inward_yaw(north: float, east: float, cx: float, cy: float) -> float:
    """Return NED yaw that points from the drone toward the circle center."""

    # Subtract current position from target position to obtain the direction
    # vector from the drone to the centre.
    #
    # atan2(y, x) converts a 2-D direction into an angle while preserving the
    # correct quadrant. It is safer than atan(y/x), which loses quadrant
    # information and fails when x is zero.
    return math.atan2(cy - east, cx - north)


# desired and measured are expected to contain three coordinates each:
# (north, east, down). The result is the straight-line distance between them.
def tracking_error(desired, measured) -> float:
    """Return 3D Euclidean distance between two NED points."""

    # [MEMORY REFRESH] zip(desired, measured) pairs matching coordinates:
    # desired North with measured North, desired East with measured East, etc.
    #
    # The generator expression computes (desired - measured)^2 for each pair.
    # sum(...) adds the three squared errors. sqrt(...) converts that sum into
    # Euclidean distance, exactly like the 3-D Pythagorean theorem.
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(desired, measured)))
