#!/usr/bin/env python3
"""
mine_sar_mission.py - PHOENIX search-and-rescue mission for the phoenix_mine world.

Flight plan (PX4 offboard, position setpoints):
  1. take off from the home pad and climb to the cruise altitude
  2. fly to the open pit and descend to 1.8 m above the pit floor
  3. go through the box-cut trench and Portal A into the underground panel
  4. SEARCH the room-and-pillar panel along a planned route (around the roof-fall)
  5. when the victim is detected -> mark it, publish its position, hover
  6. return along the same path (breadcrumbs) and land on the home pad

Victim detection
  * simulated thermal sensor (default): the victim is "seen" when it is within
    `thermal_range` metres AND in direct line of sight (pillars / rubble block it).
    This stands in for the thermal camera of the real PHOENIX drone.
  * YOLO (optional): any message on `detections_topic` that contains "person"
    while the drone is underground also counts as a detection.

ROS 2 interface
  services : /sar/start  /sar/abort (return home)  /sar/land (land where it is)
  topics   : /sar/status (std_msgs/String)  /sar/victim (geometry_msgs/PointStamped, PX4 NED)

Run:  python3 -u mine_sar_mission.py      (ROS 2 + your ros2_ws sourced, PX4 running)
Frames: Gazebo world is ENU (x east, y north, z up); PX4 local frame is NED.
"""
import math
from dataclasses import dataclass

# =============================================================================
#  Mission geometry (taken from phoenix_mine.sdf, Gazebo ENU coordinates)
# =============================================================================
FLOOR_Z = -12.0                       # pit floor / underground floor
VICTIM_ENU = (16.0, 20.0, FLOOR_Z)    # victim lying in the NW of the panel

# obstacles that block the line of sight inside the panel: (x0, x1, y0, y1)
PILLARS = [(x0, x1, y0, y1)
           for x0, x1 in [(18, 24), (28, 34), (38, 44)]
           for y0, y1 in [(-18, -12), (-8, -2), (2, 8), (12, 18)]]
RUBBLE = [(23.9, 28.1, 12.3, 17.6)]
PANEL_WALLS = [(10, 14, -30, 30), (14, 48, 22, 30), (14, 48, -30, -22),
               (48, 50, -30, -2), (48, 50, 2, 30)]
BLOCKERS = PILLARS + RUBBLE + PANEL_WALLS


def enu_to_ned(x_e, y_n, z_u):
    return (y_n, x_e, -z_u)


def ned_to_enu(n, e, d):
    return (e, n, -d)


@dataclass
class Waypoint:
    name: str
    enu: tuple          # (x east, y north, z up) in Gazebo
    speed: float        # m/s along the leg that ends here
    phase: str          # transit | descent | entry | search
    accept: float       # acceptance radius (m)


def build_route(cruise_alt=15.0, tunnel_z=FLOOR_Z + 1.8, v_surf=4.0, v_tun=1.2):
    """Outbound route. The search legs sweep the panel and go around the roof-fall."""
    T = tunnel_z
    R = [Waypoint("climb",            (0, 0, cruise_alt),  2.0,   "transit", 1.0),
         Waypoint("above_pit",        (80, 0, cruise_alt), v_surf, "transit", 1.5),
         Waypoint("pit_floor",        (80, 0, T),          1.5,   "descent", 0.6),
         Waypoint("box_cut",          (58, 0, T),          2.0,   "entry",   0.6),
         Waypoint("portal_A",         (51, 0, T),          0.8,   "entry",   0.4),
         Waypoint("panel_entry",      (46, 0, T),          0.8,   "search",  0.4)]
    sweep = [("main_drift_x36",     36,   0), ("corridor36_south", 36, -20),
             ("south_room_west",    16, -20), ("west_corridor_s",  16, -10),
             ("room_m10_east",      26, -10), ("corridor26_mid",   26,   0),
             ("corridor26_north",   26,  10), ("room10_east",      36,  10),
             ("corridor36_north",   36,  20), ("north_room_west",  16,  20)]
    R += [Waypoint(n, (x, y, T), v_tun, "search", 0.5) for n, x, y in sweep]
    return R


# =============================================================================
#  Simulated thermal sensor (line of sight + range)
# =============================================================================
def _seg_hits_rect(p, q, r, pad=0.0):
    """True if segment p->q (2D) crosses rectangle r=(x0,x1,y0,y1). Liang-Barsky."""
    x0, x1, y0, y1 = r[0] - pad, r[1] + pad, r[2] - pad, r[3] + pad
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pk, qk in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if abs(pk) < 1e-12:
            if qk < 0:
                return False
        else:
            t = qk / pk
            if pk < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


class ThermalSensorSim:
    def __init__(self, rng=8.0, target=VICTIM_ENU, blockers=BLOCKERS):
        self.rng, self.target, self.blockers = rng, target, blockers

    def sees_target(self, drone_enu):
        dx, dy = self.target[0] - drone_enu[0], self.target[1] - drone_enu[1]
        dz = self.target[2] - drone_enu[2]
        if math.sqrt(dx * dx + dy * dy + dz * dz) > self.rng:
            return False
        p, q = drone_enu[:2], self.target[:2]
        return not any(_seg_hits_rect(p, q, b) for b in self.blockers)


# =============================================================================
#  Carrot follower: a setpoint that slides along the path at the leg speed
# =============================================================================
class CarrotFollower:
    def __init__(self, start_ned, lead=2.0):
        self.sp = list(start_ned)
        self.lead = lead
        self.yaw = 0.0

    def step(self, vehicle_ned, goal_ned, speed, dt):
        """Advance the carrot toward goal; return True when the carrot sits on the goal."""
        lag = math.dist(vehicle_ned, self.sp)
        d = [g - s for g, s in zip(goal_ned, self.sp)]
        dist = math.sqrt(sum(c * c for c in d))
        if dist < 1e-3:
            return True
        if lag < self.lead:                       # do not run away from the drone
            step = min(dist, speed * dt)
            self.sp = [s + c / dist * step for s, c in zip(self.sp, d)]
        if math.hypot(d[0], d[1]) > 0.3:          # face the direction of travel
            self.yaw = math.atan2(d[1], d[0])     # NED yaw: 0 = north, +pi/2 = east
        return dist <= speed * dt


# =============================================================================
#  Mission state machine (pure Python - no ROS inside, easy to test)
# =============================================================================
class SarMission:
    IDLE, PREFLIGHT, OUTBOUND, MARK, HOLD, RETURN, LANDING, DONE = (
        "IDLE", "PREFLIGHT", "OUTBOUND", "MARK_VICTIM", "HOLD_OVER_VICTIM",
        "RETURN", "LANDING", "DONE")

    def __init__(self, route, sensor, hover_time=10.0, on_found="return",
                 min_battery=0.25, tunnel_return_speed=1.5, surf_return_speed=4.0, log=print):
        self.route, self.sensor = route, sensor
        self.hover_time, self.on_found, self.min_battery = hover_time, on_found, min_battery
        self.v_ret_tun, self.v_ret_surf = tunnel_return_speed, surf_return_speed
        self.log = log
        self.state = self.IDLE
        self.idx = 0
        self.carrot = None
        self.visited = []                 # breadcrumbs (NED) for the way back
        self.return_path = []
        self.victim_ned = None
        self.detect_count = 0
        self.yolo_hits = []
        self.t_state = 0.0
        self.t = 0.0
        self.preflight_ticks = 0
        self.commands = []                # filled each tick: "offboard", "arm", "land"
        self.events = []                  # (time, text) for /sar/status

    # ----------------------------------------------------------------- helpers
    def _set(self, state, why=""):
        self.state, self.t_state = state, self.t
        self._event(f"{state}" + (f" - {why}" if why else ""))

    def _event(self, txt):
        self.events.append((self.t, txt))
        self.log(f"[SAR t={self.t:6.1f}s] {txt}")

    @property
    def phase(self):
        if self.state == self.OUTBOUND and self.idx < len(self.route):
            return self.route[self.idx].phase
        return self.state.lower()

    def start(self, vehicle_ned):
        if self.state not in (self.IDLE, self.DONE):
            return False, f"mission already running ({self.state})"
        self.__init__(self.route, self.sensor, self.hover_time, self.on_found,
                      self.min_battery, self.v_ret_tun, self.v_ret_surf, self.log)
        self.carrot = CarrotFollower(vehicle_ned)
        self.visited = [(tuple(vehicle_ned), "start")]
        self._set(self.PREFLIGHT, "streaming setpoints, then OFFBOARD + ARM")
        return True, "SAR mission started"

    def abort(self, why="operator abort"):
        if self.state in (self.OUTBOUND, self.MARK, self.HOLD):
            self._begin_return(why)
            return True, "returning home along the explored path"
        return False, f"nothing to abort ({self.state})"

    def land_now(self):
        if self.state in (self.IDLE, self.DONE):
            return False, "not flying"
        self.commands.append("land")
        self._set(self.LANDING, "operator asked to land here")
        return True, "landing at current position"

    def yolo_person(self):
        if self.phase == "search":
            self.yolo_hits = [t for t in self.yolo_hits if self.t - t < 3.0] + [self.t]

    def _begin_return(self, why):
        """Plan the way home: shortest line-of-sight path over the EXPLORED underground
        waypoints back to the panel entry, then the entry/transit legs in reverse."""
        pts = self.visited                                   # [(ned, tag), ...] in flight order
        search = [i for i, (_, tag) in enumerate(pts) if tag == "search"]
        path = []
        if search:
            nodes = [pts[i][0] for i in search]
            path += self._shortest_explored(nodes, start=len(nodes) - 1, goal=0)
            before = [p for p, tag in pts[:search[0]] if tag != "start"]
        else:
            before = [p for p, tag in pts if tag != "start"]
        path += list(reversed(before))
        path.append((0.0, 0.0, -2.0))                       # low over the home pad, then LAND
        self.return_path = [p for i, p in enumerate(path) if i == 0 or math.dist(p, path[i - 1]) > 0.2]
        self._set(self.RETURN, f"{why} ({len(self.return_path)} legs home)")

    @staticmethod
    def _shortest_explored(nodes, start, goal, pad=0.7):
        """Dijkstra on explored waypoints; an edge exists if the straight leg is clear."""
        enu = [ned_to_enu(*n)[:2] for n in nodes]
        n = len(nodes)
        def clear(i, j):
            return not any(_seg_hits_rect(enu[i], enu[j], b, pad) for b in BLOCKERS)
        dist, prev, todo = [math.inf] * n, [None] * n, set(range(n))
        dist[start] = 0.0
        while todo:
            u = min(todo, key=lambda k: dist[k])
            todo.discard(u)
            if u == goal or dist[u] == math.inf:
                break
            for v in todo:
                if clear(u, v):
                    alt = dist[u] + math.dist(enu[u], enu[v])
                    if alt < dist[v]:
                        dist[v], prev[v] = alt, u
        if dist[goal] == math.inf:                          # fall back: retrace everything
            return list(reversed(nodes))
        out, k = [], goal
        while k is not None:
            out.append(nodes[k])
            k = prev[k]
        return list(reversed(out))

    @staticmethod
    def _on_surface(ned):
        return -ned[2] > -1.0          # above the plateau level

    # ----------------------------------------------------------------- main tick
    def tick(self, dt, vehicle_ned, armed, offboard, battery=-1.0):
        """Advance the mission. Returns (setpoint_ned, yaw) or None when not commanding."""
        self.t += dt
        self.commands = []
        if self.state in (self.IDLE, self.DONE):
            return None
        if self.state == self.LANDING:
            if not armed and self.t - self.t_state > 2.0:
                self._set(self.DONE, "landed and disarmed")
            return None
        cf = self.carrot

        if self.state == self.PREFLIGHT:
            self.preflight_ticks += 1
            if self.preflight_ticks == 20:             # ~1 s of setpoints first (PX4 rule)
                self.commands += ["offboard", "arm"]
            if self.preflight_ticks > 20 and self.preflight_ticks % 40 == 0 and not (armed and offboard):
                self.commands += ["offboard", "arm"]   # retry every 2 s
            if self.t - self.t_state > 25.0 and not (armed and offboard):
                self._set(self.DONE, "PX4 did not accept OFFBOARD/ARM within 25 s (check the px4 tab)")
                return None
            if armed and offboard:
                self.idx = 0
                self._set(self.OUTBOUND, f"armed + offboard, heading for '{self.route[0].name}'")
            return tuple(cf.sp), cf.yaw

        # operator / failsafe took control -> stop commanding
        if not offboard and self.t - self.t_state > 1.0 and self.state != self.LANDING:
            self._set(self.DONE, "left OFFBOARD (failsafe or pilot took over) - mission stopped")
            return None

        if (0.0 <= battery < self.min_battery and self.state in (self.OUTBOUND, self.HOLD)):
            self._begin_return(f"low battery ({battery*100:.0f}%) - energy-aware return")

        if self.state == self.OUTBOUND:
            wp = self.route[self.idx]
            goal = enu_to_ned(*wp.enu)
            at_goal = cf.step(vehicle_ned, goal, wp.speed, dt)
            if at_goal and math.dist(vehicle_ned, goal) < wp.accept:
                self.visited.append((goal, wp.phase))
                self._event(f"reached '{wp.name}'")
                self.idx += 1
                if self.idx >= len(self.route):
                    self._begin_return("search route finished - victim NOT found")
                    return tuple(cf.sp), cf.yaw
            # --- detection (only while searching underground)
            if wp.phase == "search" and self.victim_ned is None:
                seen = self.sensor.sees_target(ned_to_enu(*vehicle_ned))
                self.detect_count = self.detect_count + 1 if seen else 0
                yolo = len(self.yolo_hits) >= 3
                if self.detect_count >= 3 or yolo:
                    src = "YOLO person" if yolo and self.detect_count < 3 else "thermal (310 K)"
                    tgt = self.sensor.target if src.startswith("thermal") else \
                        (*ned_to_enu(*vehicle_ned)[:2], FLOOR_Z)
                    self.victim_ned = enu_to_ned(*tgt)
                    self.visited.append((tuple(vehicle_ned), "search"))
                    d = math.dist(ned_to_enu(*vehicle_ned), tgt)
                    self._event(f"VICTIM FOUND by {src} sensor at Gazebo ({tgt[0]:.1f}, {tgt[1]:.1f}) "
                                f"/ PX4 NED ({self.victim_ned[0]:.1f}, {self.victim_ned[1]:.1f}), "
                                f"{d:.1f} m away")
                    self._set(self.MARK, "flying over the victim to mark it")
            return tuple(cf.sp), cf.yaw

        if self.state == self.MARK:
            if self.on_found == "land_now":
                if cf.step(vehicle_ned, self.land_spot, 0.5, dt) and math.dist(vehicle_ned, self.land_spot) < 0.4:
                    self.commands.append("land")
                    self._set(self.LANDING, "landing 2 m from the victim (on_found=land)")
                    return None
                return tuple(cf.sp), cf.yaw
            over = (self.victim_ned[0], self.victim_ned[1], -self.route[-1].enu[2])
            if cf.step(vehicle_ned, over, 0.6, dt) and math.dist(vehicle_ned, over) < 0.5:
                self.visited.append((over, "search"))
                self._set(self.HOLD, f"hovering over the victim for {self.hover_time:.0f} s "
                                     f"(position sent to the ground team)")
            return tuple(cf.sp), cf.yaw

        if self.state == self.HOLD:
            cf.step(vehicle_ned, tuple(cf.sp), 0.1, dt)
            if self.on_found == "hover" or self.t - self.t_state < self.hover_time:
                return tuple(cf.sp), cf.yaw            # "hover" waits for /sar/abort or /sar/land
            if self.on_found == "land":
                # land 2 m from the victim, on the side we came from (never on top of it)
                came = self.visited[-2][0] if len(self.visited) > 1 else tuple(cf.sp)
                dn, de = came[0] - self.victim_ned[0], came[1] - self.victim_ned[1]
                k = 2.0 / max(math.hypot(dn, de), 1e-6)
                self.land_spot = (self.victim_ned[0] + dn * k, self.victim_ned[1] + de * k, cf.sp[2])
                self.on_found = "land_now"
                self._set(self.MARK, "moving 2 m away from the victim to land")
            else:
                self._begin_return("victim marked - returning home")
            return tuple(cf.sp), cf.yaw

        if self.state == self.RETURN:
            if not self.return_path:
                self.commands.append("land")
                self._set(self.LANDING, "over the home pad - LAND")
                return None
            goal = self.return_path[0]
            spd = self.v_ret_surf if (self._on_surface(goal) and self._on_surface(cf.sp)) else self.v_ret_tun
            if goal[2] > cf.sp[2] + 0.5 or goal[2] < cf.sp[2] - 0.5:   # vertical legs a bit slower
                spd = min(spd, 2.0)
            if cf.step(vehicle_ned, goal, spd, dt) and math.dist(vehicle_ned, goal) < 0.8:
                self.return_path.pop(0)
            return tuple(cf.sp), cf.yaw
        return None



# =============================================================================
#  Alerts: Gazebo markers, pop-up window, tmux status bar, camera snapshot
# =============================================================================
def marker_req(mid, mtype, xyz, scale, rgba, points=None, ns="phoenix_sar"):
    """Text-format gz.msgs.Marker request for:  gz service -s /marker ..."""
    r, g, b, a = rgba
    col = f"{{r: {r}, g: {g}, b: {b}, a: {a}}}"
    em = f"{{r: {r*0.8:.2f}, g: {g*0.8:.2f}, b: {b*0.8:.2f}, a: 1}}"
    req = (f'action: ADD_MODIFY, ns: "{ns}", id: {mid}, type: {mtype}, visibility: GUI, '
           f'pose: {{position: {{x: {xyz[0]:.2f}, y: {xyz[1]:.2f}, z: {xyz[2]:.2f}}}}}, '
           f'scale: {{x: {scale[0]}, y: {scale[1]}, z: {scale[2]}}}, '
           f'material: {{ambient: {col}, diffuse: {col}, emissive: {em}}}')
    for px, py, pz in (points or []):
        req += f", point: {{x: {px:.2f}, y: {py:.2f}, z: {pz:.2f}}}"
    return req


def victim_marker_reqs(victim_enu, beacon_top=25.0):
    x, y, z = victim_enu
    h = beacon_top - z
    return [marker_req(1, "SPHERE", (x, y, z + 0.6), (1.2, 1.2, 1.2), (1.0, 0.05, 0.05, 1)),
            marker_req(2, "CYLINDER", (x, y, z + h / 2), (0.5, 0.5, h), (1.0, 0.1, 0.1, 1)),
            marker_req(3, "CYLINDER", (x, y, 0.08), (6.0, 6.0, 0.1), (1.0, 0.15, 0.0, 1))]


POPUP_SCRIPT = r"""
import sys, json, tkinter as tk
d = json.loads(sys.argv[1])
RED, DARK = "#c0161b", "#6e0b0e"
root = tk.Tk()
root.title("PHOENIX ALERT")
root.attributes("-topmost", True)
root.geometry("+60+60")
root.configure(bg=RED)
box = tk.Frame(root, bg=RED, padx=30, pady=22)
box.pack()
tk.Label(box, text="⚠  VICTIM DETECTED", font=("DejaVu Sans", 30, "bold"), fg="white", bg=RED).pack(anchor="w")
tk.Label(box, text="PHOENIX search & rescue - underground panel", font=("DejaVu Sans", 13), fg="#ffd7d7", bg=RED).pack(anchor="w", pady=(0, 14))
info = tk.Frame(box, bg="white", padx=18, pady=14)
info.pack(fill="x")
for k, v in d["rows"]:
    row = tk.Frame(info, bg="white"); row.pack(fill="x", pady=2)
    tk.Label(row, text=k, width=17, anchor="w", font=("DejaVu Sans", 12, "bold"), bg="white", fg="#333").pack(side="left")
    tk.Label(row, text=v, anchor="w", font=("DejaVu Sans Mono", 12), bg="white", fg="#111").pack(side="left")
tk.Label(box, text=d["action"], font=("DejaVu Sans", 12, "italic"), fg="white", bg=RED, wraplength=700, justify="left").pack(anchor="w", pady=(12, 10))
tk.Button(box, text="ACKNOWLEDGE", font=("DejaVu Sans", 13, "bold"), fg=RED, bg="white", activeforeground=DARK,
          relief="flat", padx=18, pady=6, command=root.destroy).pack(anchor="e")
state = {"on": True, "n": 0}
def flash():
    state["on"] = not state["on"]; state["n"] += 1
    c = RED if state["on"] else DARK
    for w in [root, box] + [x for x in box.winfo_children() if isinstance(x, tk.Label)]:
        w.configure(bg=c)
    if state["n"] < 6 and state["n"] % 2: root.bell()
    root.after(500, flash)
root.after(500, flash)
root.bell()
if len(sys.argv) > 2:          # test mode: save a screenshot then quit
    root.after(int(sys.argv[2]), root.destroy)
root.mainloop()
"""


def image_msg_to_bgr(msg):
    """sensor_msgs/Image -> numpy BGR array (or None)."""
    import numpy as np
    enc = msg.encoding.lower()
    ch = {"rgb8": 3, "bgr8": 3, "rgba8": 4, "bgra8": 4, "mono8": 1}.get(enc)
    if ch is None:
        return None
    a = np.frombuffer(bytes(msg.data), dtype=np.uint8).reshape(msg.height, msg.step)
    a = a[:, :msg.width * ch].reshape(msg.height, msg.width, ch)
    if enc in ("rgb8", "rgba8"):
        a = a[..., [2, 1, 0]]
    elif enc == "bgra8":
        a = a[..., :3]
    elif ch == 1:
        a = np.repeat(a, 3, axis=2)
    return np.ascontiguousarray(a)

# =============================================================================
#  ROS 2 node (PX4 offboard over Micro XRCE-DDS)
# =============================================================================
def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import (QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy,
                           qos_profile_sensor_data)
    from std_srvs.srv import Trigger
    from std_msgs.msg import String
    from geometry_msgs.msg import PointStamped
    from sensor_msgs.msg import Image
    import os, json, shutil, subprocess, sys, time
    from px4_msgs.msg import (OffboardControlMode, TrajectorySetpoint, VehicleCommand,
                              VehicleOdometry, VehicleStatus, BatteryStatus)

    class MineSarNode(Node):
        def __init__(self):
            super().__init__("mine_sar_mission")
            p = self.declare_parameter
            self.dt = 0.05                                             # 20 Hz
            cruise = p("cruise_alt", 15.0).value
            height = p("tunnel_height", 1.8).value
            v_surf = p("speed_surface", 4.0).value
            v_tun = p("speed_tunnel", 1.2).value
            rng = p("thermal_range", 8.0).value
            hover = p("hover_time", 10.0).value
            on_found = p("on_found", "return").value                  # return | hover | land
            min_bat = p("min_battery", 0.25).value
            self.use_yolo = p("use_yolo", True).value
            self.det_topic = p("detections_topic", "/inspection/detections").value
            auto = p("auto_start", False).value
            self.popup = p("alert_popup", True).value
            self.gz_markers = p("gazebo_markers", True).value and shutil.which("gz") is not None
            self.snap_dir = p("snapshot_dir", os.path.join(os.getcwd(), "data", "sar")).value

            route = build_route(cruise, FLOOR_Z + height, v_surf, v_tun)
            self.mission = SarMission(route, ThermalSensorSim(rng), hover, on_found, min_bat,
                                      log=lambda s: self.get_logger().info(s))

            qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             history=HistoryPolicy.KEEP_LAST, depth=1)
            self.pub_mode = self.create_publisher(OffboardControlMode, "/fmu/in/offboard_control_mode", qos)
            self.pub_sp = self.create_publisher(TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos)
            self.pub_cmd = self.create_publisher(VehicleCommand, "/fmu/in/vehicle_command", qos)
            self.pub_status = self.create_publisher(String, "/sar/status", 10)
            self.pub_victim = self.create_publisher(PointStamped, "/sar/victim", 10)
            latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
            self.pub_alert = self.create_publisher(String, "/sar/alert", latched)
            self.create_subscription(Image, "/camera/image_raw", self.on_image, qos_profile_sensor_data)
            self.create_subscription(VehicleOdometry, "/fmu/out/vehicle_odometry", self.on_odom, qos)
            self.create_subscription(VehicleStatus, "/fmu/out/vehicle_status", self.on_status, qos)
            self.create_subscription(BatteryStatus, "/fmu/out/battery_status", self.on_battery, qos)
            self.create_service(Trigger, "/sar/start", self.srv_start)
            self.create_service(Trigger, "/sar/abort", self.srv_abort)
            self.create_service(Trigger, "/sar/land", self.srv_land)

            self.pos = None
            self.armed = False
            self.offboard = False
            self.battery = -1.0
            self.det_sub = None
            self.n_events = 0
            self.victim_sent = False
            self.auto = auto
            self.qos_det = qos_profile_sensor_data
            self.last_img = None
            self.alerted = False
            self.finished = False
            self.trail = []
            self.gz_proc = None
            self.create_timer(self.dt, self.loop)
            self.create_timer(1.0, self.slow_loop)
            self.get_logger().info("Mine SAR mission ready. Start: ros2 service call /sar/start "
                                   "std_srvs/srv/Trigger {}")

        # ---------------- PX4 inputs
        def on_odom(self, m):
            if m.pose_frame == 1 and not math.isnan(m.position[0]):
                self.pos = (float(m.position[0]), float(m.position[1]), float(m.position[2]))

        def on_status(self, m):
            self.armed = m.arming_state == 2
            self.offboard = m.nav_state == 14

        def on_battery(self, m):
            self.battery = float(m.remaining)

        def on_image(self, msg):
            self.last_img = msg

        def on_detection(self, msg):
            if "person" in str(msg).lower():
                self.mission.yolo_person()

        # ---------------- services
        def _answer(self, res, ok_msg):
            res.success, res.message = ok_msg
            return res

        def srv_start(self, req, res):
            if self.pos is None:
                return self._answer(res, (False, "no odometry from PX4 yet - is the XRCE agent running?"))
            return self._answer(res, self.mission.start(self.pos))

        def srv_abort(self, req, res):
            return self._answer(res, self.mission.abort())

        def srv_land(self, req, res):
            ok = self.mission.land_now()
            self.flush_commands()
            return self._answer(res, ok)

        # ---------------- outputs
        def now_us(self):
            return int(self.get_clock().now().nanoseconds / 1000)

        def command(self, cmd, p1=0.0, p2=0.0):
            m = VehicleCommand()
            m.timestamp = self.now_us()
            m.command = cmd
            m.param1, m.param2 = float(p1), float(p2)
            m.target_system, m.target_component = 1, 1
            m.source_system, m.source_component = 1, 1
            m.from_external = True
            self.pub_cmd.publish(m)

        def flush_commands(self):
            for c in self.mission.commands:
                if c == "offboard":
                    self.command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
                elif c == "arm":
                    self.command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
                elif c == "land":
                    self.command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
            self.mission.commands = []

        def loop(self):
            if self.pos is None:
                return
            if self.auto and self.mission.state == SarMission.IDLE:
                self.auto = False
                self.mission.start(self.pos)
            out = self.mission.tick(self.dt, self.pos, self.armed, self.offboard, self.battery)
            self.flush_commands()
            if out is None:
                return
            sp, yaw = out
            mode = OffboardControlMode()
            mode.timestamp = self.now_us()
            mode.position = True
            mode.velocity = mode.acceleration = mode.attitude = mode.body_rate = False
            self.pub_mode.publish(mode)
            t = TrajectorySetpoint()
            t.timestamp = mode.timestamp
            t.position = [float(sp[0]), float(sp[1]), float(sp[2])]
            nan = float("nan")
            t.velocity = [nan, nan, nan]
            t.acceleration = [nan, nan, nan]
            t.yaw = float(yaw)
            t.yawspeed = nan
            self.pub_sp.publish(t)

        # ---------------- alerts
        def _gz(self, req):
            """Send one marker to the Gazebo window (never blocks the control loop)."""
            if not self.gz_markers:
                return
            try:
                subprocess.Popen(["gz", "service", "-s", "/marker", "--reqtype", "gz.msgs.Marker",
                                  "--reptype", "gz.msgs.Empty", "--timeout", "2000", "--req", req],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as ex:
                self.get_logger().warn(f"gazebo marker failed: {ex}")

        def _tmux(self, color, text):
            if os.environ.get("TMUX") and shutil.which("tmux"):
                subprocess.run(["tmux", "set", "status-style", f"bg={color},fg=white"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["tmux", "display-message", "-d", "15000", text],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def _snapshot(self, label):
            if self.last_img is None:
                return "no camera image received"
            try:
                img = image_msg_to_bgr(self.last_img)
                if img is None:
                    return f"camera encoding {self.last_img.encoding} not supported"
                os.makedirs(self.snap_dir, exist_ok=True)
                path = os.path.join(self.snap_dir, time.strftime("victim_%Y%m%d_%H%M%S.png"))
                try:
                    import cv2
                    cv2.rectangle(img, (0, 0), (img.shape[1], 46), (20, 20, 190), -1)
                    cv2.putText(img, label, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
                    cv2.imwrite(path, img)
                except ImportError:
                    from PIL import Image as PILImage
                    PILImage.fromarray(img[..., ::-1]).save(path)
                return path
            except Exception as ex:
                return f"snapshot failed: {ex}"

        def raise_alert(self):
            ms = self.mission
            found = next((t for _, t in reversed(ms.events) if "VICTIM FOUND" in t), "VICTIM FOUND")
            v_enu = ned_to_enu(*ms.victim_ned)
            d_enu = ned_to_enu(*self.pos)
            dist = math.dist(v_enu, d_enu)
            src = "YOLO (camera)" if "YOLO" in found else "thermal sensor (310 K)"
            snap = self._snapshot(f"PHOENIX: VICTIM DETECTED  t={ms.t:.0f}s  ({v_enu[0]:.1f}, {v_enu[1]:.1f})")
            action = {"return": f"Drone is marking the position, hovering {ms.hover_time:.0f} s, then returning home.",
                      "hover": "Drone is holding over the victim. Type  sar_abort  to bring it home.",
                      "land": "Drone will land 2 m from the victim."}.get(ms.on_found, "")
            rows = [("Position (Gazebo)", f"x={v_enu[0]:6.1f}  y={v_enu[1]:6.1f}  z={v_enu[2]:6.1f} m"),
                    ("Position (PX4 NED)", f"N={ms.victim_ned[0]:6.1f}  E={ms.victim_ned[1]:6.1f}  D={ms.victim_ned[2]:5.1f} m"),
                    ("Detected by", f"{src} at {dist:.1f} m"),
                    ("Mission time", f"{ms.t:.0f} s after start"),
                    ("Snapshot", snap if len(snap) < 60 else "..." + snap[-57:])]
            # 1. terminal banner + bell (sar tab)
            bar = "!" * 64
            print(f"\a\033[1;97;41m\n{bar}\n   VICTIM DETECTED  -  {rows[0][1]}\n   {rows[2][1]}  |  t = {ms.t:.0f} s\n{bar}\033[0m\n", flush=True)
            # 2. ROS topic for any other tool (latched)
            self.pub_alert.publish(String(data=f"VICTIM DETECTED at gazebo ({v_enu[0]:.1f}, {v_enu[1]:.1f}, {v_enu[2]:.1f}) "
                                               f"ned ({ms.victim_ned[0]:.1f}, {ms.victim_ned[1]:.1f}, {ms.victim_ned[2]:.1f}) by {src}"))
            # 3. Gazebo: red sphere on the victim, red beacon through the rock, red ring on the surface
            for req in victim_marker_reqs(v_enu):
                self._gz(req)
            # 4. tmux status bar turns red in every tab
            self._tmux("red", f"VICTIM DETECTED at ({v_enu[0]:.1f}, {v_enu[1]:.1f}) - see the PHOENIX ALERT window")
            # 5. pop-up window
            if self.popup:
                try:
                    subprocess.Popen([sys.executable, "-c", POPUP_SCRIPT,
                                      json.dumps({"rows": rows, "action": action})],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as ex:
                    self.get_logger().warn(f"pop-up failed ({ex}) - install python3-tk")
            self.get_logger().info(f"ALERT raised. Snapshot: {snap}")

        def update_trail(self):
            """Green line in Gazebo showing where the drone has flown."""
            if not self.gz_markers or self.pos is None:
                return
            e = ned_to_enu(*self.pos)
            if not self.trail or math.dist(e, self.trail[-1]) > 1.0:
                self.trail = (self.trail + [e])[-400:]
            if len(self.trail) > 1 and (self.gz_proc is None or self.gz_proc.poll() is not None):
                try:
                    self.gz_proc = subprocess.Popen(
                        ["gz", "service", "-s", "/marker", "--reqtype", "gz.msgs.Marker", "--reptype",
                         "gz.msgs.Empty", "--timeout", "2000", "--req",
                         marker_req(10, "LINE_STRIP", (0, 0, 0), (1, 1, 1), (0.1, 0.9, 0.2, 1), self.trail)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    self.gz_markers = False

        def slow_loop(self):
            ms = self.mission
            try:
                if ms.victim_ned is not None and not self.alerted and self.pos is not None:
                    self.alerted = True
                    self.raise_alert()
                if ms.state not in (ms.IDLE, ms.DONE) and int(ms.t) % 2 == 0:
                    self.update_trail()
                if ms.state == ms.DONE and ms.t > 0 and not self.finished:
                    self.finished = True
                    last = ms.events[-1][1] if ms.events else ""
                    ok = "landed" in last
                    self._tmux("colour28" if ok else "colour130",
                               "PHOENIX: mission complete - drone landed" if ok else f"PHOENIX: {last}")
            except Exception as ex:                       # alerts must never stop the mission
                self.get_logger().warn(f"alert error: {ex}")
            for _, txt in ms.events[self.n_events:]:
                self.pub_status.publish(String(data=txt))
            self.n_events = len(ms.events)
            if ms.victim_ned is not None and not self.victim_sent:
                pt = PointStamped()
                pt.header.stamp = self.get_clock().now().to_msg()
                pt.header.frame_id = "px4_local_ned"
                pt.point.x, pt.point.y, pt.point.z = ms.victim_ned
                self.pub_victim.publish(pt)
                self.victim_sent = True
            if self.pos is not None and ms.state not in (ms.IDLE, ms.DONE):
                e = ned_to_enu(*self.pos)
                self.pub_status.publish(String(
                    data=f"{ms.state} phase={ms.phase} gazebo=({e[0]:.1f},{e[1]:.1f},{e[2]:.1f})"))
            # YOLO detections: subscribe as soon as the topic exists (any message type)
            if self.use_yolo and self.det_sub is None:
                for name, types in self.get_topic_names_and_types():
                    if name == self.det_topic and types:
                        try:
                            from rosidl_runtime_py.utilities import get_message
                            self.det_sub = self.create_subscription(
                                get_message(types[0]), name, self.on_detection, self.qos_det)
                            self.get_logger().info(f"YOLO detections connected: {name} [{types[0]}]")
                        except Exception as ex:          # never let this stop the mission
                            self.get_logger().warn(f"cannot use {name}: {ex}")
                            self.use_yolo = False

    rclpy.init()
    node = MineSarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
