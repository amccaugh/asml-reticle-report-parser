from __future__ import division, print_function, absolute_import
import numpy as np
import re



reticle_report = """

Reticle SE016-Y-00  (for ASML 5500/100D)
Runtime: 2 hours 11 minutes
    Cell name:toplevel  GDS File: SE016 yTron ebeam variations.gds
    Layer Name:0000 Layer Number: 0 Tone: not inverted  Mirrored: no
    Reticle position name: A
    Center coordinates: x=-28.6 y=28.6
    Image Size: width=50 height=50

    Cell name:toplevel  GDS File: SE017 SNSPD Integrator.gds
    Layer Name:0000 Layer Number: 0 Tone: not inverted  Mirrored: no
    Reticle position name: B
    Center coordinates: x=28.6 y=28.6
    Image Size: width=50 height=50

    Cell name:toplevel  GDS File: SE016 yTron ebeam variations.gds
    Layer Name:0200 Layer Number: 2 Tone: not inverted  Mirrored: no
    Reticle position name: C
    Center coordinates: x=-28.6 y=-28.6
    Image Size: width=50 height=50

    Cell name:toplevel  GDS File: SE017 SNSPD Integrator.gds
    Layer Name:0200 Layer Number: 2 Tone: not inverted  Mirrored: no
    Reticle position name: D
    Center coordinates: x=28.6 y=-28.6
    Image Size: width=50 height=50


"""
import collections

ReticleImage = collections.namedtuple('Image', ['reticle_name','die_name', 'gds_layer', 'inverted',
                                         'coords', 'image_size'])

# Extracts information from the reticle report starting from "Cell name:"
def parse_cell_text(reticle_name, cell_text):
    die = re.search("GDS File: (.*)", cell_text).group(1)
    gds_layer = int(re.search("Layer Number: (.*) Tone:", cell_text).group(1))
    tone = re.search("Tone: (.*) Mirrored:", cell_text).group(1)
    inverted = (tone == 'inverted')
    r = re.search("Center coordinates: x=(.*) y=(.*)", cell_text)
    reticle_coords = (float(r.group(1)), float(r.group(2)))
    r = re.search("Image Size: width=(.*) height=(.*)", cell_text)
    image_size = (float(r.group(1)), float(r.group(2)))
    return reticle_name, die, gds_layer, inverted, reticle_coords, image_size

def parse_reticle_report(reticle_report):
    # Split up reticle report into individual reticles
    reticle_report = reticle_report.strip()
    split_string = list(re.split("Reticle (.*) \(for ASML 5500/100D\)", reticle_report))
    split_string = list(filter(None, split_string))
    
    reticle_names = split_string[::2]
    reticle_texts = split_string[1::2]
    
    images = []
    for n, reticle_name  in enumerate(reticle_names):
        text = reticle_texts[n]
        
        cells = re.split("Cell name:", text)
        cells = list(filter(None, cells))
        cells = cells[1:]
        images += [ReticleImage(*parse_cell_text(reticle_name, cell)) for cell in cells]
#        r = Reticle(name = reticle_name, images = images)
#        images.append(r)

    return images

#==============================================================================
# Create gds_layer to Layer ID mapping
#==============================================================================
layers = {
        'nb' : Layer(gds_layer = 0, gds_datatype = 0, description = 'Niobium wiring', color = 'grey'),
        'nb_gnd' : Layer(gds_layer = 0, gds_datatype = 1, description = 'Niobium ground', color = 'grey'),
        'wsi'  : Layer(gds_layer = 200, gds_datatype = 0, description = 'WSi', color = 'lightgreen'),
        'res'  : Layer(gds_layer = 2, gds_datatype = 0, description = 'AuPd resistors', color = 'DarkGoldenRod'),
        'nb_fill' : Layer(gds_layer = 0, gds_datatype = 99, description = 'Niobium wiring', color = 'grey'),
        'res_fill'  : Layer(gds_layer = 2, gds_datatype = 99, description = 'AuPd resistors', color = 'DarkGoldenRod'),
        'ebeam'  : Layer(gds_layer = 101, gds_datatype = 0, description = 'WSi ZEP mask (ebeam)', color = 'lightblue'),
         }
         
gdslayer_to_layerid = {
                       0 : 'nb',
                       2 : 'res',
                       }
# Make sure it's ordered by layer number
gdslayer_to_layerid = collections.OrderedDict(sorted(gdslayer_to_layerid.items(), key=lambda t: t[0]))


#==============================================================================
# Sort images by layer
#==============================================================================
images = parse_reticle_report(reticle_report)

images_by_layer = {}
gds_layers_in_images = set([i.gds_layer for i in images])
for gds_layer in gds_layers_in_images:
    images_by_layer[gds_layer] = [i for i in images if i.gds_layer == gds_layer]

#==============================================================================
# Print output to clipboard for pasting
#==============================================================================
output = ''
output += '-- LAYER DEFINITION --'
for gds_layer, layer_id in gdslayer_to_layerid.items():
    output += '\n' + '- Layer Number: %s' % gds_layer
    output += '\n' + '  - Layer ID: %s' % layer_id.upper()
    
output += '\n' + '\n'
output += '\n' + '-- RETICLE DATA --'
for layer_num, images in images_by_layer.items():
    output += '\n' + '\nLayer: %s\n' % gdslayer_to_layerid[layer_num].upper()
    for i in images:
        output += '\n' + ' - Image: %s' % i.die_name
        output += '\n' + '   - Reticle ID: %s' % i.reticle_name
        output += '\n' + '   - Image Shift: ( %+g, %+g )' % i.coords
        output += '\n'
    
        
from tkinter import Tk
r = Tk()
r.withdraw()
r.clipboard_clear()
r.clipboard_append(output)
r.destroy()