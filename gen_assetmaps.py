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
json_name = "AssetsParamList.jsonc"
heightmap_name = "heightmap.png"
map_folder = "Map"
mask_folder = "Masks"
if not os.path.exists(map_folder):
        print("WARNING: no Map folder in this directory:")
        print(os.getcwd())
        print("--- EXITING ---")
        exit()

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
    print("heightmap.png found")
except:
    print("WARNING:heightmap.png not found or could not be opened!")
    print("Trying to look for a file containing the substring 'heightmap' ")
    substring = "heightmap"
    for files in os.walk(map_folder):
        for filename in files:
            if substring in filename:
                heightmap_path = os.path.join(map_folder, filename)
                print("found",heightmap_path)
                try:
                    heightmap = numpy.array(Image.open(heightmap_path).convert('L'))
                    print("success!")
                except:
                    print("still failed ---EXITING")
                    exit()
                break

if not os.path.exists(json_name):
    print("I was looking for ",json_name," but could not find it! ---EXITING")
    exit()

#parse json
print("parsing ",json_name)
with open(json_name) as json_file:
    data = json.load(json_file)
    # parse for Parameter
    grass_level = data['grass']['level']
    grass_sigma = data['grass']['sigma']
    decid_steep = data['deciduous_density_map']['steepness']
    decid_max   = data['deciduous_density_map']['max_height']
    decid_min   = data['deciduous_density_map']['min_height']
    decid_sigma = data['deciduous_density_map']['sigma']
    conif_steep = data['coniferous_density_map']['steepness']
    conif_max   = data['coniferous_density_map']['max_height']
    conif_min   = data['coniferous_density_map']['min_height']    
    conif_sigma = data['coniferous_density_map']['sigma']
    berry_dense = data['berries']['density']
    berry_group = data['berries']['grouping']
    berry_steep = data['berries']['steepness']
    berry_min   = data['berries']['min_height']
    berry_max   = data['berries']['max_height']
    berry_sigma = data['berries']['sigma']
    stone_dense = data['stone']['density']
    stone_group = data['stone']['grouping']
    stone_steep = data['stone']['steepness']
    stone_min   = data['stone']['min_height']
    stone_max   = data['stone']['max_height']
    stone_sigma = data['stone']['sigma']
    ore_dense = data['ore']['density']
    ore_group = data['ore']['grouping']
    ore_steep = data['ore']['steepness']
    ore_min   = data['ore']['min_height']
    ore_max   = data['ore']['max_height']
    ore_sigma = data['ore']['sigma']
    fish_dense  = data['fish']['density']
    fish_group  = data['fish']['grouping']
    fish_max    = data['fish']['max_height']




# generate asset masks 
print("--- generating all masks needed for generating asset maps ---")
print("generating material mask (grass/sand)")
material_map = assets.material_map(heightmap,grass_level, grass_sigma)

print("generating deciduous treeline masks")
decid_grad_map, decid_grad_mask = assets.gradient(heightmap, decid_steep, decid_sigma)
decid_asset_mask = assets.asset_mask(heightmap,decid_min,decid_max)
decid_mask = (decid_grad_mask * decid_asset_mask) / 255

print("generating coniferous treeline masks")
conif_grad_map, conif_grad_mask = assets.gradient(heightmap, conif_steep, conif_sigma)
conif_asset_mask = assets.asset_mask(heightmap,conif_min,conif_max)
conif_mask = (conif_grad_mask * conif_asset_mask) / 255

print("generating berries mask")
berries_grad_map, berries_grad_mask = assets.gradient(heightmap, berry_steep, berry_sigma) 
berries_asset_mask = assets.asset_mask(heightmap,berry_min,berry_max)
berries_mask = (berries_grad_mask * berries_asset_mask) / 255

print("generating stone mask")
stone_grad_map, stone_grad_mask = assets.gradient(heightmap, stone_steep, stone_sigma) 
stone_asset_mask = assets.asset_mask(heightmap,stone_min,stone_max)
stone_mask = (stone_grad_mask * stone_asset_mask) / 255

print("generating ore mask")
ore_grad_map, ore_grad_mask = assets.gradient(heightmap, ore_steep, ore_sigma) 
ore_asset_mask = assets.asset_mask(heightmap,ore_min,ore_max)
ore_mask = (ore_grad_mask * ore_asset_mask) / 255

print("generating fish mask")
fishing_mask = assets.asset_mask(heightmap,0,fish_max)

print(".....done") 
print()

# generating maps
print("--- generating all maps from corresponding masks ---")

berries_map = assets.asset_map(berries_mask,berry_dense,berry_group) 
print("berries - mapped")

stone_map = assets.asset_map(stone_mask,stone_dense, stone_group)
print("stone - mapped")

ore_map = assets.asset_map(ore_mask,ore_dense, ore_group)
print("iron ore - mapped")

fish_map = assets.asset_map(fishing_mask,fish_dense,fish_group)
print("fish - mapped")


cutout_mask = assets.asset_cutout_mask(berries_map, stone_map, ore_map, 10)
print("generate cutouts for berries, stone and iron ore")

conif_map = (conif_mask * cutout_mask) / 255
conif_map = gaussian_filter(conif_map, sigma=conif_sigma)
decid_map = (decid_mask * cutout_mask) / 255
decid_map = gaussian_filter(decid_map, sigma=decid_sigma)

print("trees - mapped")


clist = [(0,"red"), (1, "lime")]
green_red = mpl.colors.LinearSegmentedColormap.from_list("name", clist)
print("grass- mapped")

print("....done")
print()

print("saving files")

pp.imsave(os.path.join(map_folder,"berries_density.png"), berries_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"rock_density.png"), stone_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"iron_density.png"), ore_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"fish_density.png"), fish_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"deciduous_density.png"), decid_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"coniferous_density.png"),conif_map, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(map_folder,"material_mask.png"), material_map, vmin = 0, vmax = 255, cmap = green_red)

print("saving masks for analization")
pp.imsave(os.path.join(mask_folder,"decidmask.png"),decid_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"conifmask.png"),conif_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"berriesmask.png"),berries_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"stonemask.png"),stone_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"oremask.png"),ore_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"fishmask.png"),fishing_mask, vmin = 0, vmax = 255, cmap = 'gray')
pp.imsave(os.path.join(mask_folder,"coutout.png"),cutout_mask, vmin = 0, vmax = 255, cmap = 'gray')

print("I'm done, farewell")