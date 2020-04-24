__author__ = "Isajah"
__version__ = "1.3.1"

# pyinstaller graphic_interface.spec graphic_interface.py

# Imports
from tkinter import font
from tkinter import filedialog as filedialog
from tkinter import messagebox
import tkinter as tk
import subprocess
import mapgen_guilib as gui

import numpy
import matplotlib.pyplot as pp
from scipy.ndimage.filters import gaussian_filter
from PIL import ImageTk, Image, ImageOps
import plotly.graph_objects as go

import png

import os
import sys
import json
from shutil import copyfile

print("initializing editor")

# Constants
HEIGHT = 700
WIDTH = 800
SCREEN_SIZE = 1024
MAX_16BIT = 65535
PARTIALS = "PartialMaps"
MAPS = "Maps"
PARAM = "Parameters"
# Files Handling
map_folder = "Maps"
heightmap_file_name = "heightmap.png"
combined_file_name = "combined.png"
grid_coords = []
row = 0
for x_i in range(7, 950, 75):
    if row % 2 == 0:
        for y_i in range(58, 950, 86):
            grid_coords.append([x_i, y_i, True])
    else:
        for y_i in range(16, 950, 86):
            grid_coords.append([x_i, y_i, True])
    row += 1

print("getting local directories")
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(os.path.realpath(sys.executable))
else:
    application_path = os.path.dirname(os.path.realpath(__file__))

# Root and Toplevels
root = tk.Tk()
map_info_win = gui.MapInfo(100, 10, tk.IntVar(value=10), numpy.full((1024, 1024), 0), application_path)
map_info_win.withdraw()


# define base directory and workspace directory
root.ws_name = application_path
root.base_dir = application_path

if os.path.exists(os.path.join(root.base_dir, "Resources", "icon.ico")):
    root.iconbitmap(os.path.join(root.base_dir, "Resources", "icon.ico"))
else:
    print("tried to find icon at:", os.path.join(root.base_dir, "Resources", "icon.ico"), "but no file found ")

print("creating gui root and loading defaults")
root.str_title = "Unofficial Foundation Map Generator"
root.title(root.str_title)
root.right_zoom = 1.0
root.heightmap = numpy.full((1024, 1024), 0)
root.initialize = 5
root.view = 0
root.grid = tk.IntVar(value=0)
root.starting_tile = tk.IntVar(value=0)
root.easy = tk.IntVar(value=1)
root.path_show = tk.IntVar(value=1)
root.mountains = []
root.rivers = []
root.trees = []
root.village_paths = []
river_index = tk.IntVar(value=0)
mountain_index = tk.IntVar(value=0)
tree_index = tk.IntVar(value=0)
vp_index = tk.IntVar(value=0)
root.is_workspace = False

default_font = font.nametofont("TkDefaultFont")
default_font.configure(size=8)
default_font = font.nametofont("TkTextFont")
default_font.configure(size=8)

# load saved options fro moptions file
options_file = os.path.join(root.base_dir, "Jsons", "Options.json")
if os.path.isfile(options_file):
    with open(options_file) as json_file:
        options = json.load(json_file)
        lang = options["Language"]
        root.easy.set(options["Easy_Mode"])

# load localization package
language_file = os.path.join(root.base_dir, "Jsons", "Language.json")
labels = {}
if os.path.isfile(language_file):
    with open(language_file, encoding="utf-8") as json_file:
        lang_table = json.load(json_file)
    for name, value in lang_table.items():
        if type(value) is dict:
            print(name, value[lang])
            labels.update({name: value[lang]})

# toplevels that need language support
about_win = gui.About(application_path, labels)
about_win.withdraw()

# do full screen (depending on OS)
try:
    root.state("zoomed")
except OSError:
    try:
        root.attributes("-zoomed", True)
    except OSError:
        print("issues with your OS")


# Generate a baseline map, all objects will be added on the baseline
gui.create_defaults()


def add_river(wp_ignore=False):
    i = river_index.get()
    i += 1
    root.rivers.append(gui.River(river_container, river_canvas, preview_canvas, i, root.ws_name, labels,
                                 easy_mode=root.easy.get() == 1))
    if not wp_ignore:
        root.rivers[-1].add_wp()
        root.rivers[-1].add_wp()
    river_index.set(i)
    river_container.update()
    status.print("added river")
    set_heights()
    root.view = 0


def add_mountain(wp_ignore=False):
    i = mountain_index.get()
    i += 1
    root.mountains.append(gui.Mountain(mountain_container, mountain_canvas, preview_canvas, i, root.ws_name, labels,
                                       easy_mode=root.easy.get() == 1))
    if not wp_ignore:
        root.mountains[-1].add_wp()
        root.mountains[-1].add_wp()
    mountain_index.set(i)
    mountain_container.update()
    status.print("added mountain")
    set_heights()
    root.view = 0


def add_tree(type_ignore=False):
    i = tree_index.get()
    i += 1
    root.trees.append(gui.TreeMap(assets_container, assets_canvas, preview_canvas, i, root.ws_name, labels,
                                  easy_mode=root.easy.get() == 1))
    if not type_ignore:
        root.trees[-1].add_type()
    tree_index.set(i)
    assets_container.update()
    status.print("added tree map")
    set_heights(prio=True)
    root.view = 1
    tree = root.trees[-1]
    overlay_menu[1].add_command(label=tree.object_label,
                                command=lambda: view_asset_maps(tree.file_name, overlay=0))
    overlay_menu[1].add_command(label=tree.object_label + " Density Map",
                                command=lambda: view_asset_maps(tree.file_name, overlay=1))
    overlay_menu[1].add_command(label=tree.object_label + " Overlay + Material Mask",
                                command=lambda: view_asset_maps(tree.file_name, overlay=2))
    overlay_menu[1].add_separator()
    cook_win.get_tree_maps(root.trees)


def add_village_path():
    i = vp_index.get()
    i += 1
    root.village_paths.append(gui.VillagePath(village_path_container, village_path_canvas, i, easy_mode=root.easy.get() == 1))
    vp_index.set(i)
    village_path_container.update()
    cook_win.paths = root.village_paths
    status.print("added village path")
    set_heights(prio=True)
    root.view = 1


def cook_map():
    heightmap = global_param.baseline_map.copy()
    river_level = global_param.river_level_get(norm=65)

    # add all mountains
    for mountain in root.mountains:
        if not mountain.deleted:
            heightmap += mountain.terrain_map
    status.print("combined mountains")

    # add all rivers
    for river in root.rivers:
        if not river.deleted:
            for i in range(0, 1024):
                for j in range(0, 1024):
                    if river.terrain_map[i][j] > 0 and heightmap[i][j] > river_level:
                        heightmap[i][j] = river_level
    status.print("combined rivers")

    # add a final gauss filter
    heightmap = numpy.interp(heightmap, (heightmap.min(), heightmap.max()), (0, MAX_16BIT))  # normalizing heightmap to 0...255
    heightmap = gaussian_filter(heightmap, sigma=int(global_param.str_post_sigma.get()))
    status.print("smoothened map")
    pp.imsave(os.path.join(root.ws_name, PARTIALS, combined_file_name), heightmap, vmin=0, vmax=MAX_16BIT)

    heightmap.astype(numpy.uint16)  # converting data to 16bit unsigned integer
    status.print("saved heightmap")
    to_img = []
    for i in range(0, 1024):
        to_img.append([])
        for j in range(0, 1024):
            to_img[i].append(int(heightmap[i][j]))

    img_writer = png.Writer(1024, 1024, greyscale=True, alpha=False, bitdepth=16)
    file_buffer = open(os.path.join(root.ws_name, MAPS, heightmap_file_name), "wb")
    img_writer.write(file_buffer, to_img)
    status.print("saved heightmap")
    save_json(os.path.join(root.ws_name, PARAM, "parameters.json"))
    status.print("saved parameters")
    # load to map screen
    image = Image.open(os.path.join(root.ws_name, PARTIALS, combined_file_name))
    image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
    root.screen = ImageTk.PhotoImage(image)
    grid_image = Image.open(os.path.join(root.base_dir, "Resources", "grid.png"))
    grid_image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
    root.grid_image = ImageTk.PhotoImage(grid_image)
    root.view = 0
    root.heightmap = heightmap
    map_info_win.heightmap = heightmap
    draw_screen()


def draw_screen():
    result_canvas.delete("all")
    result_canvas.create_image(0, 0, anchor='nw', image=root.screen)
    if root.grid.get() == 1:
        root.grid_id = result_canvas.create_image(0, 0, anchor='nw', image=root.grid_image)
    if root.starting_tile.get() == 1:
        for coord in grid_coords:
            if coord[2]:
                result_canvas.create_image(int(coord[0]*root.right_zoom), int(coord[1]*root.right_zoom), anchor='nw', image=root.grid_box)

    river_poly_list = []
    for river in root.rivers:
        if not river.deleted:
            river_poly_list.append(river.get_waypoints())
    river_poly_list = [[int(j * root.right_zoom) for j in i] for i in river_poly_list]

    mountain_poly_list = []
    for mountain in root.mountains:
        if not mountain.deleted:
            mountain_poly_list.append(mountain.get_waypoints())
    mountain_poly_list = [[int(j * root.right_zoom) for j in i] for i in mountain_poly_list]

    for poly in river_poly_list:
        if len(poly) >= 4:
            result_canvas.create_line(poly, fill='lightblue', width=2)

    for poly in mountain_poly_list:
        if len(poly) >= 4:
            result_canvas.create_line(poly, fill='darkgreen', width=2)


def draw_path(paths):
    result_canvas.delete("all")
    result_canvas.create_image(0, 0, anchor='nw', image=root.screen)
    if root.grid.get() == 1:
        root.grid_id = result_canvas.create_image(0, 0, anchor='nw', image=root.grid_image)
    if root.starting_tile.get() == 1:
        for coord in grid_coords:
            if coord[2]:
                result_canvas.create_image(int(coord[0] * root.right_zoom), int(coord[1] * root.right_zoom), anchor='nw',
                                           image=root.grid_box)

    try:
        entry_im = Image.open(os.path.join(root.base_dir, "Resources", "entry.png"))
        entry_im.thumbnail((16, 16), Image.ANTIALIAS)
        root.tk_entry_im = ImageTk.PhotoImage(entry_im)
    except OSError:
        print("failed loading entry image")
    try:
        exit_im = Image.open(os.path.join(root.base_dir, "Resources", "exit.png"))
        exit_im.thumbnail((16, 16), Image.ANTIALIAS)
        root.tk_exit_im = ImageTk.PhotoImage(exit_im)
    except OSError:
        print("failed loading exit image")

    for path in paths:
        (x_entry, y_entry),  (x_exit, y_exit) = path.getval()
        max_x = 1023 * root.right_zoom
        max_y = 1023 * root.right_zoom
        x_entry = x_entry * root.right_zoom
        y_entry = y_entry * root.right_zoom
        x_exit = x_exit * root.right_zoom
        y_exit = y_exit * root.right_zoom
        if x_entry < 10:
            x_entry = 5
        elif x_entry > max_x - 5:
            x_entry = max_x - 15
        else:
            x_entry -= 5

        if y_entry < 24:
            y_entry = 8
        elif y_entry > max_y:
            y_entry = max_y - 16
        else:
            y_entry -= 16

        if x_exit < 10:
            x_exit = 5
        elif x_exit > max_x - 5:
            x_exit = max_x - 15
        else:
            x_exit -= 5

        if y_exit < 24:
            y_exit = 8
        elif y_exit > max_y:
            y_exit = max_y - 16
        else:
            y_exit -= 16

        if root.path_show.get() == 1:
            result_canvas.create_line(x_entry+5, y_entry+16, x_exit+5, y_exit+16, fill='orange', dash=(5, 1), width=1)
        result_canvas.create_image(x_entry, y_entry, anchor='nw', image=root.tk_entry_im)
        result_canvas.create_image(x_exit, y_exit, anchor='nw', image=root.tk_exit_im)


def refresh_screen():
    if root.view == 0:
        draw_screen()
    if root.view == 1:
        draw_path(root.village_paths)
    if root.initialize > 2:
        set_heights(prio=True)
        root.initialize -= 1
        disable_all()
    if map_info_win.flag_done:
        map_info_win.flag_done = False
        save_json(os.path.join(root.ws_name, PARAM, "parameters.json"))
    tree_flag = False
    for index, tree in enumerate(root.trees, 0):
        if root.trees[index].deleted:
            root.trees.pop(index)
            tree_flag = True
    if tree_flag:
        tree_index.set(1)
        for tree in root.trees:
            tree.re_index(tree_index.get())
            tree_index.set(tree_index.get() + 1)

    root.after(500, lambda: refresh_screen())


def motion(event):
    x, y = int(event.x/root.right_zoom), int(event.y/root.right_zoom)
    if 0 <= x < 1024 and 0 <= y < 1024:
        height = root.heightmap[y, x]
        status_position.configure(text="x: " + str(x) + " y: " + str(y) + " h: " + str(int(height / 65)))


def gen_asset_maps(handle):
    handle.build_asset_maps()
    save_json(os.path.join(root.ws_name, PARAM, "parameters.json"))


def new_workspace():
    """ create new Workspace folder"""
    root.ws_name = filedialog.asksaveasfilename(
        initialdir=os.getcwd(),
        title="Create new Workspace",
        filetypes=(("folder", "*.dir"), ("all files", "*.*"))
    )
    if not root.ws_name == "":
        root.is_workspace = True
        global_param.ws_name = root.ws_name
        assets_param.ws_name = root.ws_name
        cook_win.ws_dir = root.ws_name

        for river in root.rivers:
            river.destroy()
        for mountain in root.mountains:
            mountain.destroy()
        for tree in root.trees:
            tree.destroy()
        for vp in root.village_paths:
            vp.destroy()

        river_index.set(0)
        mountain_index.set(0)
        tree_index.set(0)
        vp_index.set(0)

        root.rivers = []
        root.mountains = []
        root.village_paths = []
        root.trees = []

        image = Image.open(os.path.join(root.base_dir, PARTIALS, "default.png"))
        image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
        root.screen = ImageTk.PhotoImage(image)

        for river in root.rivers:
            river.ws_name = root.ws_name
        for mountain in root.mountains:
            mountain.ws_name = root.ws_name

        os.makedirs(root.ws_name, mode=0o777)

        os.makedirs(os.path.join(root.ws_name, PARTIALS))
        copyfile(os.path.join(root.base_dir, PARTIALS, "default.png"), os.path.join(root.ws_name, PARTIALS, "default.png"))
        copyfile(os.path.join(root.base_dir, PARTIALS, "default.png"), os.path.join(root.ws_name, PARTIALS, "combined.png"))
        os.makedirs(os.path.join(root.ws_name, MAPS), mode=0o777)
        os.makedirs(os.path.join(root.ws_name, PARAM))
        save_json(os.path.join(root.ws_name, PARAM, "parameters.json"))
        root.title(root.str_title+" * "+root.ws_name)
        map_info_win.deiconify()


def load_workspace():
    """ load a Workspace folder"""
    root.ws_name = os.path.join(filedialog.askdirectory(
        initialdir=os.getcwd(),
        title="Load Workspace",
    ))
    print(root.ws_name)
    root.title(root.str_title + " * " + root.ws_name)

    param_exists = os.path.isdir(os.path.join(root.ws_name, PARAM))
    partials_exists = os.path.isdir(os.path.join(root.ws_name, PARTIALS))
    maps_exits = os.path.isdir(os.path.join(root.ws_name, MAPS))
    if param_exists and partials_exists and maps_exits:
        root.is_workspace = True
        global_param.ws_name = root.ws_name
        global_param.load_heightmap()
        assets_param.ws_name = root.ws_name
        assets_param.load_material_map()
        assets_param.load_berries_map()
        assets_param.load_stone_map()
        assets_param.load_ore_map()
        assets_param.load_fish_map()
        image = Image.open(os.path.join(root.ws_name, PARTIALS, combined_file_name))
        image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
        root.screen = ImageTk.PhotoImage(image)
        grid_image = Image.open(os.path.join(root.base_dir, "Resources", "grid.png"))
        grid_image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
        root.grid_image = ImageTk.PhotoImage(grid_image)
        root.heightmap = assets_param.load_heightmap()

        cook_win.ws_dir = root.ws_name
        enable_all()
        if os.path.isfile(os.path.join(root.ws_name, PARAM, "parameters.json")):
            load_json(os.path.join(root.ws_name, PARAM, "parameters.json"))
            root.title(root.str_title + " * " + root.ws_name)
        else:
            messagebox.showinfo("Notice!", "Selected folder is not a workspace!")
        for tree in root.trees:
            tree.ws_name = root.ws_name
            tree.load_map()
        for river in root.rivers:
            river.ws_name = root.ws_name
        for mountain in root.mountains:
            mountain.ws_name = root.ws_name
    else:
        messagebox.showinfo("Notice!", "Selected folder is not a workspace!")


def import_json():
    root.filename = filedialog.askopenfilename(
                                                initialdir=os.path.join(gui.jsons_folder),
                                                title="Select file",
                                                filetypes=(("json files", "*.json*"), ("all files", "*.*"))
                                            )
    if root.filename is not None:
        # for import, clear all lists
        root.rivers = []
        root.mountains = []
        root.village_paths = []
        root.trees = []
        # now load json
        load_json(root.filename)


def load_json(file_name):
    for river in root.rivers:
        river.destroy()
    for mountain in root.mountains:
        mountain.destroy()
    for tree in root.trees:
        tree.destroy()
    for vp in root.village_paths:
        vp.destroy()

    river_index.set(0)
    mountain_index.set(0)
    tree_index.set(0)
    vp_index.set(0)

    root.rivers = []
    root.mountains = []
    root.village_paths = []
    root.trees = []

    with open(file_name) as json_file:
        data = json.load(json_file)

        map_info_win.name.set(data.get('name', "MyMap"))
        map_info_win.subtitle.set(data.get('subheader', "Custom Map"))
        map_info_win.author.set(data.get('author', "Your Name"))
        map_info_win.version.set(data.get("version", "1.0.0"))
        map_info_win.description.set(data.get("description", "Enter Your Description"))
        map_info_win.id.set(data.get("id", "MAP_ID"))

        global_param.str_max_height.set(str(int(data['baseline_map']['max_height'])))
        global_param.str_min_height.set(str(int(data['baseline_map']['min_height'])))
        global_param.str_river_level.set(str(int(data['baseline_map']['river_level'])))
        global_param.str_pre_sigma.set(str(int(data['baseline_map']['sigma'])))
        global_param.str_post_sigma.set(str(int(data['postprocess']['sigma'])))

        for json_river in data['rivers']:
            add_river(wp_ignore=True)
            root.rivers[-1].str_width.set(str(int(json_river['width'])))
            root.rivers[-1].str_div.set(str(int(json_river['deviation'])))
            root.rivers[-1].str_sigma.set(str(int(json_river['sigma'])))
            for wp in json_river['waypoints']:
                root.rivers[-1].add_wp()
                root.rivers[-1].wp_list[-1].str_x.set(str(int(wp['x'])))
                root.rivers[-1].wp_list[-1].str_y.set(str(int(wp['y'])))

        for json_mountain in data['mountains']:
            add_mountain(wp_ignore=True)
            root.mountains[-1].str_height.set(str(int(json_mountain['height'])))
            root.mountains[-1].str_div.set(str(int(json_mountain['deviation'])))
            root.mountains[-1].str_dense.set(str(int(json_mountain['density'])))
            root.mountains[-1].str_spread.set(str(int(json_mountain['spread'])))
            root.mountains[-1].str_sigma.set(str(int(json_mountain['sigma'])))
            for wp in json_mountain['waypoints']:
                root.mountains[-1].add_wp()
                root.mountains[-1].wp_list[-1].str_x.set(str(int(wp['x'])))
                root.mountains[-1].wp_list[-1].str_y.set(str(int(wp['y'])))

        assets_param.param_from_data(data)

        for tree in data['tree_maps']:
            add_tree(type_ignore=True)
            root.trees[-1].int_steep.set(tree['steep'])
            root.trees[-1].int_min.set(tree['min'])
            root.trees[-1].int_max.set(tree['max'])
            root.trees[-1].int_sigma.set(tree['sigma'])
            root.trees[-1].float_dense.set(tree['dense'])
            for type_ in tree['tree_types']:
                root.trees[-1].add_type()
                root.trees[-1].tree_types[-1].tree_type.set(type_['tree_type'])
                root.trees[-1].tree_types[-1].weight.set(type_['weight'])
                root.trees[-1].tree_types[-1].min_scale.set(type_['scale_min'])
                root.trees[-1].tree_types[-1].max_scale.set(type_['scale_max'])
                root.trees[-1].tree_types[-1].min_color = type_['color_min']
                root.trees[-1].tree_types[-1].max_color = type_['color_max']
                root.trees[-1].tree_types[-1].update()
        for vil_path in data['village_paths']:
            add_village_path()
            root.village_paths[-1].str_x_entry.set(str(vil_path['x_entry']))
            root.village_paths[-1].str_y_entry.set(str(vil_path['y_entry']))
            root.village_paths[-1].str_x_exit.set(str(vil_path['x_exit']))
            root.village_paths[-1].str_y_exit.set(str(vil_path['y_exit']))


def disable_all():
    pass


def enable_all():
    pass


def export_json():
    json_name = filedialog.asksaveasfilename(
        initialdir=os.path.join(gui.jsons_folder),
        title="Select file",
        filetypes=(("json files", "*.json*"), ("all files", "*.*"))
    )
    if ".json" not in json_name:
        json_name = json_name + ".json"
    save_json(json_name)


def save_workspace():
    save_json(os.path.join(root.ws_name, PARAM, "parameters.json"))


def save_json(json_name):
    data = {'name': map_info_win.name.get(),
            'subheader': map_info_win.subtitle.get(),
            'author': map_info_win.author.get(),
            'version': map_info_win.version.get(),
            'id': map_info_win.id.get(),
            'description':  map_info_win.description.get(),
            'baseline_map': {
        "max_height": global_param.max_height_get(),
        "min_height": global_param.min_height_get(),
        "river_level": global_param.river_level_get(),
        "sigma": global_param.pre_sigma_get()
            },
            'postprocess': {
        "sigma": global_param.post_sigma_get()
            },
            'rivers': []}

    for river in root.rivers:
        data['rivers'].append({
                           "width": river.width_get(),
                           "deviation": river.div_get(),
                           "sigma": river.sigma_get(),
                           "waypoints": []
        })
        for wp in river.wp_list:
            data['rivers'][-1]['waypoints'].append({"x": int(wp.str_x.get()), "y": int(wp.str_y.get())})

    data['mountains'] = []
    for mountain in root.mountains:
        data['mountains'].append({
                           "height": mountain.height_get(),
                           "deviation": mountain.div_get(),
                           "density": mountain.dense_get(),
                           "sigma": mountain.sigma_get(),
                           "spread": mountain.spread_get(),
                           "waypoints": []})
        for wp in mountain.wp_list:
            data['mountains'][-1]['waypoints'].append({"x": int(wp.str_x.get()), "y": int(wp.str_y.get())})

    # assets parameter
    data['grass'] = {"level": int(assets_param.int_grass_level.get()),
                     "sigma": int(assets_param.int_grass_sigma.get()),
                     "delta": int(assets_param.int_grass_delta.get()),
                     "div": int(assets_param.int_grass_divert.get())
                     }

    data['berries'] = {"density": int(assets_param.str_berries_dense.get()),
                       "grouping": int(assets_param.str_berries_group.get()),
                       "steepness": int(assets_param.str_berries_steep.get()),
                       "max_height": int(assets_param.str_berries_max.get()),
                       "min_height": int(assets_param.str_berries_min.get()),
                       "sigma": int(assets_param.str_berries_sigma.get())}

    data['stone'] = {"density": int(assets_param.str_stone_dense.get()),
                     "grouping": int(assets_param.str_stone_group.get()),
                     "steepness": int(assets_param.str_stone_steep.get()),
                     "max_height": int(assets_param.str_stone_max.get()),
                     "min_height": int(assets_param.str_stone_min.get()),
                     "sigma": int(assets_param.str_stone_sigma.get())}

    data['ore'] = {"density": int(assets_param.str_ore_dense.get()),
                   "grouping": int(assets_param.str_ore_group.get()),
                   "steepness": int(assets_param.str_ore_steep.get()),
                   "max_height": int(assets_param.str_ore_max.get()),
                   "min_height": int(assets_param.str_ore_min.get()),
                   "sigma": int(assets_param.str_ore_sigma.get())}

    data['fish'] = {"density": int(assets_param.str_fish_dense.get()),
                    "grouping": int(assets_param.str_fish_group.get()),
                    "max_height": int(assets_param.str_fish_max.get()), }

    data['tree_maps'] = []
    for tree in root.trees:
        data['tree_maps'].append({
         "steep": tree.int_steep.get(),
         "min": tree.int_min.get(),
         "max": tree.int_max.get(),
         "sigma": tree.int_sigma.get(),
         "dense": tree.float_dense.get(),
         "tree_types": []
        })
        for tree_type in tree.tree_types:
            data['tree_maps'][-1]['tree_types'].append({
                "tree_type": tree_type.tree_type.get(),
                "weight": tree_type.weight.get(),
                "scale_min": tree_type.min_scale.get(),
                "scale_max": tree_type.max_scale.get(),
                "color_min": tree_type.min_color,
                "color_max": tree_type.max_color
            })
    data['village_paths'] = []
    for village_path in root.village_paths:
        if not village_path.deleted:
            data['village_paths'].append({
                "x_entry": int(village_path.str_x_entry.get()),
                "y_entry": int(village_path.str_y_entry.get()),
                "x_exit": int(village_path.str_x_exit.get()),
                "y_exit": int(village_path.str_y_exit.get())
            })
    with open(json_name, 'w') as outfile:
        json.dump(data, outfile, indent=4)


def set_heights(prio=False, init=False):
    """ set the height of widgets, that need dynamic distribution """

    # get how much space can be distributed to the left an right

    # define left spaces
    if init:
        left_space = root.winfo_screenheight() - icon_frame.winfo_height() - globals_frame.winfo_height() - menu.winfo_height() - bottom_frame.winfo_height() - 180
        right_space = root.winfo_screenheight() - icon_frame.winfo_height() - menu.winfo_height() - bottom_frame.winfo_height() - 180
    else:
        left_space = root.winfo_screenheight() - icon_frame.winfo_height() - globals_frame.winfo_height() - menu.winfo_height() - bottom_frame.winfo_height() - 100
        right_space = root.winfo_screenheight() - icon_frame.winfo_height() - menu.winfo_height() - bottom_frame.winfo_height() - 100
    # set left column
    if prio:
        assets_height = left_space * 0.6
        village_path_height = left_space * 0.2
        left_space_terrain = left_space - assets_height - village_path_height
        terrains_height = left_space_terrain / 2
        root.view = 1
    else:
        assets_height = int(left_space * 0.1)
        village_path_height = int(left_space * 0.1)
        terrains_height = int(left_space * 0.4)
        root.view = 0
    assets_container.canvas.configure(height=assets_height)
    village_path_container.canvas.configure(height=village_path_height)
    river_container.canvas.configure(height=terrains_height)
    mountain_container.canvas.configure(height=terrains_height)

    assets_container.update()
    river_container.update()
    mountain_container.update()
    village_path_container.update()

    # set right column
    right_width = root.winfo_screenwidth() - left_frame.winfo_width() - middle_frame.winfo_width()
    if right_space < right_width:
        root.right_zoom = right_space / 1024
    else:
        root.right_zoom = right_width / 1024

    if root.right_zoom > 1.0:
        root.right_zoom = 1.0
    result_canvas.configure(height=right_space)
    if init:
        try:
            image = Image.open(os.path.join(root.ws_name, PARTIALS, combined_file_name))
            image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
            root.screen = ImageTk.PhotoImage(image)
            result_canvas.create_image(0, 0, anchor='nw', image=root.screen)

            grid_image = Image.open(os.path.join(root.base_dir, "Resources", "grid.png"))
            grid_image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
            root.grid_image = ImageTk.PhotoImage(grid_image)
            root.grid_id = result_canvas.create_image(0, 0, anchor='nw', image=root.grid_image)

            grid_box = Image.open(os.path.join(root.base_dir, "Resources", "hexagon.png"))
            grid_box.thumbnail((int(103 * root.right_zoom), int(90 * root.right_zoom)), Image.ANTIALIAS)
            root.grid_box = ImageTk.PhotoImage(grid_box)

        except OSError:
            print("tried to open ", os.path.join(root.ws_name, PARTIALS, combined_file_name), " but failed")
            root.screen = None


def view_asset_maps(map_file_name, bg_layer="combined.png", second_layer="material_mask.png", overlay=0):
    set_heights(prio=True)

    if overlay == 1:
        image_bg = Image.open(os.path.join(root.ws_name, PARTIALS, bg_layer)).convert("RGBA")
        image_fg = Image.open(os.path.join(root.ws_name, MAPS, map_file_name)).convert("RGBA")
        image = Image.blend(image_bg, image_fg, 0.2)

    elif overlay == 2:
        image_bg = Image.open(os.path.join(root.ws_name, PARTIALS, bg_layer))
        image_fg1 = Image.open(os.path.join(root.ws_name, MAPS, second_layer))
        image_fg2 = Image.open(os.path.join(root.ws_name, MAPS, map_file_name))

        image = Image.blend(image_bg, image_fg1, 0.2)
        image = Image.blend(image, image_fg2, 0.2)
    elif overlay == 3:
        image_bg = Image.open(os.path.join(root.ws_name, PARTIALS, bg_layer)).convert("RGBA")
        image_fg1 = Image.open(os.path.join(root.ws_name, MAPS, "material_mask.png")).convert("RGBA")
        tree_images = []
        tree_images_c = []
        for maps in map_file_name:
            if os.path.isfile(Image.open(os.path.join(root.ws_name, MAPS, maps.file_name))):
                tree_images.append(Image.open(os.path.join(root.ws_name, MAPS, maps.file_name)).convert("L"))
                if len(maps.tree_types) > 0:
                    color = maps.tree_types[0].max_color_hex()
                else:
                    color = "#FFFFFF"
                tree_images_c.append(ImageOps.colorize(tree_images[-1], black="black", white=color, mid=color))
        image_fgc = tree_images_c[0]
        image_fga = tree_images[0]
        if len(tree_images_c) > 1:
            for im_index in range(0, len(tree_images_c)-1):
                image_fgc = Image.composite(image_fgc, tree_images_c[im_index+1], image_fga).convert("RGBA")
                image_fga = Image.composite(image_fga, tree_images[im_index+1], image_fga)

        image_bg = Image.blend(image_bg, image_fg1, 0.2)
        image = Image.composite(image_fgc, image_bg, image_fga)

    elif overlay == 4:
        image_bg = Image.open(os.path.join(root.ws_name, PARTIALS, bg_layer)).convert("RGBA")
        image_fg1 = Image.open(os.path.join(root.ws_name, MAPS, "material_mask.png")).convert("RGBA")
        image_fg2 = Image.open(os.path.join(root.ws_name, MAPS, "berries_density.png")).convert("L")
        image_fg3 = Image.open(os.path.join(root.ws_name, MAPS, "rock_density.png")).convert("L")
        image_fg4 = Image.open(os.path.join(root.ws_name, MAPS, "iron_density.png")).convert("L")
        image_fg5 = Image.open(os.path.join(root.ws_name, MAPS, "fish_density.png")).convert("L")
        image_fg2c = ImageOps.colorize(image_fg2, black="black", white="red")
        image_fg3c = ImageOps.colorize(image_fg3, black="black", white="darkgray")
        image_fg4c = ImageOps.colorize(image_fg4, black="black", white="maroon")
        image_fg5c = ImageOps.colorize(image_fg5, black="black", white="darkblue")
        image_fgc = Image.composite(image_fg2c, image_fg3c, image_fg2).convert("RGBA")
        image_fga = Image.composite(image_fg2, image_fg3, image_fg2)
        image_fgc = Image.composite(image_fgc, image_fg4c, image_fga).convert("RGBA")
        image_fga = Image.composite(image_fga, image_fg4, image_fga)
        image_fgc = Image.composite(image_fgc, image_fg5c, image_fga).convert("RGBA")
        image_fga = Image.composite(image_fga, image_fg5, image_fga)
        image_bg = Image.blend(image_bg, image_fg1, 0.3)
        image = Image.composite(image_fgc, image_bg, image_fga)
    else:
        image = Image.open(os.path.join(root.ws_name, MAPS, map_file_name))

    image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
    root.screen = ImageTk.PhotoImage(image)
    root.view = 1

    grid_image = Image.open(os.path.join(root.base_dir, "Resources", "grid.png"))
    grid_image.thumbnail((int(SCREEN_SIZE * root.right_zoom), int(SCREEN_SIZE * root.right_zoom)), Image.ANTIALIAS)
    root.grid_image = ImageTk.PhotoImage(grid_image)


def import_heightmap():
    global_param.get_heightmap()
    cook_map()


def import_materialmap():
    assets_param.import_materialmap()


def import_berriesmap():
    assets_param.import_berriesmap()


def import_stonemap():
    assets_param.import_stonemap()


def import_oremap():
    assets_param.import_oremap()


def import_fishmap():
    assets_param.import_fishmap()


def cook_win_open():
    cook_win.paths = root.village_paths
    cook_win.toggle_view()




def easy_mode():
    if root.easy.get() == 1:
        global_param.mode_easy()
        assets_param.mode_easy()

        for tree in root.trees:
            tree.mode_easy()
            tree.easy_mode = True
            for tree_type in tree.tree_types:
                tree_type.mode_easy()

        for path in root.village_paths:
            path.mode_easy()

        for mountain in root.mountains:
            mountain.mode_easy()
            mountain.easy_mode = True
            for wp in mountain.wp_list:
                wp.mode_easy()

        for river in root.rivers:
            river.mode_easy()
            river.easy_mode = True
            for wp in river.wp_list:
                wp.mode_easy()

        map_info_win.easy_mode = True
    else:
        assets_param.mode_normal()
        global_param.mode_normal()
        for tree in root.trees:
            tree.mode_normal()
            for tree_type in tree.tree_types:
                tree_type.mode_normal()
        for path in root.village_paths:
            path.mode_normal()
        for mountain in root.mountains:
            mountain.mode_normal()
            for wp in mountain.wp_list:
                wp.mode_normal()
        for river in root.rivers:
            river.mode_normal()
            for wp in river.wp_list:
                wp.mode_normal()

        map_info_win.easy_mode = False

    assets_container.update()
    mountain_container.update()
    river_container.update()
    set_heights(prio=root.view == 1)

def find_starting_tile():
    if root.starting_tile.get() == 1:
        berries_map = Image.open(os.path.join(root.ws_name, MAPS, "berries_density.png"))
        stone_map = Image.open(os.path.join(root.ws_name, MAPS, "rock_density.png"))
        mask = Image.open(os.path.join(root.base_dir, "Resources", "hexagon_mask.png"))

        tree_maps = []
        for tree in root.trees:
            if os.path.isfile(os.path.join(root.ws_name, MAPS, tree.file_name)):
                tree_maps.append(Image.open(os.path.join(root.ws_name, MAPS, tree.file_name)))

        for coord in grid_coords:
            berries_flag = False
            stone_flag = False
            tree_flag = False
            berries_map_masked = berries_map.crop((coord[0], coord[1], coord[0]+103, coord[1]+80))
            berries_map_masked.paste(mask, (0, 0), mask)
            berries_array = numpy.asarray(berries_map_masked.convert("L"))
            stone_map_masked = stone_map.crop((coord[0], coord[1], coord[0] + 103, coord[1] + 80))
            stone_map_masked.paste(mask, (0, 0), mask)
            stone_array = numpy.asarray(stone_map_masked.convert("L"))
            tree_maps_masked = []
            tree_arrays = []
            for tree_map in tree_maps:
                tree_maps_masked.append(tree_map.crop((coord[0], coord[1], coord[0]+103, coord[1]+80)))
                tree_maps_masked[-1].paste(mask, (0, 0), mask)
                tree_arrays.append(numpy.asarray(tree_maps_masked[-1].convert("L")))

            for y_i in range(0, 102):
                for x_i in range(0, 79):
                    if berries_array[x_i, y_i] > 100:
                        berries_flag = True
                    if stone_array[x_i, y_i] > 100:
                        stone_flag = True
                    for tree_array in tree_arrays:
                        if tree_array[x_i, y_i] > 50:
                            tree_flag = True

            #if berries_flag and stone_flag:
                #pp.imshow(berries_array)
                #pp.show()

            coord[2] = berries_flag and stone_flag and tree_flag

def preview_3d():
    show_heightmap = numpy.copy(root.heightmap)
    show_heightmap = numpy.interp(show_heightmap, (show_heightmap.min(), show_heightmap.max()), (0, int(map_info_win.str_height.get())))
    show_heightmap = numpy.flip(show_heightmap, axis=0)
    watermap = numpy.full((1024, 1024), int(map_info_win.str_water_level.get()))
    delta = float(assets_param.int_grass_sigma.get())
    sand_start = (float(assets_param.int_grass_level.get()) - assets_param.int_grass_delta.get()) / 1000
    sand_end = (float(assets_param.int_grass_level.get()) + assets_param.int_grass_delta.get()) / 1000
    scale = [(0, "wheat"), (sand_start, "wheat"), (sand_end, "green"), (1, "green")]
    fig = go.Figure(data=[go.Surface(z=show_heightmap, colorscale=scale),
                          go.Surface(z=watermap, colorscale="blues", showscale=False, opacity=0.8)])

    fig.update_layout(title='3d Preview', autosize=False,
                      template="plotly_dark",
                      width=1500, height=1024,
                      margin=dict(l=65, r=50, b=65, t=90))
    fig.update_layout(scene={"aspectratio": {"x": 1, "y": 1, "z": 0.2}})
    fig.show()

def open_explorer():
    subprocess.Popen('explorer "' + os.path.realpath(os.path.join(root.ws_name)) + '"')

# -- toplevel menues

print("building menues")
cook_win = gui.CookWin(os.path.dirname(os.path.realpath(__file__)), [], cook_map, gui.AssetParams, map_info_win,
                       gui.GlobalParams, root.rivers, root.mountains, root.village_paths, labels)
cook_win.withdraw()
menu = tk.Menu(root)
root.config(menu=menu)
file_menu = tk.Menu(menu)
import_menu = tk.Menu(menu)
add_menu = tk.Menu(menu)
gen_menu = tk.Menu(menu)
help_menu = tk.Menu(menu)
view_menu = tk.Menu(menu)
prio_menu = tk.Menu(menu)
overlay_menu = []
for menus in range(0, 8):
    overlay_menu.append(tk.Menu(menu))

menu.add_cascade(label=labels["File_Menu"], menu=file_menu)
# file_menu.add_command(label="New", command=load_json)
file_menu.add_command(label=labels["New_Menu"], command=new_workspace)
file_menu.add_command(label=labels["Load_Menu"], command=load_workspace)
file_menu.add_command(label=labels["Save_Menu"], command=save_workspace)
file_menu.add_command(label=labels["Show_Expl_Menu"], command=open_explorer)
file_menu.add_separator()
file_menu.add_command(label=labels["Imp_Param_Menu"], command=import_json)
file_menu.add_command(label=labels["Exp_Param_Menu"], command=export_json)
file_menu.add_cascade(label=labels["Imp_Menu"], menu=import_menu)
import_menu.add_command(label=labels["Imp_Hmap_Menu"], command=import_heightmap)
import_menu.add_command(label=labels["Imp_Mmap_Menu"], command=import_materialmap)
import_menu.add_command(label=labels["Imp_Bmap_Menu"], command=import_berriesmap)
import_menu.add_command(label=labels["Imp_Smap_Menu"], command=import_stonemap)
import_menu.add_command(label=labels["Imp_Imap_Menu"], command=import_oremap)
import_menu.add_command(label=labels["Imp_Fmap_Menu"], command=import_fishmap)
file_menu.add_separator()
file_menu.add_command(label=labels["Map_Info_Menu"], command=map_info_win.toggle_view)
file_menu.add_command(label=labels["Exit_Menu"], command=root.quit)

menu.add_cascade(label=labels["Add_Menu"], menu=add_menu)
add_menu.add_command(label=labels["Add_River_Menu"], command=add_river)
add_menu.add_command(label=labels["Add_Mountain_Menu"], command=add_mountain)
add_menu.add_separator()
add_menu.add_command(label=labels["Add_Tree_Menu"], command=add_tree)
add_menu.add_command(label=labels["Add_Path_Menu"], command=add_village_path)

menu.add_cascade(label=labels["Build_Menu"], menu=gen_menu)
# gen_menu.add_command(label="update Poly Preview", command=draw_screen)
gen_menu.add_command(label=labels["Build_Hmap_Menu"], command=cook_map)
gen_menu.add_command(label=labels["Build_Amap_Menu"], command=lambda: gen_asset_maps(assets_param))
gen_menu.add_command(label=labels["Cook_Menu"], command=cook_win.toggle_view)

menu.add_cascade(label=labels["Help_Menu"], menu=help_menu)
help_menu.add_command(label=labels["About_Menu"], command=about_win.toggle_view)


menu.add_cascade(label=labels["View_Menu"], menu=view_menu)
view_menu.add_cascade(label=labels["View_Prio_Menu"], menu=prio_menu)
prio_menu.add_command(label=labels["View_Assets_Menu"], command=lambda: set_heights(prio=True))
prio_menu.add_command(label=labels["View_Terrain_Menu"], command=lambda: set_heights())
view_menu.add_checkbutton(label=labels["View_Path_Menu"], onvalue=1, offvalue=0, variable=root.path_show)
view_menu.add_checkbutton(label=labels["View_Easy_Menu"], onvalue=1, offvalue=0, variable=root.easy, command=easy_mode)
view_menu.add_checkbutton(label=labels["View_Hex_Menu"], onvalue=1, offvalue=0, variable=root.grid)
view_menu.add_checkbutton(label=labels["View_Starting_Menu"], onvalue=1, offvalue=0, variable=root.starting_tile, command=find_starting_tile)
view_menu.add_command(label=labels["View_3D_Menu"], command=preview_3d)
view_menu.add_cascade(label=labels["View_MMask_Menu"], menu=overlay_menu[0])
overlay_menu[0].add_command(label=labels["View_MMask_Menu"], command=lambda: view_asset_maps("material_mask.png", overlay=0))
overlay_menu[0].add_command(label=labels["Overlay"], command=lambda: view_asset_maps("material_mask.png", overlay=1))
view_menu.add_cascade(label=labels["View_Tree_Menu"], menu=overlay_menu[1])
overlay_menu[1].add_command(label=labels["Tree_Comb_Menu"], command=lambda: view_asset_maps(root.trees, overlay=3))
overlay_menu[1].add_separator()
# submenu is generated, when TreeMap is added
view_menu.add_cascade(label=labels["View_Res_Menu"], menu=overlay_menu[2])
overlay_menu[2].add_command(label=labels["Res_Comb_Menu"], command=lambda: view_asset_maps("berries_density.png", overlay=4))
overlay_menu[2].add_separator()
overlay_menu[2].add_command(label=labels["Res_Berries_Menu"], command=lambda: view_asset_maps("berries_density.png", overlay=0))
overlay_menu[2].add_command(label=labels["Berries_Comb_Menu"], command=lambda: view_asset_maps("berries_density.png", overlay=1))
overlay_menu[2].add_command(label=labels["Berries_Mat_Menu"], command=lambda: view_asset_maps("berries_density.png", overlay=2))
overlay_menu[2].add_separator()
overlay_menu[2].add_command(label=labels["Res_Stone_Menu"], command=lambda: view_asset_maps("rock_density.png", overlay=0))
overlay_menu[2].add_command(label=labels["Stone_Comb_Menu"], command=lambda: view_asset_maps("rock_density.png", overlay=1))
overlay_menu[2].add_command(label=labels["Stone_Mat_Menu"], command=lambda: view_asset_maps("rock_density.png", overlay=2))
overlay_menu[2].add_separator()
overlay_menu[2].add_command(label=labels["Res_Ore_Menu"], command=lambda: view_asset_maps("iron_density.png", overlay=0))
overlay_menu[2].add_command(label=labels["Ore_Comb_Menu"], command=lambda: view_asset_maps("iron_density.png", overlay=1))
overlay_menu[2].add_command(label=labels["Ore_Mat_Menu"], command=lambda: view_asset_maps("iron_density.png", overlay=2))
overlay_menu[2].add_separator()
overlay_menu[2].add_command(label=labels["Res_Fish_Menu"], command=lambda: view_asset_maps("fish_density.png", overlay=0))
overlay_menu[2].add_command(label=labels["Fish_Comb_Menu"], command=lambda: view_asset_maps("fish_density.png", overlay=1))
overlay_menu[2].add_command(label=labels["Fish_Mat_Menu"], command=lambda: view_asset_maps("fish_density.png", overlay=2))

print("building frames")
# -- Basic three Areas on Screen
top_frame = tk.Frame(root, relief=tk.GROOVE, borderwidth=1)
top_frame.grid(column=0, row=0, sticky='nwe')

main_frame = tk.Frame(root)
main_frame.grid(column=0, row=1, sticky='w')

# reshaping main grid
main_frame.grid_columnconfigure(0, minsize=200)
main_frame.grid_columnconfigure(1, minsize=200)
main_frame.grid_columnconfigure(2, minsize=1024)

bottom_frame = tk.Frame(root, relief=tk.GROOVE, borderwidth=1)
bottom_frame.grid(column=0, row=2, sticky='we')

# Left Frame
left_frame = tk.Frame(main_frame, relief=tk.GROOVE, borderwidth=1)
left_frame.grid(column=0, row=0, sticky='nwse')

# middle Frame
middle_frame = tk.Frame(main_frame, relief=tk.GROOVE, borderwidth=1)
middle_frame.grid(column=1, row=0, sticky='nwse')

pre_label = tk.Label(middle_frame, text="Preview")
pre_label.pack(side='top')

# container Frame
middle_container = gui.Scrollable(middle_frame, width=16)
middle_container.canvas.configure(width=260)
preview_canvas = tk.Canvas(middle_container, width=200, height=800)
preview_canvas.pack(side='left', expand=True, fill='both')

# right frame
right_frame = tk.Frame(main_frame, relief=tk.GROOVE, borderwidth=1)
right_frame.grid(column=2, row=0, sticky='nwse')

# hosting results
result_canvas = tk.Canvas(right_frame, height=1024, width=1024)
result_canvas.pack()
result_canvas.bind('<Motion>', motion)

# all objects for the left Row: 
# first frame is hosting the add buttons to add mountains and rivers
add_frame = tk.Frame(top_frame)
icon_frame = tk.Frame(top_frame)
icon_frame.grid(column=0, row=0, sticky='w')

new_ws_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "new20x20.png"))
new_ws_btn = tk.Button(icon_frame, image=new_ws_image, command=new_workspace)
new_ws_btn.grid(column=0, row=0, sticky='w', padx=2)
new_ws_tt = gui.CreateToolTip(new_ws_btn, labels["new_ws_tt"])
load_ws_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "load20x20.png"))
load_ws_btn = tk.Button(icon_frame, image=load_ws_image, command=load_workspace)
load_ws_btn.grid(column=1, row=0, sticky='w', padx=2)
load_ws_tt = gui.CreateToolTip(load_ws_btn, labels["load_ws_tt"])
save_ws_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "save20x20.png"))
save_ws_btn = tk.Button(icon_frame, image=save_ws_image, command=save_workspace)
save_ws_btn.grid(column=2, row=0, sticky='w', padx=2)
save_ws_tt = gui.CreateToolTip(save_ws_btn, labels["save_ws_tt"])
import_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "import20x20.png"))
import_btn = tk.Button(icon_frame, image=import_image, command=import_json)
import_btn.grid(column=3, row=0, sticky='w', padx=2)
import_tt = gui.CreateToolTip(import_btn, labels["imp_json_tt"])
export_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "export20x20.png"))
export_btn = tk.Button(icon_frame, image=export_image, command=export_json)
export_btn.grid(column=4, row=0, sticky='w', padx=2)
export_tt = gui.CreateToolTip(export_btn, labels["exp_json_tt"])
mountain_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "mountain20x20.png"))
mountain_btn = tk.Button(icon_frame, image=mountain_image, command=add_mountain)
mountain_btn.grid(column=5, row=0, sticky='w', padx=2)
mountain_tt = gui.CreateToolTip(mountain_btn, labels["mountain_tt"])
river_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "river20x20.png"))
river_btn = tk.Button(icon_frame, image=river_image, command=add_river)
river_btn.grid(column=6, row=0, sticky='w', padx=2)
river_tt = gui.CreateToolTip(river_btn, labels["river_tt"])
tree_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "tree20x20.png"))
tree_btn = tk.Button(icon_frame, image=tree_image, command=add_tree)
tree_btn.grid(column=7, row=0, sticky='w', padx=2)
tree_tt = gui.CreateToolTip(tree_btn, labels["tree_tt"])
path_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "path20x20.png"))
path_btn = tk.Button(icon_frame, image=path_image, command=add_village_path)
path_btn.grid(column=8, row=0, sticky='w', padx=2)
path_tt = gui.CreateToolTip(path_btn, labels["path_tt"])
build_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "build20x20.png"))   # command via configure
build_btn = tk.Button(icon_frame, image=build_image, command=cook_map)
build_btn.grid(column=9, row=0, sticky='w', padx=2)
build_tt = gui.CreateToolTip(build_btn, labels["build_tt"])
cook_image = ImageTk.PhotoImage(file=os.path.join(root.base_dir, "Resources", "cook20x20.png"))
cook_btn = tk.Button(icon_frame, image=cook_image, command=cook_win_open)
cook_btn.grid(column=10, row=0, sticky='w', padx=2)
cook_tt = gui.CreateToolTip(cook_btn, labels["cook_tt"])

add_frame_height = add_frame.winfo_height()

# second frame will host baseline
globals_frame = tk.Frame(left_frame)
globals_frame.grid(column=0, row=1, sticky='we')
global_param = gui.GlobalParams(globals_frame, preview_canvas, 100, 500, 100, 10, 5, root.ws_name,
                                easy_mode=root.easy.get() == 1, labels=labels)
cook_win.globals = global_param

# assets
assets_frame = tk.Frame(left_frame)
assets_frame.grid(column=0, row=2, sticky='we')
assets_container = gui.Scrollable(assets_frame, width=16)
assets_canvas = tk.Frame(assets_container)
assets_canvas.pack(side='left', expand=True, fill='both')
assets_param = gui.AssetParams(assets_canvas, preview_canvas, root.ws_name,
                               easy_mode=root.easy.get() == 1, labels=labels)
map_info_win.mmap_height = assets_param.int_grass_level
cook_win.assets_handle = assets_param

# Village Pathes
village_path_frame = tk.Frame(left_frame)
village_path_frame.grid(column=0, row=3, sticky='we')
village_path_container = gui.Scrollable(village_path_frame, width=16)
village_path_canvas = tk.Frame(village_path_container)
village_path_canvas.pack(side='left', expand=True, fill='both')

# all rivers
river_frame = tk.Frame(left_frame)
river_frame.grid(column=0, row=4, sticky='nwes')
river_container = gui.Scrollable(river_frame, width=16)
river_canvas = tk.Frame(river_container)
river_canvas.pack(side='left', expand=True, fill='both')

# all mountains
mountain_frame = tk.Frame(left_frame)
mountain_frame.grid(column=0, row=5, sticky="nwes")
mountain_container = gui.Scrollable(mountain_frame, width=16)
mountain_canvas = tk.Canvas(mountain_container)
mountain_canvas.pack(side='left', expand=True, fill='both')

river_container.canvas.configure(width=300)
mountain_container.canvas.configure(width=300)
assets_container.canvas.configure(width=340)
village_path_container.canvas.configure(width=300)
# to display multiple images, and not to have the images garbage collected, here are two lists to put them
preview_canvas.river_im = []
preview_canvas.mountain_im = []

# Bottom Frame

status_label = tk.Label(bottom_frame, text="Status: ", anchor='w')
status_label.grid(column=0, row=0, sticky='w')

status_output = tk.Label(bottom_frame, text=" --- ", anchor='w')
status_output.grid(column=1, row=0, sticky='w')

status_position = tk.Label(bottom_frame, text="x: y: h:", anchor='w', width=18, relief=tk.GROOVE, bd=1)
status_position.grid(column=2, row=0, sticky='e')

status = gui.Status("", status_output, 250)
status.print("loaded GUI")

bottom_frame.columnconfigure(1, minsize=root.winfo_screenwidth()-180)
root.heightmap = assets_param.load_heightmap()
set_heights(prio=True, init=True)
refresh_screen()
print("Entering main loop ------------ ")
root.mainloop()
