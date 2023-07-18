import time
import math
from decimal import Decimal
import json
import pygame
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import Button
from pygame import gfxdraw

planets = []
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
blue = (0, 0, 255)
gray = (150, 150, 150)
green = (0, 255, 0)

#all data gotten from NASA
gravityConstant = 6.673 * 10**-11 #should be 6.67 * 10**-11 but it doesnt apply enough gravity ):

xoffset = 0
yoffset = 0
targetXoffset = 0
targetYoffset = 0

#settings
zoomSpeed = 1.4
timeScale = 250000 #dont go too high with this, it becomes unstable (the lower it is, the more physically correct it is)
planetScale = 1
orbitTraceLength = 0 #0 orbit length for infinite (it does lag if too much)
timePerOrbitSubdivide = .1 #the more frames per, the more performance (in seconds)
targetFPS = 15
drawDistances = False
planetInfo = True
key = True
debug = False
scaleEase = 10
offsetEase = 5
calculationCycleLimit = 0 #(per frame) for less CPU/processing power needed (literally nothing else). zero for no limit
paused = False

#settings functions:
def quit_callback():
	global Done
	Done = True
def pauseSimulation():
    global paused
    paused = not paused
def changeScale(value):
    global planetScale
    planetScale = round(float(value))
def changeTimeScale(value):
    global timeScale
    timeScale = round(float(value))
def toggleDistances():
    global drawDistances
    drawDistances = not drawDistances
def togglePlanetInfo():
    global planetInfo
    planetInfo = not planetInfo
def toggleKey():
    global key
    key = not key
def toggleDebug():
    global debug
    debug = not debug

#pygame initialize
pygame.init()
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
windowWidth = window.get_width()
windowHeight = window.get_height()
pygame.display.set_caption('Gravity Simulator')
icon = pygame.image.load('icon.jpg')
pygame.display.set_icon(icon)

#settings gui
objectScaleSlider = Slider(window, 10, windowHeight - 330, 400, 20, min=1, max=50, step=1, handleColour=(150, 150, 150))
objectScaleOutput = TextBox(window, 425, windowHeight - 340, 175, 40, fontSize=30)
objectScaleOutput.disable()
objectScaleSlider.setValue(25)

timeScaleSlider = Slider(window, 10, windowHeight - 380, 400, 20, min=1, max=3000000, step=1, handleColour=(150, 150, 150))
timeScaleOutput = TextBox(window, 425, windowHeight - 390, 175, 40, fontSize=30)
timeScaleOutput.disable()
timeScaleSlider.setValue(4.5e5)

yPos = windowHeight - 275
pauseButton = Button(window, 0, yPos, 100, 50, text="Pause", fontSize=20, margin=5, onClick=pauseSimulation)
distanceButton = Button(window, 125, yPos, 100, 50, text="Distance Info", fontSize=20, margin=5, onClick=toggleDistances)
planetInfoButton = Button(window, 250, yPos, 100, 50, text="Planet Info", fontSize=20, margin=5, onClick=togglePlanetInfo)
keyButton = Button(window, 375, yPos, 100, 50, text="Toggle Key", fontSize=20, margin=5, onClick=toggleKey)
debugButton = Button(window, 500, yPos, 100, 50, text="Toggle Debug", fontSize=20, margin=5, onClick=toggleDebug)

def normalizeVector(vector):
    x, y = vector
    magnitude = math.sqrt(x ** 2 + y ** 2)
    normalizedVector = [x / magnitude, y / magnitude]
    return normalizedVector

def calculateForceVector(force, coord1, coord2):
    x1, y1 = coord1
    x2, y2 = coord2
    
    #get normalized vector
    direction = (x1 - x2, y1 - y2)
    normalizedVector = normalizeVector(direction)
    #get force vector
    forceVector = (force * normalizedVector[0], force * normalizedVector[1])
    return forceVector
class planet:
	def __init__(self, mass, x, y, radius, xVel, yVel, name, color, light):
		global gravityConstant
		self.mass = mass
		self.xpos = x
		self.ypos = y
		self.xvel = xVel
		self.yvel = yVel
		self.color = color
		self.radius = radius
		self.xaccel = 0
		self.yaccel = 0
		self.name = name
		self.light = light
		self.orbitLines = []
		self.lastOrbitVel = [1, 1]
		self.preCalculatedForce = gravityConstant * self.mass
			
	def applyVelocity(self, dt):
		self.xpos += self.xvel * dt
		self.ypos += self.yvel * dt
	
	def addVelocity(self, xvel, yvel):
		self.xvel += xvel
		self.yvel += yvel
	
	def calculateGravity(self, dt):
		for planet in planets:
			if planet != self:
				distSquared = (math.pow(self.xpos - planet.xpos, 2) + math.pow(self.ypos - planet.ypos, 2))
				accell = planet.preCalculatedForce / distSquared
				xAccel, yAccel = calculateForceVector(accell, (planet.xpos, planet.ypos), (self.xpos, self.ypos))
				self.xvel += xAccel * dt
				self.yvel += yAccel * dt

	def drawDistances(self, scale, xoffset, yoffset):
		global windowHeight, windowWidth
		xoffsetPos = (self.xpos - xoffset)/scale + windowWidth/2
		yoffsetPos = (self.ypos - yoffset)/scale + windowHeight/2
		for planet in planets:
			if planet != self:
				xoffsetPos_2 = (planet.xpos - xoffset)/scale + windowWidth/2
				yoffsetPos_2 = (planet.ypos - yoffset)/scale + windowHeight/2
				pygame.draw.line(window, (150, 150, 150), (xoffsetPos_2, yoffsetPos_2), (xoffsetPos, yoffsetPos))
				distanceToShow = "{:.2E}".format(Decimal(str(int(math.pow(math.pow(self.xpos - planet.xpos, 2) + math.pow(self.ypos - planet.ypos, 2), .5))))) + " (m)"
				accel = planet.preCalculatedForce / (math.pow(self.xpos - planet.xpos, 2) + math.pow(self.ypos - planet.ypos, 2))
				forceToShow = "{:.2E}".format(Decimal(str(accel))) + "(m/s^2)"
				text_to_screen(window, distanceToShow, (xoffsetPos + xoffsetPos_2)/2, (yoffsetPos + yoffsetPos_2)/2, 12)
				text_to_screen(window, forceToShow, (xoffsetPos + xoffsetPos_2)/2, (yoffsetPos + yoffsetPos_2)/2 + 12, 12)
	def draw(self, scale, xoffset, yoffset):
		global windowHeight, windowWidth, orbitTraceLength, distancePerOrbitSubdivide
		xoffsetPos = clampNum((self.xpos - xoffset)/scale + windowWidth/2, 10000, -10000)
		yoffsetPos = clampNum((self.ypos - yoffset)/scale + windowHeight/2, 10000, -10000) #clamps are beause the aa draw complains about it

		pastLinePeice = (0, 0)
		for linePeice in self.orbitLines:
			startPos = (((linePeice[0] - xoffset)/scale + windowWidth/2), ((linePeice[1] - yoffset)/scale + windowHeight/2))
			if pastLinePeice != (0, 0):
				pygame.draw.line(window, self.color, startPos, pastLinePeice)
			pastLinePeice = startPos
		pygame.draw.line(window, self.color, (xoffsetPos, yoffsetPos), pastLinePeice)

		planetDrawScale = min(self.radius/scale*planetScale, 1000)
		if planetDrawScale > 1:
			gfxdraw.aacircle(window, int(xoffsetPos), int(yoffsetPos), int(planetDrawScale), self.color)
			gfxdraw.filled_circle(window, int(xoffsetPos), int(yoffsetPos), int(planetDrawScale), self.color)
		text_to_screen(window, self.name, xoffsetPos + planetDrawScale, yoffsetPos - 12 - planetDrawScale, clampNum(int(planetDrawScale), 70, 15))
	def getScreenPos(self):
		global windowWidth, windowHeight
		return ((self.xpos - xoffset)/scale + windowWidth/2, (self.ypos - yoffset)/scale + windowHeight/2)
	def addOrbitSub(self):
		global orbitTraceLength
		self.orbitLines.append((self.xpos, self.ypos))
		#trim orbit line
		if len(self.orbitLines) > orbitTraceLength and orbitTraceLength != 0:
			del self.orbitLines[0]

def getScaledLinePoints(points, scale, xoffset, yoffset):
    newList = []
    for point in points:
        scaledPoint = [((point[0] - xoffset)/scale + windowWidth/2), ((point[1] - yoffset)/scale + windowHeight/2)]
        newList.append(scaledPoint)
    return newList

def pointToScreen(xpos, ypos):
    global scale, windowHeight, windowWidth, xoffset, yoffset
    return ((xpos - xoffset)/scale + windowWidth/2, (ypos - yoffset)/scale + windowHeight/2)

def clampNum(num, upper, lower):
	return max(min(num, upper), lower)

def text_to_screen(screen, text, x, y, size=50, color=(200, 000, 000), font_type=pygame.font.get_default_font()):
	text = str(text)
	font = pygame.font.Font(font_type, size)
	text = font.render(text, True, color)
	screen.blit(text, (x, y))

def checkEvents():
	global windowHeight, windowWidth, targetScale, zoomSpeed
	events = pygame.event.get()
	for event in events:
		if event.type == pygame.QUIT:
			exit()
		elif event.type == pygame.VIDEORESIZE:
			windowWidth = window.get_width()
			windowHeight = window.get_height()
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				setFocusPlanet(pygame.mouse.get_pos())
			if event.button == 4:
				targetScale *= zoomSpeed
			elif event.button == 5 and scale > 1:
				targetScale /= zoomSpeed
    
    #settings
	objectScaleOutput.setText("Scale: " + str(objectScaleSlider.getValue()) + "X")
	timeScaleOutput.setText("Time: " + getScientificNotation(timeScaleSlider.getValue()) + "X")
	changeScale(objectScaleSlider.getValue())
	changeTimeScale(timeScaleSlider.getValue())
	pygame_widgets.update(events)
	pygame.display.update()

def drawAll(scale, xoffset, yoffset, day, year, calculationFrames, timeBetweenDraw, drawFrameCount):
	global totalPlanets, selectedPlanet, planetScale
	window.fill(black)
	for planet in planets:
		planet.draw(scale, xoffset, yoffset)
		if planet == selectedPlanet and drawDistances:
			planet.drawDistances(scale, xoffset, yoffset)

	#debug
	increment = 18
	numberOfDebugs = 0
	debugColor = gray
	if debug:
		text_to_screen(window, "Debug:", 1, increment * (numberOfDebugs + 0), 19, debugColor)
		text_to_screen(window, "Years: " + str(int(year)), 1, increment * (numberOfDebugs + 1), 16, debugColor)
		text_to_screen(window, "Days: " + str(int(day)), 1, increment * (numberOfDebugs + 2), 16, debugColor)
		text_to_screen(window, "FPS: " + str(drawFrameCount) + " / " + str(int(1/timeBetweenDraw)), 1, increment * (numberOfDebugs + 3), 16, debugColor)
		text_to_screen(window, "Cycles/Frame: " + str(calculationFrames), 1, increment * (numberOfDebugs + 4), 16, debugColor)
		if paused:
			text_to_screen(window, "Cycles/Second: 0", 1, increment * (numberOfDebugs + 5), 16, debugColor)
			text_to_screen(window, "Cycles per planet/Frame: 0", 1, increment * (numberOfDebugs + 6), 16, debugColor)
			text_to_screen(window, "Cycles per planet/Second: 0", 1, increment * (numberOfDebugs + 7), 16, debugColor)
		else:
			text_to_screen(window, "Cycles per planet/Frame: " + str(int(calculationFrames/totalPlanets)), 1, increment * (numberOfDebugs + 5), 16, debugColor)
			text_to_screen(window, "Cycles per planet/Second: " + str(int(calculationFrames * drawFrameCount / totalPlanets)), 1, increment * (numberOfDebugs + 6), 16, debugColor)
			text_to_screen(window, "Cycles/Second: " + str(int(calculationFrames * drawFrameCount)), 1, increment * (numberOfDebugs + 7), 16, debugColor)
		numberOfDebugs += 9

	#key
	keyColor = gray
	if key:
		text_to_screen(window, "Key:", 1, increment * (numberOfDebugs + 0), 19, keyColor)
		text_to_screen(window, "1 meter = " + getScientificNotation(scale) + " meters", 1, increment * (numberOfDebugs + 1), 16, keyColor)
		text_to_screen(window, "Scale: " + str(planetScale) + "X", 1, increment * (numberOfDebugs + 2), 16, keyColor)
		if paused:
			text_to_screen(window, "Paused", 1, increment * (numberOfDebugs + 3), 16, keyColor)
		else:
			text_to_screen(window, "1 sec = " + str(getScientificNotation(timeScale)) + " secs", 1, increment * (numberOfDebugs + 3), 16, keyColor)
		numberOfDebugs += 5

	#planet info
	planetInfoColor = gray
	if planetInfo:
		text_to_screen(window, selectedPlanet.name + ":", 1, increment * (numberOfDebugs + 0), 19, planetInfoColor)
		text_to_screen(window, "Velocity: (" + getScientificNotation(selectedPlanet.xvel) + ", " + getScientificNotation(selectedPlanet.yvel) + ") (m/s)", 1, increment * (numberOfDebugs + 1), 16, planetInfoColor)
		text_to_screen(window, "Speed: " + getScientificNotation(math.pow(math.pow(selectedPlanet.xvel, 2) + math.pow(selectedPlanet.yvel, 2), .5)) + " (m/s)", 1, increment * (numberOfDebugs + 2), 16, planetInfoColor)
		text_to_screen(window, "Mass: " + getScientificNotation(selectedPlanet.mass) + " (Kg)", 1, increment * (numberOfDebugs + 3), 16, planetInfoColor)
		text_to_screen(window, "Radius: " + getScientificNotation(selectedPlanet.radius) + " (m)", 1, increment * (numberOfDebugs + 4), 16, planetInfoColor)
	

def calculatePhysics(dt):
	for planet in planets:
		planet.calculateGravity(dt)

	for planet in planets:
		planet.applyVelocity(dt)

def loadPlanets():
	global planets, planet
	jsonFile = open("planets.json")
	jsonData = json.load(jsonFile)
	for planetInfo in jsonData:
		if planetInfo['relativeTo'] == "None":
			planets.append(planet(planetInfo['mass'], planetInfo['initialXPos'], planetInfo['initialYPos'], planetInfo['radius'], planetInfo['initialXVel'], planetInfo['initialYVel'], planetInfo['name'], (planetInfo['color'][0], planetInfo['color'][1], planetInfo['color'][2]), planetInfo['light']))
		else:
			for secondPlanet in jsonData:
				if secondPlanet['name'] == planetInfo['relativeTo']:
					relativePlanetInfo = secondPlanet
			planets.append(planet(planetInfo['mass'], planetInfo['initialXPos'] + relativePlanetInfo['initialXPos'], planetInfo['initialYPos'] + relativePlanetInfo['initialYPos'], planetInfo['radius'], planetInfo['initialXVel'] + relativePlanetInfo['initialXVel'], planetInfo['initialYVel'] + relativePlanetInfo['initialYVel'], planetInfo['name'], (planetInfo['color'][0], planetInfo['color'][1], planetInfo['color'][2]), planetInfo['light']))

def getScientificNotation(num):
    return "{:.2E}".format(Decimal(str(num)))

def setFocusPlanet(mouseClickPosition):
	global planets, selectedPlanet, targetXoffset, targetYoffset
	selectedPlanet = planets[0]
	closestDist = distance(planets[0].getScreenPos(), mouseClickPosition)
	for planet in planets:
		if distance(planet.getScreenPos(), mouseClickPosition) < closestDist:
			selectedPlanet = planet
			closestDist = distance(planet.getScreenPos(), mouseClickPosition)

def distance(point1, point2):
    return math.pow(math.pow(point1[0] - point2[0], 2) + math.pow(point1[1] - point2[1], 2), .5)

#loading planets and a few variables before start
loadPlanets()
totalPlanets = len(planets)
selectedPlanet = planets[0]
scale = planets[0].radius
targetScale = scale
pastTime = time.time()
pastDrawTime = time.time()
pastSecond = time.time()
pastOrbitSub = time.time()
frameCount = 0
drawFrameCount = 0
frameCount = 0
dayCounter = 0
yearCounter = 0
orbitFramesCounter = 0
currentFPS = 0
timeBetweenDraws = 1/targetFPS
startPauseTimer = 1 #an initial pause so that there aren't any freezes in the start that mess things up

#main loop
while True:
	if (frameCount <= calculationCycleLimit - 1 or calculationCycleLimit == 0): #physics
		dt = time.time() - pastTime
		pastTime = time.time()
		frameCount += 1
		startPauseTimer -= dt
		if not paused and startPauseTimer < 0:
			calculatePhysics(dt * timeScale)
			dayCounter += (dt * timeScale)/(24 * 60 * 60) #keeping track of days
			if dayCounter >= 365:
				dayCounter = 0
				yearCounter += 1

	if time.time() - pastDrawTime >= timeBetweenDraws: #draw everything
		if time.time() - pastSecond >= 1: #getting fps
			pastSecond = time.time()
			currentFPS = drawFrameCount
			drawFrameCount = 0

		if time.time() - pastOrbitSub >= timePerOrbitSubdivide: #orbit markings
			pastOrbitSub = time.time()
			for planet in planets:
				planet.addOrbitSub()

		#cam moving
		scale += (targetScale - scale) * scaleEase * timeBetweenDraws
		xoffset += (selectedPlanet.xpos - xoffset) * offsetEase * timeBetweenDraws
		yoffset += (selectedPlanet.ypos - yoffset) * offsetEase * timeBetweenDraws

		pastDrawTime = time.time()
		drawAll(scale, xoffset, yoffset, dayCounter, yearCounter, frameCount, timeBetweenDraws, currentFPS)
		if startPauseTimer > 0:
			text_to_screen(window, "Loading...", windowWidth/2, windowHeight/2, 30, white)
		checkEvents() #for resize, close windows, and interaction
		drawFrameCount += 1
		frameCount = 0

		pygame.display.flip() #update display

"""solar system
[
	{
		"name": "Sun",
		"mass": 1.9885e30,
		"radius": 6.96e8,
		"initialXPos": 0,
		"initialYPos": 0,
		"initialXVel": 0,
		"initialYVel": 0,
		"color": [255, 150, 0],
		"relativeTo": "None",
		"light": 5
	},
	{
		"name": "Mercury",
		"mass": 0.33e24,
		"radius": 2439500,
		"initialXPos": 0,
		"initialYPos": 57900e6,
		"initialXVel": 47400,
		"initialYVel": 0,
		"color": [26, 26, 26],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Venus",
		"mass": 4.87e24,
		"radius": 6052000,
		"initialXPos": 0,
		"initialYPos": 108200e6,
		"initialXVel": 35000,
		"initialYVel": 0,
		"color": [230, 230, 230],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Earth",
		"mass": 5.97e24,
		"radius": 6380000,
		"initialXPos": 0,
		"initialYPos": 1.496e11,
		"initialXVel": 2.98e4,
		"initialYVel": 0,
		"color": [47, 106, 105],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Moon",
		"mass": 0.073e24,
		"radius": 1737500,
		"initialXPos": 0,
		"initialYPos": 384e6,
		"initialXVel": 1000,
		"initialYVel": 0,
		"color": [150, 150, 150],
		"relativeTo": "Earth",
		"light": 0
	},
	{
		"name": "Mars",
		"mass": 0.642e24,
		"radius": 3396000,
		"initialXPos": 0,
		"initialYPos": 228.0e9,
		"initialXVel": 24.1e3,
		"initialYVel": 0,
		"color": [153, 61, 0],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Jupiter",
		"mass": 1898e24,
		"radius": 71492000,
		"initialXPos": 0,
		"initialYPos": 778.5e9,
		"initialXVel": 13.1e3,
		"initialYVel": 0,
		"color": [176, 127, 53],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Saturn",
		"mass": 568e24,
		"radius": 60268000,
		"initialXPos": 0,
		"initialYPos": 1432.0e9,
		"initialXVel": 9.7e3,
		"initialYVel": 0,
		"color": [176, 143, 54],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Uranus",
		"mass": 86.8e24,
		"radius": 25559000,
		"initialXPos": 0,
		"initialYPos": 2867.0e9,
		"initialXVel": 6.8e3,
		"initialYVel": 0,
		"color": [85, 128, 170],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Neptune",
		"mass": 102e24,
		"radius": 24764000,
		"initialXPos": 0,
		"initialYPos": 4515.0e9,
		"initialXVel": 5.4e3,
		"initialYVel": 0,
		"color": [54, 104, 150],
		"relativeTo": "Sun",
		"light": 0
	}
]"""

""" dobble:
[
	{
		"name": "Sun-1",
		"mass": 1.9885e30,
		"radius": 6.96e8,
		"initialXPos": 0,
		"initialYPos": 0,
		"initialXVel": -2e4,
		"initialYVel": 0,
		"color": [255, 150, 0],
		"relativeTo": "None",
		"light": 5
	},
	{
		"name": "Sun-2",
		"mass": 1.9885e30,
		"radius": 6.96e8,
		"initialXPos": 0,
		"initialYPos": 1.496e11,
		"initialXVel": 2e4,
		"initialYVel": 0,
		"color": [255, 150, 0],
		"relativeTo": "None",
		"light": 5
	},
	{
		"name": "Planet",
		"mass": 5.97e24,
		"radius": 6380000,
		"initialXPos": 0,
		"initialYPos": 3e11,
		"initialXVel": -3e4,
		"initialYVel": 0,
		"color": [47, 106, 105],
		"relativeTo": "None",
		"light": 0
	}
]"""