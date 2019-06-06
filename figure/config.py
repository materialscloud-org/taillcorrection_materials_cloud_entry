import collections
import yaml
from os.path import join, dirname
from bokeh.colors import RGB

static_dir = join(dirname(__file__), "static")

with open(join(static_dir, "columns.yml"), "r") as f:
    quantity_list = yaml.load(f)

quantities = collections.OrderedDict([(q["column"], q) for q in quantity_list])

plot_quantities = [q for q in quantities.keys() if quantities[q]["type"] == "float"]

group_dict = collections.OrderedDict(
    [
        ("COFs", RGB(31, 119, 180, 0.5)),  # #1f77b4
        ("MOFs", RGB(44, 160, 44, 0.5)),  # #2ca02c
        ("zeolites", RGB(255, 127, 14, 0.5)),  # #ff7f0e
    ]
)

sampled_dict = collections.OrderedDict(
    [("sampled", RGB(0, 0, 0, 1)), ("not sampled", RGB(0, 0, 0, 0))]
)

with open(join(static_dir, "filters.yml"), "r") as f:
    filter_list = yaml.load(f)

with open(join(static_dir, "presets.yml"), "r") as f:
    presets = yaml.load(f)

for k in presets.keys():
    if "clr" not in presets[k].keys():
        presets[k]["clr"] = presets["default"]["clr"]

max_points = 70000

unit_dict = {"loading": "molecules / UC"}
