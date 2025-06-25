from dash import Dash 
import dirspec_layout
from callbacks import register_callbacks

# initialize the app
app = Dash((__name__), suppress_callback_exceptions=True)
app.title = "Wave Spectral Dashboard"
app.layout = dirspec_layout.layout

register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)