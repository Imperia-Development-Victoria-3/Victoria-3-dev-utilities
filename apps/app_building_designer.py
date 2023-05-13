from dash import Dash, dcc, html, Input, Output, Patch, dash_table, State
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme, Trim

from parse_encoder import parse_text_file, parse_text
from data_utils.transformation import TransformNoInverse, Percentage, PriceCompensation
from dash.exceptions import PreventUpdate
from data_formats import Goods, PopNeeds, DashBuyPackages

from app import app

layout = [

]
