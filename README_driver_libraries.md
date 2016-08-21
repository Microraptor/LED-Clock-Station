# Install hardware driver libraries for Python

## General

```sh
sudo apt-get install build-essential python-dev git python-pip python-rpi.gpio
```

RPI pinout guide  
[http://pinout.xyz](http://pinout.xyz/)

_Note: for the guide it is assumed /home/pi/sources/ exists,
you can also take another directory for downloaded source code_

## I2C

```sh
sudo apt-get install python-smbus i2c-tools
sudo raspi-config
```

advanced->I2C  
enable I2C

```sh
sudo nano /etc/modules
```

add the lines

```text
i2c-bcm2708
i2c-dev
```

Uncomment the I2C module

```sh
sudo nano /etc/modprobe.d/raspi-blacklist.conf
sudo reboot
sudo i2cdetect -l
sudo i2cdetect -y 0 #1 instead of 0 for newer RPI
```

## PIR motion sensor

_5V-12V Vcc, <1mA, 3.3V signal_

when motion is detected signal is high
use RPi.GPIO library for input pin

## MOSFET

_5V logic_  
**needs 5V logic -> use level converter from 3.3V**  
**best is external power for VCC**  
**use heat sink if used with high current**  
**it is best to place a diode parallel to the load**

[http://elinux.org/RPi_GPIO_Interface_Circuits#Using_a_FET](http://elinux.org/RPi_GPIO_Interface_Circuits#Using_a_FET)

the MOSFET can be used to drive a standard 120mm computer fan (at 5V it runs nice and quiet)

## Relay

_3.3V logic, 5V relay_  
**remove jumper and use 3.3V for logic and
5V (external power at best) for JDVCC**

the relays activate on low level input
use RPi.GPIO library for output pin

## DS3231

_3V-5V, I2C 0x68_

```sh
sudo i2cdetect -y 0
echo ds3231 0x68 | sudo tee /sys/class/i2c-adapter/i2c-0/new_device
```

if neccessary change timezone

```sh
sudo raspi-config
```

to write time to hwclock

```sh
sudo hwclock -w
```

to check times

```sh
sudo hwclock -r
date
```

to load hwclock at startup

```sh
sudo nano /etc/rc.local
```

And write to the end of file before exit 0 (for Model B rev 1)

```text
sudo echo ds3231 0x68 > /sys/class/i2c-adapter/i2c-0/new_device
sudo hwclock -s
```

if you want to disable NTP

```sh
sudo update-rc.d ntp disable
sudo update-rc.d fake-hwclock disable
```

to update time via NTP

```sh
sudo ntpd -gq
sudo hwclock -w
```

## GY-30 BH150FVI Light Sensor

_3V-5V, <1mA, I2C 0x23_
**connect addr to ground**

[http://www.raspberrypi-spy.co.uk/2015/03/bh1750fvi-i2c-digital-light-intensity-sensor/](http://www.raspberrypi-spy.co.uk/2015/03/bh1750fvi-i2c-digital-light-intensity-sensor/)  
Credit to Matt Hawkins from Raspberrypi-Spy

for usage and demo configure and run following file

```sh
wget https://bitbucket.org/MattHawkinsUK/rpispy-misc/raw/master/python/bh1750.py
nano bh1750.py
sudo python bh1750.py
```

## Rotary Encoder

[http://www.bobrathbone.com/raspberrypi_rotary.htm](http://www.bobrathbone.com/raspberrypi_rotary.htm)  
Credit to Chris Bob Rathbone

```sh
mkdir /home/pi/sources/pi_rotary
cd /home/pi/sources/pi_rotary
wget http://www.bobrathbone.com/raspberrypi/source/pi_rotary.tar.gz
tar -xzvf pi_rotary.tar.gz
rm pi_rotary.tar.gz
sudo cp rotary_class.py /usr/local/lib/python2.7/dist-packages/rotary_class.py
```

If you have a revision 1 RPI comment the code as describe in the comments:

```sh
sudo nano /usr/local/lib/python2.7/dist-packages/rotary_class.py
```

see test_rotary_class.py and test_rotary_switches.py for usage

## 4x4 Membrane Matrix Keypad

[http://crumpspot.blogspot.de/p/keypad-matrix-python-package.html](http://crumpspot.blogspot.de/p/keypad-matrix-python-package.html)  
Credit to Chris Crumpacker

```sh
sudo pip install matrix_keypad
```

to see/change ROW and COLUMNS GPIO pins

```sh
sudo nano /usr/local/lib/python2.7/dist-packages/matrix_keypad/RPi_GPIO.py
```

Python usage

```python
from matrix_keypad import RPi_GPIO
kp = RPi_GPIO.keypad(ColumnCount = 4)
def digit():
    digitPressed = None
    while digitPressed == None:
        digitPressed = kp.getKey()
    return digitPressed
```

## DHT22 AM2302 temperature and humidity Sensor

_3V-5V, <1mA_  
**needs a 4.7k-10k Ohm resistor between data and VCC**

[https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/)  
Credit to Tony DiCola from Adafruit

```sh
cd /home/pi/sources  
git clone https://github.com/adafruit/Adafruit_Python_DHT.git  
cd Adafruit_Python_DHT  
sudo python setup.py install
```

to get the readings in the shell (data pin = BCM 4)

```sh
sudo /home/pi/sources/Adafruit_Python_DHT/examples/AdafruitDHT.py 22 4
```

Python usage (data pin = BCM 4)

```python
import Adafruit_DHT
pin = 4
humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)  
if humidity is not None and temperature is not None:
    print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
else:
    print('Failed to get reading. Try again!')
```

## WS2812 RGB Neopixel Ring

_5V_  
**needs an external 5V power supply (up to 60mA per LED)**  
**place a 1000uF capacitor between VCC and Ground**  
**needs 5V logic -> use level converter from 3.3V**  
**connect with a 300-500 Ohm resistor between the data to the RPI PWM pin 18**

[https://learn.adafruit.com/neopixels-on-raspberry-pi/overview](https://learn.adafruit.com/neopixels-on-raspberry-pi/overview)  
Credit to Jeremy Garff and Tony DiCola from Adafruit

```sh
sudo apt-get install scons swig
cd /home/pi/sources
git clone https://github.com/jgarff/rpi_ws281x.git
cd rpi_ws281x
scons
cd python
sudo python setup.py install
```

for demo configure `LED_COUNT` in the example strandtest.py and run the file

```sh
sudo nano examples/strandtest.py
sudo python examples/strandtest.py
```

## SSD1306 128x64 OLED Display

_3V-5V, 0.08W max, I2C 0x3C_

[https://learn.adafruit.com/ssd1306-oled-displays-with-raspberry-pi-and-beaglebone-black/overview](https://learn.adafruit.com/ssd1306-oled-displays-with-raspberry-pi-and-beaglebone-black/overview)  
Credit to Tony DiCola from Adafruit

```sh
sudo apt-get install python-imaging
cd /home/pi/sources
git clone https://github.com/adafruit/Adafruit_Python_SSD1306.git
cd Adafruit_Python_SSD1306
sudo python setup.py install
```

if the display doesn't have an RST pin, comment all lines containing
`self._rst` in the SSD1306.py library  
(for me lines: 87, 88 and 153-160)

```sh
sudo nano /usr/local/lib/python2.7/dist-packages/Adafruit_SSD1306-1.6.0-py2.7.egg/Adafruit_SSD1306/SSD1306.py
```

for demo configure and run the files in the example directory

## HD44780 20x4 LCD with PCF8574

_5V, I2C 0x27_  
**needs 5V logic -> use level converter from 3.3V**

[https://learn.adafruit.com/character-lcd-with-raspberry-pi-or-beaglebone-black/overview](https://learn.adafruit.com/character-lcd-with-raspberry-pi-or-beaglebone-black/overview)  
Credit to Tony DiCola from Adafruit and Sylvan Butler for the fork

we use this fork which supports the PCF8574:

```sh
cd /home/pi/sources
git clone https://github.com/sylvandb/Adafruit_Python_CharLCD.git
cd Adafruit_Python_CharLCD
sudo python setup.py install
sudo cp Adafruit_CharLCD/PCF_CharLCD.py /usr/local/lib/python2.7/dist-packages/PCF_CharLCD.py
```

python usage (busnum=1 for newer RPI)

```python
import PCF_CharLCD
lcd = PCF_CharLCD.PCF_CharLCD(0, address=0x27, busnum=0, cols=20, lines=4)
lcd.message('Hello\nworld!')
```

custom character creator  
[http://www.quinapalus.com/hd44780udg.html](http://www.quinapalus.com/hd44780udg.html)

```python
lcd.create_char(1, [2, 3, 2, 2, 14, 30, 12, 0])
lcd.clear()
lcd.message('Custom Character in Location 1: \x01')
```
