import dash
from dash import html
from dash import dcc
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

df = pd.DataFrame({
    "Frequency (Hz)": [0.05, 0.1, 0.15, 0.2],
    "Energy (m²/Hz)": [0.2, 0.5, 0.4, 0.3]
})

fig = px.bar(df, x="Frequency (Hz)", y="Energy (m²/Hz)")

app.layout = html.Div([
    html.H2("Energy Spectrum"),
    dcc.Graph(figure=fig)
])

if __name__ == '__main__':
    app.run(debug=True)