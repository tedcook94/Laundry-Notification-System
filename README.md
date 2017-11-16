# Laundry Notification System

A Python-based system that uses SMS to notify you when your laundry is done

### Original Implementation

This system was designed to be run on a Raspberry Pi using two accelerometers and two keypads (one each for both the washer and dryer). It was used in a dorm-setting where users could enter their room number to receive a SMS notification of when their laundry was done in the washer and/or dryer.

### Hardware

Raspberry Pi 2 (but should work on any model with sufficient GPIO)

2x ADXL345 compatible accelerometer

2x generic 4x4 matrix keypad from Adafruit

RPi-compatible WiFi dongle

### Additional Requirements

Twilio SMS account (does cost a very small amount of money per text sent)

adxl345-python library (https://github.com/pimoroni/adxl345-python)

### Implementation

Configure adxl345-python library, adjust both RoomEntry files with appropriate credentials from Twilio and populate the PhoneNumbers file with user's numbers. Make sure to enable I2C in Raspbian as it is disabled by default. Optionally: configure the StartRoomEntry script to run at startup for a headless setup.

### NOTE

This project was written without an formal education as a test to see what I could do on my own and figure out solely using the internet as a resource (thank you, Google!). There are undoubtedly many poorly coded sections that could be made more efficient/logical in the right hands, but it is what it is for now. Hopefully one day I'll be able to sit down and give it some more work. If you see a glaring error or fix, feel free to contribute!
