# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
This will show some Linux Statistics on the attached display. Be sure to adjust
to the display you have connected. Be sure to check the learn guides for more
usage information.

This example is for use on (Linux) computers that are using CPython with
Adafruit Blinka to support CircuitPython libraries. CircuitPython does
not support PIL/pillow (python imaging library)!
"""

import signal
import time
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont
from ST7789 import ST7789
import RPi.GPIO as GPIO
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

SPI_SPEED_MHZ = 90 
width = 240
height = 240
brightness = 100



# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
image = Image.new("RGB", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)


# pylint: disable=line-too-long

# Create Display
st7789 = ST7789(
    rotation=90,  # Needed to display the right way up on Pirate Audio
    port=0,       # SPI port
    cs=1,         # SPI port Chip-select channel
    dc=9,         # BCM pin used for data/command
    backlight=None,
    spi_speed_hz=SPI_SPEED_MHZ * 1000 * 1000
)

# The buttons on Pirate Audio are connected to pins 5, 6, 16 and 24
# Boards prior to 23 January 2020 used 5, 6, 16 and 20 
# try changing 24 to 20 if your Y button doesn't work.
BUTTONS = [5, 6, 16, 24]

# These correspond to buttons A, B, X and Y respectively
LABELS = ['A', 'B', 'X', 'Y']

GPIO.setmode(GPIO.BCM)

# We must set the backlight pin up as an output first
GPIO.setup(13, GPIO.OUT)

# Set up our pin as a PWM output at 500Hz
backlight = GPIO.PWM(13, 5000)

# Start the PWM at 100% duty cycle
backlight.start(brightness)

Song = " "
Artist = " "

# "handle_button" will be called every time a button is pressed
# It receives one argument: the associated input pin.
def handle_button(pin):
    global brightness
    global Song
    global Artist

    if pin == 16:
        brightness = brightness + 25
        if brightness > 100:
           brightness = 0
        backlight.ChangeDutyCycle(brightness)
  #      time.sleep(10)
  #      backlight.ChangeDutyCycle(0)
    elif pin == 6:
        cmd = "echo \"b8:27:eb:be:9d:3a mixer volume -10\" | nc -q 0 192.168.1.35 9090"
        Vol = subprocess.check_output(cmd, shell=True).decode("utf-8")
    elif pin == 24:
        cmd = "echo \"b8:27:eb:be:9d:3a mixer volume +10\" | nc -q 0 192.168.1.35 9090"
        Vol = subprocess.check_output(cmd, shell=True).decode("utf-8")
#    elif pin == 5:



# Buttons connect to ground when pressed, so we should set them up
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 100ms to smooth out button presses.
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=300)

# pylint: enable=line-too-long

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
st7789.display(image)

# First define some constants to allow easy positioning of text.
padding = -2
x = 0

# Load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
last_idle = last_total = 0

try:
  while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), (0,0,200) )

    # Draw a handy on-screen bar to show us the current brightness
    bar_width = int((220 / 100.0) * brightness)
    draw.rectangle((10, 220, 10 + bar_width, 230), (255, 255, 255))

    with open('/proc/stat') as f:
        fields = [float(column) for column in f.readline().strip().split()[1:]]
    idle, total = fields[3], sum(fields)
    idle_delta, total_delta = idle - last_idle, total - last_total
    last_idle, last_total = idle, total
    utilisation = 100.0 * (1.0 - idle_delta / total_delta)
    CPU = "CPU: {:02d}%".format(int(utilisation))
    # Shell scripts for system monitoring from here:
    # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "hostname -I | cut -d' ' -f1"
    IP = "IP: " + subprocess.check_output(cmd, shell=True).decode("utf-8")
 #   cmd = "top -bn1 | awk 'NR==3'{printf \"CPU: %.2f\", 100-$8}'"
 #   CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
 #   cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%s MB  %.2f%%\", $3,$2,$3*100/$2 }'"
 #   MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
 #   cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%d GB  %s", $3,$2,$5}\''
 #   Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "cat /sys/class/thermal/thermal_zone0/temp |  awk '{printf \"Temp: %.1f C\", $(NF-0) / 1000}'" # pylint: disable=line-too-long
    Temp = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "cat /proc/asound/card0/pcm*p/sub*/hw_params | awk '$1==\"rate:\" {print $1, $2/1000, \"k\"}'"
    Dac = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "echo \"get battery\" | nc -q 0 127.0.0.1 8423 | awk '{printf \"Battery: %.1f%%\", $2}'"
    Bat = subprocess.check_output(cmd, shell=True).decode("utf-8")
#    cmd= "curl -X GET \"http://192.168.1.30:9000/status.html?p0=play&player=b8:27:eb:be:9d:3a\" |\& grep -i \"playingSong\\\"\""
# | awk '{for (i=4; i<NF; i++) printf $i \" \"; if (NF >= 4) print $NF; }' | sed -r 's/^target=\"browser\">(.*)<\\/a>/\\1/'"
#    Song = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "echo  \"b8:27:eb:be:9d:3a title ?\" | nc -q 0 192.168.1.35 9090 | awk '{print \"Song: \",$3}'"
    Song1 = Song
    Song = unquote(subprocess.check_output(cmd, shell=True).decode("utf-8"))
    if Song == "":
       Song = Song1
    cmd = "echo  \"b8:27:eb:be:9d:3a artist ?\" | nc -q 0 192.168.1.35 9090 | awk '{print \"Artist: \",$3}'"
    Artist1 = Artist
    Artist = unquote(subprocess.check_output(cmd, shell=True).decode("utf-8"))
    if Artist == "":
       Artist = Artist1
    # Write four lines of text.
    y = padding
    draw.text((x, y), IP, font=font, fill="#FFFFFF")
    y += font.getsize(IP)[1]
    draw.text((x, y), CPU, font=font, fill="#FFFFFF")
    y += font.getsize(CPU)[1]
 #   draw.text((x, y), MemUsage, font=font, fill="#FFFFFF")
 #   y += font.getsize(MemUsage)[1]
 #   draw.text((x, y), Disk, font=font, fill="#FFFFFF")
 #   y += font.getsize(Disk)[1]
    draw.text((x, y), Temp, font=font, fill="#FFFFFF")
    y += font.getsize(Temp)[1]
    draw.text((x, y), Bat, font=font, fill="#FFFFFF")
    y += font.getsize(Bat)[1]
    draw.text((x, y), "Brightness: "+str(int(brightness))+"%", font=font, fill="#FFFFFF")
    y += font.getsize(Bat)[1]
    draw.text((x, y), Dac, font=font, fill="#FFFF00")
    y += font.getsize(Dac)[1]
    draw.text((x, y), Song, font=font2, fill="#FFFFFF")
    y += font.getsize(Song)[1]
    draw.text((x, y), Artist, font=font2, fill="#FFFFFF")

    # Display image.
    st7789.display(image)
    time.sleep(3)


except KeyboardInterrupt:
  print("Ctl C pressed - ending program")
  backlight.ChangeDutyCycle(0)
#  time.sleep(1)
#  backlight.stop()                   # stop PWM
#  GPIO.output(13,GPIO.LOW)
#  GPIO.cleanup()                     # resets GPIO ports used back to input mode
