# Head
__author__ = "Isajah"
__version__ = "1.1.1"

# Imports
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import colorchooser

import numpy
from scipy.ndimage.filters import gaussian_filter
import matplotlib.pyplot as pp
import matplotlib as mpl

from PIL import ImageTk, Image

import os
import subprocess
import time
import terrain
import assets
import json

# directories and file names 
hmap_name = "heightmap.png"
mmap_name = "material_mask.png"
bmap_name = "berries_density.png"
rmap_name = "rock_density.png"
imap_name = "iron_density.png"
fmap_name = "fish_density.png"

map_folder = "Maps"
partials_folder = "PartialMaps"
jsons_folder = "Jsons"
default_file = "default.png"

PREV_SIZE = 256
ENTRY_WIDTH = 4
PADX = 4
MAX_16BIT = 65535
NORM = 66


class BaseWindow:
    def __init__(self, master, prev_canvas):

        # internal variables

        self.wp_index = 0
        self.wp_list = []
        self.deleted = False
        self.index = 0

        self.object_label = "Base Window"

        self.prev_canvas = prev_canvas

        # initializing basic structure of the window
        self.master = master
        self.frame = tk.Frame(self.master, relief=tk.GROOVE, borderwidth=1)
        self.frame.pack(side='top', expand=True, fill='both')
        self.top_frame = tk.Frame(self.frame)
        self.top_frame.grid(column=0, row=0, sticky='we')
        self.top_frame.columnconfigure(0, minsize=140)
        self.main_frame = tk.Frame(self.frame)
        self.main_frame.grid(column=0, row=1, sticky='we')
        self.wp_frame = tk.Frame(self.frame)
        self.wp_frame.grid(column=0, row=2, sticky='we')

        # initialize preview
        self.preview = tk.Label(self.prev_canvas)
        self.preview_label = tk.Label(self.prev_canvas)

    def build_preview(self, handle, label, filename, index, init=False):
        # build preview
        image = Image.open(filename)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        if init:
            handle.append(ImageTk.PhotoImage(image))
            self.preview.configure(image=handle[-1])
            self.preview.pack()
            self.preview_label.configure(text=label)
            self.preview_label.pack()
            ret_val = len(handle)
        else:
            handle[index - 1] = ImageTk.PhotoImage(image)
            self.preview.configure(image=handle[index - 1])
            ret_val = index
        self.prev_canvas.master.update()
        return ret_val

    def destroy(self):
        self.frame.destroy()
        self.preview.destroy()
        self.preview_label.destroy()
        self.deleted = True

    def generate(self):
        pass


class Terrain(BaseWindow):
    def __init__(self, container, master, prev_canvas, index):
        super().__init__(master, prev_canvas)
        self.wp_index = 0
        self.container = container
        self.terrain_map = numpy.full((1024, 1024), 0)
        self.index = index
        self.object_label = "Terrain Object"

    def add_wp(self):
        # adding waypoints
        self.wp_index += 1
        self.wp_list.append(Waypoint(self.wp_frame, self.wp_index, self.container))

    def get_waypoints(self):
        retlist = []
        for wp in self.wp_list:
            if not wp.deleted:
                retlist.append(0)
                retlist.append(0)
                retlist[-2], retlist[-1] = wp.getval()
        return retlist


class GlobalParams(BaseWindow):
    def __init__(self, master, prev_canvas, min_height, max_height, river_level, pre_sigma, post_sigma, ws_name):
        super().__init__(master, prev_canvas)

        # --- initialize all internal variables
        self.min_height = min_height
        self.max_height = max_height
        self.river_level = river_level
        self.pre_sigma = pre_sigma
        self.post_sigma = post_sigma

        self.baseline_map = numpy.full((1024, 1024), 0)
        self.object_label = "Global Parameters"
        self.ws_name = ws_name

        # --- initialize all internal text representations

        self.str_min_height = tk.StringVar()
        self.str_min_height.set(str(min_height))

        self.str_max_height = tk.StringVar()
        self.str_max_height.set(str(max_height))

        self.str_river_level = tk.StringVar(value=str(int(river_level)))
        self.str_pre_sigma = tk.StringVar(value=str(int(pre_sigma)))
        self.str_post_sigma = tk.StringVar(value=str(int(post_sigma)))

        # --- built head
        self.label_name = tk.Label(self.top_frame, text=self.object_label)
        self.label_name.grid(column=0, row=0, sticky='w')
        self.gen_btn = tk.Button(self.top_frame, text="build baseline map", command=self.generate)
        self.gen_btn.grid(column=1, row=0, sticky='we')
        self.hmap_btn = tk.Button(self.top_frame, text="get heightmap", command=self.get_heightmap)
        self.hmap_btn.grid(column=2, row=0, sticky='we')

        # --- built input matrix

        # max height 
        self.label_max_height = tk.Label(self.main_frame, text="max height:")
        self.label_max_height.grid(column=0, row=1, sticky='w', padx=PADX)
        self.box_max_height = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_max_height)
        self.box_max_height.grid(column=1, row=1, sticky='w', padx=PADX)

        # min height
        self.label_min_height = tk.Label(self.main_frame, text="min height:")
        self.label_min_height.grid(column=2, row=1, sticky='w', padx=PADX)
        self.box_min_height = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_min_height)
        self.box_min_height.grid(column=3, row=1, sticky='w', padx=PADX)

        # river level
        self.label_river = tk.Label(self.main_frame, text="river level:")
        self.label_river.grid(column=4, row=1, sticky='w', padx=PADX)
        self.box_river = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_river_level)
        self.box_river.grid(column=5, row=1, sticky='w', padx=PADX)

        # pre sigma
        self.label_pre_sigma = tk.Label(self.main_frame, text="pre sigma:")
        self.label_pre_sigma.grid(column=0, row=2, sticky='w', padx=PADX)
        self.box_pre_sigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_pre_sigma)
        self.box_pre_sigma.grid(column=1, row=2, sticky='w', padx=PADX)

        # post sigma
        self.label_post_sigma = tk.Label(self.main_frame, text="post sigma:")
        self.label_post_sigma.grid(column=2, row=2, sticky='w', padx=PADX)
        self.box_post_sigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_post_sigma)
        self.box_post_sigma.grid(column=3, row=2, sticky='w', padx=PADX)

        # build preview

        self.baseline_im = Image.open(os.path.join(partials_folder, "default.png"))
        self.baseline_im.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        self.prev_canvas.baseline_im = ImageTk.PhotoImage(self.baseline_im)

        self.preview = tk.Label(self.prev_canvas, image=self.prev_canvas.baseline_im)
        self.preview.pack()
        self.preview_label = tk.Label(self.prev_canvas, text="baseline map")
        self.preview_label.pack()

    def min_height_get(self, norm=1.0):
        self.min_height = int(self.str_min_height.get())
        return self.min_height * norm

    def max_height_get(self, norm=1.0):
        self.max_height = int(self.str_max_height.get())
        return self.max_height * norm

    def river_level_get(self, norm=1.0):
        self.river_level = int(self.str_river_level.get())
        return self.river_level * norm

    def pre_sigma_get(self, norm=1):
        self.pre_sigma = int(self.str_pre_sigma.get())
        return self.pre_sigma * norm

    def post_sigma_get(self, norm=1):
        self.post_sigma = int(self.str_post_sigma.get())
        return self.post_sigma * norm

    def generate(self):
        # get all variables from form
        min_height = self.min_height_get(norm=NORM)
        max_height = self.max_height_get(norm=NORM)
        self.pre_sigma_get()
        self.post_sigma_get()

        # Generate a base_line map, all objects will be added
        self.baseline_map = numpy.random.randint(min_height, high=max_height, size=(1024, 1024))
        self.baseline_map = gaussian_filter(self.baseline_map, sigma=self.pre_sigma)
        pp.imsave(os.path.join(self.ws_name, partials_folder, "baseline.png"), self.baseline_map, vmin=0, vmax=MAX_16BIT)

        self.baseline_im = Image.open(os.path.join(self.ws_name, partials_folder, "baseline.png"))
        self.baseline_im.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        self.prev_canvas.baseline_im = ImageTk.PhotoImage(self.baseline_im)
        self.preview.configure(image=self.prev_canvas.baseline_im)

    def get_heightmap(self):
        heightmap_name = filedialog.askopenfilename(
            initialdir=os.path.join(map_folder),
            title="Select file",
            filetypes=(("png file", "*.png"), ("all files", "*.*"))
        )
        heightmap_path = os.path.join(heightmap_name)
        self.baseline_map = numpy.array(Image.open(heightmap_path).convert('I'))
        self.baseline_map = numpy.interp(self.baseline_map, (self.baseline_map.min(), self.baseline_map.max()),
                                         (0, MAX_16BIT))  # normalizing heightmap to 0...255
        pp.imsave(os.path.join(self.ws_name, partials_folder, "baseline.png"), self.baseline_map, vmin=0, vmax=MAX_16BIT)

        self.baseline_im = Image.open(os.path.join(self.ws_name, partials_folder, "baseline.png"))

        self.baseline_im.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        self.prev_canvas.baseline_im = ImageTk.PhotoImage(self.baseline_im)
        self.preview.configure(image=self.prev_canvas.baseline_im)


class AssetParams(BaseWindow):
    def __init__(self, master, prev_canvas, ws_name):
        super().__init__(master, prev_canvas)
        self.ws_name = ws_name
        # --- initialize all internal text representations
        self.str_grass_level = tk.StringVar(value=500)
        self.str_grass_sigma = tk.StringVar(value=5)

        self.str_berries_dense = tk.StringVar(value=10)
        self.str_berries_group = tk.StringVar(value=5)
        self.str_berries_steep = tk.StringVar(value=10)
        self.str_berries_min = tk.StringVar(value=600)
        self.str_berries_max = tk.StringVar(value=1000)
        self.str_berries_sigma = tk.StringVar(value=5)

        self.str_stone_dense = tk.StringVar(value=10)
        self.str_stone_group = tk.StringVar(value=5)
        self.str_stone_steep = tk.StringVar(value=10)
        self.str_stone_min = tk.StringVar(value=600)
        self.str_stone_max = tk.StringVar(value=1000)
        self.str_stone_sigma = tk.StringVar(value=5)

        self.str_ore_dense = tk.StringVar(value=5)
        self.str_ore_group = tk.StringVar(value=0)
        self.str_ore_steep = tk.StringVar(value=10)
        self.str_ore_min = tk.StringVar(value=600)
        self.str_ore_max = tk.StringVar(value=1000)
        self.str_ore_sigma = tk.StringVar(value=5)

        self.str_fish_dense = tk.StringVar(value=50)
        self.str_fish_group = tk.StringVar(value=5)
        self.str_fish_max = tk.StringVar(value=400)

        # initialize labels for the preview
        self.prev_material = tk.Label(self.prev_canvas)
        self.prev_material_label = tk.Label(self.prev_canvas)
        self.prev_berries = tk.Label(self.prev_canvas)
        self.prev_berries_label = tk.Label(self.prev_canvas)
        self.prev_stone = tk.Label(self.prev_canvas)
        self.prev_stone_label = tk.Label(self.prev_canvas)
        self.prev_ore = tk.Label(self.prev_canvas)
        self.prev_ore_label = tk.Label(self.prev_canvas)
        self.prev_fish = tk.Label(self.prev_canvas)
        self.prev_fish_label = tk.Label(self.prev_canvas)

        # initialize arrays and handles
        self.heightmap = self.load_heightmap()
        self.material_map = numpy.full((1024, 1024), 0)
        self.berries_map = numpy.full((1024, 1024), 0)
        self.stone_map = numpy.full((1024, 1024), 0)
        self.ore_map = numpy.full((1024, 1024), 0)
        self.fish_map = numpy.full((1024, 1024), 0)
        self.cutout_mask = numpy.full((1024, 1024), 255)

        self.prev_canvas.mmap_handle = []
        self.prev_index_list = {'material': 0, 'berries': 0, 'stone': 0, 'ore': 0, 'fish': 0, 'decid': 0, 'conif': 0}

        # --- built head
        self.object_label = "Asset Parameters"
        self.label_name = tk.Label(self.top_frame, text=self.object_label)
        self.label_name.grid(column=0, row=0, sticky='w')
        self.gen_btn = tk.Button(self.top_frame, text="build asset maps", command=self.build_asset_maps)
        self.gen_btn.grid(column=1, row=0, sticky='e')

        # --- built input matrix
        self.label_grass_headline = tk.Label(self.main_frame, text="grass parameter:")
        self.label_grass_headline.grid(column=0, row=0, columnspan=4, sticky='w', padx=PADX)
        self.grass_btn = tk.Button(self.main_frame, text="build material map", command=self.build_material_map)
        self.grass_btn.grid(column=5, columnspan=3, row=0, sticky='e')

        # Grass Level
        self.label_grass_level = tk.Label(self.main_frame, text="level:")
        self.label_grass_level.grid(column=0, row=1, sticky='w', padx=PADX)
        self.box_grass_level = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_grass_level)
        self.box_grass_level.grid(column=1, row=1, sticky='w', padx=PADX)

        # Grass Sigma
        self.label_grass_sigma = tk.Label(self.main_frame, text="sigma:")
        self.label_grass_sigma.grid(column=2, row=1, sticky='w', padx=PADX)
        self.box_grass_sigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_grass_sigma)
        self.box_grass_sigma.grid(column=3, row=1, sticky='w', padx=PADX)

        # --- Berries ----
        self.label_berries_headline = tk.Label(self.main_frame, text="berries parameters:")
        self.label_berries_headline.grid(column=0, row=6, sticky='w', padx=PADX, columnspan=4)
        self.berries_btn = tk.Button(self.main_frame, text="build berries map", command=self.build_berries_map)
        self.berries_btn.grid(column=5, columnspan=3, row=6, sticky='e')
        # berries steep
        self.label_berries_steep = tk.Label(self.main_frame, text="steep:")
        self.label_berries_steep.grid(column=0, row=7, sticky='w', padx=PADX)
        self.box_berries_steep = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_berries_steep)
        self.box_berries_steep.grid(column=1, row=7, sticky='w', padx=PADX)
        # berries dense
        self.label_berries_dense = tk.Label(self.main_frame, text="dense:")
        self.label_berries_dense.grid(column=2, row=7, sticky='w', padx=PADX)
        self.box_berries_dense = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_berries_dense)
        self.box_berries_dense.grid(column=3, row=7, sticky='w', padx=PADX)
        # berries group
        self.label_berries_group = tk.Label(self.main_frame, text="group:")
        self.label_berries_group.grid(column=4, row=7, sticky='w', padx=PADX)
        self.box_berries_group = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_berries_group)
        self.box_berries_group.grid(column=5, row=7, sticky='w', padx=PADX)
        # berries min
        self.label_berries_min = tk.Label(self.main_frame, text="min:")
        self.label_berries_min.grid(column=6, row=7, sticky='w', padx=PADX)
        self.box_berries_min = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_berries_min)
        self.box_berries_min.grid(column=7, row=7, sticky='w', padx=PADX)
        # berries max
        self.label_berries_max = tk.Label(self.main_frame, text="max:")
        self.label_berries_max.grid(column=0, row=8, sticky='w', padx=PADX)
        self.box_berries_max = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_berries_max)
        self.box_berries_max.grid(column=1, row=8, sticky='w', padx=PADX)
        # berries sigma
        self.label_berries_sigma = tk.Label(self.main_frame, text="sigma:")
        self.label_berries_sigma.grid(column=2, row=8, sticky='w', padx=PADX)
        self.box_berries_sigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_berries_sigma)
        self.box_berries_sigma.grid(column=3, row=8, sticky='w', padx=PADX)

        # --- stone ----
        self.label_stone_headline = tk.Label(self.main_frame, text="stone parameters:")
        self.label_stone_headline.grid(column=0, row=9, sticky='w', padx=PADX, columnspan=4)
        self.stone_btn = tk.Button(self.main_frame, text="build stone map", command=self.build_stone_map)
        self.stone_btn.grid(column=5, columnspan=3, row=9, sticky='e')
        # stone steep
        self.label_stone_steep = tk.Label(self.main_frame, text="steep:")
        self.label_stone_steep.grid(column=0, row=10, sticky='w', padx=PADX)
        self.box_stone_steep = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_stone_steep)
        self.box_stone_steep.grid(column=1, row=10, sticky='w', padx=PADX)
        # stone dense
        self.label_stonedense = tk.Label(self.main_frame, text="dense:")
        self.label_stonedense.grid(column=2, row=10, sticky='w', padx=PADX)
        self.box_stonedense = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_stone_dense)
        self.box_stonedense.grid(column=3, row=10, sticky='w', padx=PADX)
        # stone group
        self.label_stonegroup = tk.Label(self.main_frame, text="group:")
        self.label_stonegroup.grid(column=4, row=10, sticky='w', padx=PADX)
        self.box_stonegroup = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_stone_group)
        self.box_stonegroup.grid(column=5, row=10, sticky='w', padx=PADX)
        # stone min
        self.label_stonemin = tk.Label(self.main_frame, text="min:")
        self.label_stonemin.grid(column=6, row=10, sticky='w', padx=PADX)
        self.box_stonemin = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_stone_min)
        self.box_stonemin.grid(column=7, row=10, sticky='w', padx=PADX)
        # stone max
        self.label_stonemax = tk.Label(self.main_frame, text="max:")
        self.label_stonemax.grid(column=0, row=11, sticky='w', padx=PADX)
        self.box_stonemax = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_stone_max)
        self.box_stonemax.grid(column=1, row=11, sticky='w', padx=PADX)
        # stone sigma
        self.label_stonesigma = tk.Label(self.main_frame, text="sigma:")
        self.label_stonesigma.grid(column=2, row=11, sticky='w', padx=PADX)
        self.box_stonesigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_stone_sigma)
        self.box_stonesigma.grid(column=3, row=11, sticky='w', padx=PADX)
        # --- ore ----
        self.label_oreheadline = tk.Label(self.main_frame, text="ore parameters:")
        self.label_oreheadline.grid(column=0, row=12, sticky='w', padx=PADX, columnspan=4)
        self.ore_btn = tk.Button(self.main_frame, text="build iron ore map", command=self.build_ore_map)
        self.ore_btn.grid(column=5, columnspan=3, row=12, sticky='e')
        # ore steep
        self.label_ore_steep = tk.Label(self.main_frame, text="steep:")
        self.label_ore_steep.grid(column=0, row=13, sticky='w', padx=PADX)
        self.box_ore_steep = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_ore_steep)
        self.box_ore_steep.grid(column=1, row=13, sticky='w', padx=PADX)
        # ore dense
        self.label_ore_dense = tk.Label(self.main_frame, text="dense:")
        self.label_ore_dense.grid(column=2, row=13, sticky='w', padx=PADX)
        self.box_ore_dense = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_ore_dense)
        self.box_ore_dense.grid(column=3, row=13, sticky='w', padx=PADX)
        # ore group
        self.label_ore_group = tk.Label(self.main_frame, text="group:")
        self.label_ore_group.grid(column=4, row=13, sticky='w', padx=PADX)
        self.box_ore_group = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_ore_group)
        self.box_ore_group.grid(column=5, row=13, sticky='w', padx=PADX)
        # ore min
        self.label_ore_min = tk.Label(self.main_frame, text="min:")
        self.label_ore_min.grid(column=6, row=13, sticky='w', padx=PADX)
        self.box_ore_min = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_ore_min)
        self.box_ore_min.grid(column=7, row=13, sticky='w', padx=PADX)
        # ore max
        self.label_ore_max = tk.Label(self.main_frame, text="max:")
        self.label_ore_max.grid(column=0, row=14, sticky='w', padx=PADX)
        self.box_ore_max = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_ore_max)
        self.box_ore_max.grid(column=1, row=14, sticky='w', padx=PADX)
        # ore sigma
        self.label_ore_sigma = tk.Label(self.main_frame, text="sigma:")
        self.label_ore_sigma.grid(column=2, row=14, sticky='w', padx=PADX)
        self.box_ore_sigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_ore_sigma)
        self.box_ore_sigma.grid(column=3, row=14, sticky='w', padx=PADX)
        # --- fish ----
        self.label_fish_headline = tk.Label(self.main_frame, text="fish parameters:")
        self.label_fish_headline.grid(column=0, row=15, sticky='w', padx=PADX, columnspan=4)
        self.fish_btn = tk.Button(self.main_frame, text="build fish map", command=self.build_fish_map)
        self.fish_btn.grid(column=5, columnspan=3, row=15, sticky='e')
        # fish dense
        self.label_fish_dense = tk.Label(self.main_frame, text="dense:")
        self.label_fish_dense.grid(column=0, row=16, sticky='w', padx=PADX)
        self.box_fish_dense = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_fish_dense)
        self.box_fish_dense.grid(column=1, row=16, sticky='w', padx=PADX)
        # fish group
        self.label_fish_group = tk.Label(self.main_frame, text="group:")
        self.label_fish_group.grid(column=2, row=16, sticky='w', padx=PADX)
        self.box_fish_group = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_fish_group)
        self.box_fish_group.grid(column=3, row=16, sticky='w', padx=PADX)
        # fish max
        self.label_fish_max = tk.Label(self.main_frame, text="max:")
        self.label_fish_max.grid(column=4, row=16, sticky='w', padx=PADX)
        self.box_fish_max = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_fish_max)
        self.box_fish_max.grid(column=5, row=16, sticky='w', padx=PADX)

    def parse_json(self, json_name):
        with open(json_name) as json_file:
            data = json.load(json_file)
            self.param_from_data(data)

    def param_from_data(self, data):
        self.str_grass_level.set(data['grass']['level'])
        self.str_grass_sigma.set(data['grass']['sigma'])

        self.str_berries_dense.set(data['berries']['density'])
        self.str_berries_group.set(data['berries']['grouping'])
        self.str_berries_steep.set(data['berries']['steepness'])
        self.str_berries_min.set(data['berries']['min_height'])
        self.str_berries_max.set(data['berries']['max_height'])
        self.str_berries_sigma.set(data['berries']['sigma'])

        self.str_stone_dense.set(data['stone']['density'])
        self.str_stone_group.set(data['stone']['grouping'])
        self.str_stone_steep.set(data['stone']['steepness'])
        self.str_stone_min.set(data['stone']['min_height'])
        self.str_stone_max.set(data['stone']['max_height'])
        self.str_stone_sigma.set(data['stone']['sigma'])

        self.str_ore_dense.set(data['ore']['density'])
        self.str_ore_group.set(data['ore']['grouping'])
        self.str_ore_steep.set(data['ore']['steepness'])
        self.str_ore_min.set(data['ore']['min_height'])
        self.str_ore_max.set(data['ore']['max_height'])
        self.str_ore_sigma.set(data['ore']['sigma'])

        self.str_fish_dense.set(data['fish']['density'])
        self.str_fish_group.set(data['fish']['grouping'])
        self.str_fish_max.set(data['fish']['max_height'])

    def load_heightmap(self):
        # get heightmap
        heightmap_path = os.path.join(self.ws_name, map_folder, hmap_name)
        self.heightmap = numpy.full((1024, 1024), 0, dtype=numpy.uint16)
        try:
            self.heightmap = numpy.array(Image.open(heightmap_path).convert('I'), dtype=numpy.uint16)
        except IOError:
            print("WARNING:heightmap.png not found or could not be opened!")
        return self.heightmap

    def build_material_map(self):
        self.heightmap = self.load_heightmap()
        grass_level = int(self.str_grass_level.get()) * NORM
        grass_sigma = int(self.str_grass_sigma.get())
        file_name = os.path.join(self.ws_name, map_folder, "material_mask.png")
        print(self.ws_name)
        print(file_name)
        self.material_map = assets.material_map(self.heightmap, grass_level, grass_sigma)
        color_list = [(0, "red"), (1, "lime")]
        green_red = mpl.colors.LinearSegmentedColormap.from_list("name", color_list)
        pp.imsave(file_name, self.material_map, vmin=0, vmax=255, cmap=green_red)

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['material'] == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_material.configure(image=self.prev_canvas.mmap_handle[-1])
            self.prev_material.pack()
            self.prev_material_label.configure(text="material map")
            self.prev_material_label.pack()
            self.prev_index_list['material'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['material'] - 1] = ImageTk.PhotoImage(image)
            self.prev_material.configure(image=self.prev_canvas.mmap_handle[self.prev_index_list['material'] - 1])
        self.prev_canvas.master.update()

    def build_berries_map(self):
        self.heightmap = self.load_heightmap()

        file_name = os.path.join(self.ws_name, map_folder, "berries_density.png")

        sigma = int(self.str_berries_sigma.get())
        steep = int(self.str_berries_steep.get()) * NORM
        min_val = int(self.str_berries_min.get()) * NORM
        max_val = int(self.str_berries_max.get()) * NORM
        dense = int(self.str_berries_dense.get())
        group = int(self.str_berries_group.get())

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma)
        asset_mask = assets.asset_mask(self.heightmap, min_val, max_val)
        mask = (grad_mask * asset_mask) / 255
        self.berries_map = assets.asset_map(mask, dense, group)
        pp.imsave(file_name, self.berries_map, vmin=0, vmax=255, cmap='gray')

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['berries'] == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_berries.configure(image=self.prev_canvas.mmap_handle[-1])
            self.prev_berries.pack()
            self.prev_berries_label.configure(text="berries density map")
            self.prev_berries_label.pack()
            self.prev_index_list['berries'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['berries'] - 1] = ImageTk.PhotoImage(image)
            self.prev_berries.configure(image=self.prev_canvas.mmap_handle[self.prev_index_list['berries'] - 1])
        self.prev_canvas.master.update()

    def build_stone_map(self):
        self.heightmap = self.load_heightmap()

        file_name = os.path.join(self.ws_name, map_folder, "rock_density.png")

        sigma = int(self.str_stone_sigma.get())
        steep = int(self.str_stone_steep.get()) * NORM
        min_val = int(self.str_stone_min.get()) * NORM
        max_val = int(self.str_stone_max.get()) * NORM
        dense = int(self.str_stone_dense.get())
        group = int(self.str_stone_group.get())

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma)
        asset_mask = assets.asset_mask(self.heightmap, min_val, max_val)
        mask = (grad_mask * asset_mask) / 255
        self.stone_map = assets.asset_map(mask, dense, group)
        pp.imsave(file_name, self.stone_map, vmin=0, vmax=255, cmap='gray')

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['stone'] == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_stone.configure(image=self.prev_canvas.mmap_handle[-1])
            self.prev_stone.pack()
            self.prev_stone_label.configure(text="stone density map")
            self.prev_stone_label.pack()
            self.prev_index_list['stone'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['stone'] - 1] = ImageTk.PhotoImage(image)
            self.prev_stone.configure(image=self.prev_canvas.mmap_handle[self.prev_index_list['stone'] - 1])
        self.prev_canvas.master.update()

    def build_ore_map(self):
        self.heightmap = self.load_heightmap()
        file_name = os.path.join(self.ws_name, map_folder, "iron_density.png")
        sigma = int(self.str_ore_sigma.get())
        steep = int(self.str_ore_steep.get()) * NORM
        min_val = int(self.str_ore_min.get()) * NORM
        max_val = int(self.str_ore_max.get()) * NORM
        dense = int(self.str_ore_dense.get())
        group = int(self.str_ore_group.get())

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma)
        asset_mask = assets.asset_mask(self.heightmap, min_val, max_val)
        mask = (grad_mask * asset_mask) / 255
        self.ore_map = assets.asset_map(mask, dense, group)
        pp.imsave(file_name, self.ore_map, vmin=0, vmax=255, cmap='gray')

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['ore'] == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_ore.configure(image=self.prev_canvas.mmap_handle[-1])
            self.prev_ore.pack()
            self.prev_ore_label.configure(text="ore density map")
            self.prev_ore_label.pack()
            self.prev_index_list['ore'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['ore'] - 1] = ImageTk.PhotoImage(image)
            self.prev_ore.configure(image=self.prev_canvas.mmap_handle[self.prev_index_list['ore'] - 1])
        self.prev_canvas.master.update()

    def build_fish_map(self):
        self.heightmap = self.load_heightmap()

        file_name = os.path.join(self.ws_name, map_folder, "fish_density.png")

        group = int(self.str_fish_group.get())
        max_val = int(self.str_fish_max.get()) * NORM
        dense = int(self.str_fish_dense.get())

        mask = assets.asset_mask(self.heightmap, 0, max_val)
        self.fish_map = assets.asset_map(mask, dense, group)

        pp.imsave(file_name, self.fish_map, vmin=0, vmax=255, cmap='gray')

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['fish'] == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_fish.configure(image=self.prev_canvas.mmap_handle[-1])
            self.prev_fish.pack()
            self.prev_fish_label.configure(text="fish density map")
            self.prev_fish_label.pack()
            self.prev_index_list['fish'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['fish'] - 1] = ImageTk.PhotoImage(image)
            self.prev_fish.configure(image=self.prev_canvas.mmap_handle[self.prev_index_list['fish'] - 1])
        self.prev_canvas.master.update()

    def build_cutout_mask(self):
        self.cutout_mask = assets.asset_cutout_mask(self.berries_map, self.stone_map, self.ore_map, 5)

    def build_asset_maps(self):
        self.build_material_map()
        self.build_berries_map()
        self.build_stone_map()
        self.build_ore_map()
        self.build_fish_map()

        self.build_cutout_mask()


def lua_prefab_to_str(name, comment="create density prefab", density=0.9, weight=0.1,
                      offset_min=0.75, offset_max=1.0,
                      orient_min="{ 0, -180, 0 }", orient_max="{ 0, 180, 0 }",
                      scale_min=0.85, scale_max=1.15,
                      color_min="{ 0.8, 0.8, 0.8, 1 }", color_max="{ 1, 1, 1, 1 }"):
    map_name = name.upper() + '_DENSITY_MAP'
    resource_name = 'PREFAB_RESOURCE_' + name.upper()

    lua_str = ['\t\t{',
               '\t\t\t-- ' + comment,
               '\t\t\tDensityMap = "' + map_name + '",',
               '\t\t\tDensity =' + str(density) + ',',
               '\t\t\tPrefabConfigList = {',
               '\t\t\t\t{',
               '\t\t\t\t\t\tPrefabList = { "' + resource_name + '" },',
               '\t\t\t\t\t\tRandomWeight = ' + str(weight) + ',',
               '\t\t\t\t\t\tOffsetSizeRange = {',
               '\t\t\t\t\t\t\tMin = ' + str(offset_min) + ',',
               '\t\t\t\t\t\t\tMax = ' + str(offset_max),
               '\t\t\t\t\t},',
               '\t\t\t\t\t\tOrientationRange = {',
               '\t\t\t\t\t\t\tMin = ' + orient_min + ',',
               '\t\t\t\t\t\t\tMax = ' + orient_max,
               '\t\t\t\t\t},',
               '\t\t\t\t\t\tScaleRange = {',
               '\t\t\t\t\t\t\tMin = ' + str(scale_min) + ',',
               '\t\t\t\t\t\t\tMax = ' + str(scale_max),
               '\t\t\t\t\t},',
               '\t\t\t\t\t\tColorRange = {',
               '\t\t\t\t\t\t\tMin = ' + color_min + ',',
               '\t\t\t\t\t\t\tMax = ' + color_max,
               '\t\t\t\t\t}',
               '\t\t\t\t}',
               '\t\t\t}',
               '\t\t},']

    return lua_str


class TreeMap:
    def __init__(self, container, master, prev_canvas, index, ws_name):

        self.int_steep = tk.IntVar(value=10)
        self.int_max = tk.IntVar(value=1000)
        self.int_min = tk.IntVar(value=400)
        self.int_sigma = tk.IntVar(value=5)
        self.float_dense = tk.DoubleVar(value=0.8)

        self.object_label = "Tree Density Map" + str(index)
        self.master = master
        self.frame = tk.Frame(self.master, relief=tk.GROOVE, borderwidth=1)
        self.frame.pack(side='top', expand=True, fill='both')
        self.prev_canvas = prev_canvas
        self.container = container

        self.deleted = False
        self.ws_name = ws_name

        self.tree_types = []
        self.lua_str = []
        self.type_index = 0
        self.tree_map = numpy.full((1024, 1024), 0)
        self.heightmap = numpy.full((1024, 1024), 0, dtype=numpy.uint16)
        self.cutout_mask = numpy.full((1024, 1024), 255)
        self.index = index

        # initialize preview
        self.preview = tk.Label(self.prev_canvas)
        self.preview_label = tk.Label(self.prev_canvas)
        self.im_handle = []
        self.file_name = default_file
        file_name = os.path.join(partials_folder, default_file)
        self.index = self.build_preview(self.im_handle, self.object_label, file_name, self.index, init=True)

        # --- built head
        self.label_name = tk.Label(self.frame, text=self.object_label)
        self.label_name.grid(column=0, row=0, columnspan=4, sticky='w')
        self.gen_btn = tk.Button(self.frame, text="build", command=self.build_map)
        self.gen_btn.grid(column=5, row=0, sticky='e')
        self.del_btn = tk.Button(self.frame, text="delete", command=self.destroy)
        self.del_btn.grid(column=6, row=0, sticky='e')
        self.add_btn = tk.Button(self.frame, text="add", command=self.add_type)
        self.add_btn.grid(column=7, row=0, sticky='e')

        # steepness
        self.label_steep = tk.Label(self.frame, text="steep:")
        self.label_steep.grid(column=0, row=1, sticky='w', padx=PADX)
        self.box_steep = tk.Entry(self.frame, width=ENTRY_WIDTH, justify='right', textvariable=self.int_steep)
        self.box_steep.grid(column=1, row=1, sticky='w', padx=PADX)
        # min height
        self.label_min = tk.Label(self.frame, text="min:")
        self.label_min.grid(column=2, row=1, sticky='w', padx=PADX)
        self.box_min = tk.Entry(self.frame, width=ENTRY_WIDTH, justify='right', textvariable=self.int_min)
        self.box_min.grid(column=3, row=1, sticky='w', padx=PADX)
        # max height
        self.label_max = tk.Label(self.frame, text="max:")
        self.label_max.grid(column=4, row=1, sticky='w', padx=PADX)
        self.box_max = tk.Entry(self.frame, width=ENTRY_WIDTH, justify='right', textvariable=self.int_max)
        self.box_max.grid(column=5, row=1, sticky='w', padx=PADX)
        # sigma
        self.label_sigma = tk.Label(self.frame, text="sigma:")
        self.label_sigma.grid(column=6, row=1, sticky='w', padx=PADX)
        self.box_sigma = tk.Entry(self.frame, width=ENTRY_WIDTH, justify='right', textvariable=self.int_sigma)
        self.box_sigma.grid(column=7, row=1, sticky='w', padx=PADX)
        # dense
        self.label_dense = tk.Label(self.frame, text="density:")
        self.label_dense.grid(column=0, row=2, sticky='w', padx=PADX)
        self.box_dense = tk.Entry(self.frame, width=ENTRY_WIDTH, justify='right', textvariable=self.float_dense)
        self.box_dense.grid(column=1, row=2, sticky='w', padx=PADX)

        self.type_frame = tk.Frame(self.frame)
        self.type_frame.grid(column=0, row=3, columnspan=8)

        self.container.update()

    def add_type(self):
        self.type_index += 1
        self.tree_types.append(TreeType(self.type_frame, self.type_index, self.container))

    def destroy(self):
        self.frame.destroy()
        self.preview.destroy()
        self.preview_label.destroy()
        self.deleted = True

    def load_heightmap(self):
        # get heightmap
        heightmap_path = os.path.join(self.ws_name, map_folder, hmap_name)
        try:
            self.heightmap = numpy.array(Image.open(heightmap_path).convert('I'), dtype=numpy.uint16)
        except IOError:
            print("WARNING:heightmap.png not found or could not be opened!")
        return self.heightmap

    def build_map(self):
        self.load_heightmap()
        self.file_name = self.get_final_file_name()
        file_name = os.path.join(self.ws_name, map_folder, self.file_name)

        sigma = self.int_sigma.get()
        steep = self.int_steep.get() * NORM
        min_val = self.int_min.get() * NORM
        max_val = self.int_max.get() * NORM

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma)
        asset_mask = assets.asset_mask(self.heightmap, min_val, max_val)
        mask = (grad_mask * asset_mask) / 255
        tree_map = (mask * self.cutout_mask) / 255
        self.tree_map = gaussian_filter(tree_map, sigma=sigma)
        pp.imsave(file_name, self.tree_map, vmin=0, vmax=255, cmap='gray')

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)

        self.index = self.build_preview(self.im_handle, self.object_label, file_name, self.index)
        self.prev_canvas.master.update()

    def get_final_file_name(self):
        file_name = self.object_label + ".png"
        file_name = file_name.lower().replace(" ", "_")
        return file_name

    def build_preview(self, handle, label, filename, index, init=False):
        # build preview
        image = Image.open(filename)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        if init:
            handle.append(ImageTk.PhotoImage(image))
            self.preview.configure(image=handle[-1])
            self.preview.pack()
            self.preview_label.configure(text=label)
            self.preview_label.pack()
            ret_val = len(handle)
        else:
            handle[index - 1] = ImageTk.PhotoImage(image)
            self.preview.configure(image=handle[index - 1])
            ret_val = index
        self.prev_canvas.master.update()
        return ret_val

    def to_lua_str(self):
        self.lua_str = []

        name = self.object_label.upper()
        density = str(self.float_dense.get())

        self.lua_str.append('\t\t\t{')
        self.lua_str.append('\t\t\t-- creating ' + self.object_label)
        self.lua_str.append('\t\t\tDensityMap = "' + name.replace(" ", "_") + '",')
        self.lua_str.append('\t\t\tDensity = ' + density + ',')
        self.lua_str.append('\t\t\tPrefabConfigList = {')
        for tree_type in self.tree_types:
            for line in tree_type.to_lua_str():
                self.lua_str.append(line)
        self.lua_str[-1] = self.lua_str[-1][:-1]
        self.lua_str.append('\t\t\t}')
        self.lua_str.append('\t\t},')

        return self.lua_str


class TreeType:
    def __init__(self, master, index, container):
        self.tree_type = tk.StringVar(value="oak")
        self.weight = tk.DoubleVar(value=1.0)
        self.min_scale = tk.DoubleVar(value=0.8)
        self.max_scale = tk.DoubleVar(value=1.2)
        self.min_color = (0.8, 0.8, 0.8)
        min_color = self.min_color_hex()
        self.max_color = (1, 1, 1)
        max_color = self.max_color_hex()
        self.deleted = True

        self.lua_str = []

        self.frame = tk.Frame(master)
        self.frame.pack(side='top')
        self.container = container
        self.option_list = ["oak", "sycamore", "poplar", "pine"]

        self.type_label = tk.Label(self.frame, text="Type" + str(index), width=10, justify="left")
        self.type_label.grid(column=0, row=0, sticky='w')
        self.options = tk.OptionMenu(self.frame, self.tree_type, *self.option_list)
        self.options.grid(column=1, row=0, columnspan=4, sticky='w')
        self.options.configure(width=10)
        self.weight_label = tk.Label(self.frame, text="weight: ")
        self.weight_label.grid(column=1, row=1, sticky='w')
        self.box_weight = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.weight, justify='right')
        self.box_weight.grid(column=2, row=1, sticky='w')
        self.scale_label = tk.Label(self.frame, text="Scale min/max: ")
        self.scale_label.grid(column=1, row=2, sticky='w')
        self.box_min_scale = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.min_scale, justify='right')
        self.box_min_scale.grid(column=2, row=2, sticky='w')
        self.box_max_scale = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.max_scale, justify='right')
        self.box_max_scale.grid(column=3, row=2, sticky='w')
        self.color_label = tk.Label(self.frame, text="Color: ")
        self.color_label.grid(column=4, row=2, sticky='w')
        self.color_min_btn = tk.Button(self.frame, text="min", command=self.pick_min, bg=min_color)
        self.color_min_btn.grid(column=5, row=2, sticky='w')
        self.color_max_btn = tk.Button(self.frame, text="max", command=self.pick_max, bg=max_color)
        self.color_max_btn.grid(column=6, row=2, sticky='w')
        self.del_btn = tk.Button(self.frame, text="delete", command=self.destroy)
        self.del_btn.grid(column=6, row=0, sticky='w')
        self.container.update()

    def pick_min(self):
        color, hex_str = colorchooser.askcolor()
        if color is not None:
            self.min_color = color[0] / 256, color[1] / 256, color[2] / 256
            print(color, self.max_color)
            self.color_min_btn.configure(bg=hex_str)

    def pick_max(self):
        color, hex_str = colorchooser.askcolor()
        if color is not None:
            self.max_color = color[0] / 256, color[1] / 256, color[2] / 256
            print(color, self.max_color)
            self.color_max_btn.configure(bg=hex_str)

    def destroy(self):
        self.frame.destroy()
        self.container.update()
        self.deleted = True

    def min_color_hex(self):
        r = "%0.2X" % int(self.min_color[0] * 255)
        g = "%0.2X" % int(self.min_color[1] * 255)
        b = "%0.2X" % int(self.min_color[2] * 255)
        color = "#" + r + g + b
        return color

    def max_color_hex(self):
        r = "%0.2X" % int(self.max_color[0] * 255)
        g = "%0.2X" % int(self.max_color[1] * 255)
        b = "%0.2X" % int(self.max_color[2] * 255)
        color = "#" + r + g + b
        return color

    def update(self):
        min_hex = self.min_color_hex()
        max_hex = self.max_color_hex()
        self.color_min_btn.configure(bg=min_hex)
        self.color_max_btn.configure(bg=max_hex)

    def to_lua_str(self):
        self.lua_str = []

        # get lua parameters
        tree_type = "PREFAB_TREE_" + self.tree_type.get().upper()
        weight = str(self.weight.get())
        offset_min = str(0.75)
        offset_max = str(1.0)
        orient_min = '{ 0, -180, 0 }'
        orient_max = '{ 0, 180, 0 }'
        min_scale = str(self.min_scale.get())
        max_scale = str(self.max_scale.get())
        min_color = '{ '+str(self.min_color[0])+','+str(self.min_color[1])+','+str(self.min_color[2])+',1 }'
        max_color = '{ '+str(self.max_color[0])+','+str(self.max_color[1])+','+str(self.max_color[2])+',1 }'

        self.lua_str.append('\t\t\t\t{')
        self.lua_str.append('\t\t\t\t\t\tPrefabList = { "' + tree_type + '" },')
        self.lua_str.append('\t\t\t\t\t\tRandomWeight = ' + weight + ',')
        self.lua_str.append('\t\t\t\t\t\tOffsetSizeRange = {')
        self.lua_str.append('\t\t\t\t\t\t\tMin = ' + offset_min + ',')
        self.lua_str.append('\t\t\t\t\t\t\tMax = ' + offset_max)
        self.lua_str.append('\t\t\t\t\t},')
        self.lua_str.append('\t\t\t\t\t\tOrientationRange = {')
        self.lua_str.append('\t\t\t\t\t\t\tMin = ' + orient_min + ',')
        self.lua_str.append('\t\t\t\t\t\t\tMax = ' + orient_max)
        self.lua_str.append('\t\t\t\t\t},')
        self.lua_str.append('\t\t\t\t\t\tScaleRange = {')
        self.lua_str.append('\t\t\t\t\t\t\tMin = ' + min_scale + ',')
        self.lua_str.append('\t\t\t\t\t\t\tMax = ' + max_scale)
        self.lua_str.append('\t\t\t\t\t},')
        self.lua_str.append('\t\t\t\t\t\tColorRange = {')
        self.lua_str.append('\t\t\t\t\t\t\tMin = ' + min_color + ',')
        self.lua_str.append('\t\t\t\t\t\t\tMax = ' + max_color)
        self.lua_str.append('\t\t\t\t\t}')
        self.lua_str.append('\t\t\t\t},')
        return self.lua_str


class River(Terrain):
    def __init__(self, container, master, prev_canvas, index, ws_name, wp_ignore=False):
        super().__init__(container, master, prev_canvas, index)

        # internal variables
        self.width = 3
        self.div = 10
        self.sigma = 5

        self.river = terrain.ImprovedRiver(self.width, self.div, self.sigma)
        self.ws_name = ws_name

        self.object_label = "River" + str(index)
        self.str_width = tk.StringVar()
        self.str_width.set(str(self.width))
        self.str_div = tk.StringVar()
        self.str_div.set(str(self.div))
        self.str_sigma = tk.StringVar()
        self.str_sigma.set(str(self.sigma))

        # Top Frame Area        
        self.label_name = tk.Label(self.top_frame, text=self.object_label)
        self.label_name.grid(column=0, row=0, sticky='w')
        self.gen_btn = tk.Button(self.top_frame, text="generate", command=self.generate)
        self.gen_btn.grid(column=3, row=0, sticky='e')
        self.del_btn = tk.Button(self.top_frame, text="delete", command=self.destroy)
        self.del_btn.grid(column=4, row=0, sticky='e')
        self.add_wp_btn = tk.Button(self.top_frame, text="add WP", command=self.add_wp)
        self.add_wp_btn.grid(column=5, row=0, sticky='e')

        # Main Frame Area
        self.label_width = tk.Label(self.main_frame, text="width: ")
        self.label_width.grid(column=0, row=1, sticky='w')
        self.box_width = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_width)
        self.box_width.grid(column=1, row=1, sticky='w')

        self.label_div = tk.Label(self.main_frame, text="diversity: ")
        self.label_div.grid(column=2, row=1, sticky='w')
        self.box_div = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_div)
        self.box_div.grid(column=3, row=1, sticky='w')

        self.label_sigma = tk.Label(self.main_frame, text="sigma: ")
        self.label_sigma.grid(column=4, row=1, sticky='w')
        self.box_sigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_sigma)
        self.box_sigma.grid(column=5, row=1, sticky='w')

        # build waypoint references and waypoint Frame Area
        if not wp_ignore:
            self.add_wp()
            self.add_wp()

        # build preview
        file_name = os.path.join(self.ws_name, partials_folder, default_file)
        self.index = self.build_preview(self.prev_canvas.river_im, self.object_label, file_name, self.index, init=True)

    def generate(self):
        file_name = os.path.join(self.ws_name, partials_folder, "rivermap" + str(self.index) + ".png")

        self.width = int(self.str_width.get())
        self.div = int(self.str_div.get())
        self.sigma = int(self.str_sigma.get())

        self.river = terrain.ImprovedRiver(self.width, self.div, self.sigma)

        for wp in self.wp_list:
            if not wp.deleted:
                x, y = wp.getval()
                self.river.add_wps(x, y)

        self.terrain_map = self.river.run()

        pp.imsave(file_name, self.terrain_map, vmin=0, vmax=50)
        self.index = self.build_preview(self.prev_canvas.river_im, self.object_label, file_name, self.index)

    def width_get(self):
        return int(self.str_width.get())

    def div_get(self):
        return int(self.str_div.get())

    def sigma_get(self):
        return int(self.str_sigma.get())


class Mountain(Terrain):
    def __init__(self, container, master, prev_canvas, index, ws_name, wp_ignore=False):
        super().__init__(container, master, prev_canvas, index)

        # internal variables
        self.object_label = "Mountain" + str(index)

        self.height = 500
        self.spread = 200
        self.div = 10
        self.dense = 10
        self.sigma = 20

        self.mountain = terrain.Mountain(self.height, self.spread, self.div, self.dense, self.sigma)
        self.ws_name = ws_name

        self.str_height = tk.StringVar(value=str(self.height))
        self.str_spread = tk.StringVar(value=str(self.spread))
        self.str_div = tk.StringVar(value=str(self.div))
        self.str_dense = tk.StringVar(value=str(self.dense))
        self.str_sigma = tk.StringVar(value=str(self.sigma))

        self.label_name = tk.Label(self.top_frame, text=self.object_label)
        self.label_name.grid(column=0, row=0, sticky='w')
        self.gen_btn = tk.Button(self.top_frame, text="generate", command=self.generate)
        self.gen_btn.grid(column=2, row=0, sticky='w')
        self.del_btn = tk.Button(self.top_frame, text="delete", command=self.destroy)
        self.del_btn.grid(column=3, row=0, sticky='w')
        self.add_wp_btn = tk.Button(self.top_frame, text="add WP", command=self.add_wp)
        self.add_wp_btn.grid(column=4, row=0, sticky='w')

        self.label_height = tk.Label(self.main_frame, text="height: ")
        self.label_height.grid(column=0, row=1, padx=PADX)
        self.box_height = tk.Entry(self.main_frame, width=ENTRY_WIDTH, textvariable=self.str_height)
        self.box_height.grid(column=1, row=1, padx=PADX)

        self.label_spread = tk.Label(self.main_frame, text="spread: ")
        self.label_spread.grid(column=2, row=1, padx=PADX)
        self.box_spread = tk.Entry(self.main_frame, width=ENTRY_WIDTH, textvariable=self.str_spread)
        self.box_spread.grid(column=3, row=1, padx=PADX)

        self.label_div = tk.Label(self.main_frame, text="diversity: ")
        self.label_div.grid(column=4, row=1, padx=PADX)
        self.box_div = tk.Entry(self.main_frame, width=ENTRY_WIDTH, textvariable=self.str_div)
        self.box_div.grid(column=5, row=1, padx=PADX)
        self.label_dense = tk.Label(self.main_frame, text="density: ")
        self.label_dense.grid(column=0, row=2, padx=PADX)
        self.box_dense = tk.Entry(self.main_frame, width=ENTRY_WIDTH, textvariable=self.str_dense)
        self.box_dense.grid(column=1, row=2, padx=PADX)
        self.label_sigma = tk.Label(self.main_frame, text="sigma: ")
        self.label_sigma.grid(column=2, row=2, padx=PADX)
        self.box_sigma = tk.Entry(self.main_frame, width=ENTRY_WIDTH, textvariable=self.str_sigma)
        self.box_sigma.grid(column=3, row=2, padx=PADX)

        # build wp frame Area       
        if not wp_ignore:
            self.add_wp()
            self.add_wp()

        # build preview
        file_name = os.path.join(self.ws_name, partials_folder, default_file)
        self.index = self.build_preview(self.prev_canvas.mountain_im, self.object_label, file_name, self.index, init=True)

    def height_get(self, norm=1.0):
        self.height = int(self.str_height.get())
        return self.height * norm

    def spread_get(self, norm=1.0):
        self.spread = int(self.str_spread.get())
        return self.spread * norm

    def div_get(self, norm=1.0):
        self.div = int(self.str_div.get())
        return self.div * norm

    def dense_get(self, norm=1.0):
        self.dense = int(self.str_dense.get())
        return self.dense * norm

    def sigma_get(self, norm=1.0):
        self.sigma = int(self.str_sigma.get())
        return self.sigma * norm

    def generate(self):
        # file name to save the preview file
        file_name = os.path.join(self.ws_name, partials_folder, self.object_label + ".png")

        # input parameters for generation 
        self.height = int(self.str_height.get()) * NORM
        self.spread = int(self.str_spread.get())
        self.div = int(self.str_div.get())
        self.dense = int(self.str_dense.get())
        self.sigma = int(self.str_sigma.get())

        self.mountain = terrain.Mountain(self.height, self.spread, self.div, self.dense, self.sigma)
        for wp in self.wp_list:
            if not wp.deleted:
                x, y = wp.getval()
                self.mountain.add_wps(x, y)

        self.terrain_map = self.mountain.run()
        if int(self.str_height.get()) >= 0:
            pp.imsave(file_name, self.terrain_map, vmin=0, vmax=MAX_16BIT)
        else:
            pp.imsave(file_name, self.terrain_map, vmin=-MAX_16BIT, vmax=0)
        self.index = self.build_preview(self.prev_canvas.mountain_im, self.object_label, file_name, self.index)


class Waypoint:
    def __init__(self, master, index, container):
        self.x = index * 100
        self.y = index * 100

        self.str_x = tk.StringVar(value=str(self.x))
        self.str_y = tk.StringVar(value=str(self.y))

        self.index = index
        self.container = container
        self.deleted = False

        self.frame = tk.Frame(master)
        self.frame.grid(column=0, sticky='w')

        self.wp_label = tk.Label(self.frame, text="Waypoint" + str(index), width=10)
        self.wp_label.grid(column=0, row=0, sticky='w')

        self.label_x = tk.Label(self.frame, text="X: ")
        self.label_x.grid(column=1, row=0, sticky='w')
        self.box_x = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.str_x)
        self.box_x.grid(column=2, row=0, sticky='w')
        self.label_y = tk.Label(self.frame, text="Y: ")
        self.label_y.grid(column=3, row=0, sticky='w')
        self.box_y = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.str_y)
        self.box_y.grid(column=4, row=0, sticky='w')
        self.del_btn = tk.Button(self.frame, text="delete", command=self.destroy)
        self.del_btn.grid(column=5, row=0, sticky='w')
        self.container.update()

    def destroy(self):
        self.frame.destroy()
        self.container.update()
        self.deleted = True

    def getval(self):
        try:
            self.x = int(self.str_x.get())
        except ValueError:
            self.x = 0
        try:
            self.y = int(self.str_y.get())
        except ValueError:
            self.y = 0

        return self.x, self.y


class VillagePath:
    def __init__(self, container, master, index):
        """ Village path defines an entry and an exit point to the map """
        self.x_entry = index * 100
        self.y_entry = 15
        self.x_exit = index * 100
        self.y_exit = 1010
        self.lua_str = []
        self.to_lua_str()

        self.str_x_entry = tk.StringVar(value=str(self.x_entry))
        self.str_y_entry = tk.StringVar(value=str(self.y_entry))
        self.str_x_exit = tk.StringVar(value=str(self.x_exit))
        self.str_y_exit = tk.StringVar(value=str(self.y_exit))

        self.index = index
        self.container = container
        self.deleted = False

        self.frame = tk.Frame(master)
        self.frame.grid(column=0, sticky='w')

        self.wp_label = tk.Label(self.frame, text="Village Path " + str(index), justify="left")
        self.wp_label.grid(column=0, row=0, columnspan=3, sticky='w')

        self.label_x_entry = tk.Label(self.frame, text="X Entry: ")
        self.label_x_entry.grid(column=1, row=1, sticky='w')
        self.box_x_entry = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.str_x_entry)
        self.box_x_entry.grid(column=2, row=1, sticky='w')
        self.label_y_entry = tk.Label(self.frame, text="Y Entry: ")
        self.label_y_entry.grid(column=3, row=1, sticky='w')
        self.box_y_entry = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.str_y_entry)
        self.box_y_entry.grid(column=4, row=1, sticky='w')

        self.label_x_exit = tk.Label(self.frame, text="X Exit: ")
        self.label_x_exit.grid(column=1, row=2, sticky='w')
        self.box_x_exit = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.str_x_exit)
        self.box_x_exit.grid(column=2, row=2, sticky='w')
        self.label_y_exit = tk.Label(self.frame, text="Y Exit: ")
        self.label_y_exit.grid(column=3, row=2, sticky='w')
        self.box_y_exit = tk.Entry(self.frame, width=ENTRY_WIDTH, textvariable=self.str_y_exit)
        self.box_y_exit.grid(column=4, row=2, sticky='w')

        self.del_btn = tk.Button(self.frame, text="delete", command=self.destroy)
        self.del_btn.grid(column=5, row=0, sticky='w')
        self.container.update()

    def destroy(self):
        self.frame.destroy()
        self.container.update()
        self.deleted = True

    def getval(self):
        if not self.deleted:
            try:
                self.x_entry = int(self.str_x_entry.get())
                self.x_exit = int(self.str_x_exit.get())
                self.y_entry = int(self.str_y_entry.get())
                self.y_exit = int(self.str_y_exit.get())
            except ValueError:
                self.x_entry = 0
                self.x_exit = 0
                self.y_entry = 0
                self.y_exit = 0

        return (self.x_entry, self.y_entry), (self.x_exit, self.y_exit)

    def to_lua_str(self):
        self.lua_str = []
        self.lua_str.append('\t\t{')
        self.lua_str.append('\t\t\tEntrance = { ' + str(self.x_entry) + ', 0, ' + str(1023 - self.y_entry) + ' },')
        self.lua_str.append('\t\t\tExit = { ' + str(self.x_exit) + ', 0, ' + str(1023 - self.y_exit) + ' },')
        self.lua_str.append('\t\t},')

        return self.lua_str


class Scrollable(tk.Frame):
    def __init__(self, frame, width=16):
        scrollbar = tk.Scrollbar(frame, width=width)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)

        self.canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.canvas.yview)

        self.canvas.bind('<Configure>', self.__fill_canvas)

        # base class initialization
        tk.Frame.__init__(self, frame)

        # assign this obj (the inner frame) to the windows item of the canvas
        self.windows_item = self.canvas.create_window(0, 0, window=self, anchor=tk.NW)

    def __fill_canvas(self, event):
        """Enlarge the windows item to the canvas width"""

        canvas_width = event.width
        self.canvas.itemconfig(self.windows_item, width=canvas_width)

    def update(self):
        """Update the canvas and the scroll region"""

        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(self.windows_item))


def create_defaults():
    """create folders and default files"""

    # is the maps folder missing, make one
    if not os.path.exists(map_folder):
        os.mkdir(map_folder)

    # is the partials maps folder missing, make one
    if not os.path.exists(partials_folder):
        os.mkdir(partials_folder)

    # is the default partials map in partials missing, make one
    if not os.path.exists(os.path.join(partials_folder, default_file)):
        default_map = numpy.random.randint(0, high=255, size=(1024, 1024))
        pp.imsave(os.path.join(partials_folder, default_file), default_map, vmin=0, vmax=255)

    if not os.path.exists(os.path.join(partials_folder, "combined.png")):
        heightmap = numpy.random.randint(0, high=255, size=(1024, 1024))
        pp.imsave(os.path.join(partials_folder, "combined.png"), heightmap, vmin=0, vmax=255)

        # is the json config file folder missing, make one
    if not os.path.exists(jsons_folder):
        os.mkdir(jsons_folder)


class Status:
    def __init__(self, message, status_label, status_length):
        self.message = message
        self.status_message = ""
        self.label = status_label
        self.length = status_length
        self.print(self.message)

    def print(self, message):
        self.message = message
        self.status_message = " --- " + self.message + self.status_message

        if len(self.status_message) > self.length:
            self.status_message = self.status_message[:self.length]

        self.label.configure(text=self.status_message)


class MapInfo:
    def __init__(self, height, water_level):

        self.object_label = "General Map Infos"
        self.show = False
        self.flag_done = False

        # --- initialize all internal text representations
        self.name = tk.StringVar(value="My Map")
        self.id = tk.StringVar(value="MY_MAP_ID")
        self.author = tk.StringVar(value="MyName")
        self.description = tk.StringVar(value="My Map - A beautiful map, I created")
        self.version = tk.StringVar(value="0.0.1")

        self.height = height
        self.str_height = tk.StringVar(value=str(self.height))

        self.water_level = water_level
        self.str_water_level = tk.StringVar(value=str(self.water_level))

        # --- built window
        self.win = tk.Toplevel()
        self.win.geometry("+500+500")
        self.win.overrideredirect(1)
        self.win.title("Map Info")

        self.label_name = tk.Label(self.win, text=self.object_label)
        self.label_name.grid(column=0, row=0, sticky='w')
        self.frame = tk.Frame(self.win)
        self.frame.grid(column=0, row=1, sticky='we')

        # --- built input matrix
        self.label_map_name = tk.Label(self.frame, text="Map Name: ")
        self.label_map_name.grid(column=0, row=0, sticky='w', padx=PADX)
        self.box_map_name = tk.Entry(self.frame, width=40, justify='left', textvariable=self.name)
        self.box_map_name.grid(column=1, row=0, sticky='w', padx=PADX)

        self.label_id = tk.Label(self.frame, text="Map ID: ")
        self.label_id.grid(column=0, row=1, sticky='w', padx=PADX)
        self.box_id = tk.Entry(self.frame, width=40, justify='left', textvariable=self.id)
        self.box_id.bind('<Return>', self.upper_id)
        self.box_id.bind('<FocusOut>', self.upper_id)
        self.box_id.grid(column=1, row=1, sticky='w', padx=PADX)
        self.id_btn = tk.Button(self.frame, text="+", command=self.suggest_id)
        self.id_btn.grid(column=2, row=1, sticky='w')

        self.label_author = tk.Label(self.frame, text="Author: ")
        self.label_author.grid(column=0, row=2, sticky='w', padx=PADX)
        self.box_author = tk.Entry(self.frame, width=40, justify='left', textvariable=self.author)
        self.box_author.grid(column=1, row=2, sticky='w', padx=PADX)
        self.author_btn = tk.Button(self.frame, text="+", command=self.suggest_author)
        self.author_btn.grid(column=2, row=2, sticky='w')

        self.label_version = tk.Label(self.frame, text="Version: ")
        self.label_version.grid(column=0, row=3, sticky='w', padx=PADX)
        self.box_version = tk.Entry(self.frame, width=40, justify='left', textvariable=self.version)
        self.box_version.grid(column=1, row=3, sticky='w', padx=PADX)

        self.label_comment = tk.Label(self.frame, text="Description: ")
        self.label_comment.grid(column=0, row=4, sticky='w', padx=PADX)
        self.box_comment = tk.Entry(self.frame, width=40, justify='left', textvariable=self.description)
        self.box_comment.grid(column=1, row=4, sticky='w', padx=PADX)
        self.comment_btn = tk.Button(self.frame, text="+", command=self.suggest_description)
        self.comment_btn.grid(column=2, row=4, sticky='w')

        ttk.Separator(self.frame).grid(column=0, row=5, columnspan=3, sticky='we', padx=PADX)

        self.label_height = tk.Label(self.frame, text="height: ")
        self.label_height.grid(column=0, row=6, sticky='w', padx=PADX)
        self.box_height = tk.Entry(self.frame, width=5, justify='right', textvariable=self.str_height)
        self.box_height.grid(column=1, row=6, sticky='e', padx=PADX)

        self.label_water_level = tk.Label(self.frame, text="water level: ")
        self.label_water_level.grid(column=0, row=7, sticky='w', padx=PADX)
        self.box_water_level = tk.Entry(self.frame, width=5, justify='right', textvariable=self.str_water_level)
        self.box_water_level.grid(column=1, row=7, sticky='e', padx=PADX)

        ttk.Separator(self.frame).grid(column=0, row=8, columnspan=3, sticky='we', padx=PADX)

        self.done_btn = tk.Button(self.frame, text="done", command=self.done)
        self.done_btn.grid(column=0, row=9, sticky='w')
        # self.suggest_btn = tk.Button(self.frame, text = "delete", command = self.withdraw )
        # self.suggest_btn.grid(column = 1, row = 9, sticky = 'w')

    def upper_id(self, event):
        get_id = self.id.get()
        get_id = get_id.upper().replace(" ", "_")
        print(get_id)
        self.id.set(get_id)

    def done(self):
        self.withdraw()
        self.flag_done = True

    def toggle_view(self):
        if self.show:
            self.withdraw()
        else:
            self.deiconify()

    def withdraw(self):
        self.win.withdraw()
        self.show = False

    def deiconify(self):
        self.win.deiconify()
        self.show = True

    def suggest_id(self):
        map_id = self.name.get() + "_id"
        map_id = map_id.upper().replace(" ", "_")
        self.id.set(map_id)

    def suggest_author(self):
        self.author.set(os.getlogin())

    def suggest_description(self):
        self.description.set(self.name.get() + " - ")


class About:
    def __init__(self, base_dir):
        self.object_label = "About"
        self.show = False
        self.base_dir = base_dir
        # --- built window
        self.win = tk.Toplevel()
        self.win.geometry("+500+100")
        self.win.overrideredirect(1)
        self.win.title(self.object_label)
        self.frame = tk.Frame(self.win)
        self.frame.grid(column=0, row=1, sticky='we')

        self.label_name = tk.Label(self.frame, text=self.object_label, font="Arial 16 bold")
        self.label_name.grid(column=0, row=0, sticky='we')
        try:
            self.image = ImageTk.PhotoImage(Image.open(os.path.join(self.base_dir, "Resources", "logo.png")))
            self.donate_image = tk.Label(self.frame, image=self.image)
            self.donate_image.grid(column=0, row=1)
        except OSError:
            print("About failed")
        self.about_text = tk.Text(self.frame)
        self.about_text.insert(tk.END, "Hello Foundation(r) friend, this is the Unofficial Foundation Map Editor.\n"
                                       "Unofficial is the key word here, since I programed this on my own and I'm not\n"
                                       "associated with Polymorph Studios (r), nor do I own any rights to the game\n"
                                       "'Foundation' (r).\n"
                                       "This software is provided for free and open source, under GNU GPL\n"
                                       "(see http://www.gnu.org/licenses/ )\n"
                                       "This program is distributed in the hope that it will be useful,\n"
                                       "but WITHOUT ANY WARRANTY; without even the implied warranty of \n"
                                       "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. \n\n"
                                       "If you need help, do not hesitate to contact me via the\n"
                                       "Foundation Discord server: @Isajah at https://discordapp.com/\n\n"
                                       "Logo and Icon are modified from:\n"
                                       "'Mountain free icon' by Freepik from www.flaticon.com")
        self.about_text.grid(column=0, row=2, padx=PADX, pady=PADX)
        self.about_text.configure(state=tk.DISABLED)
        self.done_btn = tk.Button(self.frame, text="back", command=self.withdraw)
        self.done_btn.grid(column=0, row=3, sticky='we')

    def toggle_view(self):
        if self.show:
            self.withdraw()
        else:
            self.deiconify()

    def withdraw(self):
        self.win.withdraw()
        self.show = False

    def deiconify(self):
        self.win.deiconify()
        self.show = True


class CookWin:
    def __init__(self, ws_dir, tree_maps, build_heightmap, assets_handle, map_info_handle, globals_handle, river_handle, mountain_handle):
        self.object_label = "Cook Map"
        self.show = False
        self.ws_dir = ws_dir
        self.tree_maps = tree_maps
        self.paths = []
        # internal variables
        self.int_heightmap = tk.IntVar()
        self.int_baseline = tk.IntVar()
        self.int_rivers = tk.IntVar()
        self.int_mountains = tk.IntVar()
        self.int_material_map = tk.IntVar()
        self.int_berries_map = tk.IntVar()
        self.int_rock_map = tk.IntVar()
        self.int_iron_map = tk.IntVar()
        self.int_fish_map = tk.IntVar()
        self.int_paths = tk.IntVar()
        self.int_lua = tk.IntVar()
        self.int_tree_maps = []

        self.to_cook = {'heightmap': 0, 'baseline': 0, 'rivers': 0, 'mountains': 0, 'material': 0, 'berries': 0, 'rock': 0,
                        'iron': 0, 'fish': 0, 'tree': 0, 'copy': 0, 'lua': 0, 'json': 0}

        # build functions
        self.build_heightmap = build_heightmap
        self.assets_handle = assets_handle
        self.map_info = map_info_handle
        self.globals = globals_handle
        self.rivers = river_handle
        self.mountains = mountain_handle

        # --- built window
        self.win = tk.Toplevel()
        self.win.geometry("+500+500")
        self.win.attributes('-topmost', 'true')
        self.win.resizable(False, False)

        # self.win.transient()
        self.win.title(self.object_label)
        self.frame = tk.Frame(self.win)
        self.frame.grid(column=0, row=0, pady=5, sticky='we')
        self.bottom_frame = tk.Frame(self.win)
        self.bottom_frame.grid(column=0, row=1, pady=5, sticky='we')
        self.btn_frame = tk.Frame(self.win)
        self.btn_frame.grid(column=0, row=2, pady=5, sticky='we')

        self.label_name = tk.Label(self.frame, text=self.object_label, font="Arial 12 bold")
        self.label_name.grid(column=0, row=0, sticky='we')

        self.label_description = tk.Label(self.frame, text="select maps, masks that need\nbuild/rebuild:", justify='left')
        self.label_description.grid(column=0, sticky='w', padx=5)

        self.check_heightmap = tk.Checkbutton(self.frame, text="Build Heightmap", variable=self.int_heightmap, onvalue=1, offvalue=0)
        self.check_heightmap.grid(column=0, sticky='w', padx=5)

        self.check_baseline = tk.Checkbutton(self.frame, text="Build Baseline", variable=self.int_baseline, onvalue=1, offvalue=0)
        self.check_baseline.grid(column=0, sticky='w', padx=15)

        self.check_river = tk.Checkbutton(self.frame, text="Build Rivers", variable=self.int_rivers, onvalue=1, offvalue=0)
        self.check_river.grid(column=0, sticky='w', padx=15)

        self.check_mountains = tk.Checkbutton(self.frame, text="Build Mountains", variable=self.int_mountains, onvalue=1, offvalue=0)
        self.check_mountains.grid(column=0, sticky='w', padx=15)

        self.check_material = tk.Checkbutton(self.frame, text="Build Material Map", variable=self.int_material_map, onvalue=1, offvalue=0)
        self.check_material.grid(column=0, sticky='w', padx=5)

        self.check_berries = tk.Checkbutton(self.frame, text="Build Berries Map", variable=self.int_berries_map, onvalue=1, offvalue=0)
        self.check_berries.grid(column=0, sticky='w', padx=5)

        self.check_rock = tk.Checkbutton(self.frame, text="Build Rock Density Map", variable=self.int_rock_map, onvalue=1, offvalue=0)
        self.check_rock.grid(column=0, sticky='w', padx=5)

        self.check_iron = tk.Checkbutton(self.frame, text="Build Iron Density Map", variable=self.int_iron_map, onvalue=1, offvalue=0)
        self.check_iron.grid(column=0, sticky='w', padx=5)

        self.check_fish = tk.Checkbutton(self.frame, text="Build Fish Density Map", variable=self.int_fish_map, onvalue=1, offvalue=0)
        self.check_fish.grid(column=0, sticky='w', padx=5)

        self.check_trees = []
        self.init_tree_map_list()

        self.check_paths = tk.Checkbutton(self.bottom_frame, text="Village paths found:  ", variable=self.int_paths, onvalue=1, offvalue=0,
                                          disabledforeground="red")
        self.check_paths.grid(column=0, row=0, sticky='w', padx=5)
        self.get_village_paths(self.paths)

        self.check_mod = tk.Checkbutton(self.bottom_frame, text=" generate mod files", variable=self.int_lua, onvalue=1, offvalue=0)
        self.check_mod.grid(column=0, row=1, sticky='w', padx=5)
        self.check_mod.select()

        self.progress = ttk.Progressbar(self.btn_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.cook_btn = tk.Button(self.btn_frame, text="Cook Selected", command=self.click_cook)
        self.cook_btn.grid(row=1, column=0, padx=10, pady=10)
        self.close_btn = tk.Button(self.btn_frame, text="Close", command=self.withdraw)
        self.close_btn.grid(row=1, column=1, padx=10, pady=10)

        self.validate_maps()
        self.__refresh()

    def init_tree_map_list(self):
        for check in self.check_trees:
            check.destroy()
        self.check_trees = []

        for tree in self.tree_maps:
            self.int_tree_maps = []
            self.int_tree_maps.append(tk.IntVar())
            self.check_trees.append(tk.Checkbutton(self.frame, text="Build " + tree.object_label,
                                                   variable=self.int_tree_maps[-1],
                                                   onvalue=1, offvalue=0))
            self.check_trees[-1].grid(column=0, sticky='w', padx=5)
            if not os.path.exists(os.path.join(self.ws_dir, map_folder, tree.get_final_file_name())):
                self.check_trees[-1].select()
                self.check_trees[-1].configure(state=tk.DISABLED)
            else:
                self.check_trees[-1].configure(state=tk.NORMAL)

    def validate_maps(self):

        if not os.path.exists(os.path.join(self.ws_dir, map_folder, hmap_name)):
            self.check_heightmap.select()
            self.check_heightmap.configure(state=tk.DISABLED)
        else:
            self.check_heightmap.configure(state=tk.NORMAL)

        if not os.path.exists(os.path.join(self.ws_dir, map_folder, "material_mask.png")):
            self.check_material.select()
            self.check_material.configure(state=tk.DISABLED)
        else:
            self.check_material.configure(state=tk.NORMAL)

        if not os.path.exists(os.path.join(self.ws_dir, map_folder, "berries_density.png")):
            self.check_berries.select()
            self.check_berries.configure(state=tk.DISABLED)
        else:
            self.check_berries.configure(state=tk.NORMAL)

        if not os.path.exists(os.path.join(self.ws_dir, map_folder, "rock_density.png")):
            self.check_rock.select()
            self.check_rock.configure(state=tk.DISABLED)
        else:
            self.check_rock.configure(state=tk.NORMAL)

        if not os.path.exists(os.path.join(self.ws_dir, map_folder, "iron_density.png")):
            self.check_iron.select()
            self.check_iron.configure(state=tk.DISABLED)
        else:
            self.check_iron.configure(state=tk.NORMAL)

        if not os.path.exists(os.path.join(self.ws_dir, map_folder, "fish_density.png")):
            self.check_fish.select()
            self.check_fish.configure(state=tk.DISABLED)
        else:
            self.check_fish.configure(state=tk.NORMAL)
        for i, tree_map in enumerate(self.tree_maps):
            if not os.path.exists(os.path.join(self.ws_dir, map_folder, tree_map.get_final_file_name())):
                self.check_trees[i].configure(state=tk.NORMAL)
                self.check_trees[i].select()
                self.check_trees[i].configure(state=tk.DISABLED)
            else:
                self.check_trees[i].configure(state=tk.NORMAL)

        if os.path.exists(os.path.join(self.ws_dir, "Cooked", "mod.lua")) \
                and os.path.exists(os.path.join(self.ws_dir, "Cooked", "mod.json")):
            self.check_mod.configure(state=tk.NORMAL)
        else:
            self.check_mod.configure(state=tk.DISABLED)

    def get_tree_maps(self, tree_maps):
        self.tree_maps = tree_maps
        self.init_tree_map_list()

    def get_village_paths(self, paths):
        self.paths = paths
        self.check_paths.configure(text="Village paths found:  " + str(len(paths)))
        self.check_paths.configure(state=tk.NORMAL)
        if len(self.paths) > 0:
            self.check_paths.select()
            self.check_paths.configure(disabledforeground="black")
        else:
            self.check_paths.deselect()
            self.check_paths.configure(disabledforeground="red")
        self.check_paths.configure(state=tk.DISABLED)

    def click_cook(self):
        if self.int_baseline.get() == 1:
            self.to_cook['baseline'] = 1
        if self.int_rivers.get() == 1:
            self.to_cook['rivers'] = 1
        if self.int_mountains.get() == 1:
            self.to_cook['mountains'] = 1
        if self.int_heightmap.get() == 1:
            self.to_cook['heightmap'] = 1
        if self.int_material_map.get() == 1:
            self.to_cook['material'] = 1
        if self.int_berries_map.get() == 1:
            self.to_cook['berries'] = 1
        if self.int_rock_map.get() == 1:
            self.to_cook['rock'] = 1
        if self.int_iron_map.get() == 1:
            self.to_cook['iron'] = 1
        if self.int_fish_map.get() == 1:
            self.to_cook['fish'] = 1
        for int_check in self.int_tree_maps:
            if int_check.get() == 1:
                self.to_cook['tree'] = 1
        self.to_cook['copy'] = 1
        self.to_cook['lua'] = 1
        self.to_cook['json'] = 1

    def toggle_view(self):
        if self.show:
            if self.win.winfo_exists():
                self.withdraw()
            else:
                self.deiconify()
        else:
            self.deiconify()

    def withdraw(self):
        self.win.withdraw()
        self.show = False

    def deiconify(self):
        if self.win.winfo_exists():
            self.win.deiconify()
            self.show = True
        else:
            self.__init__(self.ws_dir, self.tree_maps, self.build_heightmap, self.assets_handle, self.map_info,
                          self.globals, self.rivers, self.mountains)
            self.show = True
            self.win.deiconify()
        self.validate_maps()
        self.get_village_paths(self.paths)

    def __cook(self):
        if self.to_cook['baseline'] == 1:
            self.globals.generate()
            print("cooked baseline map")
            self.to_cook['baseline'] = 0
            return 2
        elif self.to_cook['rivers'] == 1:
            for river in self.rivers:
                river.generate()
            print("cooked rivers")
            self.to_cook['rivers'] = 0
            return 5
        elif self.to_cook['mountains'] == 1:
            for mountain in self.mountains:
                mountain.generate()
            print("cooked mountains")
            self.to_cook['mountains'] = 0
            return 8
        elif self.to_cook['heightmap'] == 1:
            self.build_heightmap()
            print("cooked heightmap")
            self.to_cook['heightmap'] = 0
            return 10
        elif self.to_cook['material'] == 1:
            self.assets_handle.build_material_map()
            print("cooked material")
            self.to_cook['material'] = 0
            return 20
        elif self.to_cook['berries'] == 1:
            self.assets_handle.build_berries_map()
            print("cooked berries")
            self.to_cook['berries'] = 0
            return 30
        elif self.to_cook['rock'] == 1:
            self.assets_handle.build_stone_map()
            print("cooked rocks")
            self.to_cook['rock'] = 0
            return 40
        elif self.to_cook['iron'] == 1:
            self.assets_handle.build_ore_map()
            print("cooked iron")
            self.to_cook['iron'] = 0
            return 50
        elif self.to_cook['fish'] == 1:
            self.assets_handle.build_fish_map()
            print("cooked fish")
            self.to_cook['fish'] = 0
            return 60
        elif self.to_cook['tree'] == 1:
            for tree_map in self.tree_maps:
                tree_map.build_map()
            print("cooked trees")
            self.to_cook['tree'] = 0
            return 70
        elif self.to_cook['copy'] == 1:
            from shutil import copyfile
            if not os.path.exists(os.path.join(self.ws_dir, "Cooked", "maps")):
                os.makedirs(os.path.join(self.ws_dir, "Cooked", "maps"))
            copyfile(os.path.join(self.ws_dir, "Maps", hmap_name), os.path.join(self.ws_dir, "Cooked", "maps", hmap_name))
            copyfile(os.path.join(self.ws_dir, "Maps", mmap_name), os.path.join(self.ws_dir, "Cooked", "maps", mmap_name))
            copyfile(os.path.join(self.ws_dir, "Maps", hmap_name), os.path.join(self.ws_dir, "Cooked", "maps", hmap_name))
            copyfile(os.path.join(self.ws_dir, "Maps", bmap_name), os.path.join(self.ws_dir, "Cooked", "maps", bmap_name))
            copyfile(os.path.join(self.ws_dir, "Maps", rmap_name), os.path.join(self.ws_dir, "Cooked", "maps", rmap_name))
            copyfile(os.path.join(self.ws_dir, "Maps", imap_name), os.path.join(self.ws_dir, "Cooked", "maps", imap_name))
            copyfile(os.path.join(self.ws_dir, "Maps", fmap_name), os.path.join(self.ws_dir, "Cooked", "maps", fmap_name))
            for tree_map in self.tree_maps:
                tmap_name = os.path.join(tree_map.get_final_file_name())
                copyfile(os.path.join(self.ws_dir, "Maps", tmap_name), os.path.join(self.ws_dir, "Cooked", "maps", tmap_name))
            print("copied maps")
            self.to_cook['copy'] = 0
            return 80
        elif self.to_cook['lua'] == 1:
            lua_file_name = os.path.join(self.ws_dir, "Cooked", "mod.lua")
            if os.path.exists(lua_file_name):
                os.remove(lua_file_name)
            with open(lua_file_name, 'w') as lua_file:
                lua_file.writelines(self.build_lua())
            print("build mod.lua")

            self.to_cook['lua'] = 0
            return 90
        elif self.to_cook['json'] == 1:
            json_name = os.path.join(self.ws_dir, "Cooked", "mod.json")
            data = {'Name': self.map_info.name.get(),
                    'Author': self.map_info.author.get(),
                    'Description': self.map_info.description.get(),
                    'Version': self.map_info.version.get(),
                    'MapList': [{
                        'Name': "Custom map - " + self.map_info.name.get(),
                        'Id': self.map_info.id.get()
                    }]
                    }

            with open(json_name, 'w') as outfile:
                json.dump(data, outfile, indent=4)
            print("build mod.json")
            self.to_cook['json'] = 0
            print('explorer "' + os.path.realpath(os.path.join(self.ws_dir, "Cooked")) + '"')
            subprocess.Popen('explorer "' + os.path.realpath(os.path.join(self.ws_dir, "Cooked")) + '"')
            self.withdraw()
            return 100
        else:
            return 0

    def __refresh(self):
        self.progress['value'] = self.__cook()
        if self.int_paths.get() == 0:
            self.cook_btn.configure(state=tk.DISABLED)
        else:
            self.cook_btn.configure(state=tk.NORMAL)
        self.hmap_sub = self.int_baseline.get() + self.int_mountains.get() + self.int_rivers.get()
        if self.hmap_sub > 0 and self.hmap_sub != self.hmap_sub_old:
            self.check_heightmap.select()
        if self.int_heightmap.get() == 0:
            self.check_baseline.deselect()
            self.check_river.deselect()
            self.check_mountains.deselect()
        self.hmap_sub_old = self.hmap_sub
        self.win.after(200, lambda: self.__refresh())

    def build_lua(self):
        lua_string = []
        wlevel = int(self.map_info.str_water_level.get())
        height = int(self.map_info.str_height.get())

        min_height = -wlevel
        max_height = height - wlevel
        lua_string.append('local mapMod = foundation.createMod();')
        lua_string.append('')
        lua_string.append('mapMod:registerAssetId("maps/heightmap.png", "HEIGHT_MAP")')
        lua_string.append('mapMod:registerAssetId("maps/material_mask.png", "MATERIAL_MASK")')
        lua_string.append('mapMod:registerAssetId("maps/berries_density.png", "BERRIES_DENSITY_MAP")')
        lua_string.append('mapMod:registerAssetId("maps/rock_density.png", "ROCK_DENSITY_MAP")')
        lua_string.append('mapMod:registerAssetId("maps/iron_density.png", "IRON_DENSITY_MAP")')
        lua_string.append('mapMod:registerAssetId("maps/fish_density.png", "FISH_DENSITY_MAP")')
        for tree_map in self.tree_maps:
            tree_file_name = tree_map.get_final_file_name()
            tree_lua_name = tree_map.object_label.replace(" ", "_").upper()
            lua_string.append(
                'mapMod:registerAssetId("maps/' + tree_file_name + '", "' + tree_lua_name + '")')
        lua_string.append('')
        lua_string.append('-- Register Custom Map')
        lua_string.append('mapMod:register({')
        lua_string.append('\tDataType = "CUSTOM_MAP",')
        lua_string.append('\tId = "' + self.map_info.id.get() + '",')
        lua_string.append('\tHeightMap = "HEIGHT_MAP",')
        lua_string.append('\tMaterialMask = "MATERIAL_MASK",')
        lua_string.append('\tMinHeight = ' + str(min_height) + ',')
        lua_string.append('\tMaxHeight = ' + str(max_height) + ',')
        lua_string.append('\tVillagePathList = {')
        for path in self.paths:
            for line in path.to_lua_str():
                lua_string.append(line)
        lua_string[-1] = lua_string[-1][:-1]
        lua_string.append('\t},')
        lua_string.append('\tSpawnList = {')
        lua_string.append('\t\t},')
        lua_string.append('\tDensitySpawnList = {')
        # getting all tree_maps and types
        for tree_map in self.tree_maps:
            for line in tree_map.to_lua_str():
                lua_string.append(line)
        # removed(1) lua_string.append('\t\t\t\t},')
        # getting resources
        for line in lua_prefab_to_str("berries", comment="Create forest of berry bushes"):
            lua_string.append(line)
        for line in lua_prefab_to_str("rock", comment="Create rock outcrops - stone resource"):
            lua_string.append(line)
        for line in lua_prefab_to_str("iron", comment="Create iron deposits"):
            lua_string.append(line)
        for line in lua_prefab_to_str("fish", comment="Create fish shoals"):
            lua_string.append(line)
        lua_string[-1] = lua_string[-1][:-1]
        lua_string.append('\t}')
        lua_string.append('})')
        for i, line in enumerate(lua_string):
            lua_string[i] = line + '\n'

        return lua_string


def write_log(log_text, log_name="ufme_log.txt"):

    timestamp = time.localtime()
    time_string = str(timestamp.tm_hour) + ":" + str(timestamp.tm_min) + ":" + str(timestamp.tm_sec) + " -- "

    if os.path.exists(log_name):
        log_file = open(log_name, "a")
    else:
        log_file = open(log_name, "w")

    log_file.write(time_string + log_text + "\n")
    log_file.close()
