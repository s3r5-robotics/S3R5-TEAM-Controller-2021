import adafruit_bno055
import serial
import time

class BNO055:
    def __init__(self) -> None:
        self.uart = serial.Serial("/dev/serial0")
        self.bno = adafruit_bno055.BNO055_UART(self.uart)
        pass

    def sanity_check(self):
        print("BNO055 - sanity check - STARTED")
        while True:
            try:
                if not self.bno.euler:
                    raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')
                break
            except Exception as e:
                print("Got error: {}".format(e))
                print("Sleeping 1s before retrying")
                time.sleep(1)
        print("BNO055 - sanity check - COMPLETE")

    def euler(self):
        try:
            return self.bno.euler[0]
        except RuntimeError:
            return self.euler()

    def debug(self):
        try:
            print("Accelerometer (m/s^2): {}".format(self.bno.acceleration))
            print("Magnetometer (microteslas): {}".format(self.bno.magnetic))
            print("Gyroscope (rad/sec): {}".format(self.bno.gyro))
            print("Euler angle: {}".format(self.bno.euler))
            print("Quaternion: {}".format(self.bno.quaternion))
            print("Linear acceleration (m/s^2): {}".format(self.bno.linear_acceleration))
            print("Gravity (m/s^2): {}".format(self.bno.gravity))
        except RuntimeError:
            return self.debug()