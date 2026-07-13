import pigpio
import time
import json
import os
import re
import statistics

# this script is used to receive data from your remote control and print the 0's and 1's out. mostly experimental. 



# --- Configuration ---

# specify the GPIO pin that the data wire from the VS1838B receiver is connected to
IR_PIN = 17

# if you want data to be written to output file or not. change to 'no' to stop writing. 
writeToOutFile = 'yes'

# the output file that the data will be written to. create the file manually first. 
outFile = './aircon-bits/data.json'

# if you want to record the barebone raw time data into a file, to calculate its Standard Deviation.
# the text file will only consist of the time data and no structure at all (not a json file). 
outputBareTimeData = 'no'

# the txt file the time data will be written to. 
bareTimeDataFile = './time-intervals/bareboneTimeData.txt'

# use 562 for VS1838B remote control, use 400 for hitachi AC remote control. 
# for other brands, i recommend running the script blind and seeing roughly on average what the measurements are. 
# learn about 'NEC protocol in remote controls' if you do not understand what this means. 
unitTime = 400

# leaving at 200 should work fine for most scenarios. 
errorAllowed = 200

# these variables are for saving the state of your RC to a .json file alongside the bit string data. 
# make sure they are same as your RC's state.
temp = 22
keyPressed = 'testSignal'     # 'up', 'down', 'cool', 'direction'  what button did you press? 
windSpeed = 2           # 0 to 5, 0 means auto
mode = 'cool'           # 'warm', 'dehumid', 'cool', 'fan'
directionToggle = 'no'  # 'yes', 'no'
timerOff = 0            # 0, 0.5, 1 to 9 in hours
timerOn = 0             # 0, 0.5, 1 to 12 in hours
stop = 'yes'             # 'yes', 'no'

#---------------------------------------------------------------------------------------------------------------------------------------

ACstatus = [temp, keyPressed, windSpeed, mode, directionToggle, timerOff, timerOn, stop]

# Global variables to store state without slowing down the callback
last_tick = None
measurements = [] 

# gemini
def edge_callback(gpio, level, tick):
    """
    This function is automatically called by the pigpio daemon in the background
    the instant the hardware pin changes state.
    
    gpio: The pin number (17)
    level: 0 (Falling edge/LOW), 1 (Rising edge/HIGH), or 2 (Watchdog timeout)
    tick: The exact hardware microsecond timestamp of the event
    """
    global last_tick
    
    # We only care about HIGH or LOW state changes
    if level == 0 or level == 1:
        if last_tick is not None:
            # pigpio.tickDiff calculates the microsecond difference.
            # It is crucial to use this instead of standard subtraction because 
            # the hardware tick counter wraps around to 0 every 71.6 minutes!
            elapsed_time = pigpio.tickDiff(last_tick, tick)
            
            # Append to memory quickly, DO NOT print here!
            measurements.append([elapsed_time, level])
            
        # Update the last_tick for the next cycle
        last_tick = tick

# gemini
def analysis():
    # 1. Connect to the local pigpio daemon
    pi = pigpio.pi()
    if not pi.connected:
        print("ERROR: Failed to connect to pigpiod.")
        print("Did you forget to start the daemon with 'sudo pigpiod'?")
        return

    # 2. Setup the pin as an input
    pi.set_mode(IR_PIN, pigpio.INPUT)

    # 3. Attach the callback listener to both rising and falling edges
    cb = pi.callback(IR_PIN, pigpio.EITHER_EDGE, edge_callback)

    print("Listening for IR pulses with DMA precision...")
    print("Press Ctrl+C to stop and print results.")

    try:
        # The callback is running in the background independently.
        # We just need to keep the main Python script alive.
        while True:
            time.sleep(1) 
            
    except KeyboardInterrupt:
        print("\nStopping measurement...")
        
    finally:
        # 4. Safely clean up and print out all collected data
        cb.cancel()
        pi.stop()
        
        print(f"\n--- Results ({len(measurements)} samples) ---")
        for res in measurements:
            print(res)
    
    return measurements

def main(measurements):

    #convert measurements data into bit data
    bitList = []
    begin = 0
    lastMeasurement = 0

    # temporary testing variable
    last5measurements = []
    last5avg = 400

    for index, t in enumerate(measurements):

        # record time for deviation calculation, please ignore.
        if outputBareTimeData == 'yes' and t[1] == 1 and abs(t[0] - unitTime) < unitTime: 
            writeTimeToFile(bareTimeDataFile, t[0])

        # temporary testing code
        # while len(last5measurements) >= 6:
        #     last5measurements.pop(0)
        # if abs(t[0] - unitTime) < 150 and t[1] == 1:
        #     last5measurements.append(t[0])
        # if len(last5measurements) == 5:
        #     last5avg = statistics.mean(last5measurements)
        #if last5avg < 385:
        #    print(f'well well well, the compensation pattern happened at index number {index}, avg is {last5avg}')

        # bi-directional error allowance
        '''
        if begin == 0 and abs(t[0] - unitTime) < errorAllowed and t[1] == 1:
            #detected short signal, beginning bit analysis
            begin = 1

        elif begin == 1 and abs(t[0] - unitTime) < errorAllowed and t[1] == 0:
            #1T on 1T off = bit 0.
            bitList.append(0)
            begin = 0

        elif begin == 1 and abs(t[0] - unitTime * 3) < errorAllowed and t[1] == 0:
            #1T on 3T off = bit 1.
            bitList.append(1)
            begin = 0
        '''

        # compensated for shrinking activation time interval and increasing off time interval
        '''
        if begin == 0 and 150 < t[0] and t[0] < 500 and t[1] == 1:      # 250 floor buffer, 100 ceiling buffer
            begin = 1

        elif begin == 1 and t[1] == 0:
            if 300 < t[0] and t[0] < 750:                               # 100 floor buffer, 350 ceiling buffer
                bitList.append(0)
            elif 1100 < t[0] and t[0] < 1550:                           #100 floor buffer, 350 ceiling buffer
                bitList.append(1)
            begin = 0

        if t[0] <= 150 or t[0] >= 1550:
            print(f"measurement out of bound for bit judgement, t = {t[0]}ms")
        '''

        # better solution
        #'''
        if begin == 0 and t[1] == 1:
            begin = 1
            lastMeasurement = t[0]
        
        elif begin == 1 and t[1] == 0:  
            if abs(t[0] + lastMeasurement - 2 * unitTime) < errorAllowed:       # if total time of ON and OFF is ~800us
                bitList.append(0)
            elif abs(t[0] + lastMeasurement - 4 * unitTime) < errorAllowed:     # if total time of ON and OFF is ~1600us
                bitList.append(1)
            begin = 0
        else:           # edge cases
            begin = 0
        #'''

    # print(bitList)

    bitStr = ''
    for i in bitList:
        bitStr += str(i)

    # print(bitStr)

    data = {
        'temp': ACstatus[0], 
        'keyPressed': ACstatus[1],
        'windSpeed': ACstatus[2], 
        'mode': ACstatus[3], 
        'directionToggle': ACstatus[4], 
        'timerOff': ACstatus[5], 
        'timerOn': ACstatus[6], 
        'stop': ACstatus[7], 
        'bitStr_1': bitStr
    }

    return data


def writeTimeToFile(file, time):
    with open(file, "a") as f:
        f.write(f"{time}\n")

def writeDataToFile(file, dict):
    numberOfSettings = len(dict) - 1

    fileIsEmpty = 'no'
    fullData = {}

    found = 'no'
    configKey = ''
    lastKeyInConfig = ''
    if os.stat(file).st_size == 0:             #check if file is empty.
        fileIsEmpty = 'yes'
        pass
    else:
        with open(file, 'r') as f:
            fullData = json.load(f)

        for key in fullData:
            config = fullData[key]
            misMatch = 'no'
            
            if  found == 'yes':
                break

            for i in range(0, numberOfSettings):            # loop over each setting in config
                if list(config.values())[i] == list(dict.values())[i]:  # check if current settings match the ones found in config
                    pass
                else:
                    misMatch = 'yes'
                    break

            if misMatch == 'no':
                configKey = key
                lastKeyInConfig = list(config.keys())[len(config) - 1]

                found = 'yes'
    
    if found == 'yes':
        bitStr_new = increment_first_integer(lastKeyInConfig)
        fullData[configKey][bitStr_new] = dict['bitStr_1']
        # print(f"modifying config key: {configKey}, adding key: {bitStr_new} to it, and its value is: {dict['bitStr_1']}")
    else:
        if fileIsEmpty == 'yes':
            newConfigKey = "config_1"
        else:
            configKeysList = list(fullData.keys())
            lastConfigkey = configKeysList[len(configKeysList) - 1]
            newConfigKey = increment_first_integer(lastConfigkey)
        fullData[newConfigKey] = dict

    with open(file, 'w') as f:
        json.dump(fullData, f, indent=4)
        print(f"added bit data and RC state info to {file} as {configKey}")


            


# gemini
def increment_first_integer(text: str) -> str:
    """
    Scans a string for the first integer, increments it by 1, 
    and returns the updated string. Ignores negative signs.
    """
    # Define a helper function to process the matched integer
    def add_one(match):
        # Extract the matched digits, convert to an integer, add 1, and convert back to string
        return str(int(match.group(0)) + 1)
    
    # re.sub finds the pattern (\d+) and replaces it using the add_one function
    # count=1 ensures we only increment the *first* integer found
    return re.sub(r'\d+', add_one, text, count=1)



if __name__ == '__main__':
    # get raw data
    measurements = analysis()

    # running main function
    data = main(measurements)

    # write data to data.json
    if writeToOutFile == 'yes' and data['bitStr_1'] != '':
        writeDataToFile(outFile, data)

