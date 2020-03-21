import numpy
from scipy.ndimage.filters import gaussian_filter
import random
 
brush = [(-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (0, -2), (0, -1), (0, 1), (0, 2), (1, 1), (-1, 1), (1, -1), (-1, -1)]


def material_map(heightmap, min_height, sig):
    """ returns a black and white map of underwater terrain """
    return_map = numpy.full((1024, 1024), 0)
    for j in range(0, 1024):
        for i in range(0, 1024):
            if heightmap[i][j] < min_height:
                return_map[i][j] = 255
    return_map = gaussian_filter(return_map, sigma=sig)
    return return_map


def asset_mask(heightmap, min_height, max_height):
    """ returns a black and white map of areas in between specified heights """
    return_map = numpy.full((1024, 1024), 0)
    for j in range(0, 1024):
        for i in range(0, 1024):
            if min_height < heightmap[i][j] < max_height:
                return_map[i][j] = 255
    return return_map


def gradient(heightmap, steepness, sig):
    """ returns the gradient map. combined with the asset mask, asset placing can be determined """
    return_map = numpy.full((1024, 1024), 255)
    grad_map_x, grad_map_y = numpy.gradient(heightmap)
    grad_map = numpy.absolute(grad_map_x) + numpy.absolute(grad_map_y) 
    grad_map *= 10
    grad_map = gaussian_filter(grad_map, sigma=sig)
    for j in range(0, 1024):
        for i in range(0, 1024):
            if grad_map[i][j] > steepness:
                return_map[i][j] = 0
    return_map = gaussian_filter(return_map, sigma=sig)
    return grad_map, return_map


def asset_cutout_mask(berries, stone, iron, sig):
    """ returns a cut out map to create holes in the tree maps where resources are placed  """
    return_map = numpy.full((1024, 1024), 255)
    combined_map = berries + stone + iron
    combined_map = gaussian_filter(combined_map, sigma=sig)
    for j in range(0, 1024):
        for i in range(0, 1024):
            if combined_map[i][j] > 0:
                for r in range(-10, 10):
                    for c in range(-10, 10):
                        if 0 < i+r < 1023 and 0 < j+c < 1023:
                            return_map[i+r][j+c] = 0

    return_map = gaussian_filter(return_map, sigma=sig)
    return return_map


def asset_map(mask, density, group_probability):
    """ returns asset maps like berries, stone or ore. determines spots for placement"""
    return_map = numpy.full((1024, 1024), 0)
    for j in range(25, 1000):
        for i in range(25, 1000):
            if mask[i][j] > 0 and random.randrange(0, 100000) < density:
                for dot in brush:
                    return_map[i+dot[0]][j+dot[1]] = 255
                
                if random.randrange(0, 100) < group_probability:
                    for dot in brush:
                        return_map[i+dot[0]-5][j+dot[1]+5] = 255    
                    for dot in brush:
                        return_map[i+dot[0]-5][j+dot[1]-5] = 255
    return return_map  
