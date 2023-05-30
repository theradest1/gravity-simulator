import pygame
import time
import random
import math
import multiprocessing
import json
from decimal import Decimal
from pygame import gfxdraw

planets = []

black = (0, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)

#all data gotten from NASA
#only current problem is that the gravity constant isnt right
#planets are not to scale (they couldn't be seen if they were)
gravityConstant = 4 * 10**-11 #should be 6.67 * 10**-11 but it doesnt apply enough gravity ):
xoffset = 0
yoffset = 0
targetXoffset = 0
targetYoffset = 0
zoomSpeed = 1.2
timeScale = 200000#5000 #dont go too high with this, it becomes unstable (the lower it is, the more physically correct it is)
planetScale = 25
orbitTraceLength = 0 #0 orbit length for infinite (it does lag if too much)
timePerOrbitSubdivide = .1 #the more frames per, the more performance (in seconds)
#distancePerOrbitSubdivide = 3e9
#velocityRatioOrbitSub = 1.5
#velocityRatioOrbitSubInvert = 1/velocityRatioOrbitSub #dont change

windowWidth = 800
windowHeight = 800
pygame.init()
window = pygame.display.set_mode((windowWidth, windowHeight), pygame.RESIZABLE)

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
		self.preCalculatedForce = gravityConstant * self.mass
		self.orbitLines = []
		#self.distanceFromLastOrbitSubdivide = 0
		self.lastOrbitVel = [1, 1]
			
	def applyVelocity(self, dt):
		self.xpos += self.xvel * dt
		self.ypos += self.yvel * dt
	
	def addVelocity(self, xvel, yvel):
		self.xvel += xvel
		self.yvel += yvel
	
	def calculateGravity(self, dt):
		for planet in planets:
			if planet != self and math.pow(math.pow(self.xpos - planet.xpos, 2) + math.pow(self.ypos - planet.ypos, 2), .5) > self.radius + planet.radius:
				distSquared = math.pow(self.xpos - planet.xpos, 2) + math.pow(self.ypos - planet.ypos, 2)
				
				xAccel = planet.preCalculatedForce / distSquared * dt
				if self.xpos < planet.xpos:
					self.xvel += xAccel
				elif self.xpos > planet.xpos:
					self.xvel -= xAccel
				
				yAccel = planet.preCalculatedForce / distSquared * dt
				if self.ypos < planet.ypos:
					self.yvel += yAccel
				elif self.ypos > planet.ypos:
					self.yvel -= yAccel
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
			

				#self.yvel += yforce/self.mass
	def draw(self, scale, xoffset, yoffset):
		global windowHeight, windowWidth, orbitTraceLength, distancePerOrbitSubdivide
		xoffsetPos = clampNum((self.xpos - xoffset)/scale + windowWidth/2, 10000, -10000)
		yoffsetPos = clampNum((self.ypos - yoffset)/scale + windowHeight/2, 10000, -10000) #clamps are beause the aa draw complains about it
		planetDrawScale = clampLower(clampUpper(self.radius/scale*planetScale, 1000), 1)
		#segments = 20
		#colorStep = 5
		#if planetDrawScale > 1:
		#	for i in range(int(planetDrawScale), int(planetDrawScale/2), -1):
		#		colorChange = i
		#		segmentColor = (clampUpper(self.color[0] + colorChange, 255), clampUpper(self.color[1] + colorChange, 255), clampUpper(self.color[2] + colorChange, 255))
		#		pygame.draw.circle(window, segmentColor, (xoffsetPos, yoffsetPos), i)
		#else:
		
		gfxdraw.aacircle(window, int(xoffsetPos), int(yoffsetPos), int(planetDrawScale), self.color)
		gfxdraw.filled_circle(window, int(xoffsetPos), int(yoffsetPos), int(planetDrawScale), self.color)
		#pygame.draw.circle(window, self.color, (xoffsetPos, yoffsetPos), planetDrawScale)

		"""if self.light != 0:
			dist = int(self.light * planetDrawScale)
			step = 5
			for radius in range(0, dist, step):
				light = 255 - clampNum(radius/dist*255, 255, 0)
				pygame.draw.circle(window, (light, light, light), (xoffsetPos, yoffsetPos), radius, step + 1)"""
		#pygame.draw.line(window, (255, 0, 0), (xoffsetPos, yoffsetPos), (self.xvel/scale + xoffsetPos, self.yvel/scale + yoffsetPos))
		text_to_screen(window, self.name, xoffsetPos + planetDrawScale, yoffsetPos - 12 - planetDrawScale, clampNum(int(planetDrawScale), 70, 10))
		
		#print orbit lines
		#pastLinePeice = (0, 0)
		
		#if len(self.orbitLines) >= 3:
		#	gfxdraw.bezier(window, getScaledLinePoints(self.orbitLines, scale, xoffset, yoffset) + [[xoffsetPos, yoffsetPos]], 2, self.color)
		
		
		#velChange = [self.xvel/self.lastOrbitVel[0], self.yvel/self.lastOrbitVel[1]]
		#if velChange[0] > velocityRatioOrbitSub or velChange[0] < velocityRatioOrbitSubInvert or velChange[1] > velocityRatioOrbitSub or velChange[1] < velocityRatioOrbitSubInvert:
		#	self.addOrbitSub()
		#self.lastOrbitVel = [self.xvel, self.yvel]


		#print(self.orbitLines)
		pastLinePeice = (0, 0)
		for linePeice in self.orbitLines:
			startPos = (((linePeice[0] - xoffset)/scale + windowWidth/2), ((linePeice[1] - yoffset)/scale + windowHeight/2))
			if pastLinePeice != (0, 0):
				pygame.draw.line(window, self.color, startPos, pastLinePeice)
				#pygame.gfxdraw.line(window, int(startPos[0]), int(startPos[1]), int(pastLinePeice[0]), int(pastLinePeice[1]), self.color)
				#gfxdraw.line(window, int(startPos[0]), int(startPos[1]), int(pastLinePeice[0]), int(pastLinePeice[1]), self.color)
			pastLinePeice = startPos
		pygame.draw.line(window, self.color, (xoffsetPos, yoffsetPos), pastLinePeice)


		#shading (might not finish shadow marching)
		"""if self.star:
			for planet in planets:
				if planet != self:
					magnitude = distance((self.xpos, self.ypos), (planet.xpos, planet.ypos))
					slope = ((self.xpos - planet.xpos)/magnitude, (self.ypos - planet.ypos)/magnitude)
					tangent = (-slope[1], slope[0])
					if planet.name == "Mercury":
						print(slope)
					pygame.draw.line(window, self.color, pointToScreen(self.xpos + tangent[0] * self.radius * 50, self.ypos + tangent[1] * self.radius * 50), pointToScreen(planet.xpos + tangent[0] * planet.radius * 50, planet.ypos + tangent[1] * planet.radius * 50))
					pygame.draw.line(window, self.color, pointToScreen(self.xpos - tangent[0] * self.radius * 50, self.ypos - tangent[1] * self.radius * 50), pointToScreen(planet.xpos - tangent[0] * planet.radius * 50, planet.ypos - tangent[1] * planet.radius * 50))
		"""

		#if self.name == "Earth":
		#	print((xoffsetPos, yoffsetPos))
	def getScreenPos(self):
		global windowWidth, windowHeight
		return ((self.xpos - xoffset)/scale + windowWidth/2, (self.ypos - yoffset)/scale + windowHeight/2)
	def addOrbitSub(self):
		global orbitTraceLength
		self.orbitLines.append((self.xpos, self.ypos))
		#trim orbit line
		if len(self.orbitLines) > orbitTraceLength and orbitTraceLength != 0:
			del self.orbitLines[0]
		#print(len(self.orbitLines))

def getScaledLinePoints(points, scale, xoffset, yoffset):
    newList = []
    for point in points:
        scaledPoint = [((point[0] - xoffset)/scale + windowWidth/2), ((point[1] - yoffset)/scale + windowHeight/2)]
        newList.append(scaledPoint)
        #pygame.draw.circle(window, white, (scaledPoint[0], scaledPoint[1]), 2)
    return newList

def pointToScreen(xpos, ypos):
    global scale, windowHeight, windowWidth, xoffset, yoffset
    return ((xpos - xoffset)/scale + windowWidth/2, (ypos - yoffset)/scale + windowHeight/2)

def clampNum(num, upper, lower):
	return max(min(num, upper), lower)

def clampLower(num, lower):
	return max(num, lower)

def clampUpper(num, upper):
	return min(num, upper)

def text_to_screen(screen, text, x, y, size=50, color=(200, 000, 000), font_type=pygame.font.get_default_font()):
	text = str(text)
	font = pygame.font.Font(font_type, size)
	text = font.render(text, True, color)
	screen.blit(text, (x, y))

def checkEvents():
	global windowHeight, windowWidth, targetScale, zoomSpeed
	for event in pygame.event.get():
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

def drawAll(scale, xoffset, yoffset, day, calculationFrames, timeBetweenDraw, drawFrameCount):
	global totalPlanets, selectedPlanet, planetScale
	window.fill(black)
	for planet in planets:
		planet.draw(scale, xoffset, yoffset)
		if planet == selectedPlanet:
			planet.drawDistances(scale, xoffset, yoffset)
	#text_to_screen(window, "Day: " + str(day), 1, 1, 25)
	text_to_screen(window, "FPS: " + str(drawFrameCount) + " / " + str(int(1/timeBetweenDraw)), 1, 1, 13)
	text_to_screen(window, "Cycles/Frame: " + str(calculationFrames), 1, 14, 13)
	text_to_screen(window, "Cycles per planet/Frame: " + str(int(calculationFrames/totalPlanets)), 1, 27, 13)
	text_to_screen(window, "Cycles/Second: " + str(int(calculationFrames * drawFrameCount)), 1, 40, 13)
	text_to_screen(window, "Cycles per planet/Second: " + str(int(calculationFrames * drawFrameCount / totalPlanets)), 1, 53, 13)
	text_to_screen(window, "(not physically accurate, some values had to be adjusted to work)", 1, 64, 10)

	#info
	text_to_screen(window, selectedPlanet.name + ":", 1, 80, 20, white)
	text_to_screen(window, "Velocity: (" + getScientificNotation(selectedPlanet.xvel) + ", " + getScientificNotation(selectedPlanet.yvel) + ") (m/s)", 1, 100, 16, white)
	text_to_screen(window, "Speed: " + getScientificNotation(math.pow(math.pow(selectedPlanet.xvel, 2) + math.pow(selectedPlanet.yvel, 2), .5)) + " (m/s)", 1, 116, 16, white)
	text_to_screen(window, "Mass: " + getScientificNotation(selectedPlanet.mass) + " (Kg)", 1, 132, 16, white)
	text_to_screen(window, "Radius: " + getScientificNotation(selectedPlanet.radius) + " (m)", 1, 148, 16, white)
	text_to_screen(window, "(space) 1 meter = " + getScientificNotation(scale) + " meters", 1, 164, 16, white)
	text_to_screen(window, "(objects) " + str(planetScale) + "X", 1, 180, 16, white)

	

def calculatePhysics(dt): # me attempting to multiprossess this bish (fail lolz)
	#processList = []
	for planet in planets: #create processes
		planet.calculateGravity(dt)
		#processList.append(multiprocessing.Process(target=planet.calculateGravity, args=(dt, )))
	#for process in processList: #start
	#	process.start()
	#for process in processList: #wait
	#	process.join()

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
        
loadPlanets()
totalPlanets = len(planets)
selectedPlanet = planets[len(planets) - 1]
scale = planets[len(planets) - 1].ypos/200
targetScale = scale
scaleEase = 10
offsetEase = 5

#game loop
pastTime = time.time()
timeBetweenDraws = .0666 #1/target fps
calculationCycleLimit = 0 #(per frame) for less CPU/processing power needed (literally nothing else). zero for no limit
pastDrawTime = time.time()
pastSecond = time.time()
pastOrbitSub = time.time()
frameCount = 0
drawFrameCount = 0
frameCount = 0
dayCounter = 0
orbitFramesCounter = 0
currentFPS = 0
while True:
	if frameCount <= calculationCycleLimit - 1 or calculationCycleLimit == 0:
		dt = time.time() - pastTime
		pastTime = time.time()
		frameCount += 1
		calculatePhysics(dt * timeScale)

	if time.time() - pastDrawTime >= timeBetweenDraws:
		#print(scale)
		checkEvents()
		if time.time() - pastSecond >= 1:
			pastSecond = time.time()
			currentFPS = drawFrameCount
			drawFrameCount = 0
		if time.time() - pastOrbitSub >= timePerOrbitSubdivide:
			pastOrbitSub = time.time()
			for planet in planets:
				planet.addOrbitSub()
		scale += (targetScale - scale) * scaleEase * timeBetweenDraws
		xoffset += (selectedPlanet.xpos - xoffset) * offsetEase * timeBetweenDraws
		yoffset += (selectedPlanet.ypos - yoffset) * offsetEase * timeBetweenDraws
		pastDrawTime = time.time()
		#dayCounter += (timeBetweenDraws * timeScale)/(24 * 60 * 60) #convert seconds to days
		#if orbitFramesCounter >= framesPerOrbitSubdivide:
		#	orbitFramesCounter = 0
		#	for planet in planets:
		#		planet.addOrbitSub()
		drawAll(scale, xoffset, yoffset, dayCounter, frameCount, timeBetweenDraws, currentFPS)
		#orbitFramesCounter += 1
		drawFrameCount += 1
		frameCount = 0
		pygame.display.flip()


#some cool things:
""" earth, sun, and moon
[
	{
		"name": "Sun",
		"mass": 1.9885e30,
		"radius": 6.95e8,
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
		"mass": 3.3e23,
		"radius": 2430e3,
		"initialXPos": 0,
		"initialYPos": 57.9e9,
		"initialXVel": 52e3,
		"initialYVel": 0,
		"color": [100, 100, 100],
		"relativeTo": "Sun",
		"light": 0
	},
	{
		"name": "Earth",
		"mass": 5.97e24,
		"radius": 6.378e6,
		"initialXPos": 0,
		"initialYPos": 1.496e11,
		"initialXVel": 3.05e4,
		"initialYVel": 0,
		"color": [50, 50, 250],
		"relativeTo": "Sun",
		"light": 0
	}
]
"""

""" double sun dobble
	{
		"name": "Sun_1",
		"mass": 2.8e30,
		"radius": 6.95e8,
		"initialXPos": 0,
		"initialYPos": 0,
		"initialXVel": 0,
		"initialYVel": -2.98e4,
		"color": [255, 150, 0],
		"relativeTo": "None"
	},
	{
		"name": "Sun_2",
		"mass": 2.8e30,
		"radius": 6.95e8,
		"initialXPos": 1.496e11,
		"initialYPos": 0,
		"initialXVel": 0,
		"initialYVel": 2.98e4,
		"color": [255, 150, 0],
		"relativeTo": "None"
	},
	{
		"name": "Earth",
		"mass": 5.97e24,
		"radius": 6.378e6,
		"initialXPos": 0,
		"initialYPos": 1.496e11,
		"initialXVel": 3.4e4,
		"initialYVel": -8e4,
		"color": [50, 50, 250],
		"relativeTo": "Sun_2"
	}
"""