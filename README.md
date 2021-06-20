# S3R5 TEAM Raspberry Pi

Code for controlling handling thermal sensors, OpenMV, and the dispenzer for recognizing heated, visual, and colored victims and dispenzing appropriate amount of rescue packets. It also handles the rotation of the robot by communicating with the BNO055 module, and checks for the black tile using a photoresistor.

# Hardware

Raspberry Pi 4B

# Programming language

Python 3

# Principle of working

Script runs in a loop where it checks for any requests for rotations from Arduino over serial. While doing that it also checks if there's a black tile underneath the robot, if any of the thermal sensors detect anything, and if the OpenMVs found any colored or visual victims.