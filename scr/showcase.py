#showcase.py

import time
import robot as rc
import movement as m
import config as c
import rgb_led as led
import buzzer as b
import touch_sensor as t
import sound_sensor as s
import servo_control as sc
import dead_reckoning as dr
import random
import sys
import select

# --- Code Functions ---
# This program is designed to showcase the capabilities of the Gismo robot.
# It allows Gismo to wander autonomously, avoid obstacles and edges,
# react to touch and sound, and execute specific actions based on user commands.
# This script integrates various control modules for movement, sensors, feedback, and servos,
# along with dead reckoning for position and heading estimation.

# --- Helper Functions ---

def react_to_sound(pca, rgb_led_instance):
    """Makes the robot react to sound by turning, moving, and playing a tune."""
    print("Sound detected! Reacting...")
    movement.turn_left_in_place(duration=c.MOVEMENT_SETTINGS["TURN_DURATION"] * 2)
    movement.move_forward(speed=c.MOVEMENT_SETTINGS["FORWARD_SPEED"])
    rgb_led_instance.set_emotion("surprised")
    b.buzzer.play_custom_tune(b.TUNE_IMPERIAL_MARCH)  # Play the tune
    time.sleep(0.5)
    movement.stop_all_motors()
    rgb_led_instance.set_emotion("neutral")

def wiggle(pca, rgb_led_instance, duration=0.5, speed=0.7):
    """Makes the robot wiggle for a short duration."""
    movement.turn_left_in_place(duration / 2)
    movement.turn_right_in_place(duration / 2)

def handle_command(command, pca, rgb_led_instance, movement, dead_reckoning):
    """Handles commands entered by the user."""
    command = command.lower()
    if command == "forward":
        movement.move_forward()
    elif command == "backward":
        movement.move_backward()
    elif command == "left":
        movement.turn_left_in_place()
    elif command == "right":
        movement.turn_right_in_place()
    elif command == "stop":
        movement.stop_all_motors()
    elif command == "wiggle":
        wiggle(pca, rgb_led_instance)
    elif command == "happy":
        rgb_led_instance.set_emotion("happy")
    elif command == "sad":
        rgb_led_instance.set_emotion("sad")
    elif command == "angry":
        rgb_led_instance.set_emotion("angry")
    elif command == "surprised":
        rgb_led_instance.set_emotion("surprised")
    elif command == "searching":
        rgb_led_instance.set_emotion("searching")
    elif command == "neutral":
        rgb_led_instance.set_emotion("neutral")
    elif command == "arms up":
        sc.raise_arms(pca)
    elif command == "arms down":
        sc.lower_arms(pca)
    elif command == "head up":
        sc.move_head_up(pca)
    elif command == "head down":
        sc.move_head_down(pca)
    elif command == "head center":
        sc.move_head_center(pca)
    elif command == "play tune":
        b.buzzer.play_custom_tune(b.TUNE_IMPERIAL_MARCH)
    elif command == "get position":
        position = dead_reckoning.get_position()
        heading = dead_reckoning.get_heading()
        print(f"Position (X, Y): ({position[0]:.2f}, {position[1]:.2f}), Heading: {heading:.2f} degrees")
    elif command == "help":
        print("Available commands: forward, backward, left, right, stop, wiggle, happy, sad, angry, surprised, searching, neutral, arms up, arms down, head up, head down, head center, play tune, get position, help, exit, start, stop")
    elif command == "exit":
        raise KeyboardInterrupt
    else:
        print("Invalid command.")

# --- Main Program ---

if __name__ == "__main__":
    try:
        rc.initialize_pca()
        rc.initialize_edge_sensors()
        b.initialize_buzzer()
        t.initialize_touch_sensor()
        s.initialize_sound_sensor()
        sc.initialize_servos(rc.pca)
        rgb_led_instance = led.RGBLed(rc.pca)
        movement = m.Movement(rc.pca)
        dead_reckoning = dr.DeadReckoning()
        b.buzzer.play_startup_sound()
        sc.test_servos(rc.pca)
        rgb_led_instance.test()

        last_update = time.time()
        last_turn = time.time()

        # Robot starts in wandering mode
        wandering = True
        print("Gismo is in wandering mode. Press Enter to start command mode.")

        while True:
            if wandering:
                dead_reckoning.update()
                current_time = time.time()

                distance = rc.get_distance()
                left_edge, right_edge = rc.read_edge_sensors()
                sound_detected = s.is_sound_detected()

                # Print dead reckoning information every second
                if current_time - last_update >= 1.0:
                    position = dead_reckoning.get_position()
                    heading = dead_reckoning.get_heading()
                    print(f"Position (X, Y): ({position[0]:.2f}, {position[1]:.2f}), Heading: {heading:.2f} degrees")
                    last_update = current_time

                # Check for sound
                if sound_detected:
                    react_to_sound(rc.pca, rgb_led_instance)

                # Obstacle avoidance
                if distance < c.MOVEMENT_SETTINGS["OBSTACLE_DISTANCE"]:
                    print("Obstacle detected!")
                    movement.stop_all_motors()
                    sc.raise_arms(rc.pca)
                    time.sleep(0.5)
                    sc.move_head_up(rc.pca)
                    rgb_led_instance.set_emotion("surprised")
                    b.buzzer.play_obstacle_sound()
                    time.sleep(0.5)
                    sc.move_head_center(rc.pca)
                    sc.lower_arms(rc.pca)
                    # Turn to a random direction after encountering an obstacle
                    if random.choice([True, False]):
                        movement.turn_left_in_place(duration=c.MOVEMENT_SETTINGS["TURN_DURATION"])
                    else:
                        movement.turn_right_in_place(duration=c.MOVEMENT_SETTINGS["TURN_DURATION"])

                # Edge avoidance
                elif left_edge == 1:
                    print("Left edge detected! Turning right...")
                    movement.turn_right_in_place(duration=c.MOVEMENT_SETTINGS["TURN_DURATION"])
                    rgb_led_instance.set_emotion("angry")
                    b.buzzer.play_edge_sound()

                elif right_edge == 1:
                    print("Right edge detected! Turning left...")
                    movement.turn_left_in_place(duration=c.MOVEMENT_SETTINGS["TURN_DURATION"])
                    rgb_led_instance.set_emotion("angry")
                    b.buzzer.play_edge_sound()

                else:
                    # Continue moving forward
                    movement.motor_right.set_speed(c.MOVEMENT_SETTINGS["FORWARD_SPEED"])
                    movement.motor_left.set_speed(c.MOVEMENT_SETTINGS["FORWARD_SPEED"])
                    rgb_led_instance.set_emotion("searching")

            # Check for user input without blocking
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                command = sys.stdin.readline().strip()
                if command == 'exit':
                    raise KeyboardInterrupt
                elif command == 'stop':
                    wandering = False
                    movement.stop_all_motors()
                    rgb_led_instance.set_emotion("neutral")
                    print("Entering command mode. Type 'start' to resume wandering.")
                elif command == 'start':
                    wandering = True
                    rgb_led_instance.set_emotion("searching")
                    print("Resuming wandering...")
                else:
                    if not wandering:
                        handle_command(command, rc.pca, rgb_led_instance, movement, dead_reckoning)
                    else:
                        print("Command ignored in wandering mode. Type 'stop' to enter command mode.")

            time.sleep(0.1)  # Adjust timing as needed

    except KeyboardInterrupt:
        print("Stopping motors and exiting...")
        movement.stop_all_motors()
        rgb_led_instance.set_color(*c.LED_COLORS["OFF"])
        b.buzzer.play_shutdown_sound()

    finally:
        rc.cleanup(rc.pca, rgb_led_instance)