import pandas as pd
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

"""
To-Do:
    -Dashboard on engaged trades
"""

"""
Layout Setup
"""

app = dash.Dash(__name__)

data = pd.read_csv("./live_data/actions.csv", names=["symbol", "trend_state", "action"])

head_div = html.Div(id="head_div", children=[html.H1("Daytrading Status")])

info_div = html.Div(id="info_div")

trading_div = html.Div(id="trading_div")

table_div = html.Div(id="table_div")

interval = dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0)

app.layout = html.Div(children=[head_div, info_div, trading_div, table_div, interval])


"""
Table Callbacks
"""
def sorter(series):
    series[series == "noA"] = 4
    series[series == "PrecLong"] = 3
    series[series == "PrecShort"] = 3
    series[series == "Short"] = 2
    series[series == "Long"] = 1
    return series

def linker(df):
    for i in range(df.shape[0]):
        df.iloc[i,0] = f"[{df.iloc[i, 0]}]({df.iloc[i,3]})"
    df.drop(columns="link", inplace=True)

style_header={
    'backgroundColor': 'rgb(19, 23, 34)'
    }
style_cell={
    'backgroundColor': 'rgb(24, 28, 39)',
    'color': 'white',
    "textAlign": "center",
    "textDecoration": "none"
    }
style_data_conditional = [
    {"if" : {'filter_query': '{action} = PrecLong || {action} = PrecShort',
             'column_id': 'action'},
     "color": "rgb(235, 169, 56)"
    },
    {"if" : {'filter_query': '{action} = Short',
             'column_id': 'action'},
     "color": "rgb(235, 56, 172)"
    },
    {"if" : {'filter_query': '{action} = Long',
             'column_id': 'action'},
     "color": "rgb(56, 235, 104)"
    },
    {"if" : {'filter_query': '{trend_state} = up',
             'column_id': 'trend_state'},
     "color": "rgb(38, 166, 154)"
    },
    {"if" : {'filter_query': '{trend_state} = down',
             'column_id': 'trend_state'},
     "color": "rgb(239, 83, 80)"
    },
    {"if" : {"column_id": "symbol"},
     "paddingLeft": "70px",
     "fontSize": "12px",
     "width": "200px"
    }
]

@app.callback(Output('table_div', 'children'),
              Input('interval-component', 'n_intervals'))
def update_table(n):
    while True:
        try:
            data = pd.read_csv("./live_data/actions.csv", names=["symbol", "trend_state", "action", "link"])
            linker(data)
            data.sort_values(by="action", inplace=True, ignore_index=True, key=sorter)
            break
        except Exception:
            pass

    return dash_table.DataTable(id="table",
                                columns=[{"name": "Symbol", "id": "symbol", "type": "text", "presentation": "markdown"}, {"name": "Trend State", "id": "trend_state", "type": "text"}, {"name": "Action", "id": "action", "type": "text"}],
                                data=data.to_dict('records'),
                                style_header=style_header,
                                style_cell=style_cell,
                                style_data_conditional=style_data_conditional,
                                style_as_list_view=True)


"""
Info Screen Callbacks
"""
@app.callback(Output('info_div', 'children'),
              Input('interval-component', 'n_intervals'))
def update_info_screen(n):
    #read in the data
    while True:
        try:
            with open("./live_data/metadata.json", "r") as json_file:
                data = json.load(json_file)
            break
        except Exception:
            pass

    return html.Div(f"Update Duration: {round(data['complete_duration'], 2)} seconds")

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=False)