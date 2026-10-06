#!/usr/bin/env python3
"""Generate the PHOENIX mine world (phoenix_mine.sdf) for PX4 SITL + Gazebo Harmonic.

Layout (Gazebo ENU frame: x = east, y = north, z = up, metres)
  z = 0    surface plateau (home pad at the origin, where PX4 spawns the drone)
  z = -12  open-pit floor and underground level (ground plane)
  Open pit  : floor x[60,110] y[-25,25], two 4 m benches, rim at x[50,120] y[-35,35]
  Portal A  : box-cut trench through the west benches, adit opening at x=50, y[-2,2]
  Underground room-and-pillar panel under the plateau: x[14,48] y[-22,22], 4 m high
  Victim    : (16, 20, -12) deep in the NW of the panel, behind a roof-fall
  Silo      : orbit-inspection asset at (0, 35)
"""
import json, math, os

PRIMS = []          # for the preview renderer
MODELS = []         # sdf text blocks

def col(c):
    return " ".join(f"{v:.3f}" for v in c)

def material(c, emissive=None):
    s = (f"<material><ambient>{col(c)} 1</ambient><diffuse>{col(c)} 1</diffuse>"
         f"<specular>0.08 0.08 0.08 1</specular>")
    if emissive:
        s += f"<emissive>{col(emissive)} 1</emissive>"
    return s + "</material>"

def pose_str(p):
    return " ".join(f"{v:.4g}" for v in p)

class Model:
    def __init__(self, name, pose=(0, 0, 0, 0, 0, 0), static=True):
        self.name, self.pose, self.static = name, pose, static
        self.items, self.n = [], 0

    def _add(self, kind, geom_xml, dims, pose, c, collide, emissive, thermal):
        self.n += 1
        nm = f"{kind}_{self.n}"
        plug = ""
        if thermal is not None:
            plug = (f'<plugin filename="gz-sim-thermal-system" name="gz::sim::systems::Thermal">'
                    f'<temperature>{thermal}</temperature></plugin>')
        x = (f'<visual name="v_{nm}"><pose>{pose_str(pose)}</pose><geometry>{geom_xml}</geometry>'
             f'{material(c, emissive)}{plug}</visual>')
        if collide:
            x += (f'<collision name="c_{nm}"><pose>{pose_str(pose)}</pose>'
                  f'<geometry>{geom_xml}</geometry></collision>')
        self.items.append(x)
        PRIMS.append(dict(model=self.name, mpose=self.pose, kind=kind, dims=dims,
                          pose=pose, color=c, emissive=emissive is not None))

    def box(self, size, pose, c, collide=True, emissive=None, thermal=None):
        g = f"<box><size>{pose_str(size)}</size></box>"
        self._add("box", g, list(size), pose, c, collide, emissive, thermal)

    def cyl(self, r, L, pose, c, collide=True, emissive=None, thermal=None):
        g = f"<cylinder><radius>{r}</radius><length>{L}</length></cylinder>"
        self._add("cyl", g, [r, L], pose, c, collide, emissive, thermal)

    def sphere(self, r, pose, c, collide=True, emissive=None, thermal=None):
        g = f"<sphere><radius>{r}</radius></sphere>"
        self._add("sph", g, [r], pose, c, collide, emissive, thermal)

    def xml(self):
        return (f'<model name="{self.name}"><static>{"true" if self.static else "false"}</static>'
                f'<pose>{pose_str(self.pose)}</pose><link name="link">'
                + "".join(self.items) + "</link></model>")

def rect_box(m, x0, x1, y0, y1, z0, z1, c, **kw):
    """Axis-aligned box from extents."""
    m.box((x1 - x0, y1 - y0, z1 - z0),
          ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, 0, 0, 0), c, **kw)

# ---------------------------------------------------------------- colours
PLATEAU = (0.78, 0.68, 0.52)      # dry phosphate overburden
BENCH1  = (0.62, 0.55, 0.45)      # grey phosphate layer
BENCH2  = (0.70, 0.60, 0.46)
ROCK    = (0.42, 0.38, 0.34)      # underground rock
PILLAR  = (0.48, 0.44, 0.38)
STEEL   = (0.35, 0.36, 0.38)
YELLOW  = (0.95, 0.75, 0.10)
ORANGE  = (0.95, 0.45, 0.08)
WHITE   = (0.92, 0.92, 0.90)
DARK    = (0.18, 0.18, 0.20)
BLUE    = (0.12, 0.22, 0.45)
FLOOR_Z = -12.0

# ---------------------------------------------------------------- terrain
plateau = Model("terrain_plateau")
Z0, Z1 = FLOOR_Z, 0.0
rect_box(plateau, -200, 10, -250, 250, Z0, Z1, PLATEAU)    # west block (home base on top)
rect_box(plateau, 10, 300, -250, -35, Z0, Z1, PLATEAU)    # south
rect_box(plateau, 10, 300, 35, 250, Z0, Z1, PLATEAU)      # north
rect_box(plateau, 120, 300, -35, 35, Z0, Z1, PLATEAU)     # east
rect_box(plateau, 10, 50, -35, -30, Z0, Z1, PLATEAU)      # strips beside underground panel
rect_box(plateau, 10, 50, 30, 35, Z0, Z1, PLATEAU)
MODELS.append(plateau)

pit = Model("open_pit_benches")
# bench 2 (top at -4): ring between rim x[50,120]y[-35,35] and x[55,115]y[-30,30]
rect_box(pit, 50, 120, 30, 35, Z0, -4, BENCH2)
rect_box(pit, 50, 120, -35, -30, Z0, -4, BENCH2)
rect_box(pit, 115, 120, -30, 30, Z0, -4, BENCH2)
rect_box(pit, 50, 55, -30, -3, Z0, -4, BENCH2)            # west piece split by the box-cut
rect_box(pit, 50, 55, 3, 30, Z0, -4, BENCH2)
# bench 1 (top at -8): ring between x[55,115]y[-30,30] and floor x[60,110]y[-25,25]
rect_box(pit, 55, 115, 25, 30, Z0, -8, BENCH1)
rect_box(pit, 55, 115, -30, -25, Z0, -8, BENCH1)
rect_box(pit, 110, 115, -25, 25, Z0, -8, BENCH1)
rect_box(pit, 55, 60, -25, -3, Z0, -8, BENCH1)
rect_box(pit, 55, 60, 3, 25, Z0, -8, BENCH1)
# safety berms on the rim
BERM = (0.70, 0.60, 0.45)
rect_box(pit, 48, 122, 37, 39, 0, 1.2, BERM)
rect_box(pit, 48, 122, -39, -37, 0, 1.2, BERM)
rect_box(pit, 122, 124, -39, 39, 0, 1.2, BERM)
MODELS.append(pit)

# ---------------------------------------------------------------- underground panel
ug = Model("underground_panel")
rect_box(ug, 10, 50, -30, 30, -8, -0.3, ROCK)             # roof / overburden above the panel
rect_box(ug, 10, 50, -30, 30, -0.3, 0, PLATEAU)           # surface skin on top of the roof
rect_box(ug, 10, 14, -30, 30, Z0, -8, ROCK)               # west wall
rect_box(ug, 14, 48, 22, 30, Z0, -8, ROCK)                # north wall
rect_box(ug, 14, 48, -30, -22, Z0, -8, ROCK)              # south wall
rect_box(ug, 48, 50, -30, -2, Z0, -8, ROCK)               # face at the pit, portal gap y[-2,2]
rect_box(ug, 48, 50, 2, 30, Z0, -8, ROCK)
for x0, x1 in [(18, 24), (28, 34), (38, 44)]:             # 12 pillars, 4 m rooms between
    for y0, y1 in [(-18, -12), (-8, -2), (2, 8), (12, 18)]:
        rect_box(ug, x0, x1, y0, y1, Z0, -8, PILLAR)
MODELS.append(ug)

infra = Model("underground_infrastructure")
# steel arch sets at the portal
for x in (49.4, 47.0, 44.6):
    for y in (-1.8, 1.8):
        infra.cyl(0.12, 3.85, (x, y, FLOOR_Z + 1.925, 0, 0, 0), YELLOW)
    infra.box((0.25, 4.0, 0.25), (x, 0, -8.15, 0, 0, 0), YELLOW)
# portal sign
infra.box((0.06, 3.0, 0.7), (50.05, 0, -7.4, 0, 0, 0), YELLOW, collide=False)
# ventilation duct along the main drift ceiling, cable along the wall
infra.cyl(0.35, 34, (31, 1.3, -8.6, 0, math.pi / 2, 0), (0.85, 0.85, 0.80))
infra.cyl(0.03, 34, (31, -1.85, -9.6, 0, math.pi / 2, 0), DARK)
# low-hanging cable across the main drift (obstacle-avoidance hazard)
infra.cyl(0.03, 4.0, (40.5, 0, -9.3, math.pi / 2, 0, 0), DARK)
# ceiling work lights (emissive) - real light sources are added as <light> below
for x in (45.5, 35.5):
    infra.box((0.5, 0.25, 0.08), (x, -1.0, -8.06, 0, 0, 0), WHITE, collide=False, emissive=(1, 0.95, 0.8))
# roof-fall blocking cross-cut x[24,28] y[12,18]
rubble = [((1.6, 1.2, 1.0), (25.0, 13.5, -11.5, 0.3, 0.1, 0.5)),
          ((1.2, 1.4, 0.9), (26.6, 14.2, -11.55, 0.0, 0.4, 1.2)),
          ((1.8, 1.0, 1.2), (25.6, 15.6, -11.4, 0.2, 0.0, 2.0)),
          ((1.0, 1.0, 0.8), (27.2, 16.4, -11.6, 0.5, 0.3, 0.3)),
          ((1.4, 1.6, 1.1), (24.8, 16.9, -11.45, 0.1, 0.2, 0.9)),
          ((0.9, 0.8, 0.7), (26.2, 12.8, -11.65, 0.6, 0.0, 0.0)),
          ((4.2, 3.0, 0.4), (26.0, 15.0, -10.2, 0.35, 0.25, 0.2))]   # fallen roof slab
for s, p in rubble:
    infra.box(s, p, (0.40, 0.36, 0.32))
# abandoned LHD loader in the east corridor
infra.box((2.0, 3.6, 1.4), (46.0, -14.0, FLOOR_Z + 1.2, 0, 0, 0), YELLOW)
infra.box((1.9, 1.0, 0.9), (46.0, -11.6, FLOOR_Z + 0.9, 0, 0, 0), STEEL)
for y in (-15.3, -12.7):
    for x in (44.95, 47.05):
        infra.cyl(0.55, 0.45, (x, y, FLOOR_Z + 0.55, 0, math.pi / 2, 0), DARK)
# gas-monitoring station on a pillar face
infra.box((0.3, 0.2, 0.5), (21.0, -1.85, -10.5, 0, 0, 0), (0.2, 0.6, 0.3), collide=False, emissive=(0, 0.6, 0.1))
# water puddle (visual only)
infra.box((3.0, 2.0, 0.01), (36.0, -10.0, FLOOR_Z + 0.006, 0, 0, 0), (0.15, 0.25, 0.35), collide=False)
MODELS.append(infra)

# ---------------------------------------------------------------- victim (thermal target)
victim = Model("victim_thermal_target", pose=(16.0, 20.0, FLOOR_Z, 0, 0, 0.6))
T_BODY = 310.0   # 37 C
victim.box((0.55, 0.36, 0.22), (0.0, 0, 0.12, 0, 0, 0), ORANGE, thermal=T_BODY)            # torso, hi-vis vest
victim.box((0.80, 0.14, 0.14), (-0.68, 0.09, 0.08, 0, 0, 0), BLUE, thermal=T_BODY - 4)     # legs
victim.box((0.80, 0.14, 0.14), (-0.68, -0.09, 0.08, 0, 0, 0.12), BLUE, thermal=T_BODY - 4)
victim.box((0.55, 0.10, 0.10), (0.05, 0.27, 0.07, 0, 0, 0.3), ORANGE, thermal=T_BODY - 2)  # arms
victim.box((0.55, 0.10, 0.10), (0.05, -0.27, 0.07, 0, 0, -0.2), ORANGE, thermal=T_BODY - 2)
victim.sphere(0.11, (0.42, 0, 0.12, 0, 0, 0), (0.80, 0.62, 0.48), thermal=T_BODY)          # head
victim.sphere(0.13, (0.47, 0, 0.17, 0, 0, 0), WHITE, collide=False, thermal=300)           # helmet
victim.box((0.10, 0.06, 0.04), (0.60, 0, 0.17, 0, 0, 0), WHITE, collide=False, emissive=(1, 1, 0.8))  # cap lamp
MODELS.append(victim)

# ---------------------------------------------------------------- surface base (home)
base = Model("surface_base")
# home landing pad at the origin - visual only so the drone spawns cleanly
base.cyl(2.3, 0.02, (0, 0, 0.010, 0, 0, 0), DARK, collide=False)
base.cyl(2.1, 0.02, (0, 0, 0.015, 0, 0, 0), YELLOW, collide=False)
base.cyl(1.9, 0.02, (0, 0, 0.020, 0, 0, 0), DARK, collide=False)
base.box((0.25, 1.4, 0.01), (-0.45, 0, 0.032, 0, 0, 0), WHITE, collide=False)
base.box((0.25, 1.4, 0.01), (0.45, 0, 0.032, 0, 0, 0), WHITE, collide=False)
base.box((0.65, 0.22, 0.01), (0, 0, 0.032, 0, 0, 0), WHITE, collide=False)
# ground control station container + antenna mast
base.box((6.1, 2.4, 2.6), (-18, -8, 1.3, 0, 0, 0.0), WHITE)
base.box((0.05, 0.9, 2.0), (-14.93, -8.4, 1.0, 0, 0, 0), BLUE, collide=False)
base.cyl(0.06, 8.0, (-16.0, -6.4, 4.0, 0, 0, 0), STEEL)
base.cyl(0.4, 0.08, (-16.0, -6.4, 7.6, 0, 1.2, 0), WHITE)
# solar-assisted charging station: three panels tilted 30 deg facing south + charging pad
for x in (-20.2, -18.0, -15.8):
    base.box((2.0, 1.1, 0.05), (x, 10.0, 1.3, math.radians(30), 0, 0), BLUE)
    base.cyl(0.04, 1.0, (x, 10.25, 0.6, 0, 0, 0), STEEL)
    base.cyl(0.04, 1.4, (x, 9.75, 0.8, 0, 0, 0), STEEL)
base.box((2.0, 2.0, 0.02), (-18, 6.0, 0.01, 0, 0, 0), (0.10, 0.35, 0.65), collide=False)
# rescue-team staging canopy
for dx in (-1.4, 1.4):
    for dy in (-1.4, 1.4):
        base.cyl(0.04, 2.3, (-8 + dx, -18 + dy, 1.15, 0, 0, 0), STEEL)
base.box((3.1, 3.1, 0.1), (-8, -18, 2.35, 0, 0, 0), (0.75, 0.10, 0.10))
base.box((1.8, 0.6, 0.8), (-8, -18, 0.4, 0, 0, 0), (0.30, 0.32, 0.25))
# wind sock
base.cyl(0.05, 4.0, (-14, 3, 2.0, 0, 0, 0), STEEL)
base.cyl(0.22, 1.2, (-13.4, 3, 3.8, 0, math.pi / 2, 0), ORANGE, collide=False)
MODELS.append(base)

# ---------------------------------------------------------------- orbit inspection asset
silo = Model("inspection_silo", pose=(0, 35, 0, 0, 0, 0))
silo.cyl(4.0, 14.0, (0, 0, 7.0, 0, 0, 0), (0.80, 0.80, 0.78))
silo.cyl(4.2, 0.4, (0, 0, 14.2, 0, 0, 0), STEEL)
silo.cyl(0.6, 1.2, (0, 0, 15.0, 0, 0, 0), STEEL)
for i, (a, z, w, h) in enumerate([(0.3, 4.0, 0.9, 1.6), (2.2, 9.0, 1.4, 0.6), (4.0, 6.0, 0.5, 2.2)]):
    # rust / crack patches to find during inspection
    silo.box((0.04, w, h), (4.0 * math.cos(a), 4.0 * math.sin(a), z, 0, 0, a), (0.55, 0.22, 0.08), collide=False)
for k in range(8):   # external ladder rungs
    silo.box((0.05, 0.6, 0.04), (-4.05, 0, 1.0 + 1.6 * k, 0, 0, 0), YELLOW, collide=False)
MODELS.append(silo)

# ---------------------------------------------------------------- surface mining equipment
truck = Model("haul_truck", pose=(32, -52, 0, 0, 0, 0.3))
truck.box((7.5, 3.4, 1.0), (0, 0, 1.6, 0, 0, 0), YELLOW)                  # chassis
truck.box((4.8, 3.6, 1.8), (-1.2, 0, 3.0, 0, -0.12, 0), (0.85, 0.65, 0.10))  # dump body
truck.box((1.8, 1.6, 1.6), (2.7, 0.8, 2.9, 0, 0, 0), YELLOW)              # cab
truck.box((0.05, 1.3, 0.7), (3.61, 0.8, 3.1, 0, 0, 0), (0.2, 0.3, 0.4), collide=False)
for x in (-2.4, 2.6):
    for y in (-1.6, 1.6):
        truck.cyl(1.05, 0.9, (x, y, 1.05, math.pi / 2, 0, 0), DARK)
MODELS.append(truck)

stock = Model("phosphate_stockpiles")
stock.sphere(8.0, (22, 62, -5.0, 0, 0, 0), (0.72, 0.64, 0.52))
stock.sphere(6.5, (38, 70, -4.2, 0, 0, 0), (0.68, 0.60, 0.50))
MODELS.append(stock)

# contingency landing point on the pit floor
safe = Model("safe_point_pit_floor")
safe.box((3.0, 3.0, 0.02), (100, 15, FLOOR_Z + 0.01, 0, 0, 0), (0.10, 0.55, 0.20), collide=False)
safe.box((2.2, 0.3, 0.01), (100, 15, FLOOR_Z + 0.025, 0, 0, 0.785), WHITE, collide=False)
safe.box((2.2, 0.3, 0.01), (100, 15, FLOOR_Z + 0.025, 0, 0, -0.785), WHITE, collide=False)
MODELS.append(safe)

# ---------------------------------------------------------------- world text
GUI_PLUGINS = """
      <plugin filename="MinimalScene" name="3D View">
        <gz-gui><title>3D View</title><property type="bool" key="showTitleBar">false</property><property type="string" key="state">docked</property></gz-gui>
        <engine>ogre2</engine><scene>scene</scene>
        <ambient_light>0.35 0.35 0.35</ambient_light>
        <background_color>0.62 0.74 0.88</background_color>
        <camera_pose>-32 -30 26 0 0.42 0.72</camera_pose>
        <camera_clip><near>0.1</near><far>25000</far></camera_clip>
      </plugin>"""
for nm, fn in [("Entity context menu", "EntityContextMenuPlugin"), ("Scene Manager", "GzSceneManager"),
               ("Interactive view control", "InteractiveViewControl"), ("Camera Tracking", "CameraTracking"),
               ("Marker manager", "MarkerManager"), ("Select Entities", "SelectEntities"),
               ("Visualization Capabilities", "VisualizationCapabilities"), ("Spawn Entities", "Spawn")]:
    GUI_PLUGINS += f"""
      <plugin filename="{fn}" name="{nm}">
        <gz-gui><property key="resizable" type="bool">false</property><property key="width" type="double">5</property><property key="height" type="double">5</property><property key="state" type="string">floating</property><property key="showTitleBar" type="bool">false</property></gz-gui>
      </plugin>"""
GUI_PLUGINS += """
      <plugin name="World control" filename="WorldControl">
        <gz-gui><title>World control</title><property type="bool" key="showTitleBar">0</property><property type="bool" key="resizable">0</property><property type="double" key="height">72</property><property type="double" key="width">121</property><property type="double" key="z">1</property><property type="string" key="state">floating</property>
          <anchors target="3D View"><line own="left" target="left"/><line own="bottom" target="bottom"/></anchors></gz-gui>
        <play_pause>1</play_pause><step>1</step><start_paused>1</start_paused>
      </plugin>
      <plugin name="World stats" filename="WorldStats">
        <gz-gui><title>World stats</title><property type="bool" key="showTitleBar">0</property><property type="bool" key="resizable">0</property><property type="double" key="height">110</property><property type="double" key="width">290</property><property type="double" key="z">1</property><property type="string" key="state">floating</property>
          <anchors target="3D View"><line own="right" target="right"/><line own="bottom" target="bottom"/></anchors></gz-gui>
        <sim_time>1</sim_time><real_time>1</real_time><real_time_factor>1</real_time_factor><iterations>1</iterations>
      </plugin>
      <plugin name="Entity tree" filename="EntityTree"/>"""

def light_point(name, xyz, rng=14, diffuse=(1.0, 0.92, 0.75)):
    return (f'<light name="{name}" type="point"><pose>{pose_str(xyz + (0, 0, 0))}</pose>'
            f'<cast_shadows>false</cast_shadows><diffuse>{col(diffuse)} 1</diffuse>'
            f'<specular>0.1 0.1 0.1 1</specular><attenuation><range>{rng}</range>'
            f'<constant>0.2</constant><linear>0.08</linear><quadratic>0.01</quadratic></attenuation></light>')

LIGHTS = """
    <light name="sun" type="directional">
      <pose>0 0 500 0 0 0</pose>
      <cast_shadows>true</cast_shadows>
      <intensity>1</intensity>
      <direction>0.25 0.55 -0.8</direction>
      <diffuse>0.95 0.92 0.85 1</diffuse>
      <specular>0.3 0.3 0.3 1</specular>
      <attenuation><range>2000</range><constant>1</constant><linear>0</linear><quadratic>0</quadratic></attenuation>
    </light>
    """ + light_point("portal_work_light", (51.5, 0.0, -8.4), rng=18) + light_point(
        "drift_light_1", (45.5, -1.0, -8.3)) + light_point("drift_light_2", (35.5, -1.0, -8.3), rng=12)

HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!--
  PHOENIX mine world - PX4 SITL + Gazebo (Harmonic/Garden)
  Generated by make_world.py. Frame: x = east, y = north, z = up (metres).

  Zones
    Home pad (spawn) ...... (0, 0, 0)       surface plateau, z = 0
    Inspection silo ....... (0, 35)         orbit target, 14 m tall, r = 4 m
    Open pit .............. x 50..120, y -35..35, floor at z = -12 (two 4 m benches)
    Portal A (adit) ....... (50, 0, -12)    reached through the box-cut trench at x 50..60
    Underground panel ..... x 14..48, y -22..22, rooms 4 m wide x 4 m high, 12 pillars
    Victim (310 K) ........ (16, 20, -12)   behind a roof-fall in cross-cut x 24..28
    Safe landing point .... (100, 15, -12)  pit floor
  PX4 local frame is NED: Gazebo (x_e, y_n, z_u) -> PX4 (x = y_n, y = x_e, z = -z_u)
-->
<sdf version="1.9">
  <world name="phoenix_mine">
    <physics type="ode">
      <max_step_size>0.004</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>250</real_time_update_rate>
    </physics>
    <plugin name="gz::sim::systems::Physics" filename="gz-sim-physics-system"/>
    <plugin name="gz::sim::systems::UserCommands" filename="gz-sim-user-commands-system"/>
    <plugin name="gz::sim::systems::SceneBroadcaster" filename="gz-sim-scene-broadcaster-system"/>
    <plugin name="gz::sim::systems::Contact" filename="gz-sim-contact-system"/>
    <plugin name="gz::sim::systems::Imu" filename="gz-sim-imu-system"/>
    <plugin name="gz::sim::systems::AirPressure" filename="gz-sim-air-pressure-system"/>
    <plugin name="gz::sim::systems::ApplyLinkWrench" filename="gz-sim-apply-link-wrench-system"/>
    <plugin name="gz::sim::systems::NavSat" filename="gz-sim-navsat-system"/>
    <plugin name="gz::sim::systems::Sensors" filename="gz-sim-sensors-system">
      <render_engine>ogre2</render_engine>
    </plugin>
    <gui fullscreen="false">""" + GUI_PLUGINS + """
    </gui>
    <gravity>0 0 -9.8</gravity>
    <magnetic_field>6e-06 2.3e-05 -4.2e-05</magnetic_field>
    <atmosphere type="adiabatic">
      <temperature>298</temperature>
    </atmosphere>
    <scene>
      <grid>false</grid>
      <ambient>0.30 0.30 0.30 1</ambient>
      <background>0.62 0.74 0.88 1</background>
      <shadows>true</shadows>
    </scene>
    <model name="ground_plane">
      <static>true</static>
      <pose>0 0 -12 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>1 1</size></plane></geometry>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>1500 1500</size></plane></geometry>
          <material><ambient>0.66 0.58 0.46 1</ambient><diffuse>0.66 0.58 0.46 1</diffuse><specular>0.05 0.05 0.05 1</specular></material>
        </visual>
      </link>
    </model>
"""

FOOTER = """
    <spherical_coordinates>
      <!-- approximate GPS origin near Benguerir (UM6P / OCP phosphate basin), Morocco -->
      <surface_model>EARTH_WGS84</surface_model>
      <world_frame_orientation>ENU</world_frame_orientation>
      <latitude_deg>32.2196</latitude_deg>
      <longitude_deg>-7.9367</longitude_deg>
      <elevation>450</elevation>
    </spherical_coordinates>
  </world>
</sdf>
"""

def pretty_model(m):
    out = [f'    <model name="{m.name}">', f'      <static>{"true" if m.static else "false"}</static>',
           f'      <pose>{pose_str(m.pose)}</pose>', '      <link name="link">']
    out += [f"        {it}" for it in m.items]
    out += ['      </link>', '    </model>']
    return "\n".join(out)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sdf = HEADER + "\n".join(pretty_model(m) for m in MODELS) + "\n" + LIGHTS + FOOTER
    with open(os.path.join(here, "phoenix_mine.sdf"), "w") as f:
        f.write(sdf)
    with open(os.path.join(here, "prims.json"), "w") as f:
        json.dump(PRIMS, f)
    print(f"wrote phoenix_mine.sdf ({len(sdf)/1024:.1f} KB), {len(PRIMS)} primitives, {len(MODELS)} models")
