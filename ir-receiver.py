import RPi.GPIO as GPIO
import time
import json
import os
import re

IR_PIN = 17

def timeMeasure():
    maxTime = 1 #sec
    prevState = GPIO.input(IR_PIN)
    startTime = time.perf_counter()
    while time.perf_counter() - startTime < maxTime:
        nowState = GPIO.input(IR_PIN)
        if nowState != prevState:
            endTime = time.perf_counter()
            elapsedTime = (endTime - startTime) * 1000000 #microsec
            data = [round(elapsedTime), nowState]
            return data
    return None

def analysis():
    count = 0
    timeStateList = []
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IR_PIN, GPIO.IN)
    GPIO.wait_for_edge(IR_PIN, GPIO.BOTH)
    try:
        while True:
            data = timeMeasure()
            if data is None:
                break
            else:
                elapsedTime = data[0]
                nowState = data[1]
                #print(f"elapsed time: {elapsedTime}, state: {nowState}") #requires a lot of processing time
                timeStateList.append([elapsedTime, nowState])
                count += 1

    except KeyboardInterrupt:
        GPIO.cleanup(IR_PIN)
    GPIO.cleanup(IR_PIN)

    #print all time intervals and their respective on/off states
    for i in timeStateList:
        print(i)
    print(f"count: {count}")

    return timeStateList

def main(timeStateList):

    #see if two or more consecutive states appeared. example: 1010101101010
    prevState = 0
    r = 0
    stateSkipIndex = 0
    for i in timeStateList:
        if i[1] == prevState and r == 1:
            print(f"state skip detected, index: {stateSkipIndex}")
        if r == 0:
            prevState = i[1]
            r = 1
        prevState = i[1]
        stateSkipIndex += 1

    #convert timeStateList data into bit data
    bitList = []
    begin = 0
    unitTime = 400          #use 562 for toy remote control, use 400 for air-con remote control
    errorAllowed = 200
    for t in timeStateList:

        #record time for deviation calculation, please ignore.
        #if abs(t[0] - unitTime) < errorAllowed: 
        #    writeTimeToFile("./time-intervals/562MedianTime-with-desktop-env-and-geany.txt", t[0])

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

    # print(bitList)

    bitStr = ''
    for i in bitList:
        bitStr += str(i)

    # print(bitStr)

    # with open("./aircon-bits/data.json", "a") as f:
    #     for i in bitList:
    #         f.write(str(i))
    #     f.write('\n')

    temp = 22
    tempChange = 'up'       # 'up', 'down'  did you press the temperature up button or down button?
    windSpeed = 2           # 0 to 5, 0 means auto
    mode = 'cool'           # 'warm', 'dehumid', 'cool', 'fan'
    directionToggle = 'no'  # 'yes', 'no'
    timerOff = 0            # 0, 0.5, 1 to 9 in hours
    timerOn = 0             # 0, 0.5, 1 to 12 in hours
    stop = 'no'             # 'yes', 'no'
    numberOfSettings = 7    #change this as you add/remove variables above

    data = {
        'temp': temp, 
        'tempChange': tempChange,
        'windSpeed': windSpeed, 
        'mode': mode, 
        'directionToggle': directionToggle, 
        'timerOff': timerOff, 
        'timerOn': timerOn, 
        'stop': stop, 
        'bitStr_1': bitStr
    }

    print(data)
    writeDataToFile('./aircon-bits/data.json', data, numberOfSettings)


def writeTimeToFile(file, time):
    with open(file, "a") as f:
        f.write(f"{time}\n")

def writeDataToFile(file, dict, numberOfSettings):

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
        print(f"modifying config key: {configKey}, adding key: {bitStr_new} to it, and its value is: {dict['bitStr_1']}")
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


            


# asked gemini for this
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
    timeStateList = analysis()
    main(timeStateList)


