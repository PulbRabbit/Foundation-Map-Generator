# Imports
import numpy
import math
import random

from scipy.ndimage.filters import gaussian_filter

# Classes


class River:
    def __init__(self, x_start, y_start, x_end, y_end, deviation):
        self.wps = []
        self.wps.append((x_start, y_start))

        self.x = x_start
        self.y = y_start

        self.x_end = x_end
        self.y_end = y_end

        self.x_dir = self.x_end - self.x
        self.y_dir = self.y_end - self.y

        self.dev = deviation
        self.get_dir()

    def get_dir(self):
    
        last = len(self.wps) - 1
        
        x_dir = self.x_end - self.wps[last][0] + random.randrange(-self.dev, self.dev)
        y_dir = self.y_end - self.wps[last][1] + random.randrange(-self.dev, self.dev)

        length = math.sqrt(x_dir*x_dir + y_dir*y_dir)
          
        self.x_dir = x_dir / length 
        self.y_dir = y_dir / length 

    def deviate_dir(self):
        
        x_dir = self.x_dir * self.dev + random.randrange(-self.dev, self.dev)
        y_dir = self.y_dir * self.dev + random.randrange(-self.dev, self.dev)

        length = math.sqrt(x_dir*x_dir + y_dir*y_dir)

        try: 
            self.x_dir = x_dir / length
        except ZeroDivisionError:
            self.x_dir = 0

        try:
            self.y_dir = y_dir / length
        except ZeroDivisionError:
            self.y_dir = 0

    def run(self):
        run_round = 0
        loop_break = False

        while not loop_break:
            run_round += 1
            last = len(self.wps) - 1

            new_x = self.wps[last][0] + self.x_dir
            new_y = self.wps[last][1] + self.y_dir

            if 0 < new_x < 1023 and 0 < new_y < 1023:
                self.wps.append((new_x, new_y))
                if (run_round % self.dev/10) == 0:
                    self.get_dir()
                else:
                    self.deviate_dir()
            else:
                loop_break = True

        return run_round

    def gen_map(self):
        rivermap = numpy.full((1024, 1024), 0)

        for spot in self.wps:
            if 5 < spot[0] < 1019 and 5 < spot[1] < 1019:
                for i in range(-5, 5):
                    for j in range(-5, 5):
                        rivermap[int(spot[0]+i), int(spot[1]+j)] = 50

        return rivermap


class Mountain:
    def __init__(self, height, spread, deviation, density, sigma):
        self.wps = []
        self.height = height
        self.spread = spread
        self.width = 3
        self.dev = deviation
        self.dense = density
        self.height_map = numpy.full((1024, 1024), 0)
        self.sigma = sigma
        self.x_dir = 0
        self.y_dir = 0

    def add_wps(self, x, y):
        """ add coordinates to the mountain """
        self.wps.append((x, y))
    
    def run(self):
        """ generate the mountain map """
        
        # set the starting point
        x = self.wps[0][0]
        y = self.wps[0][1]

        # go from waypoint to waypoint
        i = 0
        loops = 0
        while i+1 < len(self.wps) and loops < 100000:
            # calculate the direction to the next waypoint
            
            # calculate direction
            if self.dev == 0 or (loops % self.dev) == 0:
                self.set_dir(x, y, i)      # calculating direction to next waypoint
            else:
                self.deviate_dir()
                # self.set_dir(x,y,i)

            # step forward 
            x += self.x_dir
            y += self.y_dir

            # drop a mountain
            for drops in range(0, self.dense):
                x_draw = int(x + random.gauss(0, self.spread / 2))
                y_draw = int(y + random.gauss(0, self.spread / 2))
                dist = math.sqrt((x - x_draw)*(x-x_draw) + (y - y_draw)*(y - y_draw))
                max_dist = math.sqrt(2*self.spread*self.spread)
                dist = 0.2 + 0.8*(max_dist - dist) / max_dist
                if self.width < x_draw < 1023 - self.width and self.width < y_draw < 1023 - self.width:
                    
                    for r in range(-self.width, self.width):
                        for c in range(-self.width, self.width):
                            try:
                                self.height_map[int(y_draw+r), int(x_draw+c)] = random.randrange(0, int(self.height * dist))
                            except (IndexError, ValueError):
                                try: 
                                    self.height_map[int(y_draw+r), int(x_draw+c)] = random.randrange(int(self.height * dist), 0)
                                except (IndexError, ValueError):
                                    pass

            hyst = 20
            if self.wps[i + 1][0] - hyst < x < self.wps[i + 1][0] + hyst and self.wps[i + 1][1] - hyst < y < self.wps[i + 1][1] + hyst:
                i += 1
            loops += 1
        self.height_map = gaussian_filter(self.height_map, sigma=self.sigma)
        return self.height_map

    def print(self):
        print("type:      Mountain")
        print("height:    ", self.height)
        print("deviation: ", self.dev)
        print("density:   ", self.dense)
        print("sigma:     ", self.sigma)    
        for wp in self.wps:
            print("waypoint: ", wp[0], " ", wp[1])

    def deviate_dir(self):
        dev = random.randrange(-self.dev, self.dev)
        x_dir = self.x_dir + dev / 100
        y_dir = self.y_dir - dev / 100

        length = math.sqrt(x_dir*x_dir + y_dir*y_dir)
        if length != 0:
            self.x_dir = x_dir / length
            self.y_dir = y_dir / length
        else:
            self.x_dir = 0
            self.y_dir = 0

    def set_dir(self, my_x, my_y, index):
    
        x_start = my_x
        y_start = my_y

        x_end = self.wps[index + 1][0]
        y_end = self.wps[index + 1][1]

        x_vec = x_end - x_start
        y_vec = y_end - y_start

        length = math.sqrt(x_vec * x_vec + y_vec * y_vec)

        self.x_dir = x_vec / length
        self.y_dir = y_vec / length


class ImprovedRiver:
    # improved River can use multiple coordinates and doesn't just rely on starting and endpoint
    def __init__(self, width, deviation, sigma):
        self.wps = []
        self.width = width
        self.dev = deviation
        self.height_map = numpy.full((1024, 1024), 0)
        self.sigma = sigma
        self.x_dir = 0
        self.y_dir = 0

    def add_wps(self, x, y):
        self.wps.append((x, y))
    
    def set_dir(self, my_x, my_y, index):
        
        x_start = my_x
        y_start = my_y

        x_end = self.wps[index+1][0]
        y_end = self.wps[index+1][1]

        x_vec = x_end - x_start
        y_vec = y_end - y_start

        length = math.sqrt(x_vec * x_vec + y_vec * y_vec)

        self.x_dir = x_vec / length
        self.y_dir = y_vec / length

    def deviate_dir(self):
        
        x_dir = self.x_dir * self.dev + random.randrange(-self.dev, self.dev)
        y_dir = self.y_dir * self.dev + random.randrange(-self.dev, self.dev)

        length = math.sqrt(x_dir*x_dir + y_dir*y_dir)
        if length != 0:
            self.x_dir = x_dir / length
            self.y_dir = y_dir / length
        else:
            self.x_dir = 0
            self.y_dir = 0

    def run(self):
        # run should generate the mountain map

        # starting point
        x = self.wps[0][0]
        y = self.wps[0][1]

        # waypoint index
        i = 0
        loops = 0
        while i+1 < len(self.wps) and loops < 100000:
   
            # calculate direction

            if loops % self.dev == 0:
                self.set_dir(x, y, i)      # calculating direction to next waypoint
            else:
                self.deviate_dir()
            # place river
            for r in range(-self.width, self.width):
                for c in range(-self.width, self.width):
                    rel_x = int(x+r)
                    rel_y = int(y+c)
                    if 0 <= rel_x < 1024 and 0 <= rel_y < 1024:
                        self.height_map[rel_y, rel_x] = 50

            # step forward 
            x += self.x_dir
            y += self.y_dir

            # waypoint reached
            hyst = self.dev
            if self.wps[i+1][0] - hyst < x < self.wps[i+1][0] + hyst and self.wps[i+1][1] - hyst < y < self.wps[i+1][1] + hyst:
                i += 1
            # count loops up
            loops += 1

        self.height_map = gaussian_filter(self.height_map, sigma=self.sigma)
        return self.height_map

    def print(self):
        print("type:      River")
        print("width:    ", self.width)
        print("deviation: ", self.dev)
        print("sigma:     ", self.sigma)    
        for wp in self.wps:
            print("waypoint: ", wp[0], " ", wp[1])
