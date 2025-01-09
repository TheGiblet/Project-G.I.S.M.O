# servo_calibration.py

import time
import board
import busio
from adafruit_pca9685 import PCA9685
import config as c

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create a PCA9685 object
pca = PCA9685(i2c)
pca.frequency = c.PCA_FREQUENCY

# Servo pulse width range (you'll adjust these)
SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500

def set_servo_angle(channel, angle):
    """Sets the angle of the servo motor.

    Args:
        channel: The PCA9685 channel connected to the servo.
        angle: The desired angle in degrees (0-180).
    """
    if not 0 <= angle <= 180:
        print("Servo angle out of range (0-180)")
        return

    pulse = int(angle / 180 * (SERVO_MAX_PULSE - SERVO_MIN_PULSE) + SERVO_MIN_PULSE)
    pulse = max(min(pulse, SERVO_MAX_PULSE), SERVO_MIN_PULSE) # Keep within range
    pca.channels[channel].duty_cycle = int(pulse / 20000 * 65535)

    print(f"Servo channel {channel} angle set to {angle} degrees (pulse width: {pulse})")

def calibrate_servo(channel):
    """Calibrates the servo connected to the specified channel."""
    global SERVO_MIN_PULSE, SERVO_MAX_PULSE

    print(f"Calibrating servo on channel {channel}. Make sure the servo is not physically obstructed.")
    print("Enter 'u' to increase pulse width, 'd' to decrease, 's' to set current as a limit, 'q' to quit.")

    current_pulse = (SERVO_MAX_PULSE + SERVO_MIN_PULSE) // 2 # Start at midpoint
    current_angle = 90

    while True:
        pca.channels[channel].duty_cycle = int(current_pulse / 20000 * 65535)

        command = input("Enter command (u/d/s/q): ").lower()

        if command == 'u':
            current_pulse += 50  # Increase pulse width
            current_pulse = min(current_pulse, 2500) # Limit to maximum
        elif command == 'd':
            current_pulse -= 50  # Decrease pulse width
            current_pulse = max(current_pulse, 500)  # Limit to minimum
        elif command == 's':
            limit_type = input("Set as minimum (min) or maximum (max)? ").lower()
            if limit_type == 'min':
                SERVO_MIN_PULSE = current_pulse
                print(f"Minimum pulse width set to: {SERVO_MIN_PULSE}")
            elif limit_type == 'max':
                SERVO_MAX_PULSE = current_pulse
                print(f"Maximum pulse width set to: {SERVO_MAX_PULSE}")
            else:
                print("Invalid limit type.")
        elif command == 'q':
            print("Exiting calibration.")
            break
        else:
            print("Invalid command.")

        current_angle = int((current_pulse - SERVO_MIN_PULSE) / (SERVO_MAX_PULSE - SERVO_MIN_PULSE) * 180)
        print(f"Current pulse: {current_pulse}, Estimated angle: {current_angle}")

def main():
    """Allows manual control of the servos for calibration."""
    print("Servo Calibration Program")
    print("Make sure your servos are connected to the PCA9685 board.")

    while True:
        command = input("Enter 'calibrate' followed by the channel number (e.g., calibrate 0), 'set' followed by channel and angle (e.g., set 0 90), or 'q' to quit: ")

        if command.startswith("calibrate"):
            try:
                channel = int(command.split()[1])
                if 0 <= channel <= 15:
                    calibrate_servo(channel)
                else:
                    print("Invalid channel number. Must be between 0 and 15.")
            except (IndexError, ValueError):
                print("Invalid command format. Use 'calibrate <channel>'.")
        elif command.startswith("set"):
            try:
                _, channel, angle = command.split()
                channel = int(channel)
                angle = int(angle)
                if 0 <= channel <= 15:
                    set_servo_angle(channel, angle)
                else:
                    print("Invalid channel number. Must be between 0 and 15.")
            except (IndexError, ValueError):
                print("Invalid command format. Use 'set <channel> <angle>'.")
        elif command.lower() == 'q':
            print("Exiting program.")
            pca.deinit()
            break
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()