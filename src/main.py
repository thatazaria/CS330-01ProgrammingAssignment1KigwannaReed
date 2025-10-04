# Project: CS 330
# Program: Programming Assignment 1 (Dynamic Movements Continue, Seek, Flee, and Arrive)
# Purpose: Implement the dynamic movements Continue, Seek, Flee, and Arrive.
# Authors: Rebecca N. Kigwanna and Azaria A. Reed

import math
from pathlib import Path

# Initialize simulation settings.
DT = 0.5 # Each update advances the clock by half a second.
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
                ne1_update(character, DT) # Update accordingly with physics.
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
    
    return 0.0, 0.0

# Continue.
def continue_behavior(character, characters):
    return 0.0, 0.0 # Maintains current velocity

# Flee.
def flee_behavior(character, characters):
    # Find target.
    target_id = 2600 + character["target"]
    target = next((char for char in characters if char["id"] == target_id), None)
    if not target:
        return 0.0, 0.0

    # Find direction.
    dx = character["position_x"] - target["position_x"]
    dz = character["position_z"] - target["position_z"]
    distance = math.hypot(dx, dz)

    # Multiply the normalized distance by the maximum acceleration to output linear acceleration.
    if distance > 0:
        acceleration_x = (dx / distance) * character["max_acceleration"]
        acceleration_z = (dz / distance) * character["max_acceleration"]
        return acceleration_x, acceleration_z
    return 0.0, 0.0

# Seek.
def seek_behavior(character, characters):
    # Find target.
    target_id = 2600 + character["target"]
    target = next((char for char in characters if char["id"] == target_id), None)
    if not target:
        return 0.0, 0.0

    # Find direction.
    dx = target["position_x"] - character["position_x"]
    dz = target["position_z"] - character["position_z"]
    distance = math.hypot(dx, dz)

    # Multiply the normalized distance by the maximum acceleration to output linear acceleration.
    if distance > 0:
        acceleration_x = (dx / distance) * character["max_acceleration"]
        acceleration_z = (dz / distance) * character["max_acceleration"]
        return acceleration_x, acceleration_z
    return 0.0, 0.0

# Arrive.
def arrive_behavior(character, characters):
    # Find target.
    target_id = 2600 + character["target"]
    target = next((char for char in characters if char["id"] == target_id), None)
    if not target:
        return 0.0, 0.0

    # Find distance to target.
    dx = target["position_x"] - character["position_x"]
    dz = target["position_z"] - character["position_z"]
    distance = math.hypot(dx, dz)
    
    # Maintain current velocity if at target.
    arrive_radius = character.get("arrival_radius", 0.0) or 0.0
    time_to_target = character.get("time_to_target", 1.0) or 1.0
    if distance <= arrive_radius:
        velocity_x, velocity_z = character["velocity_x"], character["velocity_z"]
        speed = math.hypot(velocity_x, velocity_z)
        
        if speed < 1e-6:
            return 0.0, 0.0

        acceleration_x = -velocity_x / time_to_target
        acceleration_z = -velocity_z / time_to_target
        if distance > 0:
            direction_x, direction_z = dx / distance, dz / distance
            nudge = 0.1 * character["max_acceleration"]
            acceleration_x += nudge * direction_x
            acceleration_z += nudge * direction_z	

        acceleration_magnitude = math.hypot(acceleration_x, acceleration_z)
        if acceleration_magnitude > character["max_acceleration"] and acceleration_magnitude > 0:
            scale = character["max_acceleration"] / acceleration_magnitude
            acceleration_x *= scale
            acceleration_z *= scale
            
        return acceleration_x, acceleration_z

    # If outside slow radius, set targetSpeed = maxSpeed. If inside slow radius, set targetSpeed proportional to distance.
    slow_radius = character.get("slowing_radius", 0.0) or 0.0
    if slow_radius <= 0.0 or distance > slow_radius:
        target_speed = character["max_velocity"]
    else:
        target_speed = character["max_velocity"] * (distance / slow_radius)

    # Accelerate toward that targetSpeed.
    if distance > 0:
        direction_x, direction_z = dx / distance, dz / distance
    else:
        direction_x, direction_z = 0.0, 0.0
    target_velocity_x = direction_x * target_speed
    target_velocity_z = direction_z * target_speed
    acceleration_x = (target_velocity_x - character["velocity_x"]) / time_to_target
    acceleration_z = (target_velocity_z - character["velocity_z"]) / time_to_target

    # Regulate acceleration.
    acceleration_magnitude = math.hypot(acceleration_x, acceleration_z)
    if acceleration_magnitude > character["max_acceleration"] and acceleration_magnitude > 0:
        scale = character["max_acceleration"] / acceleration_magnitude
        acceleration_x *= scale
        acceleration_z *= scale

    return acceleration_x, acceleration_z

# Write a record.
def write_record(file, time, character):
    file.write(
        f"{time:.15g},{character['id']},{character['position_x']:.15g},{character['position_z']:.15g},"
        f"{character['velocity_x']:.15g},{character['velocity_z']:.15g},{character['acceleration_x']:.15g},{character['acceleration_z']:.15g},"
        f"{character['orientation']:.15g},{character['behavior']},FALSE\n"
    )


# Update with Newton-Euler-1 integration update algorithm.
def ne1_update(character, dt):
    # updates one character for one frame:
    # 1. move position forward based on current velocity
    # 2. update velocity using current acceleration
    # 3. clamp velocity to max_velocity

    # Update position.
    character["position_x"] += character["velocity_x"] * dt
    character["position_z"] += character["velocity_z"] * dt

    # Update velocity.
    character["velocity_x"] += character["acceleration_x"] * dt
    character["velocity_z"] += character["acceleration_z"] * dt

    # Regulate speed.
    character["velocity_x"], character["velocity_z"] = clamp_velocity(character["velocity_x"], character["velocity_z"], character["max_velocity"])


# Regulate velocity.
def clamp_velocity(position_x, position_z, max_length):
    magnitude = math.hypot(position_x, position_z)      
    if magnitude > max_length and magnitude > 0:
        scale = max_length / magnitude
        return position_x * scale, position_z * scale
    return position_x, position_z


if __name__ == "__main__":
    characters = initialize_characters()
    run_sim(characters, OUTPUT_PATH)
    print("trajectory.txt saved at", OUTPUT_PATH.resolve())

    # Verify functionality.
    with open(OUTPUT_PATH) as trajectory_file:
        for i in range(5):
            print(trajectory_file.readline().strip())
