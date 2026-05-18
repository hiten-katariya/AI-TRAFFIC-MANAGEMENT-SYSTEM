import random
import math
import time
import threading
import pygame
import sys
import os

defaultRed = 150
defaultYellow = 5
defaultGreen = 20
defaultMinimum = 10
defaultMaximum = 60

signals = []
noOfSignals = 4
simTime = 300
timeElapsed = 0

currentGreen = 0
nextGreen = (currentGreen + 1) % noOfSignals
currentYellow = 0

bikeTime = 1
rickshawTime = 2.25
busTime = 2.5
truckTime = 2.5
ambulanceTime = 2.0  
noOfCars = 0
noOfBikes = 0
noOfBuses = 0
noOfTrucks = 0
noOfRickshaws = 0
noOfAmbulances = 0  
noOfLanes = 2
detectionTime = 5

speeds = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'rickshaw': 2, 'bike': 2.5, 'ambulance': 3.0}  
x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0}, 'up': {0: [], 1: [], 2: [], 'crossed': 0}}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'rickshaw', 4: 'bike', 5: 'ambulance'}  
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]
vehicleCountCoods = [(480, 210), (880, 210), (880, 550), (480, 550)]
vehicleCountTexts = ["0", "0", "0", "0"]

stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stops = {'right': [580, 580, 580], 'down': [320, 320, 320], 'left': [810, 810, 810], 'up': [545, 545, 545]}

mid = {'right': {'x': 705, 'y': 445}, 'down': {'x': 695, 'y': 450}, 'left': {'x': 695, 'y': 425}, 'up': {'x': 695, 'y': 400}}
rotationAngle = 3

gap = 15
gap2 = 15

pygame.init()
simulation = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red, yellow, green, minimum, maximum):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.signalText = "30"
        self.totalGreenTime = 0

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        image_name = 'car' if vehicleClass == 'ambulance' else vehicleClass
        path = "images/" + direction + "/" + image_name + ".png"
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)
        if direction == 'right':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].currentImage.get_rect().width - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif direction == 'left':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].currentImage.get_rect().width + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] += temp
            stops[direction][lane] += temp
        elif direction == 'down':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].currentImage.get_rect().height - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif direction == 'up':
            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].currentImage.get_rect().height + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] += temp
            stops[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.currentImage, (self.x, self.y))

    def move(self):
        global currentGreen, currentYellow, nextGreen
        if self.vehicleClass == 'ambulance' and self.crossed == 0:
            emergencyDirection = self.direction_number
            currentGreen = emergencyDirection
            currentYellow = 0
            for i in range(noOfSignals):
                if i != emergencyDirection:
                    signals[i].red = defaultRed
                    signals[i].yellow = 0
                    signals[i].green = 0
                else:
                    signals[i].green = 10
                    signals[i].yellow = 0
                    signals[i].red = 0
        if self.direction == 'right':
            if self.crossed == 0 and self.x + self.currentImage.get_rect().width > stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.vehicleClass == 'ambulance':
                    resumeNormalTraffic()
            if self.willTurn == 1:
                if self.crossed == 0 or self.x + self.currentImage.get_rect().width < mid[self.direction]['x']:
                    if ((self.x + self.currentImage.get_rect().width <= self.stop or (currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and
                            (self.index == 0 or self.x + self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - gap2) or
                             vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.x += self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if self.index == 0 or self.y + self.currentImage.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - gap2) or \
                                self.x + self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - gap2):
                            self.y += self.speed
            else:
                if ((self.x + self.currentImage.get_rect().width <= self.stop or self.crossed == 1 or (currentGreen == 0 and currentYellow == 0)) and
                        (self.index == 0 or self.x + self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - gap2) or
                         (vehicles[self.direction][self.lane][self.index - 1].turned == 1))):
                    self.x += self.speed
        elif self.direction == 'down':
            if self.crossed == 0 and self.y + self.currentImage.get_rect().height > stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.vehicleClass == 'ambulance':
                    resumeNormalTraffic()
            if self.willTurn == 1:
                if self.crossed == 0 or self.y + self.currentImage.get_rect().height < mid[self.direction]['y']:
                    if ((self.y + self.currentImage.get_rect().height <= self.stop or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1) and
                            (self.index == 0 or self.y + self.currentImage.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - gap2) or
                             vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.y += self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 2.5
                        self.y += 2
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width + gap2) or \
                                self.y < (vehicles[self.direction][self.lane][self.index - 1].y - gap2):
                            self.x -= self.speed
            else:
                if ((self.y + self.currentImage.get_rect().height <= self.stop or self.crossed == 1 or (currentGreen == 1 and currentYellow == 0)) and
                        (self.index == 0 or self.y + self.currentImage.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - gap2) or
                         (vehicles[self.direction][self.lane][self.index - 1].turned == 1))):
                    self.y += self.speed
        elif self.direction == 'left':
            if self.crossed == 0 and self.x < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.vehicleClass == 'ambulance':
                    resumeNormalTraffic()
            if self.willTurn == 1:
                if self.crossed == 0 or self.x > mid[self.direction]['x']:
                    if ((self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1) and
                            (self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width + gap2) or
                             vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.x -= self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 1.8
                        self.y -= 2.5
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().height + gap2) or \
                                self.x > (vehicles[self.direction][self.lane][self.index - 1].x + gap2):
                            self.y -= self.speed
            else:
                if ((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0)) and
                        (self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width + gap2) or
                         (vehicles[self.direction][self.lane][self.index - 1].turned == 1))):
                    self.x -= self.speed
        elif self.direction == 'up':
            if self.crossed == 0 and self.y < stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.vehicleClass == 'ambulance':
                    resumeNormalTraffic()
            if self.willTurn == 1:
                if self.crossed == 0 or self.y > mid[self.direction]['y']:
                    if ((self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1) and
                            (self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().height + gap2) or
                             vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.y -= self.speed
                else:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 1
                        self.y -= 1
                        if self.rotateAngle == 90:
                            self.turned = 1
                    else:
                        if self.index == 0 or self.x < (vehicles[self.direction][self.lane][self.index - 1].x - vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().width - gap2) or \
                                self.y > (vehicles[self.direction][self.lane][self.index - 1].y + gap2):
                            self.x += self.speed
            else:
                if ((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0)) and
                        (self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].currentImage.get_rect().height + gap2) or
                         (vehicles[self.direction][self.lane][self.index - 1].turned == 1))):
                    self.y -= self.speed

def resumeNormalTraffic():
    global currentGreen, currentYellow, nextGreen
    if all(not any(v.vehicleClass == 'ambulance' and v.crossed == 0 for v in vehicles[d][l]) for d in vehicles for l in range(3)):
        currentGreen = 0
        currentYellow = 0
        nextGreen = 1
        for i in range(noOfSignals):
            signals[i].green = defaultGreen
            signals[i].yellow = defaultYellow
            signals[i].red = defaultRed if i != currentGreen else 0

def initialize():
    ts1 = TrafficSignal(0, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts3)
    ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen, defaultMinimum, defaultMaximum)
    signals.append(ts4)
    repeat()

def setTime():
    global noOfCars, noOfBikes, noOfBuses, noOfTrucks, noOfRickshaws, noOfAmbulances
    global carTime, busTime, truckTime, rickshawTime, bikeTime, ambulanceTime
    os.system("say detecting vehicles, " + directionNumbers[(currentGreen + 1) % noOfSignals])
    noOfCars, noOfBuses, noOfTrucks, noOfRickshaws, noOfBikes, noOfAmbulances = 0, 0, 0, 0, 0, 0
    for j in range(len(vehicles[directionNumbers[nextGreen]][0])):
        vehicle = vehicles[directionNumbers[nextGreen]][0][j]
        if vehicle.crossed == 0:
            vclass = vehicle.vehicleClass
            if vclass == 'bike':
                noOfBikes += 1
    for i in range(1, 3):
        for j in range(len(vehicles[directionNumbers[nextGreen]][i])):
            vehicle = vehicles[directionNumbers[nextGreen]][i][j]
            if vehicle.crossed == 0:
                vclass = vehicle.vehicleClass
                if vclass == 'car':
                    noOfCars += 1
                elif vclass == 'bus':
                    noOfBuses += 1
                elif vclass == 'truck':
                    noOfTrucks += 1
                elif vclass == 'rickshaw':
                    noOfRickshaws += 1
                elif vclass == 'ambulance':
                    noOfAmbulances += 1
    greenTime = math.ceil(((noOfCars * carTime) + (noOfRickshaws * rickshawTime) + (noOfBuses * busTime) +
                          (noOfTrucks * truckTime) + (noOfBikes * bikeTime) + (noOfAmbulances * ambulanceTime)) / (noOfLanes + 1))
    print('Green Time: ', greenTime)
    if greenTime < defaultMinimum:
        greenTime = defaultMinimum
    elif greenTime > defaultMaximum:
        greenTime = defaultMaximum
    signals[(currentGreen + 1) % (noOfSignals)].green = greenTime

class FineSystem:
    def __init__(self):
        self.fines = {'red_light': 500, 'speeding': 300, 'illegal_turn': 200}
        self.violators = {}
        self.total_fines = 0
        self.violations_count = {'red_light': 0, 'speeding': 0, 'illegal_turn': 0}

    def check_red_light_violation(self, vehicle, signals, currentGreen, currentYellow):
        if vehicle.vehicleClass != 'ambulance':
            if vehicle.crossed == 0 and ((vehicle.direction == 'right' and currentGreen != 0 and currentYellow == 0) or
                                         (vehicle.direction == 'down' and currentGreen != 1 and currentYellow == 0) or
                                         (vehicle.direction == 'left' and currentGreen != 2 and currentYellow == 0) or
                                         (vehicle.direction == 'up' and currentGreen != 3 and currentYellow == 0)):
                if ((vehicle.direction == 'right' and vehicle.x + vehicle.currentImage.get_rect().width > stopLines[vehicle.direction]) or
                    (vehicle.direction == 'down' and vehicle.y + vehicle.currentImage.get_rect().height > stopLines[vehicle.direction]) or
                    (vehicle.direction == 'left' and vehicle.x < stopLines[vehicle.direction]) or
                    (vehicle.direction == 'up' and vehicle.y < stopLines[vehicle.direction])):
                    vehicle_id = id(vehicle)
                    if vehicle_id not in self.violators:
                        self.violators[vehicle_id] = []
                    if 'red_light' not in self.violators[vehicle_id]:
                        self.violators[vehicle_id].append('red_light')
                        self.violations_count['red_light'] += 1
                        self.total_fines += self.fines['red_light']
                        print(f"RED LIGHT VIOLATION: {vehicle.vehicleClass} in {vehicle.direction} direction - Fine: {self.fines['red_light']}")
                        return True
        return False

    def check_speeding_violation(self, vehicle):
        if vehicle.vehicleClass != 'ambulance':
            speed_threshold = speeds[vehicle.vehicleClass] * 1.5
            if random.random() < 0.01 and vehicle.speed > speed_threshold:
                vehicle_id = id(vehicle)
                if vehicle_id not in self.violators:
                    self.violators[vehicle_id] = []
                if 'speeding' not in self.violators[vehicle_id]:
                    self.violators[vehicle_id].append('speeding')
                    self.violations_count['speeding'] += 1
                    self.total_fines += self.fines['speeding']
                    print(f"SPEEDING VIOLATION: {vehicle.vehicleClass} in {vehicle.direction} direction - Fine: {self.fines['speeding']}")
                    return True
        return False

    def check_illegal_turn_violation(self, vehicle):
        if vehicle.vehicleClass != 'ambulance':
            if vehicle.vehicleClass == 'bus' and vehicle.willTurn == 1:
                vehicle_id = id(vehicle)
                if vehicle_id not in self.violators:
                    self.violators[vehicle_id] = []
                if 'illegal_turn' not in self.violators[vehicle_id] and vehicle.turned == 1:
                    self.violators[vehicle_id].append('illegal_turn')
                    self.violations_count['illegal_turn'] += 1
                    self.total_fines += self.fines['illegal_turn']
                    print(f"ILLEGAL TURN VIOLATION: Bus in {vehicle.direction} direction - Fine: {self.fines['illegal_turn']}")
                    return True
        return False

    def check_violations(self, vehicle, signals, currentGreen, currentYellow):
        red_light = self.check_red_light_violation(vehicle, signals, currentGreen, currentYellow)
        speeding = self.check_speeding_violation(vehicle)
        illegal_turn = self.check_illegal_turn_violation(vehicle)
        return red_light or speeding or illegal_turn

    def get_stats(self):
        return {'total_fines': self.total_fines, 'total_violations': sum(self.violations_count.values()), 'violations_breakdown': self.violations_count}

    def render_stats(self, screen, font):
        stats = self.get_stats()
        total_fines_text = font.render(f"Total Fines: ₹{stats['total_fines']}", True, (0, 0, 0), (255, 255, 255))
        violations_text = font.render(f"Violations: {stats['total_violations']}", True, (0, 0, 0), (255, 255, 255))
        red_light_text = font.render(f"Red Light: {stats['violations_breakdown']['red_light']}", True, (255, 0, 0), (255, 255, 255))
        speeding_text = font.render(f"Speeding: {stats['violations_breakdown']['speeding']}", True, (255, 165, 0), (255, 255, 255))
        illegal_turn_text = font.render(f"Illegal Turn: {stats['violations_breakdown']['illegal_turn']}", True, (0, 0, 255), (255, 255, 255))
        screen.blit(total_fines_text, (1100, 100))
        screen.blit(violations_text, (1100, 130))
        screen.blit(red_light_text, (1100, 160))
        screen.blit(speeding_text, (1100, 190))
        screen.blit(illegal_turn_text, (1100, 220))

def repeat():
    global currentGreen, currentYellow, nextGreen
    while signals[currentGreen].green > 0:
        printStatus()
        updateValues()
        if signals[(currentGreen + 1) % noOfSignals].red == detectionTime:
            thread = threading.Thread(name="detection", target=setTime, args=())
            thread.daemon = True
            thread.start()
        time.sleep(1)
    currentYellow = 1
    vehicleCountTexts[currentGreen] = "0"
    for i in range(0, 3):
        stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while signals[currentGreen].yellow > 0:
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 0
    signals[currentGreen].green = defaultGreen
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
    currentGreen = nextGreen
    nextGreen = (currentGreen + 1) % noOfSignals
    signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green
    repeat()

def printStatus():
    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                print(" GREEN TS", i + 1, "-> r:", signals[i].red, " y:", signals[i].yellow, " g:", signals[i].green)
            else:
                print("YELLOW TS", i + 1, "-> r:", signals[i].red, " y:", signals[i].yellow, " g:", signals[i].green)
        else:
            print("   RED TS", i + 1, "-> r:", signals[i].red, " y:", signals[i].yellow, " g:", signals[i].green)
    print()

def updateValues():
    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                signals[i].green -= 1
                signals[i].totalGreenTime += 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1

def generateVehicles():
    ambulanceSpawned = False
    while True:
        if not ambulanceSpawned and random.random() < 0.1:
            vehicle_type = 5
            ambulanceSpawned = True
        else:
            vehicle_type = random.randint(0, 4)
        if vehicle_type == 4:
            lane_number = 0
        else:
            lane_number = random.randint(0, 1) + 1
        will_turn = 0
        if lane_number == 2:
            temp = random.randint(0, 4)
            if temp <= 2:
                will_turn = 1
            elif temp > 2:
                will_turn = 0
        temp = random.randint(0, 999)
        direction_number = 0
        a = [400, 800, 900, 1000]
        if temp < a[0]:
            direction_number = 0
        elif temp < a[1]:
            direction_number = 1
        elif temp < a[2]:
            direction_number = 2
        elif temp < a[3]:
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(0.75)

def simulationTime():
    global timeElapsed, simTime
    while True:
        timeElapsed += 1
        time.sleep(1)
        if timeElapsed == simTime:
            totalVehicles = 0
            print('Lane-wise Vehicle Counts')
            for i in range(noOfSignals):
                print('Lane', i + 1, ':', vehicles[directionNumbers[i]]['crossed'])
                totalVehicles += vehicles[directionNumbers[i]]['crossed']
            print('Total vehicles passed: ', totalVehicles)
            print('Total time passed: ', timeElapsed)
            print('No. of vehicles passed per unit time: ', (float(totalVehicles) / float(timeElapsed)))
            os._exit(1)

# [Previous imports and variables remain the same until Main class]

# [Previous imports and variables remain the same until Main class]

class Main:
    def __init__(self):
        pygame.init()  # Ensure Pygame is initialized only once
        self.thread4 = threading.Thread(name="simulationTime", target=simulationTime, args=())
        self.thread4.daemon = True
        self.thread4.start()

        self.thread2 = threading.Thread(name="initialization", target=initialize, args=())
        self.thread2.daemon = True
        self.thread2.start()

        self.black = (0, 0, 0)
        self.white = (255, 255, 255)
        self.red = (255, 0, 0)
        self.green = (0, 255, 0)

        self.screenWidth = 1400
        self.screenHeight = 800
        self.screenSize = (self.screenWidth, self.screenHeight)

        self.background = pygame.image.load('images/mod_int.png')

        self.screen = pygame.display.set_mode(self.screenSize)
        pygame.display.set_caption("SIMULATION")

        self.redSignal = pygame.image.load('images/signals/red.png')
        self.yellowSignal = pygame.image.load('images/signals/yellow.png')
        self.greenSignal = pygame.image.load('images/signals/green.png')
        self.font = pygame.font.Font(None, 30)
        self.fine_system = FineSystem()
        self.thread3 = threading.Thread(name="generateVehicles", target=generateVehicles, args=())
        self.thread3.daemon = True
        self.thread3.start()

        # New variables for minute timer
        self.green_start_time = time.time()
        self.MAX_GREEN_TIME = 60  # 1 minute in seconds

    def check_and_switch_green(self):
        global currentGreen, currentYellow, nextGreen
        current_time = time.time()
        elapsed_green_time = current_time - self.green_start_time
        
        if elapsed_green_time >= self.MAX_GREEN_TIME and currentYellow == 0:
            # Switch to yellow
            currentYellow = 1
            signals[currentGreen].green = 0
            signals[currentGreen].yellow = defaultYellow
            
            # Prepare for next green
            vehicleCountTexts[currentGreen] = "0"
            for i in range(0, 3):
                stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
                for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                    vehicle.stop = defaultStop[directionNumbers[currentGreen]]
            
            # After yellow period, switch to next signal
            if signals[currentGreen].yellow <= 0:
                currentYellow = 0
                signals[currentGreen].green = defaultGreen
                signals[currentGreen].yellow = defaultYellow
                signals[currentGreen].red = defaultRed
                currentGreen = nextGreen
                nextGreen = (currentGreen + 1) % noOfSignals
                signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green
                self.green_start_time = time.time()  # Reset timer when lane changes
            return True
        return False

    def update_signal_timings(self):
        global currentGreen, currentYellow, nextGreen
        # Update signal timings similar to the repeat function
        if currentYellow == 0:
            if signals[currentGreen].green > 0:
                signals[currentGreen].green -= 1
                signals[currentGreen].totalGreenTime += 1
            else:
                currentYellow = 1
                vehicleCountTexts[currentGreen] = "0"
                for i in range(0, 3):
                    stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
                    for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                        vehicle.stop = defaultStop[directionNumbers[currentGreen]]
        else:
            if signals[currentGreen].yellow > 0:
                signals[currentGreen].yellow -= 1
            else:
                currentYellow = 0
                signals[currentGreen].green = defaultGreen
                signals[currentGreen].yellow = defaultYellow
                signals[currentGreen].red = defaultRed
                currentGreen = nextGreen
                nextGreen = (currentGreen + 1) % noOfSignals
                signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green

    def run(self):
        global currentGreen, currentYellow, nextGreen
        previousGreen = currentGreen  # Track the previous green lane to detect changes
        last_update_time = time.time()  # Track time for signal updates

        while True:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Update signal timings every second (similar to repeat)
            current_time = time.time()
            if current_time - last_update_time >= 1:
                self.update_signal_timings()
                last_update_time = current_time

                # Check for detection time and set green time
                if signals[(currentGreen + 1) % noOfSignals].red == detectionTime:
                    thread = threading.Thread(name="detection", target=setTime, args=())
                    thread.daemon = True
                    thread.start()

            # Check and switch green light if 1 minute has passed
            self.check_and_switch_green()

            # Detect lane change and reset timer
            if previousGreen != currentGreen:
                self.green_start_time = time.time()  # Reset timer when lane changes
                previousGreen = currentGreen

            # Render background
            self.screen.blit(self.background, (0, 0))
            
            # Render traffic signals
            for i in range(0, noOfSignals):
                if i == currentGreen:
                    if currentYellow == 1:
                        if signals[i].yellow == 0:
                            signals[i].signalText = "STOP"
                        else:
                            signals[i].signalText = signals[i].yellow
                        self.screen.blit(self.yellowSignal, signalCoods[i])
                    else:
                        if signals[i].green == 0:
                            signals[i].signalText = "SLOW"
                        else:
                            signals[i].signalText = signals[i].green
                        self.screen.blit(self.greenSignal, signalCoods[i])
                else:
                    if signals[i].red <= 10:
                        if signals[i].red == 0:
                            signals[i].signalText = "GO"
                        else:
                            signals[i].signalText = signals[i].red
                    else:
                        signals[i].signalText = "---"
                    self.screen.blit(self.redSignal, signalCoods[i])

            # Render signal texts and vehicle counts
            signalTexts = ["", "", "", ""]
            for i in range(0, noOfSignals):
                signalTexts[i] = self.font.render(str(signals[i].signalText), True, self.white, self.black)
                self.screen.blit(signalTexts[i], signalTimerCoods[i])
                displayText = vehicles[directionNumbers[i]]['crossed']
                vehicleCountTexts[i] = self.font.render(str(displayText), True, self.black, self.white)
                self.screen.blit(vehicleCountTexts[i], vehicleCountCoods[i])

            # Dashboard display (on left side)
            dashboard_x = 50  # x-coordinate for dashboard
            timeElapsedText = self.font.render(("Time Elapsed: " + str(timeElapsed)), True, self.black, self.white)
            self.screen.blit(timeElapsedText, (dashboard_x, 50))
            
            # Add green light timer to dashboard (on right)
            green_time_remaining = max(0, self.MAX_GREEN_TIME - (time.time() - self.green_start_time))
            green_timer_text = self.font.render(f"Green Light Time: {int(green_time_remaining)}s", 
                                              True, self.green if green_time_remaining > 10 else self.red, self.white)
            self.screen.blit(green_timer_text, (1100, 80))  # Kept at right for visibility
            
            # Show current green light direction
            current_green_text = self.font.render(f"Current Green: {directionNumbers[currentGreen]}", 
                                                True, self.green, self.white)
            self.screen.blit(current_green_text, (dashboard_x, 80))

            # Render fine system stats
            stats = self.fine_system.get_stats()
            total_fines_text = self.font.render(f"Total Fines: ₹{stats['total_fines']}", True, self.black, self.white)
            violations_text = self.font.render(f"Violations: {stats['total_violations']}", True, self.black, self.white)
            red_light_text = self.font.render(f"Red Light: {stats['violations_breakdown']['red_light']}", True, self.red, self.white)
            speeding_text = self.font.render(f"Speeding: {stats['violations_breakdown']['speeding']}", True, (255, 165, 0), self.white)
            illegal_turn_text = self.font.render(f"Illegal Turn: {stats['violations_breakdown']['illegal_turn']}", True, (0, 0, 255), self.white)
            self.screen.blit(total_fines_text, (dashboard_x, 110))
            self.screen.blit(violations_text, (dashboard_x, 140))
            self.screen.blit(red_light_text, (dashboard_x, 170))
            self.screen.blit(speeding_text, (dashboard_x, 200))
            self.screen.blit(illegal_turn_text, (dashboard_x, 230))

            # Render vehicles and check violations
            for vehicle in simulation:
                self.screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
                vehicle.move()
                self.fine_system.check_violations(vehicle, signals, currentGreen, currentYellow)

            pygame.display.update()

# Create and run the Main instance
if __name__ == "__main__":
    main_instance = Main()
    main_instance.run()