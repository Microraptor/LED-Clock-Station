# !/usr/bin/env python
"""
A LED Clock Station equipped with various sensors and displays

Usage: sudo python clock_station.py start
Written for the Raspberry Pi Revision 1.
Author: Till Runge
"""

# Standard libraries
import datetime
import logging
from PIL import Image
import signal
import smbus
import subprocess
import threading
import time

# Downloaded libraries
from daemon import runner

# Hardware libraries, comment out all modules not used
import Adafruit_DHT
import Adafruit_SSD1306
import neopixel
import PCF_CharLCD
import rotary_class
import RPi.GPIO as GPIO

# Enable/disable hardware
LED_ENABLED = True
LCD_ENABLED = True
DISP_ENABLED = True
ROTARY_ENABLED = True
DHT_ENABLED = True
LIGHT_ENABLED = True
PIR_ENABLED = True

# Hardware constants (BCM-GPIO pin layout)
I2C_BUS = 0  # 0 for Rev 1 and 1 for older RPI
LED_COUNT = 60  # Number of LED pixels
LED_CLOCKWISE = False  # If the strip is enumerated clockwise
LED_TOP = 43  # The number of the LED which is on the very top
LED_PIN = 18  # Has to support PWM (only pin 18 on RPI Rev 1)
LED_FREQ_HZ = 800000  # Signal frequency in hertz (usually 800000)
LED_DMA = 5  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 16  # 0 darkest; 255 brightest
LED_INVERT = False  # True to invert the pin signal
LCD_ADDRESS = 0x27  # Try 0x27
LCD_COLUMNS = 20  # Usually 16 or 20
LCD_ROWS = 4  # Usually 2 or 4
ROTARY_PIN_A = 22
ROTARY_PIN_B = 21
ROTARY_BUTTON_PIN = 17
DHT_PIN = 23
LIGHT_ADDRESS = 0x23  # Try 0x23
LIGHT_MODE = 0x20  # 0.5lx mode 0x20; 1lx mode: 0x21; low res mode: 0x23
PIR_PIN = 24

# Misc settings
SECONDS_ENABLED = True
DHT_POLL_TIME = 30.0  # In Seconds
LIGHT_POLL_TIME = 30.0  # In Seconds
PIR_POLL_TIME = 30.0  # In Seconds
LOW_HOUR_BRIGHTNESS = 16  # 0 darkest; 255 brightest
HIGH_HOUR_BRIGHTNESS = 128  # 0 darkest; 255 brightest


class ThreadLoop(threading.Thread):
    """This thread executes the target function every specified seconds"""

    def __init__(self, time_offset, time_increment, target, stop_event):
        """The constructor which assigns attributes"""

        threading.Thread.__init__(self)

        self._next_call = time_offset + time.time()
        self._time_increment = time_increment
        self._target = target
        self._stop_event = stop_event

        # Flag thread as daemon, so it stops when the main thread stops
        self.daemon = True

    def run(self):
        """Repeatedly calls the target until the stop event is triggered"""

        # while loop only true if event true and false fi timeout
        while not self._stop_event.wait(self._next_call - time.time()):
            self._target()
            self._next_call = self._next_call + self._time_increment


class ClockStationDaemon(object):
    """Daemon class to run the Clock Station in the background"""

    def __init__(self):
        """The constructor which assigns attributes"""

        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = '/var/run/clockStation.pid'
        self.pidfile_timeout = 5

        # Define events and locks
        self.stop_flag = threading.Event()
        self.locks = {
            'led': threading.Lock(),
            'lcd': threading.Lock(),
            'disp': threading.Lock(),
            'dht': threading.Lock(),
            'light': threading.Lock(),
            'pir': threading.Lock(),
            'disp': threading.Lock(),
        }

    def message(self, message="", level="info"):
        """This function routes out messages to info, warn or error"""

        # Print to stdout
        print(message)

        # Save to log
        if level == 'info':
            logger.info(message)
        if level == 'warn':
            logger.warn(message)
        if level == 'error':
            logger.error(message)

    def run(self):
        """Creates objects, threads and is running the show"""

        # Initalize hardware
        GPIO.setmode(GPIO.BCM)

        if LED_ENABLED:
            self.locks['led'].acquire()
            self.led_strip = neopixel.Adafruit_NeoPixel(
                LED_COUNT,
                LED_PIN,
                LED_FREQ_HZ,
                LED_DMA,
                LED_INVERT,
                LED_BRIGHTNESS
            )
            self.led_strip.begin()
            self.locks['led'].release()
            # 2D array for storing color channels of each LED
            self.led_array = [[0 for x in range(3)] for y in range(60)]

        if LCD_ENABLED:
            self.locks['lcd'].acquire()
            self.lcd = PCF_CharLCD.PCF_CharLCD(
                0,
                address=LCD_ADDRESS,
                busnum=I2C_BUS,
                cols=LCD_COLUMNS,
                lines=LCD_ROWS
            )
            self.lcd.enable_display(True)
            self.lcd.set_backlight(1)
            self.lcd.clear()
            self.lcd.home()
            self.lcd.create_char(1, [7, 5, 7, 0, 0, 0, 0, 0])  # Degree symbol
            self.locks['lcd'].release()

        if DISP_ENABLED:
            self.locks['disp'].acquire()
            self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=0)
            self.disp.begin()
            self.disp.clear()
            self.disp.display()
            self.locks['disp'].release()

        if ROTARY_ENABLED:
            rotary_class.RotaryEncoder(
                ROTARY_PIN_A,
                ROTARY_PIN_B,
                ROTARY_BUTTON_PIN,
                self.rotary_event
            )

        if LIGHT_ENABLED:
            self.i2c_bus = smbus.SMBus(I2C_BUS)

        if PIR_ENABLED:
            GPIO.setup(PIR_PIN, GPIO.IN)

        self.message("Clock Station started!")
        self.startup()

        # Create times
        self.second = datetime.datetime.now().second
        self.minute = datetime.datetime.now().minute
        self.hour = datetime.datetime.now().hour

        minute_offset = 60 - self.second
        hour_offset = ((60 - self.minute) * 60 - minute_offset)
        day_offset = (24 - self.hour) * 3600 - hour_offset
        week_offset = (24 - datetime.datetime.now().day) * 86400 - day_offset

        if self.hour > 12:  # Put in 12h format
            self.hour = self.hour - 12

        # Run current time once
        if LED_ENABLED:
            self.locks['led'].acquire()
            self.led_overlay(self.second, 0, 255, 0)
            self.led_overlay(self.minute, 255, 0, 0)
            self.led_overlay(self.hour * 5, 0, 0, 255)
            self.led_strip.show()
            self.locks['led'].release()
        self.on_day()
        self.on_week()
        self.show_date()

        # Create thread loops
        thread_second = ThreadLoop(
            0,
            1.0,
            self.on_second,
            self.stop_flag)
        thread_minute = ThreadLoop(
            minute_offset,
            60.0,
            self.on_minute,
            self.stop_flag)
        thread_hour = ThreadLoop(
            hour_offset,
            3600.0,
            self.on_hour,
            self.stop_flag)
        thread_day = ThreadLoop(
            day_offset,
            86400.0,
            self.on_day,
            self.stop_flag)
        thread_week = ThreadLoop(
            week_offset,
            604800.0,
            self.on_week,
            self.stop_flag)
        thread_dht = ThreadLoop(
            0,
            DHT_POLL_TIME,
            self.show_dht,
            self.stop_flag)
        thread_light = ThreadLoop(
            0,
            LIGHT_POLL_TIME,
            self.show_light,
            self.stop_flag)
        thread_pir = ThreadLoop(
            0,
            PIR_POLL_TIME,
            self.show_pir,
            self.stop_flag)
        thread_date = ThreadLoop(
            minute_offset,
            60.0,
            self.show_date,
            self.stop_flag)

        # Start the thread loops
        if LED_ENABLED:
            if SECONDS_ENABLED:
                thread_second.start()
            thread_minute.start()
            thread_hour.start()
        thread_day.start()
        thread_week.start()
        if LCD_ENABLED and DHT_ENABLED:
            thread_dht.start()
        if LCD_ENABLED and LIGHT_ENABLED:
            thread_light.start()
        if LCD_ENABLED and PIR_ENABLED:
            thread_pir.start()
        if LCD_ENABLED:
            thread_date.start()

        # Wait until termination
        signal.pause()
        self.message("Clock Station shutdown!")

        # Turn everything off
        if DISP_ENABLED:
            self.locks['disp'].acquire()
            self.disp.clear()
            self.disp.display()
            self.locks['disp'].release()

        if LCD_ENABLED:
            self.locks['lcd'].acquire()
            self.lcd.home()
            self.lcd.clear()
            self.lcd.set_backlight(0)
            self.lcd.enable_display(False)
            self.locks['lcd'].release()

        if LED_ENABLED:
            self.locks['led'].acquire()
            for i in range(self.led_strip.numPixels()):
                self.led_strip.setPixelColorRGB(i, 0, 0, 0)
            self.led_strip.show()
            self.locks['led'].release()

        GPIO.cleanup()

    def startup(self):
        """Startup animation and clock setup"""

        if DISP_ENABLED:
            self.locks['disp'].acquire()
            image = Image.open('/home/pi/scripts/dragon.png').resize(
                (self.disp.width, self.disp.height),
                Image.ANTIALIAS).convert('1')
            self.disp.image(image)
            self.disp.display()
            self.locks['disp'].release()

        if LED_ENABLED:
            self.locks['led'].acquire()
            # Startup circle animation
            for i in range(60):
                self.led_strip.setPixelColorRGB(self.led_pixel(i), 255, 0, 0)
                self.led_strip.show()
                time.sleep(0.02)
            # Clock outline
            for i in range(60):
                if i % 5 == 0:  # Hours
                    if i % 15 == 0:
                        self.led_array[self.led_pixel(i)][
                            0] = HIGH_HOUR_BRIGHTNESS
                        self.led_array[self.led_pixel(i)][
                            1] = HIGH_HOUR_BRIGHTNESS
                        self.led_array[self.led_pixel(i)][
                            2] = HIGH_HOUR_BRIGHTNESS
                    else:
                        self.led_array[self.led_pixel(i)][
                            0] = LOW_HOUR_BRIGHTNESS
                        self.led_array[self.led_pixel(i)][
                            1] = LOW_HOUR_BRIGHTNESS
                        self.led_array[self.led_pixel(i)][
                            2] = LOW_HOUR_BRIGHTNESS
                else:
                    self.led_array[self.led_pixel(i)][0] = 0
                    self.led_array[self.led_pixel(i)][1] = 0
                    self.led_array[self.led_pixel(i)][2] = 0
                self.led_strip.setPixelColorRGB(
                    self.led_pixel(i),
                    self.led_array[self.led_pixel(i)][0],
                    self.led_array[self.led_pixel(i)][1],
                    self.led_array[self.led_pixel(i)][2],
                )
                self.led_strip.show()
                time.sleep(0.02)
            self.locks['led'].release()

    def on_second(self):
        """This function is started in its own thread each second"""

        self.locks['led'].acquire()
        self.led_overlay(self.second, 0, 255, 0, substract=True)
        self.second = (self.second + 1) % 60
        self.led_overlay(self.second, 0, 255, 0)
        self.led_strip.show()
        self.locks['led'].release()

    def on_minute(self):
        """This function is started in its own thread each minute"""

        self.locks['led'].acquire()
        self.led_overlay(self.minute, 255, 0, 0, substract=True)
        self.minute = (self.minute + 1) % 60
        self.led_overlay(self.minute, 255, 0, 0)
        self.led_strip.show()
        self.locks['led'].release()

    def on_hour(self):
        """This function is started in its own thread each hour"""

        self.locks['led'].acquire()
        self.led_overlay(self.hour * 5, 0, 0, 255, substract=True)
        self.hour = (self.hour + 1) % 12
        self.led_overlay(self.hour * 5, 0, 0, 255)
        self.led_strip.show()
        self.locks['led'].release()

    def on_day(self):
        """This function is started in its own thread each day"""

    def on_week(self):
        """This function is started in its own thread each week"""

    def show_dht(self):
        """Started in its own thread to read and display the DHT sensor"""

        self.locks['dht'].acquire()
        humidity, temperature = Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22, DHT_PIN)
        self.locks['dht'].release()
        if humidity is not None and temperature is not None:
            self.lcd_line(0, str(temperature)[:4] + "\x01C - " + str(
                humidity)[:4] + "% humid")
        else:
            self.lcd_line(0, "DHT reading failed!")

    def show_light(self):
        """Started in its own thread to read and display the light sensor"""

        light_intensity = str(self.read_light())[:5]
        self.lcd_line(1, "Brightness: " + light_intensity + " lx")

    def show_pir(self):
        """Started in its own thread to read and display the PIR sensor"""

        self.locks['pir'].acquire()
        i = GPIO.input(PIR_PIN)
        self.locks['pir'].release()
        motion = "no"
        if i == 0:
            motion = "yes"
        self.lcd_line(2, "Motion: " + motion)

    def show_date(self):
        """Started in its own thread to read and display the date"""

        self.lcd_line(3, datetime.datetime.now().strftime('%H:%M %A %d.%m.'))

    def rotary_event(self, event):
        """Handles rotary switch events"""

        if event == rotary_class.RotaryEncoder.CLOCKWISE:
            self.message("Clockwise")
        elif event == rotary_class.RotaryEncoder.ANTICLOCKWISE:
            self.message("Anticlockwise")
        elif event == rotary_class.RotaryEncoder.BUTTONDOWN:
            self.cleanup()
            subprocess.Popen(["sudo", "halt"])
        return

    def read_light(self):
        """Reads from an I2C light intensity sensor and returns the lux"""

        self.locks['light'].acquire()
        data = self.i2c_bus.read_i2c_block_data(LIGHT_ADDRESS, LIGHT_MODE)
        self.locks['light'].release()
        return ((data[1] + (256 * data[0])) / 1.2)

    def lcd_line(self, row, message, left_align=True):
        """Writes a message on a LCD line"""

        # In case the row number is too high start at the beginning
        row = row % LCD_ROWS

        #  Write blank to extra characters and truncate to row length
        if left_align:
            message = message + "                    "
            message = message[:LCD_COLUMNS]
        else:
            message = "                    " + message
            message = message[(len(message) - LCD_COLUMNS):]

        # Write to LCD
        self.locks['lcd'].acquire()
        self.lcd.set_cursor(0, row)
        self.lcd.message(message)
        self.locks['lcd'].release()

    def led_pixel(self, px_id):
        """Allocates a pixel index in the clock"""

        if not LED_CLOCKWISE:  # Reverse if neccessary
            px_id = LED_COUNT - px_id
        px_id = (px_id + LED_TOP) % LED_COUNT  # Adjust to top
        # Allocate towards a base of 60 and return value
        return int(round((px_id + 1) * LED_COUNT / 60) - 1)

    def led_overlay(self, px_id, red, green, blue, substract=False):
        """Adds or subtracts values from the color channels"""

        # Do not show hours
        hour = 0
        if px_id % 5 == 0:
            if px_id % 15 == 0:
                hour = HIGH_HOUR_BRIGHTNESS
            else:
                hour = LOW_HOUR_BRIGHTNESS

        px_id = self.led_pixel(px_id)  # Allocate pixel

        if substract:
            self.led_array[px_id][0] = self.led_array[px_id][0] - red + hour
            self.led_array[px_id][1] = self.led_array[px_id][1] - green + hour
            self.led_array[px_id][2] = self.led_array[px_id][2] - blue + hour
        else:
            self.led_array[px_id][0] = self.led_array[px_id][0] + red - hour
            self.led_array[px_id][1] = self.led_array[px_id][1] + green - hour
            self.led_array[px_id][2] = self.led_array[px_id][2] + blue - hour

        self.led_strip.setPixelColorRGB(
            px_id,
            max(0, min(255, self.led_array[px_id][0])),
            max(0, min(255, self.led_array[px_id][1])),
            max(0, min(255, self.led_array[px_id][2]))
        )

    def cleanup(self, signal_number=None, stack_frame=None):
        """This function sets the stop event for all threads and cleans up"""

        self.stop_flag.set()


# Create daemon object
clock_station_daemon = ClockStationDaemon()

# Setup logging
logger = logging.getLogger('ClockStationLog')
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('/var/log/clock_station.log')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Run daeman
daemon_runner = runner.DaemonRunner(clock_station_daemon)
daemon_runner.daemon_context.files_preserve = [
    handler.stream]  # preserve log file
daemon_runner.daemon_context.signal_map = {
    signal.SIGTERM: clock_station_daemon.cleanup}  # on termination
daemon_runner.do_action()
