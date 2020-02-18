WHAT IS IT:
Its a map generator for the game Foundation. 
The final project will consist of two units: the first one generates a heightmap from a jsonc file,
the second unit will generate all nesseccary maps from a heightmap (like berries, stone, fish, ore )

WHATS THE STATUS:
its Work In Progress

WHAT ARE THE FILES:

assets - is a library for generating all those asset maps from the heightmap
terrain - is a library for all types of terrain for generation
map_gen - is basically a test map to test and watch new functions
TerrainObjectList - is the sample jsonc that can be adjusted for the heightmap generation process
gen_heightmap - generates a heightmap from the TerrainObjectList.jsonc file 
gen_assetmaps - generates assetmaps from the TerrainObjectList.jsonc file 
HOW TO GENERATE A HEIGHTMAP

Adjust the TerrainObjectList.jsonc file to your wishes, run the gen_heightmap.py file

HOW TO GENERATE ASSET MAPS

Adjust the TerrainObjectList.jsonc file to your wishes,run the gen_assetmaps.py file
