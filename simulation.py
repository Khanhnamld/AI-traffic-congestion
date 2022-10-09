import random
import time
import threading
import pygame
import sys
import neat
import pickle
import os


class Cood:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Signal:
    def __init__(self, cood: tuple[int, int], timerCood: tuple[int, int]):
        self.cood: tuple[int, int] = cood
        self.timerCood: tuple[int, int] = timerCood


class TrafficSignalGroup:
    def __init__(self, signalsList: list[Signal], red: int, yellow: int, green: int):
        self.red: int = red
        self.yellow: int = yellow
        self.green: int = green
        self.signalText: str = ""
        self.signalsList: list[Signal] = signalsList

    def alter(self, f):
        for signal in self.signalsList:
            f(signal)


# Variables for NN
outputNN = 0
gen = 0
pop = 0
SumOfvePass = 0

# Num of vehicles per lane
NoVL = [0, 0, 0, 0, 0, 0, 0, 0]

# Screensize
screenWidth = 1400
screenHeight = 800
screenSize = (screenWidth, screenHeight)

vehiclesSpawntime = 0.4  # time between two vehicles spawn

# Default values of signal timers
defaultGreen = 10
redSignalDuration = 5
defaultYellow = 1

signals: list[Signal] = []
signalsGroup: list[TrafficSignalGroup] = []
noOfSignalsGroups = 4
currentGreen = 0  # Indicates which signal is green currently
nextGreen = 1  # Indicates which signal will turn green next
isYellow = False  # Indicates whether yellow signal is on or off

speeds = {'car': 10, 'bus': 10, 'truck': 10, 'bike': 10}  # average speeds of vehicles

# Tọa độ điểm bắt đầu
initPos = {
    'r-t': Cood(-20, 436),
    'r-s': Cood(-20, 466),
    'l-t': Cood(1420, 398),
    'l-s': Cood(1420, 370),
    'u-t': Cood(697, 820),
    'u-s': Cood(727, 820),
    'd-t': Cood(657, -20),
    'd-s': Cood(627, -20),
}

vehicles = {'r-t': {'vehicles': [], 'crossed': 0},
            'r-s': {'vehicles': [], 'crossed': 0},
            'l-t': {'vehicles': [], 'crossed': 0},
            'l-s': {'vehicles': [], 'crossed': 0},
            'u-t': {'vehicles': [], 'crossed': 0},
            'u-s': {'vehicles': [], 'crossed': 0},
            'd-t': {'vehicles': [], 'crossed': 0},
            'd-s': {'vehicles': [], 'crossed': 0},
            }

vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
directionClasses = {0: ['r-s', 'l-s'], 1: ['u-s', 'd-s'], 2: ['l-t', 'r-t'], 3: ['d-t', 'u-t'], 'u-t': 3, 'd-t': 3,
                    'l-t': 2, 'r-t': 2, 'u-s': 1, 'd-s': 1, 'l-s': 0, 'r-s': 0}

# Tọa độ điểm dừng + điểm rẽ
stopLines = {'r-s': 590, 'r-t': 590, 'd-s': 330, 'd-t': 330, 'l-s': 800, 'l-t': 800, 'u-s': 535, 'u-t': 535}
defaultStop = {'r-s': 580, 'r-t': 580, 'd-s': 320, 'd-t': 320, 'l-s': 810, 'l-t': 810, 'u-s': 620, 'u-t': 620}
turnRightPos = {'r-s': [700, 700, 700, 700], 'd-s': [440, 440, 440, 440], 'l-s': [770, 800, 770, 770],
                'u-s': [480, 480, 480, 480]}
turnLeftPos = {'r-t': [760, 760, 760, 760], 'd-t': [510, 510, 510, 510], 'l-t': [710, 710, 710, 710],
               'u-t': [405, 405, 405, 405]}

# Khoảng cách giữa phương tiện và phương tiện trước nó
stoppingGap = 30  # Lúc dừng
movingGap = 30  # Lúc di chuyển

pygame.init()
simulation = pygame.sprite.Group()


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, vehicleClass, direction, turn, NoL):
        pygame.sprite.Sprite.__init__(self)
        self.turn = turn
        self.vehicleClassID = vehicleClass
        self.vehicleClass = vehicleTypes[vehicleClass]
        self.speed = speeds[self.vehicleClass]
        self.direction = direction
        self.x = initPos[direction].x
        self.y = initPos[direction].y
        self.crossed = False
        self.turned = False
        self.count = False
        self.NoL = NoL
        # print(direction)
        vehicles[direction]['vehicles'].append(self)
        self.index = len(vehicles[direction]['vehicles']) - 1
        if direction[0] == 'r':
            path = "images/right/" + self.vehicleClass + ".png"
        elif direction[0] == 'l':
            path = "images/left/" + self.vehicleClass + ".png"
        elif direction[0] == 'd':
            path = "images/down/" + self.vehicleClass + ".png"
        else:
            path = "images/up/" + self.vehicleClass + ".png"
        self.image = pygame.image.load(path)
        self.wid = self.image.get_width()
        self.ht = self.image.get_height()
        if (len(vehicles[direction]['vehicles']) > 1
                and not vehicles[direction]['vehicles'][
                    self.index - 1].crossed):  # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
            # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap
            if direction[0] == 'r':
                self.stop = vehicles[direction]['vehicles'][self.index - 1].stop - vehicles[direction]['vehicles'][
                    self.index - 1].image.get_rect().width - stoppingGap
            elif direction[0] == 'l':
                self.stop = vehicles[direction]['vehicles'][self.index - 1].stop + vehicles[direction]['vehicles'][
                    self.index - 1].image.get_rect().width + stoppingGap
            elif direction[0] == 'd':
                self.stop = vehicles[direction]['vehicles'][self.index - 1].stop - vehicles[direction]['vehicles'][
                    self.index - 1].image.get_rect().height - stoppingGap
            elif direction[0] == 'u':
                self.stop = vehicles[direction]['vehicles'][self.index - 1].stop + vehicles[direction]['vehicles'][
                    self.index - 1].image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]

        # Set new starting and stopping coordinate
        if direction == 'right':
            temp = self.image.get_rect().width + stoppingGap
            initPos[direction] -= temp
        elif direction == 'left':
            temp = self.image.get_rect().width + stoppingGap
            initPos[direction] += temp
        elif direction == 'down':
            temp = self.image.get_rect().height + stoppingGap
            initPos[direction] -= temp
        elif direction == 'up':
            temp = self.image.get_rect().height + stoppingGap
            initPos[direction] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        global SumOfvePass
        x_ct = self.x + (self.wid / 2)
        y_ct = self.y + (self.ht / 2)
        # print(x_ct, y_ct)
        # quit()
        # ['r-s', 'd-s', 'l-s', 'u-s', 'r-t', 'd-t', 'u-t', 'l-t']
        #         initPos = {
        #     'r-t': Cood(-20, 436),
        #     'r-s': Cood(-20, 466),
        #     'l-t': Cood(1420, 398),
        #     'l-s': Cood(1420, 370),
        #     'u-t': Cood(697, 820),
        #     'u-s': Cood(727, 820),
        #     'd-t': Cood(657, -20),
        #     'd-s': Cood(627, -20),
        # }
        # stopLines = {'r-s': 590, 'r-t': 590, 'd-s': 330, 'd-t': 330, 'l-s': 800, 'l-t': 800, 'u-s': 535, 'u-t': 535}
        if (self.count == False):
            if (self.NoL == 0):
                if (x_ct > 600) and (x_ct <= 610) and (y_ct > 466) and (y_ct < 496):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
            elif (self.NoL == 1):
                if (x_ct > 627) and (x_ct < 657) and (y_ct > 340) and (y_ct <= 350):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
            elif (self.NoL == 2):
                if (x_ct > 780) and (x_ct <= 790) and (y_ct > 370) and (y_ct < 400):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
            elif (self.NoL == 3):
                if (x_ct > 727) and (x_ct <= 757) and (y_ct > 515) and (y_ct <= 525):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
            elif (self.NoL == 4):
                if (x_ct > 600) and (x_ct <= 610) and (y_ct > 436) and (y_ct < 466):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
            elif (self.NoL == 5):
                if (x_ct > 657) and (x_ct < 687) and (y_ct > 340) and (y_ct <= 350):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
            elif (self.NoL == 6):
                if (x_ct > 697) and (x_ct < 727) and (y_ct > 515) and (y_ct <= 525):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
            elif (self.NoL == 7):
                if (x_ct > 780) and (x_ct <= 790) and (y_ct > 398) and (y_ct < 428):
                    NoVL[self.NoL] -= 1
                    SumOfvePass += 1
                    self.count = True
        # print(NoVL)

        if self.direction == 'r-s' and not self.turn:
            if not self.crossed and self.x + self.image.get_rect().width > stopLines[
                self.direction]:  # if the image has crossed stop line now
                self.crossed = True
            if (self.x + self.image.get_rect().width <= self.stop or self.crossed or (
                    currentGreen == directionClasses['r-s'] and not isYellow)) and (
                    self.index == 0 or ((self.x + self.image.get_rect().width <
                                         vehicles[self.direction]['vehicles'][self.index - 1].x - movingGap)
            if not vehicles[self.direction]['vehicles'][self.index - 1].turned else True
            )):
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                self.x += self.speed  # move the vehicle

        elif self.direction == 'd-s' and not self.turn:
            if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                self.crossed = True
            if (self.y + self.image.get_rect().height <= self.stop or self.crossed or (
                    currentGreen == directionClasses['d-s'] and not isYellow)) and (
                    self.index == 0 or ((self.y + self.image.get_rect().width <
                                         vehicles[self.direction]['vehicles'][self.index - 1].y +
                                         vehicles[self.direction]['vehicles'][
                                             self.index - 1].image.get_rect().height - movingGap)) if
                    not vehicles[self.direction]['vehicles'][self.index - 1].turned else True):
                self.y += self.speed

        elif self.direction == 'l-s' and not self.turn:
            if not self.crossed and self.x + self.image.get_rect().width < stopLines[self.direction]:
                self.crossed = True
            if ((self.x >= self.stop or self.crossed or (
                    currentGreen == directionClasses['l-s'] and not isYellow)) and (
                    self.index == 0 or ((self.x - self.image.get_rect().width >
                                         vehicles[self.direction]['vehicles'][self.index - 1].x +
                                         vehicles[self.direction]['vehicles'][
                                             self.index - 1].image.get_rect().width + movingGap) if not
            vehicles[self.direction]['vehicles'][
                self.index - 1].turned else True
            ))):
                self.x -= self.speed

        elif self.direction == 'u-s' and not self.turn:
            if not self.crossed and self.y + self.image.get_rect().height < stopLines[self.direction]:
                self.crossed = True
            if ((self.y + self.image.get_rect().height >= self.stop or self.crossed or (
                    currentGreen == directionClasses['u-s'] and not isYellow)) and (
                    self.index == 0 or
                    ((self.y + self.image.get_rect().height >
                      vehicles[self.direction]['vehicles'][self.index - 1].y - movingGap) if
                    not vehicles[self.direction]['vehicles'][self.index - 1].turned else True
                    ))):
                self.y -= self.speed

        elif self.direction == 'r-s' and self.turn:
            if not self.crossed and self.x + self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.x + self.image.get_rect().width > turnRightPos['r-s'][self.vehicleClassID]:
                self.turned = True
                path = "images/down/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if (self.x + self.image.get_rect().width <= self.stop or self.crossed or (
                    currentGreen == directionClasses['r-s'] and not isYellow)) and (
                    self.index == 0 or ((self.x + self.image.get_rect().width <
                                         vehicles[self.direction]['vehicles'][self.index - 1].x - movingGap)
            if not vehicles[self.direction]['vehicles'][self.index - 1].turned
            else (self.y + self.image.get_rect().height <
                  vehicles[self.direction]['vehicles'][self.index - 1].y - movingGap)
            )):
                if self.turned:
                    self.y += self.speed
                else:
                    self.x += self.speed

        elif self.direction == 'd-s' and self.turn:
            if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.y + self.image.get_rect().height > turnRightPos['d-s'][self.vehicleClassID]:
                self.turned = True
                path = "images/right/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if (self.y + self.image.get_rect().height <= self.stop or self.crossed or (
                    currentGreen == directionClasses['d-s'] and not isYellow)) and (
                    self.index == 0 or ((self.y + self.image.get_rect().height <
                                         vehicles[self.direction]['vehicles'][self.index - 1].y +
                                         vehicles[self.direction]['vehicles'][
                                             self.index - 1].image.get_rect().width - movingGap) if
            not vehicles[self.direction]['vehicles'][self.index - 1].turned else
            (self.x - self.image.get_rect().width >
             vehicles[self.direction]['vehicles'][self.index - 1].x + movingGap)
            )):
                if self.turned:
                    self.x -= self.speed
                else:
                    self.y += self.speed

        elif self.direction == 'l-s' and self.turn:
            if not self.crossed and self.x + self.image.get_rect().width < stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.x + self.image.get_rect().width < turnRightPos['l-s'][self.vehicleClassID]:
                self.turned = True
                path = "images/up/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if (self.x - self.image.get_rect().width >= self.stop or self.crossed or (
                    currentGreen == directionClasses['l-s'] and not isYellow)) and (
                    self.index == 0 or ((self.x - self.image.get_rect().width >
                                         vehicles[self.direction]['vehicles'][self.index - 1].x + movingGap)
            if not vehicles[self.direction]['vehicles'][self.index - 1].turned
            else (self.y - self.image.get_rect().height >
                  vehicles[self.direction]['vehicles'][self.index - 1].y + movingGap)
            )):

                if self.turned:
                    self.y -= self.speed
                else:
                    self.x -= self.speed



        elif self.direction == 'u-s' and self.turn:
            if not self.crossed and self.y + self.image.get_rect().height < stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.y + self.image.get_rect().width < turnRightPos['u-s'][self.vehicleClassID]:
                self.turned = True
                path = "images/left/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if ((self.y + self.image.get_rect().height >= self.stop or self.crossed or (
                    currentGreen == directionClasses['u-s'] and not isYellow)) and (
                    self.index == 0 or
                    ((self.y - self.image.get_rect().height >
                      vehicles[self.direction]['vehicles'][self.index - 1].y + movingGap) if
                    not vehicles[self.direction]['vehicles'][self.index - 1].turned else
                    ((self.x + self.image.get_rect().width <
                      vehicles[self.direction]['vehicles'][self.index - 1].x - movingGap))
                    ))):
                if self.turned:
                    self.x += self.speed
                else:
                    self.y -= self.speed

        elif self.direction == 'r-t':
            if not self.crossed and self.x + self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.x + self.image.get_rect().width > turnLeftPos['r-t'][self.vehicleClassID]:
                self.turned = True
                path = "images/up/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if (self.x + self.image.get_rect().width <= self.stop or self.crossed or (
                    currentGreen == directionClasses['r-t'] and not isYellow)) and (
                    self.index == 0 or (((self.x + self.image.get_rect().width <
                                          vehicles[self.direction]['vehicles'][self.index - 1].x - movingGap))
            if not vehicles[self.direction]['vehicles'][self.index - 1].turned
            else ((self.y - self.image.get_rect().height >
                   vehicles[self.direction]['vehicles'][self.index - 1].y + movingGap))
            )):
                if self.turned:
                    self.y -= self.speed
                else:
                    self.x += self.speed

        elif self.direction == 'd-t':
            if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.y + self.image.get_rect().height > turnLeftPos['d-t'][self.vehicleClassID]:
                self.turned = True
                path = "images/right/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if (self.y - self.image.get_rect().height <= self.stop or self.crossed or (
                    currentGreen == directionClasses['d-t'] and not isYellow)) and (
                    self.index == 0 or
                    ((self.y + self.image.get_rect().height <
                      vehicles[self.direction]['vehicles'][self.index - 1].y - movingGap) if
                    not vehicles[self.direction]['vehicles'][self.index - 1].turned else
                    ((self.x + self.image.get_rect().width <
                      vehicles[self.direction]['vehicles'][self.index - 1].x - movingGap))
                    )):
                if self.turned:
                    self.x += self.speed
                else:
                    self.y += self.speed

        elif self.direction == 'l-t':
            if not self.crossed and self.x + self.image.get_rect().width < stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.x + self.image.get_rect().width < turnLeftPos['l-t'][self.vehicleClassID]:
                self.turned = True
                path = "images/down/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if ((self.x >= self.stop or self.crossed or (
                    currentGreen == directionClasses['l-t'] and not isYellow)) and (
                    self.index == 0 or ((self.x >
                                         vehicles[self.direction]['vehicles'][self.index - 1].x +
                                         vehicles[self.direction]['vehicles'][
                                             self.index - 1].image.get_rect().width - movingGap) if not
            vehicles[self.direction]['vehicles'][
                self.index - 1].turned else ((self.y + self.image.get_rect().height <
                                              vehicles[self.direction]['vehicles'][self.index - 1].y - movingGap))
            ))):
                if self.turned:
                    self.y += self.speed
                else:
                    self.x -= self.speed

        elif self.direction == 'u-t':
            if not self.crossed and self.y + self.image.get_rect().height < stopLines[self.direction]:
                self.crossed = True
            if not self.turned and self.y + self.image.get_rect().width < turnLeftPos['u-t'][self.vehicleClassID]:
                self.turned = True
                path = "images/left/" + self.vehicleClass + ".png"
                self.image = pygame.image.load(path)
            if ((self.y + self.image.get_rect().height >= self.stop or self.crossed or (
                    currentGreen == directionClasses['u-t'] and not isYellow)) and (
                    self.index == 0 or
                    ((self.y - self.image.get_rect().height >
                      vehicles[self.direction]['vehicles'][self.index - 1].y + movingGap) if
                    not vehicles[self.direction]['vehicles'][self.index - 1].turned else
                    ((self.x - self.image.get_rect().width >
                      vehicles[self.direction]['vehicles'][self.index - 1].x + movingGap))
                    ))):
                if self.turned:
                    self.x -= self.speed
                else:
                    self.y -= self.speed

            # time.sleep(10)


# Initialization of signals with default values
inited = False


def initialize():
    global signals
    global signalsGroup
    global inited
    signals = []
    signalsGroup = []

    ts1 = Signal((530, 230), (530, 210))
    ts2 = Signal((810, 230), (810, 210))
    ts3 = Signal((810, 570), (810, 550))
    ts4 = Signal((530, 570), (530, 550))
    ts5 = Signal((420, 230), (420, 210))
    ts6 = Signal((920, 230), (920, 210))
    ts7 = Signal((920, 570), (920, 550))
    ts8 = Signal((420, 570), (420, 550))

    signals.append(ts1)
    signals.append(ts2)
    signals.append(ts3)
    signals.append(ts4)
    signals.append(ts5)
    signals.append(ts6)
    signals.append(ts7)
    signals.append(ts8)
    signalsGroup.append(
        TrafficSignalGroup(
            [ts2, ts4], 0, defaultYellow, defaultGreen))
    signalsGroup.append(
        TrafficSignalGroup(
            [ts5, ts7], signalsGroup[currentGreen].yellow + signalsGroup[currentGreen].green,
            defaultYellow, defaultGreen))
    signalsGroup.append(
        TrafficSignalGroup(
            [ts6, ts8], 0, defaultYellow, defaultGreen))
    signalsGroup.append(
        TrafficSignalGroup(
            [ts1, ts3], 0, defaultYellow, defaultGreen))

    if not inited:
        repeat()
        inited = True


def repeat():
    global currentGreen, isYellow, nextGreen, outputNN
    while signalsGroup[currentGreen].green > 0:  # while the timer of current green signal is not zero
        updateValues()
        time.sleep(1)
    isYellow = True  # set yellow signal on
    # reset stop coordinates of lanes and vehicles 

    for directionClass in directionClasses[currentGreen]:
        for vehicle in vehicles[directionClass]['vehicles']:
            vehicle.stop = defaultStop[directionClass]

    while signalsGroup[currentGreen].yellow > 0 and isYellow == True:  # while the timer of current yellow signal is not zero
        updateValues()
        time.sleep(1)
    isYellow = False  # set yellow signal off

    # reset all signal times of current signal to default times
    signalsGroup[currentGreen].green = defaultGreen
    signalsGroup[currentGreen].yellow = defaultYellow
    signalsGroup[currentGreen].red = redSignalDuration

    if (outputNN == 0):
        nextGreen = (nextGreen + 1) % noOfSignalsGroups
    elif (outputNN == 1):
        nextGreen = (nextGreen + 2) % noOfSignalsGroups
    elif (outputNN == 2):
        nextGreen = (nextGreen + 3) % noOfSignalsGroups
    elif (outputNN == 3):
        nextGreen = (nextGreen + 4) % noOfSignalsGroups
    outputNN = -1

    currentGreen = nextGreen  # set next signal as green signal
    # nextGreen = (nextGreen + 1) % noOfSignalsGroups  # set next green signal
    signalsGroup[nextGreen].red = signalsGroup[currentGreen].yellow + signalsGroup[
        currentGreen].green  # set the red time of next to next signal as (yellow time + green time) of next signal
    repeat()


# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignalsGroups):
        if i == currentGreen:
            if not isYellow and signalsGroup[currentGreen].green > 0:
                signalsGroup[i].green -= 1
            else:
                signalsGroup[i].yellow -= 1
        else:
            signalsGroup[i].red -= 1


# Generating vehicles in the simulation
def generateVehicles():
    while True:
        rd = random.randint(0, 7)
        NoVL[rd] = NoVL[rd] + 1
        Vehicle(random.randint(0, 3), ['r-s', 'd-s', 'l-s', 'u-s', 'r-t', 'd-t', 'u-t', 'l-t'][rd],
                random.randint(0, 1), rd)
        # time.sleep(10)
        # Vehicle(vehicleTypes[random.randint(0, 3)], 'l-t')
        # Vehicle(vehicleTypes[random.randint(0, 3)], 'r-t')
        time.sleep(vehiclesSpawntime)


class Main:
    def __init__(self, black, white, background, screen, redSignal, yellowSignal, greenSignal, font):
        # Setting up variables
        self.black = black
        self.white = white
        self.background = background
        self.screen = screen
        self.redSignal = redSignal
        self.yellowSignal = yellowSignal
        self.greenSignal = greenSignal
        self.font = font

    def reset(self):
        global SumOfvePass
        global vehicles
        global simulation
        global currentGreen
        global nextGreen
        global isYellow
        global sum
        global NoVL
        global signals
        global signalsGroup
        global outputNN
        global nextGreen
        
        outputNN = -1
        nextGreen = 0

        signals = []
        signalsGroup = []

        NoVL = [0, 0, 0, 0, 0, 0, 0, 0]
        currentGreen = 0  # Indicates which signal is green currently
        nextGreen = 1  # Indicates which signal will turn green next
        isYellow = False  # Indicates whether yellow signal is on or off
        SumOfvePass = 0
        simulation = pygame.sprite.Group()
        vehicles = {'r-t': {'vehicles': [], 'crossed': 0},
                    'r-s': {'vehicles': [], 'crossed': 0},
                    'l-t': {'vehicles': [], 'crossed': 0},
                    'l-s': {'vehicles': [], 'crossed': 0},
                    'u-t': {'vehicles': [], 'crossed': 0},
                    'u-s': {'vehicles': [], 'crossed': 0},
                    'd-t': {'vehicles': [], 'crossed': 0},
                    'd-s': {'vehicles': [], 'crossed': 0},
                    }

        ts1 = Signal((530, 230), (530, 210))
        ts2 = Signal((810, 230), (810, 210))
        ts3 = Signal((810, 570), (810, 550))
        ts4 = Signal((530, 570), (530, 550))
        ts5 = Signal((420, 230), (420, 210))
        ts6 = Signal((920, 230), (920, 210))
        ts7 = Signal((920, 570), (920, 550))
        ts8 = Signal((420, 570), (420, 550))

        signals.append(ts1)
        signals.append(ts2)
        signals.append(ts3)
        signals.append(ts4)
        signals.append(ts5)
        signals.append(ts6)
        signals.append(ts7)
        signals.append(ts8)
        signalsGroup.append(
            TrafficSignalGroup(
                [ts2, ts4], 0, defaultYellow, defaultGreen))
        signalsGroup.append(
            TrafficSignalGroup(
                [ts5, ts7], signalsGroup[currentGreen].yellow + signalsGroup[currentGreen].green,
                defaultYellow, defaultGreen))
        signalsGroup.append(
            TrafficSignalGroup(
                [ts6, ts8], 0, defaultYellow, defaultGreen))
        signalsGroup.append(
            TrafficSignalGroup(
                [ts1, ts3], 0, defaultYellow, defaultGreen))

    def train_ai(self, genome1, config):
        global outputNN, NoV1, NoV2, NoV3, NoV4, t1, t2, t3, t4
        net = neat.nn.FeedForwardNetwork.create(genome1, config)
        # output = net.activate(
        #     (NoVL[0], NoVL[1], NoVL[2], NoVL[3], NoVL[4], NoVL[5], NoVL[6], NoVL[7]))
        # decision = output.index(max(output))
        # outputNN = decision
        check = 0

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            if (outputNN == -1):
                output = net.activate(
                    (NoVL[0], NoVL[1], NoVL[2], NoVL[3], NoVL[4], NoVL[5], NoVL[6], NoVL[7]))
                decision = output.index(max(output))
                outputNN = decision
                # print(output)

            self.screen.blit(self.background, (0, 0))  # display background in simulation
            for i in range(noOfSignalsGroups):  # display signal and set timer according to current status: green, yello, or red
                if i == currentGreen:
                    if isYellow:
                        signalsGroup[i].signalText = signalsGroup[i].yellow
                        for signal in signalsGroup[i].signalsList:
                            self.screen.blit(self.yellowSignal, signal.cood)

                    else:
                        signalsGroup[i].signalText = signalsGroup[i].green
                        for signal in signalsGroup[i].signalsList:
                            self.screen.blit(self.greenSignal, signal.cood)

                else:
                    if i == nextGreen and signalsGroup[i].red <= 10:
                        signalsGroup[i].signalText = signalsGroup[i].red
                    else:
                        signalsGroup[i].signalText = "---"

                    for signal in signalsGroup[i].signalsList:
                        self.screen.blit(self.redSignal, signal.cood)

            signalTexts = ["", "", "", ""]

            # display signal timer
            for i in range(0, noOfSignalsGroups):
                signalTexts[i] = self.font.render(str(signalsGroup[i].signalText), True, self.white, self.black)
                for signal in signalsGroup[i].signalsList:
                    self.screen.blit(signalTexts[i], signal.timerCood)

            # debug
            # print(NoVL)
            # print(signalsGroup)

            # display the vehicles
            for vehicle in simulation:
                self.screen.blit(vehicle.image, [vehicle.x, vehicle.y])
                vehicle.move()

            # caculate fitness score
            if signalsGroup[currentGreen].green % 2 != 0:
                check = 0
            if (signalsGroup[currentGreen].green % 2 == 0) and (check == 0):
                vesum = 0
                for i in NoVL:
                    vesum += i
                if (vesum != 0): genome1.fitness += 1 / vesum
                check = 1
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(600, 466, 10, 30))
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(627, 340, 30, 10))
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(780, 370, 10, 30))
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(727, 515, 30, 10))
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(600, 436, 10, 30))
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(657, 340, 30, 10))
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(697, 515, 30, 10))
            # pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(780, 398, 10, 30))

            # break the simulation
            vesum = 0
            for i in NoVL:
                vesum += i
            if (SumOfvePass >= 300) or (genome1.fitness >= 5) or (vesum >= 50):
                print("siuuuuuuuuuuuuuuuuu")
                self.reset()
                break
            # print(vesum)
            # display NN indicators
            pygame.font.init()
            my_font = pygame.font.SysFont('Comic Sans MS', 25)
            str1 = "GEN_NUM: " + str(gen)
            str2 = "POP_NUM: " + str(pop)
            str3 = "Score: " + str(genome1.fitness)
            str4 = "Sum vehicles: " + str(vesum)
            str5 = "Sum vehicles pass: " + str(SumOfvePass)
            text_surface = my_font.render(str4, False, (0, 0, 0))
            self.screen.blit(text_surface, (1, 10))
            text_surface = my_font.render(str1, False, (0, 0, 0))
            self.screen.blit(text_surface, (1, 100))
            text_surface = my_font.render(str2, False, (0, 0, 0))
            self.screen.blit(text_surface, (1, 200))
            text_surface = my_font.render(str3, False, (0, 0, 0))
            self.screen.blit(text_surface, (1, 300))
            text_surface = my_font.render(str5, False, (0, 0, 0))
            self.screen.blit(text_surface, (300, 10))
            pygame.display.update()

    # def caculate_finessScore(self, genome1):
    #     sum = 0
    #     for i in NoVL:
    #         sum += i
    #     genome1.fitness += 1 / sum


def eval_genomes(genomes, config):
    global gen, pop, SumOfvePass, NoVL, vehicles
    width, height = 700, 500
    window = pygame.display.set_mode((width, height))
    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    # Colours 
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize 
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)
    background = pygame.image.load('images/intersection.png')
    screen = pygame.display.set_mode(screenSize)

    gen = gen + 1
    pop = 0
    for i, (genome_id1, genome1) in enumerate(genomes):
        SumOfvePass = 0
        for i in range(len(NoVL)):
            NoVL[i] = 0
        if i == len(genomes) - 1:
            break
        pop = pop + 1
        genome1.fitness = 0
        game = Main(black, white, background, screen, redSignal, yellowSignal, greenSignal, font)
        game.train_ai(genome1, config)


def run_neat(config):
    p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-5')

    # p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(1))

    winner = p.run(eval_genomes, 15)
    with open("best.pickle", "wb") as f:
        pickle.dump(winner, f)


if __name__ == "__main__":
    thread1 = threading.Thread(name="initialization", target=initialize, args=())  # initialization
    thread1.daemon = True
    thread1.start()

    pygame.display.set_caption("SIMULATION")

    thread2 = threading.Thread(name="generateVehicles", target=generateVehicles, args=())  # Generating vehicles
    thread2.daemon = True
    thread2.start()
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    run_neat(config)
