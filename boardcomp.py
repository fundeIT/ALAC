from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

import monitoring.website

def generate_figure():
    data = monitoring.website.count_hits()
    data['month'] = data['month'].apply(lambda s: 'M' + s[:4] + '-' + s[4:])
    fig = {
        'data': [go.Bar(x=data['month'].values, y=data['hits'])],
        'layout' : go.Layout(
            xaxis = {
                'title': 'Meses',
            },
            yaxis = {
                'title': 'Hits',
            },
        ),
    }
    return fig

def make_figure():
    return html.Div([
        dcc.Graph(
            id = 'website_usage_plot',
            figure = generate_figure(),
        )
    ])
    
layout = dbc.Container([
    dbc.Row(dbc.Col(html.H3('Uso del sitio web'))),
    dbc.Row(dbc.Col([make_figure()])),
    dbc.Row([
        dbc.Col(html.A(
            'Descargar CSV',
            href='/api/v1/admin/website_usage',
            download='budget.csv',
            id='download_csv',
            className='btn btn-primary'
        ), className='text-center'),
    ])
])
