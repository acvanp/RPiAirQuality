# Air Quality Analyzer
## Perform relative air quality measurements

By using a three-way valve, air pump, and plastic bag around the air quality sensors, this device and software perform relative measurements on the outdoor and indoor samples (or sample A and sample B) and so it functions in the same way as an expensive benchtop analyzer. Regardless of the quality of these cheap sensors, you can use this device and software to get a relative picture of times of day or days of the week when indoor or outdoor air is particularly dirty or clean. You may further use additional sensors to explore broader meteorological trends that may correlate with air quality (e.g., explore barometric pressure trends, humidity, temperature etc.). I used this device to demonstrate that my plug-in particle filter does indeed reduce the PM2.5 in the indoor air.

__See the diagram PDF for more details.__

## Operating Code
This code was collected from open resources, with either the MIT open software license or no license, to make a not-for-profit device. I combined the code together and inserted timing for the three-way valve, and binary columns for indoor/outdoor sample source, and conditioning/sampling sample state.
* PMS5003 sensor code: https://github.com/aproano2/pms5003py
* BMP180 sensor code: https://github.com/m-rtijn/bmp180
* DHT sensor code: https://github.com/Freenove/Freenove_RFID_Starter_Kit_for_Raspberry_Pi/tree/master/Code/Python_Code/21.1.1_DHT11
* MQ2 sensor code adapted from: http://osoyoo.com/driver/mq-5.py

__Download code with:__

`cd /directory`

`git clone git@github.com:acvanp/RPiAirQuality.git`


__Run program:__
* Set up the hardware.
* Name output CSV filename in "AQ_class.py"

`python air_quality.py`

### Analyze the data with the AQdataanalysis.py script. 
The idea is to reduce the CSV data from all data entries to just the sampling state of sample (state 1), not conditioning samples (sample state of 0). This is then split into two dataframes, the indoor samples and the outdoor samples. In practice, it is mainly the MQ2 gas sensor that benefits from 5 minutes of throwaway conditioning before taking the data as actual sample data, whereas the PMS, DHT, and BMP only need a minute or less of conditioning (depending on your pump and your sample manifold). You can plot your data any way you want. The most difficult thing for me was the date-time values. The values of my date-times were created using dates.datestr2num() and the X-axis labels were created using the timestamp text with the second dropped (useless information). 

You would want to have some QA/QC if you want to immitate an expensive benchtop analyzer. You will see that there are several data filter functions at the top of the script for throwing out "fliers" or sudden unrealistic jumps in the data value that represent bad datapoints; removing samples that are taken when the device errors out and returns incomplete data; or bundling and smoothing the data into 1 30-row averages, etc.

Use the shell script AQdataanalysis.sh to continually update the graph if you want this automated.

__Interpreting PM2.5 data:__
* https://publiclab.org/questions/samr/04-07-2019/how-to-interpret-pms5003-sensor-values
* "In conclusion, I always use the "standard" readings for reporting but keep the "ambient conditions" for analysis. I haven't used these things in high altitudes so for all my deployments the standard and ambient are very similar."

__Plots:__
* Panel time series with indoor and outdoor comparison of temperature, humidity, MQ2 volatile gas normalized % variation, barometeric pressure in Pascals, PM10_std, PM2.5_std, raw indoor and outdoor particle concentrations of different sizes, then the ratio with a horizontal line for ratio of 1 to see when indoor or outdoor air is dirtier.
* Scatter diagram concept, comparing indoor and outdoor air raw particle values.


__Materials List:__
* Raspberry Pi 4B with standard RPi debian Linux
* GPIO connector ribbon
* Breadboard
* jumper wires
* 220 ohm resistors
* NPN transistor (S8050)
* 3-6V aquarium pump (NW Air Pump5-6V DC from Amazon)
* 3-6V three way valve (from Adafruit)
* 3mm internal diameter tubing to connect valve, pump, and outdoor air source (my office window)
* MCP3008 anolog digital converter
* MQ-2 gas sensor
* DHT sensor
* BMP180 GY-68 digital pressure sensor (I had to double-ground the ground pin, but you might prefer to use a soldering iron)
* PMS5003 particle sensor with ribbon cable connection
* optional LED indicator for three-way valve
* plastic bag to place the gas, particle, and humidity sensors inside of
* rubber band to connect bag to the pump
* tape to close the end of the bag around the exiting electrical cables

