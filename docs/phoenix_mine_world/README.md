# PHOENIX mine world for PX4 + Gazebo

`phoenix_mine.sdf` is a Gazebo world built to match the PHOENIX mission. It has:

- a surface base (home pad, ground station, solar charging station);
- an open-pit phosphate mine;
- a mine portal leading into a dark underground room-and-pillar panel;
- a victim to find behind a roof-fall.

It uses only simple shapes and needs no internet or extra model downloads. It was checked with sdformat 14, the SDF parser used by Gazebo Harmonic, and loads with 0 errors.

## 1. Install (one time)

```bash
cp phoenix_mine.sdf ~/PX4-Autopilot/Tools/simulation/gz/worlds/
```

## 2. Run

```bash
cd ~/PX4-Autopilot
PX4_GZ_WORLD=phoenix_mine make px4_sitl gz_x500_depth
```

If you start the binary directly, add the same variable:

```bash
PX4_GZ_WORLD=phoenix_mine PX4_SYS_AUTOSTART=4002 PX4_GZ_MODEL=x500_depth ./build/px4_sitl_default/bin/px4
```

The drone spawns on the H pad at the origin. Everything else stays the same:

- the camera bridge (`/camera` to `/camera/image_raw`);
- the XRCE agent;
- `orbit_controller` and `mission_monitor`.

**Important:** the world is now called `phoenix_mine`, not `default`. If one of your scripts spawns models with `/world/default/create`, change it to `/world/phoenix_mine/create`.

## 3. Where things are

Gazebo uses ENU (x = east, y = north, z = up). PX4 uses NED (x = north, y = east, z = down).

| Place | Gazebo (x, y, z) | PX4 local (x, y, z) | Notes |
|---|---|---|---|
| Home pad (spawn) | 0, 0, 0 | 0, 0, 0 | surface plateau |
| Inspection silo (orbit target) | 0, 35, 0 | 35, 0, 0 | 14 m tall, radius 4 m, 18 m clear all around |
| Open-pit centre (floor) | 85, 0, -12 | 0, 85, +12 | the pit floor is 12 m **below** home |
| Box-cut trench entrance | 58, 0, -12 | 0, 58, +12 | 6 m wide trench through the benches |
| Portal A (adit) | 50, 0, -12 | 0, 50, +12 | 4 m wide, about 3.7 m clear height under the steel arches |
| Victim (310 K thermal target) | 16, 20, -12 | 20, 16, +12 | NW corner of the panel |
| Safe landing point | 100, 15, -12 | 15, 100, +12 | green pad on the pit floor (contingency) |

## 4. Example SAR route (PX4 NED, flying 2 m above the floor)

1. Take off to `(0, 0, -15)`, then fly to `(0, 85, -15)`, above the pit.
2. Descend to `(0, 85, +10)`, then fly west to `(0, 56, +10)` and `(0, 50, +10)`. This is the portal.
3. Fly along the main drift to `(0, 16, +10)`.
4. Turn north up the west corridor to `(18, 16, +10)`. The victim is at `(20, 16)`.
5. Return the same way, or land at the safe point.

The direct route through the cross-cut at Gazebo x 24–28, y 12–18 is blocked by a roof-fall. The drone has to find another way, which tests planning and avoidance.

Hazards inside:

- a low cable across the main drift at 2.7 m above the floor (Gazebo x = 40.5);
- a ventilation duct along the ceiling;
- an abandoned loader in the east corridor;
- a water puddle.

## 5. Mission phases mapped to the world

| PHOENIX phase | Where in the world |
|---|---|
| P0 Preparation | home pad, ground-station container, solar charging pad |
| P1–P2 Launch / transit / entry | surface flight to the pit, descent, box-cut, Portal A |
| P3 Inspection / SAR | underground panel (dark, GPS should be treated as lost), victim, roof-fall |
| Orbit inspection | silo with rust/crack patches to detect |
| P5 Return / abort | back to the home pad, or the safe point on the pit floor |

## 6. Good to know

- **GPS still works underground in Gazebo.** The simulator does not block satellites under rock. In PX4 v1.15 with Gazebo, GPS comes from the `sensor_gps_sim` module. To test what PHOENIX does when GPS disappears (its contingency logic), type this in the PX4 shell (`pxh>`):

  ```
  sensor_gps_sim stop
  ```

  Restart it with `sensor_gps_sim start`. For real GPS-denied flight, PX4 needs another position source: your SLAM odometry published on `/fmu/in/vehicle_visual_odometry`. Until then, keep GPS on and treat the underground part as "GPS-denied" in the scenario only.
- **Light.** Only the portal and the first part of the drift have lights. The deep panel is dark on purpose ("unlit sector"), so it suits LiDAR and depth more than the RGB camera.
- **Thermal camera.** The victim carries Gazebo thermal temperatures (body 310 K, air 298 K), so it shows up hot if you add a `thermal_camera` sensor later.
- **LiDAR.** `x500_depth` has an RGB camera and a depth camera, but no LiDAR. To test Point-LIO you would add a `gpu_lidar` sensor to a copy of the model.
- **GPS origin.** It is set approximately near Benguerir (UM6P / OCP area): 32.2196 N, -7.9367 E, 450 m. PX4 computes the magnetic field from this position automatically.

## 7. Changing the world

Edit `make_world.py` (sizes, positions, colours, victim location) and run:

```bash
python3 make_world.py   # rewrites phoenix_mine.sdf
```
