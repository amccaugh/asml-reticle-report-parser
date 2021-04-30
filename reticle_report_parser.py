#%%
from __future__ import division, print_function, absolute_import
import numpy as np
import re
import os

localdir = r'G:\My Drive\NIST Work\161214 ASML Stepper Python Parsing'
report_in_filename = 'reticleset_report_input.txt'
report_out_filename = 'reticleset_report_parsed.txt'
report_in_filepath = os.path.join(localdir, report_in_filename)
report_out_filepath = os.path.join(localdir, report_out_filename)
#layers = {
#        'pads' : Layer(gds_layer = 1, gds_datatype = 0, description = 'Nb wiring', color = 'gold'),
#        'gnd' : Layer(gds_layer = 1, gds_datatype = 99, description = 'Nb wiring gnd', color = 'gray'),
#        'wsi_optical'  : Layer(gds_layer = 2, gds_datatype = 0, description = 'WSi etch', color = 'lightgreen', inverted = True),
#        'wsi_ebeam1'  : Layer(gds_layer = 100, gds_datatype = 0, description = 'WSi etch', color = 'orange', inverted = False),
#        'wsi_ebeam2'  : Layer(gds_layer = 101, gds_datatype = 0, description = 'WSi etch', color = 'orange', inverted = False),
#        'wsi_ebeam3'  : Layer(gds_layer = 102, gds_datatype = 0, description = 'WSi etch', color = 'orange', inverted = False),
#        'via' : Layer(gds_layer = 3, gds_datatype = 0, description = 'interlayer via', color = 'lightpink'),
#        'res'  : Layer(gds_layer = 4, gds_datatype = 0, description = 'Heating resistor', color = 'red'),
#        'pads_upper' : Layer(gds_layer = 5, gds_datatype = 0, description = 'Heating resistor', color = 'goldenrod'),
#         }

         
gdslayer_to_layerid = {
#        1: 'pads',
#        2: 'nw',
#        3: 'via',
#        4: 'cnt',
        
                       101 : '1_nw',
                       102 : '2_nwpad',
                       103 : '3_v3',
                       104 : '6_nw2',
                       105 : '4_res',
                       106 : '5_wiring',
                       }


with open(report_in_filepath, 'r') as myfile:
    reticle_report = myfile.read()

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

# Make sure it's ordered by layer number
gdslayer_to_layerid = collections.OrderedDict(sorted(gdslayer_to_layerid.items(), key=lambda t: t[0]))


#==============================================================================
# Sort images by layer
#==============================================================================
images = parse_reticle_report(reticle_report)

images_by_layer = {}
gds_layers_in_images = list([i.gds_layer for i in images])
for gds_layer in gds_layers_in_images:
    images_by_layer[gds_layer] = [i for i in images if i.gds_layer == gds_layer]

#==============================================================================
# Print output to clipboard for pasting
#==============================================================================
output = '[code]\n'
output += '-- LAYER DEFINITION --'
for gds_layer, layer_id in gdslayer_to_layerid.items():
    output += '\n \n' + '- Layer Number: %s' % gds_layer
    output += '\n' + '  - Layer ID: %s' % layer_id.upper()
    
output += '\n \n \n '
output += '\n' + '-- RETICLE DATA --'
for layer_num, images in images_by_layer.items():
    output += '\n' + '\nLayer: %s\n' % gdslayer_to_layerid[layer_num].upper()
    for i in images:
        output += '\n' + ' - Image: %s' % i.die_name
        output += '\n' + '    - Reticle ID: %s' % i.reticle_name
        output += '\n' + '    - Image Shift: ( %+g, %+g )' % i.coords
        output += '\n '
output += ' \n[/code]'
        
from tkinter import Tk
r = Tk()
r.withdraw()
r.clipboard_clear()
r.clipboard_append(output)
r.destroy()


with open(report_out_filepath, 'w') as myfile:
    reticle_report = myfile.write(output)