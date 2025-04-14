# ----- W.I.P -----
# Raspberry-Pi Energy Meter

This Project is a combination of custom Hardware and Software, that will allow you to monitor your unique power situation in real time.

This project is derived from and inspired by the resources located at https://github.com/David00/rpi-power-monitor and https://learn.openenergymonitor.org.


## What does it do?
This code accompanies DIY circuitry that supports monitoring of up to 3 Phases with 6 current transformers each. The individual readings are then used in calculations to provide real data on consumption and generation, including the following key metrics:
* Voltage of every pahse
* Current on up to 6 channels per phase
* Power Factor
* Harmonics inspection through a built in snapshot/plotting mechanism.

The code takes thousands of samples per second, corrects for phase errors in the measurements, calculates the instantaneous power for the tens of thousands of sampled points, and uses the instantaneous power calculations to determine real power, apparent power, and power factor. This means the project is able to monitor any type of load, including reactive, capacitive, and resisitve loads.

## Where can I get it?
The whole Project is open sourced. You can order your PCBs via the Files provided in the [PCB Folder](PCB).  
You'll also find a [README](PCB/README.md) there which will provide more useful information.


## Installation & Documentation

### Ordering
#### Components for the PCB
#### The PCB

### Preparing the Pi
#### System-Setup
#### Installing the necessary software

### Installation and Configuration
#### Installation into the Cabinet
#### Measuring required references
#### Configuring the Energy-Meter

## Contributing

## Credits

---

## If you like what I did, you are welcome to leave me some support
[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=Z8UFRA9MN84UG&currency_code=EUR&source=url)

[![BTC](https://img.shields.io/badge/Donate-BTC-orange.svg)]("bitcoin:bc1qe4243jv0xt2qryldwzpq49n6eh2c9t8zyleun5?label=Rpi%20Energy%20Meter")
