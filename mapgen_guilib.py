# Head



# Imports
import tkinter as tk
from tkinter import filedialog

import numpy    
from scipy.ndimage.filters import gaussian_filter
import matplotlib.pyplot as pp
import matplotlib as mpl

from PIL import ImageTk, Image

import os
import time
import terrain
import assets
import json

# directories and file names 
gen_json_name = "TerrainObjectList.jsonc"
asset_json_name = "AssetsParamList.jsonc"
hmap_name = "heightmap.png"
map_folder = "Maps"
partials_folder = "PartialMaps"
jsons_folder = "Jsons"
default_file = "default.png"

PREV_SIZE = 256
ENTRY_WIDTH = 4
PADX = 4
MAX_16BIT = 65535
NORM = 66


class BaseWindow():
    def __init__(self, master, prev_canvas):
        
        # internal variables

        self.wp_index = 0
        self.wp_list = []
        self.deleted = False
        self.index = 0

        self.object_label = "Base Window"

        self.prev_canvas = prev_canvas
        self.master = master

        # initializing basic structure of the window
        self.master = master
        self.frame = tk.Frame(self.master, relief=tk.GROOVE, borderwidth = 1)
        self.frame.pack(side='top', expand=True, fill='both')
        self.top_frame = tk.Frame(self.frame)
        self.top_frame.grid(column=0, row=0, sticky='we')
        self.top_frame.columnconfigure(0, minsize=140)
        self.main_frame = tk.Frame(self.frame)
        self.main_frame.grid(column=0, row=1, sticky='we')
        self.wp_frame = tk.Frame(self.frame)
        self.wp_frame.grid(column=0, row=2, sticky='we')

    def build_preview(self, handle, label, filename, index, init=False):
        # build preview
        retval = 0
        image = Image.open(filename)
        image.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        if init:
            handle.append(ImageTk.PhotoImage(image))
            self.preview = tk.Label(self.prev_canvas, image=handle[-1])

            self.preview.pack()
            self.preview_label = tk.Label(self.prev_canvas, text = label)
            self.preview_label.pack()
            retval = len(handle)
        else:
            handle[index-1] = ImageTk.PhotoImage(image)
            self.preview.configure(image=handle[index-1])
            retval = index
        self.prev_canvas.master.update()
        return retval

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
        self.terrain_map = numpy.full((1024,1024),0)
        self.index = index
        self.object_label = "Terrain Object"

    def add_wp(self):
        # adding waypoints
        self.wp_index += 1
        self.wp_list.append(Waypoint(self.wp_frame,self.wp_index, self.container))

    def get_waypoints(self):
        retlist = []
        for wp in self.wp_list:
            if not wp.deleted:
                retlist.append(0)
                retlist.append(0)
                retlist[-2], retlist[-1] = wp.getval()
        return retlist


class GlobalParams(BaseWindow):
    def __init__(self, master, prev_canvas, min_height, max_height, river_level, presigma, postsigma):
        super().__init__(master, prev_canvas) 

        # --- initialize all internal variables
        self.min_height = min_height
        self.max_height = max_height
        self.river_level = river_level
        self.pre_sigma = presigma
        self.post_sigma = postsigma

        self.baseline_map = numpy.full((1024, 1024), 0)
        self.object_label = "Global Parameters"

        # --- initialize all internal text representations

        self.str_min_height = tk.StringVar()
        self.str_min_height.set(str(min_height))

        self.str_max_height = tk.StringVar()
        self.str_max_height.set(str(max_height))

        self.str_riverlevel = tk.StringVar()
        self.str_riverlevel.set(str(river_level))

        self.str_pre_sigma = tk.StringVar()
        self.str_pre_sigma.set(str(presigma))

        self.str_postsigma = tk.StringVar()
        self.str_postsigma.set(str(postsigma))

        # --- built head
        self.label_name = tk.Label(self.top_frame, text = self.object_label)
        self.label_name.grid(column = 0, row = 0, sticky = 'w')
        self.gen_btn = tk.Button(self.top_frame, text = "build baseline map", command= self.generate)
        self.gen_btn.grid(column = 1, row = 0, sticky='we')
        self.hmap_btn = tk.Button(self.top_frame, text = "get heightmap", command= self.get_heightmap)
        self.hmap_btn.grid(column = 2, row = 0, sticky='we')

        # --- built input matrix

        # max height 
        self.label_maxheight = tk.Label(self.main_frame, text = "max height:")
        self.label_maxheight.grid(column = 0, row = 1, sticky= 'w', padx=PADX) 
        self.box_maxheight = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_max_height)
        self.box_maxheight.grid(column = 1, row = 1, sticky= 'w', padx=PADX)
        # min height
        self.label_minheight = tk.Label(self.main_frame, text = "min height:")
        self.label_minheight.grid(column = 2, row = 1, sticky= 'w', padx=PADX)
        self.box_minheight = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_min_height)
        self.box_minheight.grid(column = 3, row = 1, sticky= 'w', padx=PADX)
        # river level
        self.label_river = tk.Label(self.main_frame, text = "river level:")
        self.label_river.grid(column = 4, row = 1, sticky= 'w', padx=PADX)
        self.box_river = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_riverlevel)
        self.box_river.grid(column = 5, row = 1 , sticky= 'w', padx=PADX)
        # presigma
        self.label_presigma = tk.Label(self.main_frame, text = "pre sigma:")
        self.label_presigma.grid(column = 0, row = 2, sticky= 'w', padx=PADX)
        self.box_presigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_pre_sigma)
        self.box_presigma.grid(column = 1, row = 2, sticky= 'w', padx=PADX)
        #post sigma
        self.label_postsigma = tk.Label(self.main_frame, text = "post sigma:")
        self.label_postsigma.grid(column = 2, row = 2, sticky= 'w', padx=PADX)
        self.box_postsigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right',textvariable = self.str_postsigma)
        self.box_postsigma.grid(column = 3, row = 2, sticky= 'w', padx=PADX)

        # build preview

        self.baseline_im = Image.open(os.path.join(partials_folder,"default.png"))
        self.baseline_im.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        self.prev_canvas.baseline_im = ImageTk.PhotoImage(self.baseline_im)
        
        self.preview = tk.Label(self.prev_canvas, image=self.prev_canvas.baseline_im)
        self.preview.pack()
        self.preview_label = tk.Label(self.prev_canvas, text = "baseline map")
        self.preview_label.pack()
    
    def get_minheight(self, norm=1):
        self.min_height = int(self.str_min_height.get()) * norm
        return self.min_height 

    def get_maxheight(self, norm=1):
        self.max_height = int(self.str_max_height.get()) * norm
        return self.max_height 

    def get_riverlevel(self, norm=1):
        self.river_level = int(self.str_riverlevel.get()) * norm
        return self.river_level 

    def get_presigma(self, norm=1):
        self.pre_sigma = int(self.str_pre_sigma.get()) * norm
        return self.pre_sigma 

    def get_postsigma(self, norm=1):
        self.post_sigma = int(self.str_postsigma.get()) * norm
        return self.post_sigma 


    def generate(self):
        #get all variables from form
        self.get_minheight(norm=NORM)
        self.get_maxheight(norm=NORM)
        self.get_riverlevel(norm=NORM)
        self.get_presigma()
        self.get_postsigma()

        # Generate a base_line map, all objects will be added
        self.baseline_map = numpy.random.randint(self.min_height, high = self.max_height, size=(1024,1024))
        self.baseline_map = gaussian_filter(self.baseline_map, sigma=self.pre_sigma)
        pp.imsave(os.path.join(partials_folder,"baseline.png"), self.baseline_map, vmin = 0, vmax = MAX_16BIT )
        time.sleep(1)
        self.baseline_im = Image.open(os.path.join(partials_folder,"baseline.png"))
        #self.baseline_im.load()
        self.baseline_im.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)
        self.prev_canvas.baseline_im = ImageTk.PhotoImage(self.baseline_im)
        self.preview.configure(image = self.prev_canvas.baseline_im)

    def get_heightmap(self):
        hmap_name = filedialog.askopenfilename(
                                                initialdir=os.path.join(map_folder),
                                                title="Select file",
                                                filetypes=(("png file", "*.png"), ("all files", "*.*"))
                                            )
        heightmap_path = os.path.join(hmap_name)
        self.baseline_map = numpy.array(Image.open(heightmap_path).convert('I'))
        self.baseline_map = numpy.interp(self.baseline_map, (self.baseline_map.min(), self.baseline_map.max()), (0, MAX_16BIT)) # normalizing heightmap to 0...255
        pp.imsave(os.path.join(partials_folder,"baseline.png"), self.baseline_map, vmin = 0, vmax = MAX_16BIT )
        time.sleep(1)
        self.baseline_im = Image.open(os.path.join(partials_folder,"baseline.png"))
        #self.baseline_im.load()
        self.baseline_im.thumbnail((PREV_SIZE, PREV_SIZE), Image.ANTIALIAS)
        self.prev_canvas.baseline_im = ImageTk.PhotoImage(self.baseline_im)
        self.preview.configure(image = self.prev_canvas.baseline_im)


class AssetParams(BaseWindow):
    def __init__(self, master, prev_canvas,json):
        super().__init__(master, prev_canvas) 
        self.json_name = json
        # --- initialize all internal text representations
        self.str_grass_level = tk.StringVar()
        self.str_grass_level.set(500)
        self.str_grass_sigma = tk.StringVar()
        self.str_grass_sigma.set(5)

        self.str_decid_steep = tk.StringVar()
        self.str_decid_steep.set(10)
        self.str_decid_max = tk.StringVar()
        self.str_decid_max.set(1000)
        self.str_decid_min = tk.StringVar()
        self.str_decid_min.set(600)
        self.str_decid_sigma = tk.StringVar()
        self.str_decid_sigma.set(5)
        
        self.str_conif_steep = tk.StringVar()
        self.str_conif_steep.set(10)
        self.str_conif_max = tk.StringVar()
        self.str_conif_max.set(1000)
        self.str_conif_min = tk.StringVar()
        self.str_conif_min.set(600)
        self.str_conif_sigma = tk.StringVar()
        self.str_conif_sigma.set(5)

        self.str_berries_dense = tk.StringVar()
        self.str_berries_dense.set(10)
        self.str_berries_group = tk.StringVar()
        self.str_berries_group.set(5)
        self.str_berries_steep = tk.StringVar()
        self.str_berries_steep.set(10)
        self.str_berries_min = tk.StringVar()
        self.str_berries_min.set(600)
        self.str_berries_max = tk.StringVar()
        self.str_berries_max.set(1000)
        self.str_berries_sigma = tk.StringVar()
        self.str_berries_sigma.set(5)

        self.str_stone_dense = tk.StringVar()
        self.str_stone_dense.set(10)
        self.str_stone_group = tk.StringVar()
        self.str_stone_group.set(5)
        self.str_stone_steep = tk.StringVar()
        self.str_stone_steep.set(10)
        self.str_stone_min = tk.StringVar()
        self.str_stone_min.set(600)
        self.str_stone_max = tk.StringVar()
        self.str_stone_max.set(1000)
        self.str_stone_sigma = tk.StringVar()
        self.str_stone_sigma.set(5)

        self.str_ore_dense = tk.StringVar()
        self.str_ore_dense.set(5)
        self.str_ore_group = tk.StringVar()
        self.str_ore_group.set(0)
        self.str_ore_steep = tk.StringVar()
        self.str_ore_steep.set(10)
        self.str_ore_min = tk.StringVar()
        self.str_ore_min.set(600)
        self.str_ore_max = tk.StringVar()
        self.str_ore_max.set(1000)
        self.str_ore_sigma = tk.StringVar()
        self.str_ore_sigma.set(5)

        self.str_fish_dense = tk.StringVar()
        self.str_fish_dense.set(50)
        self.str_fish_group = tk.StringVar()
        self.str_fish_group.set(5)
        self.str_fish_max = tk.StringVar()
        self.str_fish_max.set(400)

        # initially read in all values
        # self.parse_json(self.json_name)
        
        self.heightmap = self.load_heightmap()
        self.cutout_mask = numpy.full((1024, 1024), 255)
        self.prev_canvas.mmap_handle = []
        self.prev_index_list = {'material':0, 'berries':0, 'stone':0, 'ore':0, 'fish':0, 'decid':0, 'conif':0}

        # --- built head
        self.object_label = "Asset Parameters"
        self.label_name = tk.Label(self.top_frame, text = self.object_label)
        self.label_name.grid(column = 0, row = 0, sticky = 'w')
        self.gen_btn = tk.Button(self.top_frame, text = "build asset maps", command= self.build_asset_maps)
        self.gen_btn.grid(column = 1, row = 0, sticky='e')
        
        # --- built input matrix

        self.label_grassheadline = tk.Label(self.main_frame, text = "grass parameter:")
        self.label_grassheadline.grid(column = 0, row = 0, columnspan = 4, sticky= 'w', padx=PADX)
        self.grass_btn = tk.Button(self.main_frame, text = "build material map", command= self.build_material_map)
        self.grass_btn.grid(column = 5, columnspan = 3,row = 0, sticky='e')
        # Grass Level
        self.label_grasslevel = tk.Label(self.main_frame, text = "level:")
        self.label_grasslevel.grid(column = 0, row = 1, sticky= 'w', padx=PADX) 
        self.box_grasslevel = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_grass_level)
        self.box_grasslevel.grid(column = 1, row = 1, sticky= 'w', padx=PADX)

    
        # Grass Sigma
        self.label_grasssigma = tk.Label(self.main_frame, text = "sigma:")
        self.label_grasssigma.grid(column = 2, row = 1, sticky= 'w', padx=PADX)
        self.box_grasssigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_grass_sigma)
        self.box_grasssigma.grid(column = 3, row = 1, sticky= 'w', padx=PADX)
        
        # --- Deciduous ---
        self.label_decidheadline = tk.Label(self.main_frame, text = "deciduous parameters:")
        self.label_decidheadline.grid(column = 0, row = 2, sticky= 'w', padx=PADX, columnspan = 4)
        self.decid_btn = tk.Button(self.main_frame, text = "build decid map", command= self.build_decid_map)
        self.decid_btn.grid(column = 5, columnspan = 3,row = 2, sticky='e')
        
        # decid steep
        self.label_decidsteep = tk.Label(self.main_frame, text = "steep:")
        self.label_decidsteep.grid(column = 0, row = 3, sticky= 'w', padx=PADX)
        self.box_decidsteep = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_decid_steep)
        self.box_decidsteep.grid(column = 1, row = 3, sticky= 'w', padx=PADX)
        # decid min
        self.label_decidmin = tk.Label(self.main_frame, text = "min:")
        self.label_decidmin.grid(column = 2, row = 3, sticky= 'w', padx=PADX)
        self.box_decidmin = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_decid_min)
        self.box_decidmin.grid(column = 3, row = 3, sticky= 'w', padx=PADX)
        # decid max
        self.label_decidmax = tk.Label(self.main_frame, text = "max:")
        self.label_decidmax.grid(column = 4, row = 3, sticky= 'w', padx=PADX)
        self.box_decidmax = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_decid_max)
        self.box_decidmax.grid(column = 5, row = 3, sticky= 'w', padx=PADX)
        # decid sigma
        self.label_decidsigma = tk.Label(self.main_frame, text = "sigma:")
        self.label_decidsigma.grid(column = 6, row = 3, sticky= 'w', padx=PADX)
        self.box_decidsigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right',textvariable = self.str_decid_sigma)
        self.box_decidsigma.grid(column = 7, row = 3, sticky= 'w', padx=PADX)
        
        # --- Coniferous ---
        self.label_conifheadline = tk.Label(self.main_frame, text = "coniferous parameters:")
        self.label_conifheadline.grid(column = 0, row = 4, sticky= 'w', padx=PADX, columnspan = 4)
        self.conif_btn = tk.Button(self.main_frame, text = "build conif map", command= self.build_conif_map)
        self.conif_btn.grid(column = 5, columnspan = 3,row = 4, sticky='e')
        # conif steep
        self.label_conifsteep = tk.Label(self.main_frame, text = "steep:")
        self.label_conifsteep.grid(column = 0, row = 5, sticky= 'w', padx=PADX)
        self.box_conifsteep = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_conif_steep)
        self.box_conifsteep.grid(column = 1, row = 5, sticky= 'w', padx=PADX)
        # conif min
        self.label_conifmin = tk.Label(self.main_frame, text = "min:")
        self.label_conifmin.grid(column = 2, row = 5, sticky= 'w', padx=PADX)
        self.box_conifmin = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_conif_min)
        self.box_conifmin.grid(column = 3, row = 5, sticky= 'w', padx=PADX)
        # conif max
        self.label_conifmax = tk.Label(self.main_frame, text = "max:")
        self.label_conifmax.grid(column = 4, row = 5, sticky= 'w', padx=PADX)
        self.box_conifmax = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_conif_max)
        self.box_conifmax.grid(column = 5, row = 5, sticky= 'w', padx=PADX)
        # conif sigma
        self.label_conifsigma = tk.Label(self.main_frame, text = "sigma:")
        self.label_conifsigma.grid(column=6, row=5, sticky= 'w', padx=PADX)
        self.box_conifsigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right',textvariable = self.str_conif_sigma)
        self.box_conifsigma.grid(column=7, row=5, sticky='w', padx=PADX)
        
        # --- Berries ----
        self.label_berriesheadline = tk.Label(self.main_frame, text = "berries parameters:")
        self.label_berriesheadline.grid(column=0, row=6, sticky='w', padx=PADX, columnspan=4)
        self.berries_btn = tk.Button(self.main_frame, text="build berries map", command=self.build_berries_map)
        self.berries_btn.grid(column=5, columnspan=3, row=6, sticky='e')
        # berries steep
        self.label_berriessteep = tk.Label(self.main_frame, text = "steep:")
        self.label_berriessteep.grid(column = 0, row = 7, sticky= 'w', padx=PADX)
        self.box_berriessteep = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_berries_steep)
        self.box_berriessteep.grid(column = 1, row = 7, sticky= 'w', padx=PADX)    
        # berries dense
        self.label_berriesdense = tk.Label(self.main_frame, text = "dense:")
        self.label_berriesdense.grid(column = 2, row = 7, sticky= 'w', padx=PADX)
        self.box_berriesdense = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_berries_dense)
        self.box_berriesdense.grid(column = 3, row = 7, sticky= 'w', padx=PADX)
        # berries group
        self.label_berriesgroup = tk.Label(self.main_frame, text = "group:")
        self.label_berriesgroup.grid(column = 4, row = 7, sticky= 'w', padx=PADX)
        self.box_berriesgroup = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_berries_group)
        self.box_berriesgroup.grid(column = 5, row = 7, sticky= 'w', padx=PADX)
        # berries min
        self.label_berriesmin = tk.Label(self.main_frame, text = "min:")
        self.label_berriesmin.grid(column = 6, row = 7, sticky= 'w', padx=PADX)
        self.box_berriesmin = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_berries_min)
        self.box_berriesmin.grid(column = 7, row = 7, sticky= 'w', padx=PADX)
        # berries max
        self.label_berriesmax = tk.Label(self.main_frame, text = "max:")
        self.label_berriesmax.grid(column = 0, row = 8, sticky= 'w', padx=PADX)
        self.box_berriesmax = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_berries_max)
        self.box_berriesmax.grid(column = 1, row = 8, sticky= 'w', padx=PADX)
        # berries sigma
        self.label_berriessigma = tk.Label(self.main_frame, text = "sigma:")
        self.label_berriessigma.grid(column = 2, row = 8, sticky= 'w', padx=PADX)
        self.box_berriessigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right',textvariable = self.str_berries_sigma)
        self.box_berriessigma.grid(column = 3, row = 8, sticky= 'w', padx=PADX)

        # --- stone ----
        self.label_stoneheadline = tk.Label(self.main_frame, text = "stone parameters:")
        self.label_stoneheadline.grid(column = 0, row = 9, sticky= 'w', padx=PADX, columnspan = 4)
        self.stone_btn = tk.Button(self.main_frame, text = "build stone map", command= self.build_stone_map)
        self.stone_btn.grid(column = 5, columnspan = 3,row = 9, sticky='e')
        # stone steep
        self.label_stonesteep = tk.Label(self.main_frame, text = "steep:")
        self.label_stonesteep.grid(column = 0, row = 10, sticky= 'w', padx=PADX)
        self.box_stonesteep = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_stone_steep)
        self.box_stonesteep.grid(column = 1, row = 10, sticky= 'w', padx=PADX)    
        # stone dense
        self.label_stonedense = tk.Label(self.main_frame, text = "dense:")
        self.label_stonedense.grid(column = 2, row = 10, sticky= 'w', padx=PADX)
        self.box_stonedense = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_stone_dense)
        self.box_stonedense.grid(column = 3, row = 10, sticky= 'w', padx=PADX)
        # stone group
        self.label_stonegroup = tk.Label(self.main_frame, text = "group:")
        self.label_stonegroup.grid(column = 4, row = 10, sticky= 'w', padx=PADX)
        self.box_stonegroup = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_stone_group)
        self.box_stonegroup.grid(column = 5, row = 10, sticky= 'w', padx=PADX)
        # stone min
        self.label_stonemin = tk.Label(self.main_frame, text = "min:")
        self.label_stonemin.grid(column = 6, row = 10, sticky= 'w', padx=PADX)
        self.box_stonemin = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_stone_min)
        self.box_stonemin.grid(column = 7, row = 10, sticky= 'w', padx=PADX)
        # stone max
        self.label_stonemax = tk.Label(self.main_frame, text = "max:")
        self.label_stonemax.grid(column = 0, row = 11, sticky= 'w', padx=PADX)
        self.box_stonemax = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_stone_max)
        self.box_stonemax.grid(column = 1, row = 11, sticky= 'w', padx=PADX)
        # stone sigma
        self.label_stonesigma = tk.Label(self.main_frame, text = "sigma:")
        self.label_stonesigma.grid(column = 2, row = 11, sticky= 'w', padx=PADX)
        self.box_stonesigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right',textvariable = self.str_stone_sigma)
        self.box_stonesigma.grid(column = 3, row = 11, sticky= 'w', padx=PADX)
# --- ore ----
        self.label_oreheadline = tk.Label(self.main_frame, text = "ore parameters:")
        self.label_oreheadline.grid(column = 0, row = 12, sticky= 'w', padx=PADX, columnspan = 4)
        self.ore_btn = tk.Button(self.main_frame, text = "build iron ore map", command= self.build_ore_map)
        self.ore_btn.grid(column = 5, columnspan = 3,row = 12, sticky='e')
        # ore steep
        self.label_oresteep = tk.Label(self.main_frame, text = "steep:")
        self.label_oresteep.grid(column = 0, row = 13, sticky= 'w', padx=PADX)
        self.box_oresteep = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_ore_steep)
        self.box_oresteep.grid(column = 1, row = 13, sticky= 'w', padx=PADX)    
        # ore dense
        self.label_oredense = tk.Label(self.main_frame, text = "dense:")
        self.label_oredense.grid(column = 2, row = 13, sticky= 'w', padx=PADX)
        self.box_oredense = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_ore_dense)
        self.box_oredense.grid(column = 3, row = 13, sticky= 'w', padx=PADX)
        # ore group
        self.label_oregroup = tk.Label(self.main_frame, text = "group:")
        self.label_oregroup.grid(column = 4, row = 13, sticky= 'w', padx=PADX)
        self.box_oregroup = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_ore_group)
        self.box_oregroup.grid(column = 5, row = 13, sticky= 'w', padx=PADX)
        # ore min
        self.label_oremin = tk.Label(self.main_frame, text = "min:")
        self.label_oremin.grid(column = 6, row = 13, sticky= 'w', padx=PADX)
        self.box_oremin = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_ore_min)
        self.box_oremin.grid(column = 7, row = 13, sticky= 'w', padx=PADX)
        # ore max
        self.label_oremax = tk.Label(self.main_frame, text = "max:")
        self.label_oremax.grid(column = 0, row = 14, sticky= 'w', padx=PADX)
        self.box_oremax = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_ore_max)
        self.box_oremax.grid(column = 1, row = 14, sticky= 'w', padx=PADX)
        # ore sigma
        self.label_oresigma = tk.Label(self.main_frame, text = "sigma:")
        self.label_oresigma.grid(column = 2, row = 14, sticky= 'w', padx=PADX)
        self.box_oresigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right',textvariable = self.str_ore_sigma)
        self.box_oresigma.grid(column = 3, row = 14, sticky= 'w', padx=PADX)
        # --- fish ----
        self.label_fishheadline = tk.Label(self.main_frame, text = "fish parameters:")
        self.label_fishheadline.grid(column = 0, row = 15, sticky= 'w', padx=PADX, columnspan = 4)
        self.fish_btn = tk.Button(self.main_frame, text = "build fish map", command= self.build_fish_map)
        self.fish_btn.grid(column = 5, columnspan = 3,row = 15, sticky='e')
        # fish dense
        self.label_fishdense = tk.Label(self.main_frame, text = "dense:")
        self.label_fishdense.grid(column = 0, row = 16, sticky= 'w', padx=PADX)
        self.box_fishdense = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_fish_dense)
        self.box_fishdense.grid(column = 1, row = 16, sticky= 'w', padx=PADX)
        # fish group
        self.label_fishgroup = tk.Label(self.main_frame, text = "group:")
        self.label_fishgroup.grid(column = 2, row = 16, sticky= 'w', padx=PADX)
        self.box_fishgroup = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_fish_group)
        self.box_fishgroup.grid(column = 3, row = 16, sticky= 'w', padx=PADX)
        # fish max
        self.label_fishmax = tk.Label(self.main_frame, text = "max:")
        self.label_fishmax.grid(column = 4, row = 16, sticky= 'w', padx=PADX)
        self.box_fishmax = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_fish_max)
        self.box_fishmax.grid(column = 5, row = 16, sticky= 'w', padx=PADX)


    def parse_json(self,json_name):
        with open(json_name) as json_file:
            data = json.load(json_file)
            self.param_from_data(data)

    def param_from_data(self,data):

            self.str_grass_level.set(data['grass']['level'])
            self.str_grass_sigma.set(data['grass']['sigma'])

            self.str_decid_steep.set(data['deciduous_density_map']['steepness'])
            self.str_decid_max.set(data['deciduous_density_map']['max_height'])
            self.str_decid_min.set(data['deciduous_density_map']['min_height'])
            self.str_decid_sigma.set(data['deciduous_density_map']['sigma'])
            
            self.str_conif_steep.set(data['coniferous_density_map']['steepness']) 
            self.str_conif_max.set(data['coniferous_density_map']['max_height'])
            self.str_conif_min.set(data['coniferous_density_map']['min_height'])
            self.str_conif_sigma.set(data['coniferous_density_map']['sigma'])

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
        try:
            heightmap_path = os.path.join(map_folder,hmap_name)
            heightmap = numpy.full((1024,1024),0,dtype = numpy.uint16)
            heightmap = numpy.array(Image.open(heightmap_path).convert('I'),dtype = numpy.uint16)
        except:
            print("WARNING:heightmap.png not found or could not be opened!")
        return heightmap

    def build_preview(self, canvas, handle, label, filename, index):
        # build preview
        retval = 0
        image = Image.open(filename)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if index == 0:
            handle.append(ImageTk.PhotoImage(image))
            self.preview = tk.Label(canvas, image=handle[-1])

            self.preview.pack()
            self.preview_label = tk.Label(canvas, text = label)
            self.preview_label.pack()
            retval = len(handle)
        else:
            handle[index-1] = ImageTk.PhotoImage(image)
            self.preview.configure(image = handle[index-1])
            retval = index

        return retval

    def build_material_map(self):
        self.heightmap = self.load_heightmap()
        grass_level = int(self.str_grass_level.get()) * NORM
        grass_sigma = int(self.str_grass_sigma.get())
        file_name = os.path.join(map_folder,"material_mask.png")

        self.material_map = assets.material_map(self.heightmap, grass_level, grass_sigma)
        clist = [(0,"red"), (1, "lime")]
        green_red = mpl.colors.LinearSegmentedColormap.from_list("name", clist)
        pp.imsave(file_name, self.material_map, vmin = 0, vmax = 255, cmap = green_red)

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['material']  == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_material = tk.Label(self.prev_canvas, image=self.prev_canvas.mmap_handle[-1])
            self.prev_material.pack()
            self.prev_material_label = tk.Label(self.prev_canvas, text = "material map")
            self.prev_material_label.pack()
            self.prev_index_list['material'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['material']-1] = ImageTk.PhotoImage(image)
            self.prev_material.configure(image = self.prev_canvas.mmap_handle[self.prev_index_list['material']-1])
        self.prev_canvas.master.update()

    def build_decid_map(self):
        self.heightmap = self.load_heightmap()
        file_name = os.path.join(map_folder,"deciduous_density.png")

        sigma = int(self.str_decid_sigma.get())
        steep = int(self.str_decid_steep.get()) * NORM
        minval = int(self.str_decid_min.get())  * NORM
        maxval = int(self.str_decid_max.get())  * NORM  

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma)
        asset_mask = assets.asset_mask(self.heightmap,minval,maxval)
        mask = (grad_mask * asset_mask) / 255
        tree_map = (mask * self.cutout_mask) / 255
        self.decid_map = gaussian_filter(tree_map, sigma=sigma)
        pp.imsave(file_name, self.decid_map, vmin = 0, vmax = 255, cmap = 'gray')

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['decid']  == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_decid = tk.Label(self.prev_canvas, image=self.prev_canvas.mmap_handle[-1])
            self.prev_decid.pack()
            self.prev_decid_label = tk.Label(self.prev_canvas, text = "deciduous density map")
            self.prev_decid_label.pack()
            self.prev_index_list['decid'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['decid']-1] = ImageTk.PhotoImage(image)
            self.prev_decid.configure(image = self.prev_canvas.mmap_handle[self.prev_index_list['decid']-1])
        self.prev_canvas.master.update()

    def build_conif_map(self):
        self.heightmap = self.load_heightmap()
        file_name = os.path.join(map_folder,"coniferous_density.png")

        sigma = int(self.str_conif_sigma.get()) 
        steep = int(self.str_conif_steep.get()) * NORM
        minval = int(self.str_conif_min.get())  * NORM
        maxval = int(self.str_conif_max.get())  * NORM 

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma)
        asset_mask = assets.asset_mask(self.heightmap,minval,maxval)
        mask = (grad_mask * asset_mask) / 255
        tree_map = (mask * self.cutout_mask) / 255
        self.conif_map = gaussian_filter(tree_map, sigma=sigma)
        pp.imsave(file_name,self.conif_map, vmin = 0, vmax = 255, cmap = 'gray')
      
        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['conif']  == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_conif = tk.Label(self.prev_canvas, image=self.prev_canvas.mmap_handle[-1])
            self.prev_conif.pack()
            self.prev_conif_label = tk.Label(self.prev_canvas, text = "coniferous density map")
            self.prev_conif_label.pack()
            self.prev_index_list['conif'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['conif']-1] = ImageTk.PhotoImage(image)
            self.prev_conif.configure(image = self.prev_canvas.mmap_handle[self.prev_index_list['conif']-1])
        self.prev_canvas.master.update()


    def build_berries_map(self):
        self.heightmap = self.load_heightmap()

        file_name = os.path.join(map_folder,"berries_density.png")

        sigma = int(self.str_berries_sigma.get())
        steep = int(self.str_berries_steep.get())  * NORM
        minval = int(self.str_berries_min.get())   * NORM
        maxval = int(self.str_berries_max.get())   * NORM
        dense = int(self.str_berries_dense.get())
        group = int(self.str_berries_group.get())

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma) 
        asset_mask = assets.asset_mask(self.heightmap,minval,maxval)
        mask = (grad_mask * asset_mask) / 255
        self.berries_map = assets.asset_map(mask,dense,group) 
        pp.imsave(file_name, self.berries_map, vmin = 0, vmax = 255, cmap = 'gray')
      
        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['berries']  == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_berries = tk.Label(self.prev_canvas, image=self.prev_canvas.mmap_handle[-1])
            self.prev_berries.pack()
            self.prev_berries_label = tk.Label(self.prev_canvas, text = "berries density map")
            self.prev_berries_label.pack()
            self.prev_index_list['berries'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['berries']-1] = ImageTk.PhotoImage(image)
            self.prev_berries.configure(image = self.prev_canvas.mmap_handle[self.prev_index_list['berries']-1])
        self.prev_canvas.master.update()

    def build_stone_map(self):
        self.heightmap = self.load_heightmap()

        file_name = os.path.join(map_folder,"rock_density.png")

        sigma = int(self.str_stone_sigma.get())
        steep = int(self.str_stone_steep.get()) * NORM
        minval = int(self.str_stone_min.get())  * NORM
        maxval = int(self.str_stone_max.get())  * NORM
        dense = int(self.str_stone_dense.get())
        group = int(self.str_stone_group.get())

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma) 
        asset_mask = assets.asset_mask(self.heightmap,minval,maxval)
        mask = (grad_mask * asset_mask) / 255
        self.stone_map = assets.asset_map(mask,dense,group) 
        pp.imsave(file_name, self.stone_map, vmin = 0, vmax = 255, cmap = 'gray')

        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['stone']  == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_stone = tk.Label(self.prev_canvas, image=self.prev_canvas.mmap_handle[-1])
            self.prev_stone.pack()
            self.prev_stone_label = tk.Label(self.prev_canvas, text = "stone density map")
            self.prev_stone_label.pack()
            self.prev_index_list['stone'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['stone']-1] = ImageTk.PhotoImage(image)
            self.prev_stone.configure(image = self.prev_canvas.mmap_handle[self.prev_index_list['stone']-1])
        self.prev_canvas.master.update()

    def build_ore_map(self):
        self.heightmap = self.load_heightmap()
        file_name = os.path.join(map_folder,"iron_density.png")
        sigma = int(self.str_ore_sigma.get()) 
        steep = int(self.str_ore_steep.get()) * NORM
        minval = int(self.str_ore_min.get())  * NORM
        maxval = int(self.str_ore_max.get())  * NORM
        dense = int(self.str_ore_dense.get())
        group = int(self.str_ore_group.get())

        grad_map, grad_mask = assets.gradient(self.heightmap, steep, sigma) 
        asset_mask = assets.asset_mask(self.heightmap,minval,maxval)
        mask = (grad_mask * asset_mask) / 255
        self.ore_map = assets.asset_map(mask,dense,group) 
        pp.imsave(file_name, self.ore_map, vmin = 0, vmax = 255, cmap = 'gray')
   
        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['ore']  == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_ore = tk.Label(self.prev_canvas, image=self.prev_canvas.mmap_handle[-1])
            self.prev_ore.pack()
            self.prev_ore_label = tk.Label(self.prev_canvas, text = "ore density map")
            self.prev_ore_label.pack()
            self.prev_index_list['ore'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['ore']-1] = ImageTk.PhotoImage(image)
            self.prev_ore.configure(image = self.prev_canvas.mmap_handle[self.prev_index_list['ore']-1])
        self.prev_canvas.master.update()

    def build_fish_map(self):
        self.heightmap = self.load_heightmap()

        file_name = os.path.join(map_folder,"fish_density.png")

        group = int(self.str_fish_group.get())
        maxval = int(self.str_fish_max.get())  * NORM
        dense = int(self.str_fish_dense.get())

        mask = assets.asset_mask(self.heightmap,0,maxval)
        self.fish_map = assets.asset_map(mask,dense,group)
        
        pp.imsave(file_name, self.fish_map, vmin = 0, vmax = 255, cmap = 'gray')
      
        image = Image.open(file_name)
        image.thumbnail((PREV_SIZE,PREV_SIZE), Image.ANTIALIAS)

        if self.prev_index_list['fish']  == 0:
            self.prev_canvas.mmap_handle.append(ImageTk.PhotoImage(image))
            self.prev_fish = tk.Label(self.prev_canvas, image=self.prev_canvas.mmap_handle[-1])
            self.prev_fish.pack()
            self.prev_fish_label = tk.Label(self.prev_canvas, text = "fish density map")
            self.prev_fish_label.pack()
            self.prev_index_list['fish'] = len(self.prev_canvas.mmap_handle)
        else:
            self.prev_canvas.mmap_handle[self.prev_index_list['fish']-1] = ImageTk.PhotoImage(image)
            self.prev_fish.configure(image = self.prev_canvas.mmap_handle[self.prev_index_list['fish']-1])
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

        self.build_decid_map()
        self.build_conif_map()

    def suggest_heights(self):
        above = str(int(self.str_grass_level.get()) + 200)
        below = str(int(self.str_grass_level.get()) - 200)
        self.str_berries_min.set(above)
        self.str_decid_min.set(above)
        self.str_conif_min.set(above)
        self.str_stone_min.set(above)
        self.str_ore_min.set(above)
        self.str_fish_max(below)


class River(Terrain):
    def __init__(self, container, master, prev_canvas, index, wp_ignore=False):
        super().__init__(container, master, prev_canvas, index)

        # internal variables
        self.object_label = "River"+str(index)
        self.str_width = tk.StringVar()
        self.str_width.set(str(3))
        self.str_div = tk.StringVar()
        self.str_div.set(str(10))
        self.str_sigma = tk.StringVar()
        self.str_sigma.set(str(5))

        # Top Frame Area        
        self.label_name = tk.Label(self.top_frame, text=self.object_label)
        self.label_name.grid(column=0, row=0, sticky='w')
        self.gen_btn = tk.Button(self.top_frame, text="generate", command=self.generate )
        self.gen_btn.grid(column=3, row=0, sticky='e')
        self.del_btn = tk.Button(self.top_frame, text="delete", command=self.destroy )
        self.del_btn.grid(column=4, row=0, sticky='e')
        self.add_wp_btn = tk.Button(self.top_frame, text="add WP", command=self.add_wp )
        self.add_wp_btn.grid(column=5, row=0, sticky='e')

        # Main Frame Area
        self.label_width = tk.Label(self.main_frame, text="width: ")
        self.label_width.grid(column=0, row=1, sticky='w')
        self.box_width = tk.Entry(self.main_frame, width=ENTRY_WIDTH, justify='right', textvariable=self.str_width)
        self.box_width.grid(column=1, row=1, sticky='w')
        
        self.label_div = tk.Label(self.main_frame, text = "diversity: ")
        self.label_div.grid(column = 2, row = 1, sticky = 'w')
        self.box_div = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_div)
        self.box_div.grid(column = 3, row = 1, sticky = 'w')

        self.label_sigma = tk.Label(self.main_frame, text = "sigma: ")
        self.label_sigma.grid(column = 4, row = 1, sticky = 'w')
        self.box_sigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, justify = 'right', textvariable = self.str_sigma)
        self.box_sigma.grid(column = 5, row = 1, sticky = 'w')

        # build waypoint references and waypoint Frame Area
        if not wp_ignore:
            self.add_wp()
            self.add_wp()

        # build preview
        file_name = os.path.join(partials_folder,default_file)
        self.index = self.build_preview(self.prev_canvas.river_im,self.object_label, file_name, self.index, init=True)

    def generate(self):
        file_name = os.path.join(partials_folder,"rivermap"+str(self.index)+".png")
        
        self.width = int(self.str_width.get())
        self.div   = int(self.str_div.get())
        self.sigma = int(self.str_sigma.get())


        self.river = terrain.ImprovedRiver(self.width, self.div, self.sigma)
        for wp in self.wp_list:
            if not wp.deleted:
                x, y = wp.getval()
            self.river.add_coords(x, y)

        self.terrain_map = self.river.run()

        pp.imsave(file_name, self.terrain_map, vmin = 0, vmax = 50)
        time.sleep(1)
        self.index = self.build_preview(self.prev_canvas.river_im,self.object_label, file_name, self.index)

    def width_get(self):
        return int(self.str_width.get())
    def div_get(self):
        return int(self.str_div.get())
    def sigma_get(self):
        return int(self.str_sigma.get())


      
class Mountain(Terrain):
    def __init__(self, container, master, prev_canvas, index, wp_ignore = False):
        super().__init__(container, master, prev_canvas, index)
        
         #internal veriables
        self.object_label = "Mountain" + str(index)

        self.str_height = tk.StringVar()
        self.str_height.set(str(500))
        self.str_spread = tk.StringVar()
        self.str_spread.set(str(100))
        self.str_div = tk.StringVar()
        self.str_div.set(str(20))
        self.str_dense = tk.StringVar()
        self.str_dense.set(str(10))
        self.str_sigma = tk.StringVar()
        self.str_sigma.set(str(20))
        

        self.label_name = tk.Label(self.top_frame, text = self.object_label)
        self.label_name.grid(column = 0, row = 0, sticky = 'w')
        self.gen_btn = tk.Button(self.top_frame, text = "generate", command = self.generate )
        self.gen_btn.grid(column = 2, row = 0, sticky = 'w')
        self.del_btn = tk.Button(self.top_frame, text = "delete", command = self.destroy )
        self.del_btn.grid(column = 3, row = 0, sticky = 'w')
        self.add_wp_btn = tk.Button(self.top_frame, text = "add WP", command = self.add_wp )
        self.add_wp_btn.grid(column = 4, row = 0, sticky = 'w')
        
        self.label_height = tk.Label(self.main_frame, text = "height: ")
        self.label_height.grid(column = 0, row = 1, padx = PADX)
        self.box_height = tk.Entry(self.main_frame, width = ENTRY_WIDTH, textvariable = self.str_height)
        self.box_height.grid(column = 1, row = 1, padx = PADX)
        
        self.label_spread = tk.Label(self.main_frame, text = "spread: ")
        self.label_spread.grid(column = 2, row = 1, padx = PADX)
        self.box_spread = tk.Entry(self.main_frame, width = ENTRY_WIDTH, textvariable = self.str_spread)
        self.box_spread.grid(column = 3, row = 1, padx = PADX)
        
        self.label_div = tk.Label(self.main_frame, text = "diversity: ")
        self.label_div.grid(column = 4, row = 1, padx = PADX)
        self.box_div = tk.Entry(self.main_frame, width = ENTRY_WIDTH, textvariable = self.str_div)
        self.box_div.grid(column = 5, row = 1, padx = PADX)
        self.label_dense = tk.Label(self.main_frame, text = "density: ")
        self.label_dense.grid(column = 0, row = 2, padx = PADX)
        self.box_dense = tk.Entry(self.main_frame, width = ENTRY_WIDTH, textvariable = self.str_dense)
        self.box_dense.grid(column = 1, row = 2, padx = PADX)
        self.label_sigma = tk.Label(self.main_frame, text = "sigma: ")
        self.label_sigma.grid(column = 2, row = 2, padx = PADX)
        self.box_sigma = tk.Entry(self.main_frame, width = ENTRY_WIDTH, textvariable = self.str_sigma)
        self.box_sigma.grid(column = 3, row = 2, padx = PADX)

        # build wp frame Area       
        if not wp_ignore:
            self.add_wp()
            self.add_wp()

        # build preview
        file_name = os.path.join(partials_folder,default_file)
        self.index = self.build_preview(self.prev_canvas.mountain_im, self.object_label,file_name,self.index, init=True)

    def height_get(self):
        return int(self.str_height.get())

    def spread_get(self):
        return int(self.str_spread.get())

    def div_get(self):
        return int(self.str_div.get())
    
    def dense_get(self):
        return int(self.str_dense.get())


    def generate(self):
        # file name to save the preview file
        file_name = os.path.join(partials_folder,"mountainmap"+str(self.index)+".png")

        # input parameters for generation 
        self.height = int(self.str_height.get()) * NORM
        self.spread = int(self.str_spread.get())
        self.div    = int(self.str_div.get())    
        self.dense  = int(self.str_dense.get()) 
        self.sigma  = int(self.str_sigma.get())

        self.mountain = terrain.Mountain(self.height * self.sigma/5 , self.spread, self.div, self.dense, self.sigma )
        for wp in self.wp_list:
            if not wp.deleted:
                x, y = wp.getval()
                self.mountain.add_coords(x, y)

        self.terrain_map = self.mountain.run()
        if int(self.str_height.get()) >= 0:
            pp.imsave(file_name, self.terrain_map, vmin = 0, vmax = MAX_16BIT )
        else:
            pp.imsave(file_name, self.terrain_map, vmin = -MAX_16BIT, vmax =0 )
        time.sleep(1)
        self.index =self.build_preview(self.prev_canvas.mountain_im,self.object_label, file_name, self.index)

class Waypoint():
    def __init__(self,master, index, container ):
        self.str_x = tk.StringVar()
        self.str_x.set(str(index * 100))
        self.str_y = tk.StringVar()
        self.str_y.set(str(index * 100))
        
        self.index = index
        self.container = container
        self.deleted = False        

        self.frame = tk.Frame(master)
        self.frame.grid(column = 0, sticky = 'w')
        
        self.wp_label = tk.Label(self.frame, text = "Waypoint"+str(index), width = 10)
        self.wp_label.grid(column = 0, row = 0, sticky = 'w')

        self.label_x = tk.Label(self.frame, text="X: ")
        self.label_x.grid(column = 1, row = 0, sticky = 'w')
        self.box_x = tk.Entry(self.frame, width = ENTRY_WIDTH, textvariable = self.str_x)
        self.box_x.grid(column = 2, row = 0, sticky = 'w')
        self.label_y = tk.Label(self.frame, text="Y: ")
        self.label_y.grid(column = 3, row = 0, sticky = 'w')
        self.box_y = tk.Entry(self.frame, width =ENTRY_WIDTH, textvariable = self.str_y)
        self.box_y.grid(column = 4, row = 0, sticky = 'w')
        self.del_btn = tk.Button(self.frame, text = "delete", command = self.destroy)
        self.del_btn.grid(column = 5, row = 0, sticky = 'w')
        self.container.update()

    def destroy(self):
        self.frame.destroy()
        self.container.update()
        self.deleted = True
    
    def getval(self):
        return int(self.str_x.get()), int(self.str_y.get()) 


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
        self.windows_item = self.canvas.create_window(0,0, window=self, anchor=tk.NW)


    def __fill_canvas(self, event):
        "Enlarge the windows item to the canvas width"

        canvas_width = event.width
        self.canvas.itemconfig(self.windows_item, width = canvas_width)        

    def update(self):
        "Update the canvas and the scrollregion"

        self.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox(self.windows_item))

def create_defaults():
    #is the maps folder missing, make one
    if not os.path.exists(map_folder):
        os.mkdir(map_folder)
    
    #is the partials maps folder missing, make one
    if not os.path.exists(partials_folder):
        os.mkdir(partials_folder)
    #is the default partials map in partials missing, make one
    if not os.path.exists(os.path.join(partials_folder,default_file)):    
        default_map = numpy.random.randint(0, high = 255, size=(1024,1024))
        pp.imsave(os.path.join(partials_folder,default_file), default_map, vmin = 0, vmax = 255 )

    if not os.path.exists(os.path.join(partials_folder, "combined.png")):    
        heightmap = numpy.random.randint(0, high = 255, size=(1024,1024))
        pp.imsave(os.path.join(partials_folder,"combined.png"), heightmap, vmin = 0, vmax = 255 )    

    # is the json config file folder missing, make one
    if not os.path.exists(jsons_folder):
        os.mkdir(jsons_folder)

class Status():
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

        self.label.configure(text = self.status_message) 

