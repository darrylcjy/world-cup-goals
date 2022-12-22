from dash import Dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np

##### Functions #####

def query(data, start, end, stage):  # filtering out relevant data based on the specified conditions
    min_year = start
    max_year = end
    which_stage = stage
    
    if which_stage == "All":
        query_df = data[(data["year"]>=min_year) & (data["year"]<=max_year)]  # show stats for all stages
    else:
        query_df = data[(data["year"]>=min_year) & (data["year"]<=max_year) & (data["stage"]==which_stage)]  # show stats for specific stage (eg. finals)

    return query_df

def over_goals(df, period):  # to prepare dataframe for creating datatable
    if period == "ft":
        goal_count = df.groupby("ft_total_goals").count()[["year"]]
    elif period == "ht":
        goal_count = df.groupby("ht_total_goals").count()[["year"]]
    goal_dist = list(goal_count.to_dict()["year"].items())
    goal_cum = []
    total_games = goal_count["year"].sum()
    for i in range(5):  # --> over0.5, over1.5, over2.5, over3.5, over4.5
        cumsum = 0
        for item in goal_dist:
            if item[0] > i:
                cumsum += item[1]
        goal_cum.append(cumsum)
        
    goal_table = pd.DataFrame([("Over 0.5", goal_cum[0]),
                              ("Over 1.5", goal_cum[1]),
                              ("Over 2.5", goal_cum[2]),
                              ("Over 3.5", goal_cum[3]),
                              ("Over 4.5", goal_cum[4]),],
                             columns=["Total Goals","%"])
    
    total_games = goal_count["year"].sum()
    goal_table["%"] = goal_table["%"] / total_games  # normalizing to get percentage
    
    return goal_table.round({"%":3})

def hist_formatted(df, period): # to create a histogram that starts from 0
    if period == "ft":
        hist_values = np.unique(df["ft_total_goals"], return_counts=True)
        hist_title = "Fulltime Total Goals"
    elif period == "ht":
        hist_values = np.unique(df["ht_total_goals"], return_counts=True)
        hist_title = "Halftime Total Goals"
    bins = list(hist_values[0])
    counts = list(hist_values[1])

    if bins[0] != 0:  # check if the 1st bin is 0
        bins.insert(0,0)
        counts.insert(0,0)

    return px.bar(x=bins, y=counts, title=hist_title, labels={'x':'Goals', 'y':'Count'})

def generate_viz(df):  # to create the tables and graphs

    # dataframe of 'total goals over X' (fulltime & halftime)
    ft_over_goals = over_goals(df, "ft")
    ht_over_goals = over_goals(df, "ht")

    # histogram of 'fulltime total goals'
    hist_ft_goals = hist_formatted(df, "ft")
    hist_ft_goals.update_layout(bargap=0.1, xaxis=dict(tickmode="linear"))

    # histogram of 'halftime total goals'
    hist_ht_goals = hist_formatted(df, "ht")
    hist_ht_goals.update_layout(bargap=0.1, xaxis=dict(tickmode="linear"))

    # donut chart of 'which half has more goals'
    which_half = df.groupby("which_half_more_goals").count()[["year"]].reset_index()
    pie_which_half = px.pie(which_half, values="year", names="which_half_more_goals", 
                            labels={"year":"Count", "which_half_more_goals":"Which half"}, 
                            hole=.5, title="Which Half Has More Goals?")

    # donut chart of 'both teams to score'
    btts = df.groupby("both_teams_to_score").count()[["year"]].reset_index()
    pie_btts = px.pie(btts, values="year", names="both_teams_to_score", 
                      labels={"year":"Count", "both_teams_to_score":"BTTS"}, 
                      hole=.5, title="Both Teams To Score?")

    return ft_over_goals, ht_over_goals, hist_ft_goals, hist_ht_goals, pie_which_half, pie_btts


##### Data #####

data = pd.read_csv("data/worldcup_cleaned_updated.csv")


##### Intro / General Overview (Not interactive!) #####

number_of_games_by_year = list(data.groupby("year").count()["stage"])
overview = data.groupby("year").sum(numeric_only=True)[["ft_total_goals","ht_total_goals"]].reset_index()
overview["ft_total_goals"] = overview["ft_total_goals"] / number_of_games_by_year
overview["ht_total_goals"] = overview["ht_total_goals"] / number_of_games_by_year
overview

overview_avg_goals = px.line(overview, 
            x='year', y=['ft_total_goals', 'ht_total_goals'], 
            labels={"year":"Year", "value":"Avg Goals"}, title="Average Goals per Game",
            markers=True,
            )
overview_avg_goals.update_xaxes(showline=True, linewidth=1, gridcolor='#cccccc', linecolor='black')
overview_avg_goals.update_yaxes(showline=True, linewidth=1, gridcolor='#cccccc', linecolor='black')


##### Graphs & Tables (Interactive!) #####

query_df = query(data, data["year"].min(), data["year"].max(), "All")   # default parameters for initialization

ft_over_goals, ht_over_goals, hist_ft_goals, hist_ht_goals, pie_which_half, pie_btts = generate_viz(query_df)


##### Text/Copywriting #####

description = '''
### Explore the goal stats in depth
---
  - Fulltime total goals
  - Halftime total goals
  - Which half has more goals?
  - Both team to score?
'''

credits = "© [_darrylcjy_](https://www.linkedin.com/in/darryl-chua-331832230/)"


##### Others - Parameters for Dash Core Components (Widgets) #####

# dropdown
list_of_stages = list(data["stage"].unique())
list_of_stages.insert(0, "All")
dropdown_menu = list_of_stages

# range slider
list_of_years = list(data["year"].unique())
slider_range = {int(year):str(year) for year in list_of_years}   # need to include int() to prevent TypeError 


##### App #####

app = Dash(__name__)
app.title = "World Cup Dashboard"
app._favicon = ("assets/favicon.ico")

app.layout = html.Div([
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H2(children="World Cup Dashboard", style={"textAlign":"center"},),
                    html.H5(children="Analyzing the Goals", style={"textAlign":"center", "fontStyle":"italic"},),
                    ]),
                dbc.CardImg(src='/assets/worldcup-logo1.png', top=False, style={"height":"250px",},),                                
                ],
                color="info", inverse=True
                ),
            width={"size":3},
            ),
        dbc.Col(
            dcc.Graph(
                id="overview-graph",
                figure=overview_avg_goals,
                ),
            width={"size":8},
            ),
        ],        
        align="center",
        justify="center",
        ),
    html.Hr(),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                        dcc.Markdown(children=description),
                        html.Br(), html.Br(),
                        dcc.RangeSlider(
                            id="year",
                            min = min(list_of_years), 
                            max = max(list_of_years), 
                            step = None, 
                            marks = slider_range,
                            value = [min(list_of_years), max(list_of_years)]
                        ),
                        html.Br(),
                        dcc.Dropdown(
                            id="stage",
                            options=dropdown_menu,
                            value=dropdown_menu[0],
                        ),
                        html.Br(), 
                        dbc.Button(
                            'Reset', 
                            id='reset-button',
                            color="info",
                            size="sm",
                            style={"float":"right"}, 
                            n_clicks=0,
                        ),
                        html.Br(),
                        dcc.Markdown(children=credits),
                    ])
                ),
            width={"size":3},
            ),
        dbc.Col([
            dcc.Graph(
                id="hist-ft-total-goals",
                figure=hist_ft_goals,
                style={"height":"400px"},
                ),
            ],
            width={"size":3},
            ),
        dbc.Col([
            dbc.Card(
                dash_table.DataTable(
                    id="table-ft-total-goals",
                    data=ft_over_goals.to_dict('records'),
                    columns=[{'id': c, 'name': c} for c in ft_over_goals.columns],
                    style_header={
	                    'backgroundColor': '#e1e1ea',
	                    'color': 'black',
	                    'fontWeight': 'bold',
	                },
                ),
                ),
            ],
            width={"size":2},
            ),
        dbc.Col(
            dcc.Graph(
                id="which_half",
                figure=pie_which_half,
                style={"height":"400px"},
                ),
            width={"size":3},
            ),
        ],
        align="center",
        justify="center",
        ),
    dbc.Row([
        dbc.Col(
            width={"size":3}
            ),
        dbc.Col(
            dcc.Graph(
                id="hist-ht-total-goals",
                figure=hist_ht_goals,
                style={"height":"400px"},
                ),
            width={"size":3},
            ),
        dbc.Col(
            dbc.Card(
                dash_table.DataTable(
                    id="table-ht-total-goals",
                    data=ht_over_goals.to_dict('records'),
                    columns=[{'id': c, 'name': c} for c in ht_over_goals.columns],
                    style_header={
	                    'backgroundColor': '#e1e1ea',
	                    'color': 'black',
	                    'fontWeight': 'bold',
	                },
	            ),
                ),
            width={"size":2},
            ),
        dbc.Col(
            dcc.Graph(
                id="btts",
                figure=pie_btts,
                style={"height":"400px"},
                ),
            width={"size":3}
            ),
        ],
        align="center",
        justify="center",
        )
    ])


##### Callbacks ######

# filters: year (range slider) & stage (dropdown)
@app.callback(
    [Output(component_id="table-ft-total-goals", component_property="data"),
    Output(component_id="table-ht-total-goals", component_property="data"),
    Output(component_id="hist-ft-total-goals", component_property="figure"),
    Output(component_id="hist-ht-total-goals", component_property="figure"),
    Output(component_id="which_half", component_property="figure"),
    Output(component_id="btts", component_property="figure"),],
    [Input(component_id="year", component_property="value"),
    Input(component_id="stage", component_property="value")]
    )
def update_viz(year_range, which_stage):
    if which_stage not in dropdown_menu:
        raise PreventUpdate
    else:
        query_df = query(data, year_range[0], year_range[1], which_stage)
        ft_over_goals, ht_over_goals, hist_ft_goals, hist_ht_goals, pie_which_half, pie_btts = generate_viz(query_df)

        # print("New parameters: \nYear Range: {}, \nStage: {}".format(year_range, which_stage))
        return ft_over_goals.to_dict('records'), ht_over_goals.to_dict('records'), hist_ft_goals, hist_ht_goals, pie_which_half, pie_btts 

# reset button
@app.callback(
    [Output(component_id="year", component_property="value"),
    Output(component_id="stage", component_property="value"),],
    [Input(component_id="reset-button", component_property="n_clicks"),]
    )
def reset_viz(n_clicks):
    year_range = [data["year"].min(), data["year"].max()]
    stage = "All"

    return year_range, stage


if __name__ == "__main__":
    app.run_server(debug=True)