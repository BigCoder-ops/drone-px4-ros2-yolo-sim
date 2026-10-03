import math
from px4_orbit_inspection.trajectory import smoothstep, orbit_point, inward_yaw, tracking_error

def test_smoothstep_limits():
    assert smoothstep(-1.0)==0.0 and smoothstep(0.0)==0.0
    assert smoothstep(1.0)==1.0 and smoothstep(2.0)==1.0

def test_cardinal_circle_points():
    assert orbit_point(0.0,0.0,5.0,0.0)==(5.0,0.0)
    n,e=orbit_point(0.0,0.0,5.0,math.pi/2)
    assert abs(n)<1e-9 and abs(e-5.0)<1e-9

def test_tracking_error(): assert tracking_error((0,0,0),(3,4,0))==5.0

def test_inward_yaw(): assert abs(inward_yaw(5.0,0.0,0.0,0.0)-math.pi)<1e-9