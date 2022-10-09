import random
import time
import threading
import pygame
import os
import neat
import pickle


#define NN
gen = 0
pop = 0
outputNN = -1

#num of vehicles
NoV1 = 0
NoV2 = 0
NoV3 = 0
NoV4 = 0

# cu lua algo
t1 = 0
t2 = 0
t3 = 0 
t4 = 0

# Default values of signal timers
defaultGreen = {0:10, 1:10, 2:10, 3:10}
defaultRed = 150
defaultYellow = 5

signals = []
noOfSignals = 4
currentGreen = 0   # Indicates which signal is green currently
nextGreen = (currentGreen+1)%noOfSignals    # Indicates which signal will turn green next
currentYellow = 0   # Indicates whether yellow signal is on or off 

speeds = {'car':2.25, 'bus':1.8, 'truck':1.8, 'bike':2.5}  # average speeds of vehicles

# Coordinates of vehicles' start
x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
stoppingGap = 25    # stopping gap
movingGap = 25   # moving gap

# set allowed vehicle types here
allowedVehicleTypes = {'car': True, 'bus': True, 'truck': True, 'bike': True}
allowedVehicleTypesList = []
vehiclesTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
vehiclesNotTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
rotationAngle = 3
mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
# set random or default green signal time here 
randomGreenSignalTimer = True
# set random green signal time range here 
randomGreenSignalTimerRange = [10,20]

pygame.init()
simulation = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        
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
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)

        if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):   
            if(direction=='right'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                - vehicles[direction][lane][self.index-1].image.get_rect().width 
                - stoppingGap         
            elif(direction=='left'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                + vehicles[direction][lane][self.index-1].image.get_rect().width 
                + stoppingGap
            elif(direction=='down'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                - vehicles[direction][lane][self.index-1].image.get_rect().height 
                - stoppingGap
            elif(direction=='up'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                + vehicles[direction][lane][self.index-1].image.get_rect().height 
                + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Set new starting and stopping coordinate
        if(direction=='right'):
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif(direction=='left'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif(direction=='down'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif(direction=='up'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.image.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.x+self.image.get_rect().width<stopLines[self.direction]+40):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):               
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 2.4
                            self.y -= 2.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):
                                self.y -= self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.x+self.image.get_rect().width<mid[self.direction]['x']):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                 
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 2
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y+self.image.get_rect().height)<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):
                                self.y += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap))):                
                        self.x += self.speed
                else:
                    if((self.crossedIndex==0) or (self.x+self.image.get_rect().width<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):                 
                        self.x += self.speed
        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.image.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.y+self.image.get_rect().height<stopLines[self.direction]+50):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 1.2
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.x + self.image.get_rect().width) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):
                                self.x += self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.y+self.image.get_rect().height<mid[self.direction]['y']):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 2.5
                            self.y += 2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))): 
                                self.x -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap))):                
                        self.y += self.speed
                else:
                    if((self.crossedIndex==0) or (self.y+self.image.get_rect().height<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):                
                        self.y += self.speed
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.x>stopLines[self.direction]-70):
                        if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else: 
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 1
                            self.y += 1.2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y + self.image.get_rect().height) <(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y  -  movingGap))):
                                self.y += self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.x>mid[self.direction]['x']):
                        if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 1.8
                            self.y -= 2.5
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height +  movingGap))):
                                self.y -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x>=self.stop or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.x>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.y>stopLines[self.direction]-60):
                        if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 2
                            self.y -= 1.2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):
                                self.x -= self.speed
                elif(self.lane == 2):
                    if(self.crossed==0 or self.y>mid[self.direction]['y']):
                        if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 1
                            self.y -= 1
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width - movingGap))):
                                self.x += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y>=self.stop or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.y>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed 

# Initialization of signals with default values
def initialize():
    minTime = randomGreenSignalTimerRange[0]
    maxTime = randomGreenSignalTimerRange[1]
    ts1 = TrafficSignal(0, defaultYellow, 10)
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, random.randint(minTime,maxTime))
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, 10)
    signals.append(ts3)
    ts4 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, random.randint(minTime,maxTime))
    signals.append(ts4)
    repeat()

def repeat():
    global currentGreen, currentYellow, nextGreen, outputNN
    while(signals[currentGreen].green>0):   # while the timer of current green signal is not zero
        updateValues()
        time.sleep(1)
    currentYellow = 1   # set yellow signal on
    # reset stop acoordinates of lanes and vehicles 
    for i in range(0,3):
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            # vehicle.stop = defaultStop[directionNumbers[currentGreen]]
            vehicle.stop = defaultStop[directionNumbers[(currentGreen + 3)%noOfSignals]]
    while(signals[currentGreen].yellow>0):  # while the timer of current yellow signal is not zero
        updateValues()
        time.sleep(1)
    currentYellow = 0   # set yellow signal off
    
    # reset all signal times of current signal to default
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
    signals[(currentGreen + 2)%noOfSignals].yellow = defaultYellow
    signals[(currentGreen + 2)%noOfSignals].red = defaultRed
    if (outputNN == 0):
        signals[currentGreen].green = 5
        signals[(currentGreen + 2)%noOfSignals].green = 5
    else:
        signals[currentGreen].green = 1
        signals[(currentGreen + 2)%noOfSignals].green = 1
    outputNN = -1

       
    currentGreen = nextGreen # set next signal as green signal
    nextGreen = (currentGreen+1)%noOfSignals    # set next green signal 
    # print(currentGreen)
    signals[nextGreen].red = signals[currentGreen].yellow+signals[currentGreen].green
    signals[(nextGreen + 2)%noOfSignals].red = signals[currentGreen].yellow+signals[currentGreen].green     # set the red time of next to next signal as (yellow time + green time) of next signal
    repeat()  

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
                # signals[(i + 2)%noOfSignals].green-=1
            else:
                signals[i].yellow-=1
                signals[(i + 2)%noOfSignals].yellow-=1
        else:
            signals[i].red-=1
            # signals[(i + 2)%noOfSignals].red-=1


# Generating vehicles in the simulation
def generateVehicles():
    global NoV1, NoV2, NoV3, NoV4
    while(True):
        vehicle_type = random.choice(allowedVehicleTypesList)
        lane_number = random.randint(1,2)
        will_turn = 0
        if(lane_number == 1):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        elif(lane_number == 2):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        temp = random.randint(0,99)
        direction_number = 0
        dist = [25,50,75,100]
        if(temp<dist[0]):
            NoV1 = NoV1 + 1
            direction_number = 0
        elif(temp<dist[1]):
            NoV2 = NoV2 + 1
            direction_number = 1
        elif(temp<dist[2]):
            NoV3 = NoV3 + 1
            direction_number = 2
        elif(temp<dist[3]):
            NoV4 = NoV4 + 1
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(1)

class Main:
    def __init__(self, black, white, background, screen, redSignal, yellowSignal, greenSignal, font):             
        global allowedVehicleTypesList
        i = 0
        for vehicleType in allowedVehicleTypes:
            if(allowedVehicleTypes[vehicleType]):
                allowedVehicleTypesList.append(i)
            i += 1
        thread1 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
        thread1.daemon = True
        thread1.start()
        

        pygame.display.set_caption("SIMULATION")


        thread2 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
        thread2.daemon = True
        thread2.start()
        #Setting up variables
        self.black = black
        self.white = white
        self.background = background
        self.screen = screen
        self.redSignal = redSignal
        self.yellowSignal = yellowSignal
        self.greenSignal = greenSignal
        self.font = font

    def train_ai(self, genome1, config):
        global outputNN, NoV1, NoV2, NoV3, NoV4, t1, t2, t3, t4
        net1 = neat.nn.FeedForwardNetwork.create(genome1, config)
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit()
            if (outputNN == -1):
                output1 = net1.activate(
                    (NoV1, NoV2, NoV3, NoV4))
                decision1 = output1.index(max(output1))
                outputNN = decision1
                print(outputNN)
            

            self.screen.blit(self.background,(0,0))   # display background in simulation
            for i in range(0,noOfSignals):  # display signal and set timer according to current status: green, yello, or red
                if(i==currentGreen):
                    if(currentYellow==1):
                        if(signals[i].yellow==0):
                            signals[i].signalText = "STOP"
                            signals[(i + 2)%noOfSignals].signalText = "STOP"
                        else:
                            signals[i].signalText = signals[i].yellow
                            signals[(i + 2)%noOfSignals].signalText = signals[(i + 2)%noOfSignals].yellow
                        self.screen.blit(self.yellowSignal, signalCoods[i])
                        self.screen.blit(self.yellowSignal, signalCoods[(i + 2)%noOfSignals])
                    else:
                        if(signals[i].green==0):
                            signals[i].signalText = "SLOW"
                            signals[(i + 2)%noOfSignals].signalText = "SLOW"
                            # vehicles[directionNumbers[i]]['crossed'] = 0
                            if (NoV1 != 0) or (NoV2 != 0) or (NoV3 != 0) or (NoV4 != 0): 
                                genome1.fitness += 1 / (NoV1 + NoV3 + NoV2 + NoV4) 
                                print(1)
                        else:
                            signals[i].signalText = signals[i].green
                            signals[(i + 2)%noOfSignals].signalText = signals[i].green
                        self.screen.blit(self.greenSignal, signalCoods[i])
                        self.screen.blit(self.greenSignal, signalCoods[(i + 2)%noOfSignals])
                elif(i == (currentGreen + 2)%noOfSignals):
                    if(currentYellow==1):
                        if(signals[(i + 2)%noOfSignals].yellow==0):
                            signals[(i + 2)%noOfSignals].signalText = "STOP"
                        else:
                            signals[(i + 2)%noOfSignals].signalText = signals[(i + 2)%noOfSignals].yellow
                        self.screen.blit(self.yellowSignal, signalCoods[(i + 2)%noOfSignals])
                    else:
                        if(signals[(i + 2)%noOfSignals].green==0):
                            signals[(i + 2)%noOfSignals].signalText = "SLOW"
                            # vehicles[directionNumbers[(i + 2)%noOfSignals]]['crossed'] = 0
                        else:
                            signals[(i + 2)%noOfSignals].signalText = signals[(i + 2)%noOfSignals].green
                            signals[(i + 2)%noOfSignals].signalText = signals[(i + 2)%noOfSignals].green
                        self.screen.blit(self.greenSignal, signalCoods[(i + 2)%noOfSignals])
                else:
                    if(signals[i].red<=10):
                        if(signals[i].red==0):
                            signals[i].signalText = "GO"
                            signals[(i + 2)%noOfSignals].signalText = "GO"
                            if (NoV1 != 0) or (NoV2 != 0) or (NoV3 != 0) or (NoV4 != 0): genome1.fitness += 1 / (NoV1 + NoV3 + NoV2 + NoV4)
                        else:
                            signals[i].signalText = signals[i].red
                            signals[(i + 2)%noOfSignals].signalText = signals[i].red
                    else:
                        signals[i].signalText = "---"
                        signals[(i + 2)%noOfSignals].signalText = "---"
                    self.screen.blit(self.redSignal, signalCoods[i])
                    self.screen.blit(self.redSignal, signalCoods[(i + 2)%noOfSignals])
            signalTexts = ["","","",""]

            # display signal timer and vehicle count
            for i in range(0,noOfSignals):  
                signalTexts[i] = self.font.render(str(signals[i].signalText), True, self.white, self.black)
                self.screen.blit(signalTexts[i],signalTimerCoods[i]) 


            for i in range(0, noOfSignals):
                if (i == 0) and (t1 != vehicles[directionNumbers[i]]['crossed']):
                    NoV1 = NoV1 - 1
                    t1 = vehicles[directionNumbers[i]]['crossed']                   
                elif (i == 1) and (t2 != vehicles[directionNumbers[i]]['crossed']):
                    NoV2 = NoV2 - 1
                    t2 = vehicles[directionNumbers[i]]['crossed']    
                elif (i == 2) and (t3 != vehicles[directionNumbers[i]]['crossed']):
                    NoV3 = NoV3 - 1
                    t3 = vehicles[directionNumbers[i]]['crossed']
                elif(i == 4) and (t4 != vehicles[directionNumbers[i]]['crossed']):
                    NoV4 = NoV4 - 1
                    t4 = vehicles[directionNumbers[i]]['crossed']
                    #print(1)
                    
                #print(t2, " ", vehicles[directionNumbers[1]]['crossed'])
            
            # print("1:", vehicles[directionNumbers[0]]['crossed'], "2:", vehicles[directionNumbers[1]]['crossed'], "3:", vehicles[directionNumbers[2]]['crossed'], "4:", vehicles[directionNumbers[3]]['crossed'])
            # print("1:", NoV1, "2:", NoV2, "3:", NoV3, "4:", NoV4)
            # for i in range(0, noOfSignals):
            #     if (i == currentGreen):
            #         chk = (i + 1) % noOfSignals
            #         if (chk == 0) or (chk == 2) or (NoV1 != 0) or (NoV3 != 0):
            #             genome1.fitness += 1 / (NoV1 + NoV3)
            #         elif (chk == 1) or (chk == 3) or (NoV2 != 0) or (NoV4 != 0):
            #             genome1.fitness += 1 / (NoV2 + NoV4)
            
            if (genome1.fitness >= 10): break
            #display NN indicators
            pygame.font.init()
            my_font = pygame.font.SysFont('Comic Sans MS', 25)
            str1 = "GEN_NUM: " + str(gen)
            str2 = "POP_NUM: " + str(pop)
            str3 = "Score: " + str(genome1.fitness)
            text_surface = my_font.render(str1, False, (0, 0, 0))
            self.screen.blit(text_surface,(1,100))
            text_surface = my_font.render(str2, False, (0, 0, 0))
            self.screen.blit(text_surface,(1, 200))
            text_surface = my_font.render(str3, False, (0, 0, 0))
            self.screen.blit(text_surface,(1,300))

            
            
            # display the vehicles
            for vehicle in simulation:  
                self.screen.blit(vehicle.image, [vehicle.x, vehicle.y])
                # vehicle.render(screen)
                vehicle.move()
            pygame.display.update()
            

           



def eval_genomes(genomes, config):
    global gen, pop
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
    for i, (genome_id1, genome1) in enumerate(genomes):
        if i == len(genomes) - 1:
            break
        pop = pop + 1
        genome1.fitness = 0
        game = Main(black, white, background, screen, redSignal, yellowSignal, greenSignal, font)
        game.train_ai(genome1, config)


def run_neat(config):
    #p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-7')
    
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(1))

    winner = p.run(eval_genomes, 10)
    with open("best.pickle", "wb") as f:
        pickle.dump(winner, f)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")

    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    run_neat(config)

