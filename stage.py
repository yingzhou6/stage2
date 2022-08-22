import pandas as pd
import numpy as np
from datetime import datetime,timedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px

sentiment = pd.read_csv('Sentiment_Data_File_Daily.csv')
covid_dates = pd.read_csv('covid_timeline.csv')
sentiment = sentiment.dropna().reset_index()

sent_mean=np.mean(sentiment.Sentiment)
sent_std=np.std(sentiment.Sentiment)
maxnews=30

upper_bound = sent_mean+3*sent_std
lower_bound = sent_mean-3*sent_std

key_date = []
for i in range(len(sentiment.Sentiment)):
    if (sentiment.Sentiment)[i] > upper_bound or (sentiment.Sentiment)[i] < lower_bound:
        if sentiment.Sentiment_News_Volume[i]>maxnews:
            key_date.append(sentiment.Timestamp[i])

key_date1 = covid_dates['Timestamp']
new_key_dates = list(map(lambda x : datetime.strptime(x,'%Y-%m-%d').date(),key_date1))

sentiment.Timestamp=pd.to_datetime(sentiment.Timestamp)
sentiment.Timestamp= sentiment.Timestamp.apply(lambda x: x.date())


coviddict = {}
for i in new_key_dates:
    range_up = i+timedelta(3)
    range_low = i-timedelta(3)
    time_range=sentiment[(sentiment.Timestamp<=range_up) & (sentiment.Timestamp>=range_low)]
    rangedict = {}
    for j in time_range.Ticker.unique():
        score = np.abs(time_range[time_range['Ticker']==j]['Sentiment'])
        real_range = (np.max(score)-np.min(score))
        rangedict[j]=real_range
    sort={n: m for n, m in sorted(rangedict.items(), key=lambda x: x[1],reverse=True)}
    sort_ten={n:m for n,m in list(sort.items())[:11]}
    coviddict[i]=sort_ten

company_list={n:pd.DataFrame(m,index=['score']).transpose().reset_index() for n,m in coviddict.items()}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}])

server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Covid Sentiment",
                        className='text-center text-primary, mb-3'),
                width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.P('Select Date:', style={'textDecoration': 'underline'}),
            dcc.Dropdown(id='my-company', multi=False, value=new_key_dates[0],
                         options=[{'label': x, 'value': x}
                                  for x in new_key_dates]),
            dcc.Graph(id='fig1', figure={})
        ], width={'size': 20}),
        dbc.Row([
            dbc.Col([
                html.P('Select Date:', style={'textDecoration': 'underline'}),
                dcc.Dropdown(id='my-date', multi=False, value=new_key_dates[0],
                             options=[{'label': x, 'value': x}
                                      for x in new_key_dates]),
                dcc.Graph(id='fig2', figure={})
            ], width={'size': 20}),

        ])
    ])])


@app.callback(
    Output('fig1', 'figure'),
    Input('my-company', 'value')
)
def update_graph(com):
    date = datetime.strptime(com, '%Y-%m-%d').date()
    data = company_list[date]
    fighist = px.scatter_polar(data, r=data['score'], theta=data['index'])
    return fighist


@app.callback(
    Output('fig2', 'figure'),
    Input('my-date', 'value')
)
def update_graph(com):
    date = datetime.strptime(com, '%Y-%m-%d').date()
    data = company_list[date]
    fighist = px.histogram(x=data['index'], y=data['score'])
    return fighist


if __name__ == '__main__':
    app.run_server(debug=False, port=3000)
