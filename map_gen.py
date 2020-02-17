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

mountain_range1 = terrain.Mountain(200,100,100,30)
mountain_range1.add_coords(100,300)
mountain_range1.add_coords(400,100)
mountain_range1.add_coords(900,50)

mountain_range2 = terrain.Mountain(200,100,100,30)
mountain_range2.add_coords(200,900)
mountain_range2.add_coords(600,800)
mountain_range2.add_coords(800,400)

mountain_range3 = terrain.Mountain(250,200,200,50)
mountain_range3.add_coords(1020,50)
mountain_range3.add_coords(900,500)
mountain_range3.add_coords(1000,1000)


mountain_map1 = mountain_range1.run()
mountain_map2 = mountain_range2.run()
mountain_map3 = mountain_range3.run()

heightmap_array = heightmap_array + mountain_map1 
heightmap_array = heightmap_array + mountain_map2
heightmap_array = heightmap_array - mountain_map3

while True:
    new_river = terrain.River(50,750,1050,512,20)
    if new_river.run() > 5000:
        break
    else:
        print("retry generating rivermap")
while True:
    new_river2 = terrain.River(50,750,1050,512,20)
    if new_river2.run() > 5000:
        break
    else:
        print("retry generating rivermap")

rivermap = new_river.gen_map()
rivermap = gaussian_filter(rivermap, sigma=3)

rivermap2 = new_river2.gen_map()
rivermap2 = gaussian_filter(rivermap2, sigma=3)

for i in range(0,1024):
    for j in range(0,1024):
        if rivermap[i][j] > 0 or rivermap2[i][j] > 0:
            heightmap_array[i][j] = 50

heightmap_array = gaussian_filter(heightmap_array, sigma=5)


gradientmap, gradmask = assets.gradient(heightmap_array,5)
low_mask = assets.low_mask(heightmap_array,80)
asset_mask = assets.asset_mask(heightmap_array,80,180)
asset_mask2 = (asset_mask * gradmask) / 255

berry_map = assets.berry_map(asset_mask2,7) 
stone_map = assets.berry_map(asset_mask2,7)
ore_map = assets.berry_map(asset_mask2,2)
fish_map = assets.berry_map(low_mask,25)

fig = pp.figure()
ax1 = fig.add_subplot(231)
ax2 = fig.add_subplot(232)
ax3 = fig.add_subplot(233)
ax4 = fig.add_subplot(234)
ax5 = fig.add_subplot(235)
ax6 = fig.add_subplot(236)


ax1.imshow(heightmap_array)
ax2.imshow(asset_mask2)
ax3.imshow(berry_map)
ax4.imshow(stone_map)
ax5.imshow(ore_map)
ax6.imshow(fish_map)

pp.show()

pp.imsave("Map/heightmap.png", heightmap_array, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("Map/berrymap.png", berry_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("Map/stonemap.png", stone_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("Map/oremap.png", ore_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("Map/fishmap.png", fish_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("Map/mask.png", asset_mask2, vmin = 0, vmax = 255, cmap = 'gray')

