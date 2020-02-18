import numpy
from scipy.ndimage.filters import gaussian_filter
import random

def low_mask(heightmap, min_height):
# returns a black and white map of underwater terrain
    return_map = numpy.full((1024,1024),0)
    for j in range(0,1024):
        for i in range(0, 1024):
            if heightmap[i][j] < min_height:
                return_map[i][j] = 255
    return return_map

def asset_mask(heightmap, min_height, max_height):
# returns a black and white map of areas inbetween specified heights     
    return_map = numpy.full((1024,1024),0)
    for j in range(0,1024):
        for i in range(0, 1024):
            if min_height < heightmap[i][j] < max_height:
                return_map[i][j] = 255
    return return_map

def gradient(heightmap, steepness, sig):
# returns the gradient map. combined with the asset mask , asset placing can be determined
    return_map = numpy.full((1024,1024),255)
    grad_map_x, grad_map_y = numpy.gradient(heightmap)
    grad_map = numpy.absolute(grad_map_x) + numpy.absolute(grad_map_y) 
    grad_map *= 10
    grad_map = gaussian_filter(grad_map, sigma=sig)
    for j in range(0,1024):
        for i in range(0, 1024):
            if grad_map[i][j] > steepness:
                return_map[i][j] = 0
    return grad_map, return_map

def asset_map(mask, density):
    return_map = numpy.full((1024,1024),0)  
    for j in range(20,1003):
        for i in range(20, 1003):
            if mask[i][j] > 0 and random.randrange(0,50000) < density:
                
                return_map[i-1][j] = 255
                return_map[i+1][j] = 255
                return_map[i][j] = 255
                return_map[i][j-1] = 255
                return_map[i][j+1] = 255

    return return_map  



