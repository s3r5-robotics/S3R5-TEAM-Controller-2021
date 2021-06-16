# region Imports
import logging
import os
import sys
import time

import RPi.GPIO as GPIO
import serial
from mlx90614 import MLX90614
from smbus2 import SMBus
import bno055

# endregion Imports

# region Serial communication codes
ROGER_THAT = b"!"
STOP = b"%"
CONTINUE = b"*"
INTERRUPT_ROGER = b"^"
ROTATION_COMPLETED = b"@"
REQUEST_FOR_LEFT_ROTATION = b"#"
REQUEST_FOR_RIGHT_ROTATION = b"$"
START = b"&"
BACKWARDS = b"("
# endregion Serial communication codes

# TODO: Change this
POWER_BUTTON = 3
LDR = 5

OPENMV_P0_1 = 26
OPENMV_P1_1 = 19
OPENMV_P2_1 = 20
OPENMV_P3_1 = 16

OPENMV_P0_2 = 13
OPENMV_P1_2 = 6
OPENMV_P2_2 = 12
OPENMV_P3_2 = 7

# region Systems
serial_arduino = None
bno = None
bus = SMBus(1)
# endregion Systems

power_bool = True

VICTIM_LED = 22
SERVO_PIN = 18

# region Command args
if len(sys.argv) == 2 and sys.argv[1].lower() == "-v":
    logging.basicConfig(level=logging.DEBUG)
# endregion Command args

thermal_sensor1 = MLX90614(bus, address=0x5A)
thermal_sensor2 = MLX90614(bus, address=0x6A)

GPIO.setmode(GPIO.BCM)

# region Systems initialization
def initialize_arduino():
    global serial_arduino
    print("Arduino - initialization")
    for i in range(0, 100):
        try:
            for _, _, files in os.walk("/dev/"):
                for filename in files:
                    if filename[:7] == "ttyAMA3":
                        print(filename)
                        tty_num = filename
            serial_arduino = serial.Serial("/dev/" + tty_num, 115200)
        except TypeError:
            print("No Arduino found")
            time.sleep(1)
            continue
        break

    serial_arduino.setDTR(False)
    time.sleep(1)
    serial_arduino.flushInput()
    serial_arduino.setDTR(True)
    print("Arduino - initialized")


# endregion Systems initialization


def wait_for_char(wanted_char):
    received_char = serial_arduino.read()
    while received_char != wanted_char:
        received_char = serial_arduino.read()
    print("received " + str(wanted_char) + "\n")


def wait_for_anything():
    received_char = serial_arduino.read()
    print("received " + str(received_char) + "\n")
    return received_char


def flip_rotation(angle):
    if angle > 360:
        angle -= 360
    elif angle < 0:
        angle += 360
    return angle


def rotation(rotation_direction):
    print("Rotation " + rotation_direction)
    while True:
        try:
            flipped_yaw = int(bno.euler())
            print("Initial yaw: " + str(flipped_yaw))
            if rotation_direction == "left":
                target_yaw = flipped_yaw - 90
            else:
                target_yaw = flipped_yaw + 90

            target_yaw = flip_rotation(target_yaw)

            target_yaw = round(target_yaw / 90) * 90
            target_yaw -= 20
            print("Target yaw: " + str(target_yaw))
            serial_arduino.write(ROGER_THAT)
            while not ((target_yaw - 5) <= flipped_yaw <= (target_yaw + 5)):
                print(flipped_yaw)
                flipped_yaw = int(bno.euler())
            break
        except TypeError:
            print("Caught None retrying")
            continue

    print(rotation_direction + "rotation completed")
    serial_arduino.write(ROTATION_COMPLETED)
    wait_for_char(ROGER_THAT)


def set_angle(angle):
    global pwm
    duty = angle / 18 + 2
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.3)
    pwm.ChangeDutyCycle(0)


def right_packet():
    time.sleep(0.3)
    set_angle(0)
    time.sleep(0.4)
    set_angle(90)
    time.sleep(0.4)


def left_packet():
    time.sleep(0.3)
    set_angle(180)
    time.sleep(0.4)
    set_angle(90)
    time.sleep(0.4)


def dispense_victims(side, number):
    for i in range(0, number):
        if side == 0:
            left_packet()
            pass
        else:
            right_packet()
            pass


def signaling_victim():
    print("Signaling victim")
    for i in range(0, 2):
        GPIO.output(VICTIM_LED, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(VICTIM_LED, GPIO.LOW)
        time.sleep(1)
    GPIO.output(VICTIM_LED, GPIO.HIGH)
    time.sleep(1)
    serial_arduino.write(CONTINUE)
    wait_for_char(INTERRUPT_ROGER)


def handle_dispenzing(array, side):
    signaling_victim()

    # side
    # 0 - left
    # 1 - right

    # S
    if array == [0, 0, 1]:
        dispense_victims(side, 3)
    # U
    elif array == [0, 1, 0]:
        dispense_victims(side, 2)
    # H
    elif array == [0, 1, 1]:
        pass
    # Y
    elif array == [1, 0, 0]:
        dispense_victims(side, 1)
    # G
    elif array == [1, 0, 1]:
        pass
    # R
    elif array == [1, 1, 0]:
        dispense_victims(side, 1)


def check_openmv():
    gpio_cam_P6 = [GPIO.input(6), GPIO.input(19)]
    gpio_cam_P7 = [GPIO.input(13), GPIO.input(26)]
    gpio_cam_P8 = [GPIO.input(12), GPIO.input(16)]
    gpio_cam_P9 = [GPIO.input(1), GPIO.input(20)]

    for i in range(2):
        if gpio_cam_P6[i] == GPIO.HIGH:
            stop_servos()
            handle_dispenzing([gpio_cam_P7[i], gpio_cam_P8[i], gpio_cam_P9[i]], i)


def check_photoresistor():
    if GPIO.input(LDR) == 0:
        stop_servos()
        backwards()
        while GPIO.input(LDR) == 0:
            pass
        stop_servos()


def check_thermal_sensor():
    temperature1 = thermal_sensor1.get_object_1()
    temperature2 = thermal_sensor2.get_object_1()
    if temperature1 > 28 or temperature2 > 28:
        stop_servos()
        if temperature1 > 28:
            dispense_victims(1, 0)
        else:
            dispense_victims(1, 1)
        signaling_victim()


def backwards():
    serial_arduino.write(BACKWARDS)
    wait_for_char(ROGER_THAT)


def stop_servos():
    serial_arduino.write(STOP)
    wait_for_char(ROGER_THAT)


def power_button_callback():
    global power_bool
    power_bool = not power_bool


GPIO.setup(LDR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VICTIM_LED, GPIO.OUT)
GPIO.setup(POWER_BUTTON, GPIO.IN)

GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(2.1)

GPIO.add_event_detect(
    POWER_BUTTON, GPIO.RISING, callback=power_button_callback, bouncetime=300
)

print("Sleeping for 9 seconds")
time.sleep(9)
print("Woke up from 9 seconds")

bno = bno055.BNO055()

time.sleep(4)
initialize_arduino()
bno.sanity_check()
bno.debug()

serial_arduino.write(START)
print("Sent START")
wait_for_char(ROGER_THAT)
print("Got ROGER_THAT")
serial_arduino.flushInput()

# region Communication event loop
try:
    while power_bool:
        print("Loop started")
        while serial_arduino.inWaiting() == 0:
            pass
        if serial_arduino.inWaiting() > 0:
            print("Got character")
            answer = serial_arduino.readline()
            print(answer)
            answer = answer.replace(b"\r\n", b"")
            print("CHARACTER RECEIVED: " + str(answer))
            if answer == REQUEST_FOR_LEFT_ROTATION:
                rotation("left")
            elif answer == REQUEST_FOR_RIGHT_ROTATION:
                rotation("right")
            serial_arduino.flushInput()
# endregion Communication event loop

except KeyboardInterrupt:
    print("\nSerial finishing")
    serial_arduino.close()
    set_angle(90)
    GPIO.cleanup()
    initialize_arduino()
    bus.close()
