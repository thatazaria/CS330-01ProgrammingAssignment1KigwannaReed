# Project: CS 330
# Program: Programming Assignment 1 (Dynamic Movements Continue, Seek, Flee, and Arrive)
# Purpose: Implement the dynamic movements Continue, Seek, Flee, and Arrive.
# Authors: Rebecca N. Kigwanna and Azaria A. Reed

import math
from pathlib import Path

# Initialize simulation settings.
DT = 0.5    # Each update advances the clock by half a second.
STEPS = 100 # 0.5 seconds/step * 100 steps = 50 seconds.

# Initialize steering behavior constants.
CONTINUE = 1
SEEK = 6
FLEE = 7
ARRIVE = 8

# Put the trajectory data file in the root's output folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FOLDER = PROJECT_ROOT / "output"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_FOLDER / "trajectory.txt"

# Initialize characters with a list of dictionaries.
def initialize_characters():
    return [
        {"number": 1, "id": 2601, "behavior": CONTINUE, "position_x": 0, "position_z": 0, "velocity_x": 0, "velocity_z": 0, "orientation": 0.0,
         "max_velocity": 0, "max_acceleration": 0, "target": 0, "arrival_radius": 0, "slowing_radius": 0, "time_to_target": 0},

        {"number": 2, "id": 2602, "behavior": FLEE, "position_x": -30, "position_z": -50, "velocity_x": 2, "velocity_z": 7, "orientation": math.pi/4,
         "max_velocity": 8, "max_acceleration": 1.5, "target": 1, "arrival_radius": 0, "slowing_radius": 0, "time_to_target": 0},

        {"number": 3, "id": 2603, "behavior": SEEK, "position_x": -50, "position_z": 40, "velocity_x": 0, "velocity_z": 8, "orientation": (3*math.pi)/2,
         "max_velocity": 8, "max_acceleration": 2, "target": 1, "arrival_radius": 0, "slowing_radius": 0, "time_to_target": 0},

        {"number": 4, "id": 2604, "behavior": ARRIVE, "position_x": 50, "position_z": 75, "velocity_x": -9, "velocity_z": 4, "orientation": math.pi,
         "max_velocity": 10, "max_acceleration": 2, "target": 1, "arrival_radius": 4, "slowing_radius": 32, "time_to_target": 1},
    ]

# Run full simulation.
def run_sim(characters, output_path):
    # Open trajectory file for writing.
    with open(output_path, "w") as trajectory_file:
        # Write initial character records.
        for character in characters:
            character["acceleration_x"], character["acceleration_z"] = get_steering(character, characters)
            write_record(trajectory_file, 0.0, character)

        # Write one record per character per timestep.
        clock = 0.0
        for i in range(STEPS):
            clock += DT
            for character in characters:
                character["acceleration_x"], character["acceleration_z"] = get_steering(character, characters)
                step_ne1(character, DT) # Update accordingly with physics.
                write_record(trajectory_file, clock, character)

# Get steering behavior.
def get_steering(character, characters):
    if character["behavior"] == CONTINUE:
        return continue_behavior(character, characters)
    if character["behavior"] == FLEE:
        return flee_behavior(character, characters)
    if character["behavior"] == SEEK:
        return seek_behavior(character, characters)
    if character["behavior"] == ARRIVE:
        return arrive_behavior(character, characters)
    # default: nothing fancy
    return 0.0, 0.0

# Continue.
def continue_behavior(character, characters):
    return 0.0, 0.0 # Maintains current velocity

# Flee.
def flee_behavior(character, characters):
    
    #Flee = accelerate directly away from the target.
    #this is basically Seek but the direction is flipped.
    
    # map target index (1 → 2601, etc.) to actual id
    target_id = 2600 + character["target"]
    target = next((ch for ch in characters if ch["id"] == target_id), None)
    if not target:
        return 0.0, 0.0  # no valid target, no push

    # vector from target to me (points outward)
    dx = character["position_x"] - target["position_x"]
    dz = character["position_z"] - target["position_z"]
    dist = math.hypot(dx, dz)

    if dist > 0:
        ax = (dx / dist) * character["max_acceleration"]
        az = (dz / dist) * character["max_acceleration"]
        return ax, az
    return 0.0, 0.0  # if we are on top of each other, there’s no direction to push

# Seek.
def seek_behavior(char, chars):
    # Seek means: “accelerate toward your target character as hard as you can.”
    # we figure out the direction (target minus self)
    # normalize it
    # scale by max acceleration

    # figure out which character is the target (target=1 -> 2601, etc.)
    target_id = 2600 + char["target"]
    target = next((ch for ch in chars if ch["id"] == target_id), None)
    if not target:
        return 0.0, 0.0  # if no target found, no push

    # vector from me -> target
    dx = target["position_x"] - char["position_x"]
    dz = target["position_z"] - char["position_z"]
    dist = math.hypot(dx, dz)

    if dist > 0:
        # push = unit vector * max_acceleration
        acceleration_x = (dx / dist) * char["max_acceleration"]
        acceleration_z = (dz / dist) * char["max_acceleration"]
        return acceleration_x, acceleration_z
    return 0.0, 0.0  # sitting right on the target -> nothing to do

# Arrive.
def arrive_behavior(character, characters):
    
    # Arrive = go toward the target but ease in smoothly.
      # outside slowing_radius- aim for max speed.
      # inside slowing_radius- scale speed down as distance shrinks (linear ramp).
      # inside arrival_radius- stop (no acceleration).
      # use time_to_target to gently nudge current velocity toward the target velocity.
      # clamp accel to max_acceleration (physics step already clamps velocity to max_velocity).
   
    target_id = 2600 + character["target"]
    target = next((ch for ch in characters if ch["id"] == target_id), None)
    if not target:
        return 0.0, 0.0

    # direction to the target
    dx = target["position_x"] - character["position_x"]
    dz = target["position_z"] - character["position_z"]
    dist = math.hypot(dx, dz)

    # if we’re basically at the target, don’t push
    arrive_r = character.get("arrival_radius", 0.0) or 0.0
    if dist <= arrive_r:
        return 0.0, 0.0

    # choose a target speed depending on distance
    max_v = character["max_velocity"]
    slow_r = character.get("slowing_radius", 0.0) or 0.0
    if slow_r <= 0.0 or dist > slow_r:
        target_speed = max_v
    else:
        # linearly reduce speed as we enter the slowing zone
        target_speed = max_v * (dist / slow_r)

    # target velocity points at the target with the chosen speed
    if dist > 0:
        dir_x, dir_z = dx / dist, dz / dist
    else:
        dir_x, dir_z = 0.0, 0.0
    target_vx = dir_x * target_speed
    target_vz = dir_z * target_speed

    # acceleration tries to match current vel to target vel over time_to_target
    ttt = character.get("time_to_target", 1.0) or 1.0
    ax = (target_vx - character["velocity_x"]) / ttt
    az = (target_vz - character["velocity_z"]) / ttt

    # clamp accel to max_acceleration so we don’t exceed allowed push
    a_mag = math.hypot(ax, az)
    max_a = character["max_acceleration"]
    if a_mag > max_a and a_mag > 0:
        scale = max_a / a_mag
        ax *= scale
        az *= scale

    return ax, az


# CLAMP VELOCITY
def clamp_vec(position_x, position_z, max_len):
    # shrink the vector (position_x,position_z) if it’s longer than max_len.
    # this keeps speeds under control so no one goes faster than allowed.
    mag = math.hypot(position_x, position_z)      # length of the vector
    if mag > max_len and mag > 0:
        scale = max_len / mag
        return position_x * scale, position_z * scale
    return position_x, position_z


# YUCKY PHYSICS (NEWTON-EULER-1)
def step_ne1(char, dt):
    # updates one character for one frame:
    # 1. move position forward based on current velocity
    # 2. update velocity using current acceleration
    # 3. clamp velocity to max_velocity

    # 1. position update
    char["position_x"] += char["velocity_x"] * dt
    char["position_z"] += char["velocity_z"] * dt

    # 2. velocity update
    char["velocity_x"] += char["acceleration_x"] * dt
    char["velocity_z"] += char["acceleration_z"] * dt

    # 3. cap speed
    char["velocity_x"], char["velocity_z"] = clamp_vec(char["velocity_x"], char["velocity_z"], char["max_velocity"])


# WRITE A LINE OF OUTPUT
def write_record(f, t, char):
    # every line of trajectory.txt must have 11 fields:
    # time,id,posX,posZ,velX,velZ,accelX,accelZ,orientation,behaviorCode,collision
    # (collision is always FALSE for this assignment)
    f.write(
        f"{t:.15g},{char['id']},{char['position_x']:.15g},{char['position_z']:.15g},"
        f"{char['velocity_x']:.15g},{char['velocity_z']:.15g},{char['acceleration_x']:.15g},{char['acceleration_z']:.15g},"
        f"{char['orientation']:.15g},{char['behavior']},FALSE\n"
    )


if __name__ == "__main__":
    characters = initialize_characters()
    run_sim(characters, OUTPUT_PATH)
    print("trajectory.txt saved at", OUTPUT_PATH.resolve())

    # Verify functionality.
    with open(OUTPUT_PATH) as trajectory_file:
        for i in range(5):
            print(trajectory_file.readline().strip())
