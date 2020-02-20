# Author: Kay "Isajah" Halbauer
# Date: 18.02.2020
# Version : 0.0.1
# Description:
# This app reads a Json for all Terrain information and generates a heightmap from it

import numpy    # für die Array Mathematik
from PIL import Image 
from scipy.ndimage.filters import gaussian_filter
import matplotlib.pyplot as pp
import matplotlib as mpl
import assets 
import json
import os

import matplotlib.pyplot as pp

# directory of the json file and the heightmap
json_name = "TerrainObjectList.jsonc"
heightmap_name = "heightmap.png"
map_folder = "Map"
mask_folder = "Masks"
os.chdir("..")
if not os.path.exists(map_folder):
    try:
        os.makedirs(map_folder)
    except: 
        print("WARNING: creating Map folder failed --- EXITING ---")
        exit()
    else: 
        print("created Map folder")

if not os.path.exists(mask_folder):
    try:
        os.makedirs(mask_folder)
    except: 
        print("WARNING: creating Mask folder failed --- EXITING ---")
        exit()
    else: 
        print("created Mask folder")

heightmap_path = os.path.join(map_folder,heightmap_name)

try:
    heightmap = numpy.array(Image.open(heightmap_path).convert('L'))
except:
    print("WARNING:heightmap could not be opened! --- EXITING---")
    exit()

#parse json
print("parsing ",json_name)
with open(json_name) as json_file:
    data = json.load(json_file)
    # parse for Parameter
    max_height = data['map_attributes']['max_height']
    min_height = data['map_attributes']['min_height']
    decid_steep = data['deciduous_density_map']['steepness']
    decid_sigma = data['deciduous_density_map']['sigma']
    conif_steep = data['coniferous_density_map']['steepness']
    conif_sigma = data['coniferous_density_map']['sigma']
    berry_dense = data['densities']['berries']
    berry_group = data['group_probabilities']['berries']
    stone_dense = data['densities']['stone']
    stone_group = data['group_probabilities']['stone']
    ore_dense = data['densities']['ore']
    ore_group = data['group_probabilities']['ore']
    fish_dense = data['densities']['fish']
    fish_group = data['group_probabilities']['fish']



# generate asset maps 
print("generating asset masks")
gradientmap, decid_mask = assets.gradient(heightmap, decid_steep, decid_sigma)
gradientmap2, conif_mask = assets.gradient(heightmap, conif_steep, conif_sigma)
material_map = assets.material_map(heightmap,min_height + 30, 10)
asset_mask = assets.asset_mask(heightmap,min_height,max_height)
asset_mask2 = (asset_mask * decid_mask) / 255

print("generating asset maps")
berries_map = assets.asset_map(asset_mask2,berry_dense,berry_group) 
print("berries - mapped")
stone_map = assets.asset_map(asset_mask2,stone_dense, stone_group)
print("stone - mapped")
ore_map = assets.asset_map(asset_mask2,ore_dense, ore_group)
print("iron ore - mapped")
fish_map = assets.asset_map(material_map,fish_dense,fish_group)
print("fish - mapped")
cutout_mask = assets.asset_cutout_mask(berries_map, stone_map,ore_map,10)
conif_map = (asset_mask * conif_mask * cutout_mask) / (255*255)

decid_map = (asset_mask * decid_mask * cutout_mask) / (255*255)

print("trees - mapped")


clist = [(0,"red"), (1, "lime")]
green_red = mpl.colors.LinearSegmentedColormap.from_list("name", clist)
print("grass- mapped")

print("saving files")

pp.imsave(os.path.join(map_folder,"berries_density.png"), berries_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"rock_density.png"), stone_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"iron_density.png"), ore_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"fish_density.png"), fish_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"deciduous_density.png"), decid_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"coniferous_density.png"),conif_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"material_mask.png"), material_map, vmin = 0, vmax = 255, cmap = green_red)

pp.imsave(os.path.join(mask_folder,"decidmask.png"),decid_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"conifmask.png"),conif_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"asset_mask.png"),asset_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"asset_mask2.png"),asset_mask2, vmin = 0, vmax = 255, cmap = 'gray')