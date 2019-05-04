import collections
import yaml
from os.path import join, dirname

static_dir = join(dirname(__file__), "static")

with open(join(static_dir, "columns.yml"), 'r') as f:
    quantity_list = yaml.load(f)

quantities = collections.OrderedDict([(q['column'], q) for q in quantity_list])

plot_quantities = [ q for q in quantities.keys() if quantities[q]['type'] == 'float' ]

group_dict = collections.OrderedDict([
    ('cof', "#1f77b4"),
    ('mof', "#d62728"),
    ('zeolite', "#ff7f0e"),
    ('sampled', "#2ca02c"),
])

with open(join(static_dir, "filters.yml"), 'r') as f:
    filter_list = yaml.load(f)

with open(join(static_dir, "presets.yml"), 'r') as f:
    presets = yaml.load(f)

for k in presets.keys():
    if 'clr' not in presets[k].keys():
        presets[k]['clr'] = presets['default']['clr']

max_points = 70000
