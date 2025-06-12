from ee_wildfire.UserInterface import map_maker
from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from ee_wildfire.command_line_args import parse
from ee_wildfire.constants import *
from shapely.geometry import Polygon

import ee

uf = parse()
uf.authenticate()

ConsoleUI.setup_logging(DEFAULT_LOG_DIR, "fire_config_test")
map_maker.setup_logging(uf)
map_maker.get_map_html()

coords = map_maker.launch_draw_map()
print(coords)
img = ee.Geometry.Polygon(coords)
map_maker.show_bbox_on_map(img)

poly = Polygon(coords[0])
assert poly.is_valid, "invalid polygon"
assert poly.exterior.is_closed, "polygon not closed"






