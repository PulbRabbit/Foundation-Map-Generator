# Author: Kay "Isajah" Halbauer
# Date: 18.02.2020
# Version : 0.0.1
# Description:
# This app reads a Json for all Terrain information and generates a heightmap from it

import numpy    # für die Array Mathematik

from scipy.ndimage.filters import gaussian_filter

import terrain 
import json

import matplotlib.pyplot as pp

#directory of the json file
json_name = "TerrainObjectList.jsonc"

#initializing empy lists for mountains and rivers
mountains = []
rivers = []
river_level = 40
water_level = 50

#parse json and add mountains and rivers to their lists
with open(json_name) as json_file:
    data = json.load(json_file)
    # parse for Mountains
    for mountain in data['mountains']:
        mountains.append(
            terrain.Mountain(
                mountain['attributes']['height'],
                mountain['attributes']['deviation'],
                mountain['attributes']['density'],
                mountain['attributes']['sigma']
            )
        )
        for waypoint in mountain['waypoints']:
            
            mountains[len(mountains)-1].add_coords(waypoint['x'],waypoint['y'])

    # parse for rivers
    for river in data['rivers']:
        rivers.append(
            terrain.ImprovedRiver(
                river['attributes']['width'],
                river['attributes']['deviation'],
                river['attributes']['sigma'],              
            )
        )    
        for waypoint in river['waypoints']:
            
            rivers[len(rivers)-1].add_coords(waypoint['x'],waypoint['y'])


# now generate maps from objects
mountain_maps = []
river_maps = []


for mountain in mountains:
    mountain.print()
    print()
    mountain_maps.append(mountain.run())

for river in rivers:
    river.print()
    print()
    river_maps.append(river.run())

# Generate a base_line map, all obects will be added
heightmap = numpy.random.randint(water_level, high = 100, size=(1024,1024))


# add all mountains
for mountain_map in mountain_maps:
    heightmap += mountain_map

# adding all rivers
for i in range(0,1024):
    for j in range(0,1024):
       for river_map in river_maps:
            if river_map[i][j] > 0 and  heightmap[i][j] > river_level:
                heightmap[i][j] = river_level

# add a final gaussfilter
print("smoothening the map")
heightmap = gaussian_filter(heightmap, sigma=5)


# save heightmap
pp.imsave("heightmap.png", heightmap, vmin = 0, vmax = 255, cmap = 'gray')
pp.imshow(heightmap)
pp.show()
