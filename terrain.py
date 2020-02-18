import numpy    # für die Array Mathematik
import math
from PIL import Image      # für die Bildbearbeitung

import random
import time 

from scipy.ndimage.filters import gaussian_filter
import matplotlib.pyplot as pp
import matplotlib.image as imp

class River:

    def __init__(self,x_start, y_start, x_end, y_end, deviation):
        self.coords = []
        self.coords.append((x_start,y_start))
        self.x_end = x_end
        self.y_end = y_end
        self.dev = deviation
        self.get_dir()

    def get_dir(self):
    
        last = len(self.coords) - 1 

        
        x_dir = self.x_end - self.coords[last][0] + random.randrange(-self.dev,self.dev)
        y_dir = self.y_end - self.coords[last][1] + random.randrange(-self.dev,self.dev)
        

        length = math.sqrt(x_dir*x_dir + y_dir*y_dir)
          
        self.x_dir = x_dir / length 
        self.y_dir = y_dir / length 

    def deviate_dir(self):
        
        x_dir = self.x_dir * self.dev + random.randrange(-self.dev,self.dev)
        y_dir = self.y_dir * self.dev + random.randrange(-self.dev,self.dev)

        length = math.sqrt(x_dir*x_dir + y_dir*y_dir)

        try: 
            self.x_dir = x_dir / length
        except:
            self.x_dir = 0

        try:
            self.y_dir = y_dir / length
        except:
            self.y_dir = 0

    def run(self):
        run_round = 0
        loop_break = False

        while not loop_break:
            run_round += 1
            last = len(self.coords) - 1

            new_x = self.coords[last][0] + self.x_dir
            new_y = self.coords[last][1] + self.y_dir
            

            if 0 < new_x < 1023 and 0 < new_y < 1023:       
                self.coords.append((new_x,new_y))
                if (run_round % self.dev/10) == 0:
                    self.get_dir()
                else:
                    self.deviate_dir()
                #print("round: ",run_round,new_x, new_y)
            else:
                loop_break = True

        return run_round
            

    def gen_map(self):
        rivermap = numpy.full((1024,1024),0)

        for spot in self.coords:
            if 5 < spot[0] < 1019 and 5 < spot[1] < 1019:
                for i in range(-5,5):
                    for j in range(-5,5):
                        rivermap[int(spot[0]+i),int(spot[1]+j)] = 50


        return rivermap


class Mountain:
    def __init__(self, height, deviation, density,sigma):
        self.coords = []
        self.height = height
        self.width = 3
        self.dev = deviation
        self.dense = density
        self.height_map = numpy.full((1024,1024),0)
        self.sigma = sigma

    def add_coords(self,x,y):
        self.coords.append((x,y))
    
    def run(self):
        #run should generate the mountain map
        
        # set the startingpoint
        x = self.coords[0][0]
        y = self.coords[0][1]

        #go from coord to coord
        i = 1
        while i < len(self.coords):
            # calculate the direction to the next waypoint
            x_vec = self.coords[i][0] - x
            y_vec = self.coords[i][1] - y

            length = math.sqrt(x_vec * x_vec + y_vec * y_vec )

            x_dir = x_vec / length
            y_dir = y_vec / length

            # step forward 
            x += x_dir
            y += y_dir

            # drop a mountain
            for drops in range(0,self.dense):
                x_draw = int(x + random.gauss(0,self.dev))
                y_draw = int(y + random.gauss(0,self.dev))
                if 1 < x_draw < 1023 and 1 < y_draw < 1023:
                    
                    for r in range(-self.width,self.width):
                        for c in range(-self.width,self.width):
                            try:
                                   self.height_map[int(y_draw+r),int(x_draw+c)] = random.randrange(0,self.height)
                            except:
                                try: 
                                    self.height_map[int(y_draw+r),int(x_draw+c)] = random.randrange(self.height,0)
                                except:
                                    pass

            hyst = 5
            if self.coords[i][0] - hyst < x < self.coords[i][0] + hyst and self.coords[i][1] - hyst < y < self.coords[i][1] + hyst:
                i += 1

        self.height_map = gaussian_filter(self.height_map, sigma=self.sigma)
        return self.height_map

    def print(self):
        print("type:      Mountain")
        print("height:    ",self.height)
        print("deviation: ",self.dev)
        print("density:   ", self.dense)
        print("sigma:     ", self.sigma)    
        for wp in self.coords:
            print("waypoint: ",wp[0]," ",wp[1])

class ImprovedRiver:
    # improved River can use multiple coordinates and doesn't just rely on starting and endpoint
    def __init__(self, width, deviation,sigma):
        self.coords = []
        self.width = width
        self.dev = deviation
        self.height_map = numpy.full((1024,1024),0)
        self.sigma = sigma
        self.x_dir = 0
        self.y_dir = 0

    def add_coords(self,x,y):
        self.coords.append((x,y))
    
    def set_dir(self,my_x,my_y, index):
        
        x_start = my_x
        y_start = my_y

        x_end = self.coords[index+1][0]
        y_end = self.coords[index+1][1]

        x_vec = x_end - x_start
        y_vec = y_end - y_start

        length = math.sqrt(x_vec * x_vec + y_vec * y_vec )

        self.x_dir = x_vec / length
        self.y_dir = y_vec / length


    def deviate_dir(self):
        
        x_dir = self.x_dir * self.dev + random.randrange(-self.dev,self.dev)
        y_dir = self.y_dir * self.dev + random.randrange(-self.dev,self.dev)

        length = math.sqrt(x_dir*x_dir + y_dir*y_dir)
        if length != 0 : 
            self.x_dir = x_dir / length
            self.y_dir = y_dir / length
        else:
            self.x_dir = 0
            self.y_dir = 0

    def run(self):
        #run should generate the mountain map

        # starting point
        x = self.coords[0][0]
        y = self.coords[0][1]

        # waypoint index
        i = 0
        loops = 0
        while i+1 < len(self.coords) and loops < 100000:
   
            # calculate direction

            if (loops % (self.dev)) == 0:
                self.set_dir(x,y,i)      # calculating direction to next waypoint
            else:
                self.deviate_dir()
            # place river
            for r in range(-self.width,self.width):
                    for c in range(-self.width,self.width):
                        try:
                            self.height_map[int(y+r),int(x+c)] = 50
                        except:
                            pass
            # step forward 
            x += self.x_dir
            y += self.y_dir
            #print("loops: ",loops, " wp: ",i," x/y: ",x,y)
            #time.sleep(0.1)
            #waypoint reached
            hyst = self.dev
            if self.coords[i+1][0] - hyst < x < self.coords[i+1][0] + hyst and self.coords[i+1][1] - hyst < y < self.coords[i+1][1] + hyst:
                i += 1
                #print("waypoint ",i," reached")
            # count loops up
            loops += 1
        #print(loops)
        self.height_map = gaussian_filter(self.height_map, sigma=self.sigma)
        return self.height_map

    def print(self):
        print("type:      River")
        print("width:    ",self.width)
        print("deviation: ",self.dev)
        print("sigma:     ", self.sigma)    
        for wp in self.coords:
            print("waypoint: ",wp[0]," ",wp[1])
