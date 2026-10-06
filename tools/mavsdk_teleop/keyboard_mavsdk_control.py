import asyncio

from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.manual_control import ManualControlError
from mavsdk.telemetry import LandedState

import KeyPressModule as kp

# ------------------------------------------------------------------
# Keyboard teleop for PX4 SITL through MAVSDK
#
#   Click the pygame window first, keys only work when it has focus.
#
#   r          arm + switch to Position mode
#   w / s      climb / descend   (release = hold altitude)
#   arrows     forward/back, left/right
#   a / d      yaw left / right
#   l          land
#   i          print flight mode
#
#   Do NOT run the orbit launch at the same time: only one program
#   should command the drone.
# ------------------------------------------------------------------

SPEED = 0.5
LOOP_DT = 0.05  # 20 Hz

kp.init()
drone = System()

# MAVSDK order: x = forward (pitch), y = right (roll), z = throttle 0..1, r = yaw
cmd = {"x": 0.0, "y": 0.0, "z": 0.5, "r": 0.0}
connected = False


async def safe(coro, label):
    """Run a MAVSDK call without killing the loop if PX4 refuses it."""
    try:
        await coro
        print(f"-- {label}: OK")
        return True
    except (ActionError, ManualControlError) as e:
        print(f"-- {label} FAILED: {e}")
        return False


async def is_on_ground():
    async for state in drone.telemetry.landed_state():
        return state == LandedState.ON_GROUND


async def arm_and_start():
    if not await is_on_ground():
        print("-- Already flying, ignoring arm")
        return
    if await safe(drone.action.arm(), "Arm"):
        # Without this, PX4 stays in Hold and ignores the keyboard
        await safe(drone.manual_control.start_position_control(), "Position mode")
        print("-- Press w now to take off (PX4 disarms if you wait too long)")


async def print_flight_mode():
    async for mode in drone.telemetry.flight_mode():
        print("FlightMode:", mode)
        return


async def keyboard_loop():
    while True:
        x = y = r = 0.0
        z = 0.5

        if kp.getKey("UP"):
            x = SPEED
        elif kp.getKey("DOWN"):
            x = -SPEED
        if kp.getKey("RIGHT"):
            y = SPEED
        elif kp.getKey("LEFT"):
            y = -SPEED
        if kp.getKey("w"):
            z = 1.0
        elif kp.getKey("s"):
            z = 0.0
        if kp.getKey("a"):
            r = -SPEED
        elif kp.getKey("d"):
            r = SPEED

        cmd.update(x=x, y=y, z=z, r=r)

        if connected:
            if kp.getKey("r"):
                await arm_and_start()
                await asyncio.sleep(0.5)  # avoid repeating on one key press
            elif kp.getKey("l"):
                await safe(drone.action.land(), "Land")
                await asyncio.sleep(0.5)
            elif kp.getKey("i"):
                await print_flight_mode()
                await asyncio.sleep(0.5)

        await asyncio.sleep(LOOP_DT)


async def sender_loop():
    last = None
    while True:
        values = (cmd["x"], cmd["y"], cmd["z"], cmd["r"])
        try:
            await drone.manual_control.set_manual_control_input(*values)
        except ManualControlError as e:
            print("-- Manual input error:", e)
        # Print only when it changes: if this never changes, the keys aren't reaching pygame
        if values != last:
            print("input  fwd=%.1f  right=%.1f  thr=%.1f  yaw=%.1f" % values)
            last = values
        await asyncio.sleep(LOOP_DT)


async def main():
    global connected

    # Start reading the keyboard right away so the pygame window stays responsive
    keyboard_task = asyncio.create_task(keyboard_loop())

    print("Waiting for drone to connect...")
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Connected to drone!")
            break

    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position state is good enough for flying.")
            break

    connected = True
    print("-- Ready. Click the pygame window, press r to arm, then w to climb.")
    await asyncio.gather(keyboard_task, sender_loop())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye")
