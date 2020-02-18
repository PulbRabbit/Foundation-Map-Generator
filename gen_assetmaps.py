# Author: Kay "Isajah" Halbauer
# Date: 18.02.2020
# Version : 0.0.1
# Description:
# This app reads a Json for all Terrain information and generates a heightmap from it

import numpy    # für die Array Mathematik
from PIL import Image 
from scipy.ndimage.filters import gaussian_filter
import matplotlib.pyplot as pp

import assets 
import json

import matplotlib.pyplot as pp

# directory of the json file and the heightmap
json_name = "TerrainObjectList.jsonc"
heightmap_name = "heightmap.png"

heightmap = numpy.array(Image.open(heightmap_name).convert('L'))


#parse json and add mountains and rivers to their lists
with open(json_name) as json_file:
    data = json.load(json_file)
    # parse for Mountains
    max_height = data['map_attributes']['max_height']
    min_height = data['map_attributes']['min_height']
    grad_steep = data['gradient_map']['steepness']
    grad_sigma = data['gradient_map']['sigma']
    berry_dense = data['densities']['berries']
    stone_dense = data['densities']['stone']
    ore_dense = data['densities']['ore']
    fish_dense = data['densities']['fish']


# generate asset maps 
print("generating asset masks")
gradientmap, gradmask = assets.gradient(heightmap, grad_steep, grad_sigma)
low_mask = assets.low_mask(heightmap,min_height)
asset_mask = assets.asset_mask(heightmap,min_height,max_height)
asset_mask2 = (asset_mask * gradmask) / 255

print("generating asset maps")
berries_map = assets.asset_map(asset_mask2,berry_dense) 
stone_map = assets.asset_map(asset_mask2,stone_dense)
ore_map = assets.asset_map(asset_mask2,ore_dense)
fish_map = assets.asset_map(low_mask,fish_dense)

print("saving files")

pp.imsave("berrymap.png", berries_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("stonemap.png", stone_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("oremap.png", ore_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("fishmap.png", fish_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave("mask.png", asset_mask2, vmin = 0, vmax = 255, cmap = 'gray')
