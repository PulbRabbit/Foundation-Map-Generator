import numpy    # für die Array Mathematik

import math     # für einfache mathematik
import random   # für zufallszahlen

from scipy.ndimage.filters import gaussian_filter

import matplotlib.pyplot as pp
import matplotlib.image as imp

import terrain 
import assets


heightmap_array = numpy.random.randint(50, high = 200, size=(1024,1024))

#print(heightmap_array)

heightmap_array = gaussian_filter(heightmap_array, sigma=10)


# adding Mountains
mountain_range = []
mountain_map = []

print("Adding a Mountain")
mountain_range.append(terrain.Mountain(200,200,10,30))
mountain_range[0].add_coords(100,300)
mountain_range[0].add_coords(400,100)
mountain_range[0].add_coords(900,50)

mountain_map.append(mountain_range[0].run())

heightmap_array = heightmap_array + mountain_map[0] 



# Rivers
print("Adding a river")
improved_river = terrain.ImprovedRiver(3,15,5)
improved_river.add_coords(0,200) # Starting Point
improved_river.add_coords(200,100)
improved_river.add_coords(600,900)
improved_river.add_coords(900,1023) # End Point

rivermap = improved_river.run()

# apply river
print("Apply rivers")
for i in range(0,1024):
    for j in range(0,1024):
       if rivermap[i][j] > 0 :
            heightmap_array[j][i] = 50

# add a final gaussfilter
print("smoothening the map")
heightmap_array = gaussian_filter(heightmap_array, sigma=5)

# generate asset maps 
#print("generating asset masks")
gradientmap, gradmask = assets.gradient(heightmap_array,5,5)
#low_mask = assets.low_mask(heightmap_array,80)
#asset_mask = assets.asset_mask(heightmap_array,80,180)
#asset_mask2 = (asset_mask * gradmask) / 255

print("generating asset maps")
#berry_map = assets.berry_map(asset_mask2,7) 
#stone_map = assets.berry_map(asset_mask2,7)
#ore_map = assets.berry_map(asset_mask2,2)
#fish_map = assets.berry_map(low_mask,25)

print("preparing forecast")
fig = pp.figure()
ax1 = fig.add_subplot(231)
ax2 = fig.add_subplot(232)
ax3 = fig.add_subplot(233)
ax4 = fig.add_subplot(234)
ax5 = fig.add_subplot(235)
ax6 = fig.add_subplot(236)


ax1.imshow(heightmap_array)
ax2.imshow(mountain_map[0])
#ax3.imshow(mountain_map[1])
#ax4.imshow(mountain_map[2])
ax5.imshow(rivermap)
#ax6.imshow(fish_map)

pp.show()

print("saving files")

#pp.imsave("Map/heightmap.png", heightmap_array, vmin = 0, vmax = 255, cmap = 'gray')
#pp.imsave("Map/berrymap.png", berry_map, vmin = 0, vmax = 255, cmap = 'gray')
#pp.imsave("Map/stonemap.png", stone_map, vmin = 0, vmax = 255, cmap = 'gray')
#pp.imsave("Map/oremap.png", ore_map, vmin = 0, vmax = 255, cmap = 'gray')
#pp.imsave("Map/fishmap.png", fish_map, vmin = 0, vmax = 255, cmap = 'gray')
#pp.imsave("Map/mask.png", asset_mask2, vmin = 0, vmax = 255, cmap = 'gray')

