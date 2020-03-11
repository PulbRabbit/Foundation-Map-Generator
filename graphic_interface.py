from tkinter import font
from tkinter import filedialog as fdialog
import tkinter as tk
import mapgen_guilib as GUI

import numpy
import matplotlib.pyplot as pp
from scipy.ndimage.filters import gaussian_filter
from PIL import ImageTk, Image

import png

import os 
import json

HEIGHT = 700
WIDTH = 800
SCREEN_SIZE = 1024
MAX_16BIT = 65535


root = tk.Tk()
root.right_zoom = 1.0
try: 
    root.state("zoomed")
except:
    try:
        root.attributes("-zoomed", True)
    except:
        print("issues with your OS")

root.title("Unofficial Foundation Map Generator")


default_font = font.nametofont("TkDefaultFont")
default_font.configure(size=8)
default_font = font.nametofont("TkTextFont")
default_font.configure(size=8)


mountains = []
rivers = []
river_index = tk.IntVar()
river_index.set(0)

mountain_index = tk.IntVar()
mountain_index.set(0)

heightmap = numpy.full((1024,1024),0) #initialize final heightmap

# Files Handling
map_folder = "Maps"
heightmap_file_name = "heightmap.png"
partials_folder = "PartialMaps"
combined_file_name = "combined.png"

# Generate a base_line map, all obects will be added
GUI.create_defaults()

def add_river(wp_ignore = False):
    i = river_index.get()
    i += 1
    rivers.append(GUI.River(river_container, river_canvas,preview_canvas,i,wp_ignore = wp_ignore))
    river_index.set(i)
    river_container.update()
    status.print("added river")
    set_heights(root,assets_container,river_container,mountain_container)


def add_mountain(wp_ignore = False):
    i = mountain_index.get()
    i += 1
    mountains.append(GUI.Mountain(mountain_container, mountain_canvas,preview_canvas,i,wp_ignore = wp_ignore))
    mountain_index.set(i)
    mountain_container.update()
    status.print("added mountain")
    set_heights(root, assets_container, river_container, mountain_container)


def cook_map():
    heightmap = globalparam.baseline_map.copy()
    river_level = int(globalparam.str_riverlevel.get())

    # add all mountains
    for mountain in mountains:
        if not mountain.deleted:
            heightmap += mountain.terrain_map
    status.print("combined mountains")

    # add all rivers
    for river in rivers:
        if not river.deleted:
            for i in range(0, 1024):
                for j in range(0, 1024):
                 if river.terrain_map[i][j] > 0 and heightmap[i][j] > river_level:
                    heightmap[i][j] = river_level
    status.print("combined rivers")

    # add a final gaussfilter
    heightmap = numpy.interp(heightmap, (heightmap.min(), heightmap.max()), (0, MAX_16BIT)) # normalizing heightmap to 0...255
    heightmap = gaussian_filter(heightmap, sigma=int(globalparam.str_postsigma.get()))    
    status.print("smoothened map")
    pp.imsave(os.path.join(GUI.partials_folder,combined_file_name), heightmap, vmin = 0, vmax = MAX_16BIT )
    
    heightmap.astype(numpy.uint16) # converting data to 16bit unsigned integer
    status.print("saved heightmap")
    to_img = []
    for i in range(0,1024):
        to_img.append([])
        for j in range(0,1024):
           to_img[i].append(int(heightmap[i][j]))

    imgWriter = png.Writer(1024, 1024, greyscale=True, alpha=False, bitdepth=16)
    file_buffer = open(os.path.join(map_folder,heightmap_file_name), "wb")
    imgWriter.write(file_buffer,to_img)
    status.print("saved heightmap")
    #load to map screen
    image = Image.open(os.path.join(GUI.partials_folder,combined_file_name))    
    image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
    root.screen = ImageTk.PhotoImage(image)

    draw_screen()


def draw_screen():

    result_canvas.create_image(0, 0, anchor='nw', image=root.screen)
    
    river_polylist = []
    for river in rivers:
        river_polylist.append(river.get_waypoints())
    river_polylist = [[int(j * root.right_zoom) for j in i] for i in river_polylist]

    mountain_polylist = []
    for mountain in mountains:
        mountain_polylist.append(mountain.get_waypoints())
    mountain_polylist = [[int(j * root.right_zoom) for j in i] for i in mountain_polylist]
    
    for poly in river_polylist:
        result_canvas.create_line(poly, fill='lightblue', width = 2)

    for poly in mountain_polylist:
        result_canvas.create_line(poly, fill='darkgreen', width = 2)


def gen_asset_maps():
    pass

def load_json():
    root.filename = fdialog.askopenfilename(
                                                initialdir = os.path.join(GUI.jsons_folder),
                                                title = "Select file",
                                                filetypes = (("json files","*.json*"),("all files","*.*"))
                                            )

    with open(os.path.join(GUI.jsons_folder,root.filename)) as json_file:
            data = json.load(json_file)
            if data['type'] == "terrain" or data['type'] == "combined":
                globalparam.str_max_height.set(str(data['baseline_map']['max_height']))
                globalparam.str_min_height.set(str(data['baseline_map']['min_height']))
                globalparam.str_riverlevel.set(str(data['baseline_map']['river_level']))
                globalparam.str_pre_sigma.set(str(data['baseline_map']['sigma']))
                globalparam.str_postsigma.set(str(data['postprocess']['sigma']))

                for json_river in data['rivers']:
                    add_river(wp_ignore = True)
                    rivers[-1].str_width.set(str(json_river['attributes']['width'])) 
                    rivers[-1].str_div.set(str(json_river['attributes']['deviation']))
                    rivers[-1].str_sigma.set(str(json_river['attributes']['sigma']))
                    for wp in json_river['waypoints']:
                        rivers[-1].add_wp()
                        rivers[-1].wp_list[-1].str_x.set(str(wp['x']))
                        rivers[-1].wp_list[-1].str_y.set(str(wp['y']))

                for json_mountain in data['mountains']:
                    add_mountain(wp_ignore = True)
                    mountains[-1].str_height.set(str(json_mountain['attributes']['height'])) 
                    mountains[-1].str_div.set(str(json_mountain['attributes']['deviation']))
                    mountains[-1].str_dense.set(str(json_mountain['attributes']['density']))
                    mountains[-1].str_spread.set(str(json_mountain['attributes']['spread']))
                    mountains[-1].str_sigma.set(str(json_mountain['attributes']['sigma']))
                    for wp in json_mountain['waypoints']:
                        mountains[-1].add_wp()
                        mountains[-1].wp_list[-1].str_x.set(str(wp['x']))
                        mountains[-1].wp_list[-1].str_y.set(str(wp['y']))

            if data['type'] == "assets" or data['type'] == "combined":
                assets_param.param_from_data(data)

def save_json():
    root.filename =  fdialog.asksaveasfilename(
                                                initialdir = os.path.join(GUI.jsons_folder),
                                                title = "Select file",
                                                filetypes = (("json files","*.json*"),("all files","*.*"))
                                            )
    if not ".json" in root.filename:
        root.filename = root.filename + ".json" 

    data = {}
    data['version'] = "0.1.1"
    data['type'] = "combined"
    data['baseline_map'] = {
                                "max_height":  globalparam.get_maxheight(), 
                                "min_height":  globalparam.get_minheight(), 
                                "river_level": globalparam.get_riverlevel(), 
                                "sigma":       globalparam.get_presigma()
                            }
    data['postprocess'] = {"sigma":globalparam.get_postsigma()}
    data['rivers'] = []
    for river in rivers:
        data['rivers'].append({
            "attributes":{"width": river.width_get(), "deviation": river.div_get(),"sigma": river.sigma_get()}})
        data['rivers'][-1]["waypoints"] = []  
        for wp in river.wp_list:  
            data['rivers'][-1]["waypoints"].append({"x": int(wp.str_x.get()), "y": int(wp.str_y.get())})
    
    data['mountains'] = []
    for mountain in mountains:
        data['mountains'].append({
            "attributes":{"height": mountain.height_get(), "deviation": mountain.div_get(), "density": mountain.dense_get(), "sigma": mountain.sigma_get()}})
        data['mountains'][-1]["waypoints"] = []  
        for wp in mountain.wp_list:  
            data['mountains'][-1]["waypoints"].append({"x": int(wp.str_x.get()), "y": int(wp.str_y.get())})

    # assets parameter
    data['grass'] =  {"level":int(assets_param.str_grass_level.get()), "sigma": int(assets_param.str_grass_sigma.get())}
    
    data['deciduous_density_map'] = {"steepness":  int(assets_param.str_decid_steep.get()), 
                                     "max_height": int(assets_param.str_decid_max.get()),
                                     "min_height": int(assets_param.str_decid_min.get()), 
                                     "sigma":      int(assets_param.str_decid_sigma.get())}

    data['coniferous_density_map'] = {"steepness":  int(assets_param.str_conif_steep.get()),
                                      "max_height": int(assets_param.str_conif_max.get()), 
                                      "min_height": int(assets_param.str_conif_min.get()), 
                                      "sigma":      int(assets_param.str_conif_sigma.get())}

    data['berries'] = { "density" :   int(assets_param.str_berries_dense.get()), 
                        "grouping":   int(assets_param.str_berries_group.get()), 
                        "steepness":  int(assets_param.str_berries_steep.get()), 
                        "max_height": int(assets_param.str_berries_max.get()), 
                        "min_height": int(assets_param.str_berries_min.get()), 
                        "sigma":      int(assets_param.str_berries_sigma.get())}

    data['stone']   = { "density":    int(assets_param.str_stone_dense.get()), 
                        "grouping":   int(assets_param.str_stone_group.get()),
                        "steepness":  int(assets_param.str_stone_steep.get()), 
                        "max_height": int(assets_param.str_stone_max.get()), 
                        "min_height": int(assets_param.str_stone_min.get()),
                        "sigma":      int(assets_param.str_stone_sigma.get())}

    data['ore']     = { "density":    int(assets_param.str_ore_dense.get()), 
                        "grouping":   int(assets_param.str_ore_group.get()), 
                        "steepness":  int(assets_param.str_ore_steep.get()), 
                        "max_height": int(assets_param.str_ore_max.get()), 
                        "min_height": int(assets_param.str_ore_min.get()), 
                        "sigma":      int(assets_param.str_ore_sigma.get())}

    data['fish'] = { "density":       int(assets_param.str_fish_dense.get()),
                     "grouping":      int(assets_param.str_fish_group.get()),
                     "max_height":    int(assets_param.str_fish_max.get()),}  


    with open(os.path.join(GUI.jsons_folder,root.filename), 'w') as outfile:
        json.dump(data, outfile, indent = 4)

def set_heights(root, assets_cont, river_cont, mountain_cont,prio=False, init = False):
    ''' set the height of widgets, that need dynamic distribution '''
    
    #get how much space can be dispributed to the left an right
    
    #define left spaces
    if init:
        left_space = root.winfo_screenheight()  - globals_frame.winfo_height() - menu.winfo_height() - bottom_frame.winfo_height() - 180
        right_space = root.winfo_screenheight() - menu.winfo_height() - bottom_frame.winfo_height() - 180
    else:
       left_space = root.winfo_screenheight()  - globals_frame.winfo_height() - menu.winfo_height() - bottom_frame.winfo_height() - 92
       right_space = root.winfo_screenheight() - menu.winfo_height() - bottom_frame.winfo_height() - 92
    # set left column
    if prio:
        assets_initial_height = left_space * 0.6
        if assets_initial_height > 450:
            assets_initial_height = 450
        left_space_terrain = left_space - assets_initial_height
        terrains_initial_height = left_space_terrain / 2

        assets_cont.canvas.configure(height = assets_initial_height)
        river_cont.canvas.configure(height = terrains_initial_height)
        mountain_cont.canvas.configure(height = terrains_initial_height)
    else:
        assets_final_height = int(left_space * 0.1)
        terrains_final_height = int(left_space * 0.45)
        assets_cont.canvas.configure(height = assets_final_height)
        river_cont.canvas.configure(height = terrains_final_height)
        mountain_cont.canvas.configure(height = terrains_final_height)
        assets_cont.update()
        river_cont.update()
        mountain_cont.update()


    #set right column
    right_width = root.winfo_screenwidth() - left_frame.winfo_width() - middle_frame.winfo_width()
    if right_space < right_width:
        root.right_zoom = right_space / 1024
    else:
        root.right_zoom = right_width / 1024

    if root.right_zoom > 1.0:
        root.right_zoom = 1.0
    print(root.right_zoom)
    result_canvas.configure(height = right_space)
    image = Image.open(os.path.join(GUI.partials_folder, combined_file_name))
    image.thumbnail((int(SCREEN_SIZE*root.right_zoom), int(SCREEN_SIZE*root.right_zoom)), Image.ANTIALIAS)
    root.screen = ImageTk.PhotoImage(image)
    result_canvas.create_image(0, 0, anchor='nw', image=root.screen)


def view_assetmaps(map_file_name, overlay = False):
    set_heights(root, assets_container, river_container, mountain_container, prio=True)
    if overlay:
        image_bg = Image.open(os.path.join(GUI.partials_folder, "combined.png"))
        image_fg = Image.open(os.path.join(GUI.map_folder, map_file_name))
        image_fg.putalpha(80)
        image = Image.alpha_composite(image_bg, image_fg)

    else: 
        image = Image.open(os.path.join(GUI.map_folder, map_file_name))
    print(root.right_zoom, image.size)
    image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
    root.screen = ImageTk.PhotoImage(image)
    result_canvas.create_image(0, 0, anchor='nw', image=root.screen)


def import_heightmap():
    globalparam.get_heightmap()

# -- toplevel menues


def about():
    print("this is supposed to help you")


menu = tk.Menu(root)
root.config(menu=menu)
file_menu = tk.Menu(menu)
add_menu = tk.Menu(menu)
gen_menu = tk.Menu(menu)
help_menu = tk.Menu(menu)
view_menu = tk.Menu(menu)
prio_menu = tk.Menu(menu)

menu.add_cascade(label="File", menu=file_menu)
#file_menu.add_command(label="New", command=load_json)
file_menu.add_command(label="Load Parameters", command=load_json)
file_menu.add_command(label="Save Parameters", command=save_json)
file_menu.add_separator()
file_menu.add_command(label="Import Heightmap", command=import_heightmap)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

menu.add_cascade(label = "Add", menu = add_menu)
add_menu.add_command(label = "River", command=add_river)
add_menu.add_command(label = "Mountain", command = add_mountain)

menu.add_cascade(label = "Generator",  menu = gen_menu)
gen_menu.add_command(label = "update Poly Preview", command = draw_screen)
gen_menu.add_command(label = "cook heightmap", command = cook_map)
gen_menu.add_command(label = "generate assets maps", command = gen_asset_maps)

menu.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About...", command=about)

menu.add_cascade(label = "View",  menu = view_menu)
view_menu.add_cascade(label = "Priority",  menu = prio_menu)
prio_menu.add_command(label = "Assets", command = lambda:  set_heights(root,assets_container,river_container,mountain_container,prio=True))
prio_menu.add_command(label = "Terrain", command = lambda: set_heights(root,assets_container,river_container,mountain_container))
view_menu.add_command(label = "Material Mask", command = lambda: view_assetmaps("material_mask.png", overlay = True))
view_menu.add_command(label = "Deciduous Density Map", command = lambda: view_assetmaps("deciduous_density.png", overlay = True))
view_menu.add_command(label = "Coniferous Density Map", command = lambda: view_assetmaps("coniferous_density.png", overlay = True))
view_menu.add_command(label = "Berries Density Map", command = lambda: view_assetmaps("berries_density.png", overlay = True))
view_menu.add_command(label = "Rocks Density Map", command = lambda: view_assetmaps("rock_densiy.png", overlay = True))
view_menu.add_command(label = "Iron Density Map", command = lambda: view_assetmaps("iron_density.png", overlay = True))
view_menu.add_command(label = "Fish Density Map", command = lambda: view_assetmaps("fish_density.png", overlay = True))

# -- Basic three Areas on Screen
top_frame = tk.Frame(root, relief = tk.GROOVE, borderwidth = 1)
top_frame.grid(column = 0, row = 0, sticky = 'nwe')

main_frame = tk.Frame(root)
main_frame.grid(column = 0, row = 1, sticky='w')


#reshaping main grid
main_frame.grid_columnconfigure(0, minsize= 200)
main_frame.grid_columnconfigure(1, minsize= 200)
main_frame.grid_columnconfigure(2, minsize= 1024)

bottom_frame = tk.Frame(root,  relief = tk.GROOVE, borderwidth = 1)
bottom_frame.grid(column = 0, row = 2, sticky='we')


# Left Frame
left_frame = tk.Frame(main_frame, relief = tk.GROOVE, borderwidth = 1)
left_frame.grid(column = 0, row = 0, sticky='nwse')

# middle Frame
middle_frame = tk.Frame(main_frame, relief = tk.GROOVE, borderwidth = 1)
middle_frame.grid(column = 1, row = 0, sticky='nwse')

pre_label = tk.Label(middle_frame, text = "Preview")
pre_label.pack(side='top')  

#container Frame
middle_container = GUI.Scrollable(middle_frame,width=16)
middle_container.canvas.configure(width = 260)
preview_canvas = tk.Canvas(middle_container,width=200,height=800)
preview_canvas.pack(side='left', expand=True, fill='both')

#right frame
right_frame = tk.Frame(main_frame, relief = tk.GROOVE, borderwidth = 1)
right_frame.grid(column = 2, row = 0, sticky='nwse')
  
#hosting results
result_canvas = tk.Canvas(right_frame, height = 900, width = 1000)
result_canvas.pack()

# all objects for the left Row: 
# first frame is hosting the add buttons to add mountains and rivers
add_frame = tk.Frame(top_frame)
#add_frame.grid(column = 0, row = 0, sticky = 'w')

add_frame_label = tk.Label(add_frame, text = "Add Terrain Objects")
add_frame_label.grid(column = 0, row = 0, sticky = 'w', padx=2)

btn_load_json = tk.Button(add_frame, text = "Load", command = load_json)
btn_load_json.grid(column = 1, row = 0, sticky = 'nw', padx=2)

btn_save_json = tk.Button(add_frame, text = "Save", command = save_json)
btn_save_json.grid(column = 2, row = 0, sticky = 'nw', padx=2)

btn_add_river = tk.Button(add_frame, text = "add river", command = add_river)
btn_add_river.grid(column = 3, row = 0, sticky = 'nw', padx=2)

btn_add_mountain = tk.Button(add_frame, text = "add mountain", command = add_mountain)
btn_add_mountain.grid(column = 4, row = 0, sticky = 'nw',  padx=2)

btn_poly_prev = tk.Button(add_frame, text = "preview as poly", command = draw_screen)
btn_poly_prev.grid(column = 5, row = 0, sticky = 'nw',  padx=2)

btn_cook_map = tk.Button(add_frame, text = "cook map", command = cook_map)
btn_cook_map.grid(column = 6, row = 0, sticky = 'nw',  padx=2)

add_frame_height = add_frame.winfo_height()

#second frame will host baseline
globals_frame = tk.Frame(left_frame)
globals_frame.grid(column = 0, row = 1, sticky = 'we')
globalparam = GUI.GlobalParams(globals_frame, preview_canvas, 100, 500, 100, 5, 5)

#assets
assets_frame = tk.Frame(left_frame)
assets_frame.grid(column = 0, row = 2, sticky = 'we')
assets_container = GUI.Scrollable(assets_frame,width=16)
assets_canvas = tk.Frame(assets_container, height = 500)
assets_canvas.pack(side='left', expand=True, fill='both')
assets_param = GUI.AssetParams(assets_canvas, preview_canvas, os.path.join(GUI.jsons_folder,GUI.asset_json_name))


#third frame will host all rivers
river_frame = tk.Frame(left_frame)
river_frame.grid(column = 0, row = 3, sticky = 'nwes')
river_container = GUI.Scrollable(river_frame,width=16)
river_canvas = tk.Frame(river_container)
river_canvas.pack(side='left', expand=True, fill='both')

#fourth frame will host all mountains
mountain_frame = tk.Frame(left_frame)
mountain_frame.grid(column = 0, row = 4, sticky = "nwes")
mountain_container = GUI.Scrollable(mountain_frame, width = 16)
mountain_canvas = tk.Canvas(mountain_container)
mountain_canvas.pack(side='left', expand=True, fill='both')

river_container.canvas.configure(width=300)
mountain_container.canvas.configure(width=300)
assets_container.canvas.configure(width=340)
# to display multiple images, and not to have the images garbage collected, here are two lists to put them
preview_canvas.river_im =[]     
preview_canvas.mountain_im =[]  

#Bottom Frame

status_label = tk.Label(bottom_frame, text="Status: ")
status_label.grid(column = 0, row = 0, sticky='w')

status_output = tk.Label(bottom_frame, text=" --- ")
status_output.grid(column = 1, row = 0, sticky='w')

status = GUI.Status("",status_output,400)
status.print("loaded GUI")

set_heights(root,assets_container,river_container,mountain_container,prio = True, init=True)
root.mainloop()

