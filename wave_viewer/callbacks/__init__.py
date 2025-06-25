from .map_callbacks import register_map_callbacks
from .plot_callbacks import register_plot_callbacks

def register_callbacks(app):
    register_map_callbacks(app)
    register_plot_callbacks(app)
