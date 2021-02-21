import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output


app = dash.Dash()

data = pd.read_csv("actions.csv", names=["symbol", "trend_state", "action"])

head_div = html.Div()

table_div = html.Div(id="table_div")

interval = dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0)

app.layout = html.Div(children=[head_div, table_div, interval], style={"backgroundColor": "rgb(24, 28, 39)"})

style_header={
    'backgroundColor': 'rgb(19, 23, 34)'
    }
style_cell={
    'backgroundColor': 'rgb(24, 28, 39)',
    'color': 'white',
    "textAlign": "center"
    }
style_data_conditional = [
    {"if" : {'filter_query': '{action} = PrecLong || {action} = PrecShort',
             'column_id': 'action'},
     "backgroundColor": "rgb(235, 169, 56)",
     "color": "white"
    },
    {"if" : {'filter_query': '{action} = Short',
             'column_id': 'action'},
     "backgroundColor": "rgb(235, 56, 172)",
     "color": "white"
    },
    {"if" : {'filter_query': '{action} = Long',
             'column_id': 'action'},
     "backgroundColor": "rgb(56, 235, 104)",
     "color": "white"
    },
    {"if" : {'filter_query': '{trend_state} = up',
             'column_id': 'trend_state'},
     "backgroundColor": "rgb(38, 166, 154)",
     "color": "white"
    },
    {"if" : {'filter_query': '{trend_state} = down',
             'column_id': 'trend_state'},
     "backgroundColor": "rgb(239, 83, 80)",
     "color": "white"
    }
]

@app.callback(Output('table_div', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    while True:
        try:
            data = pd.read_csv("actions.csv", names=["symbol", "trend_state", "action"])
            break
        except Exception:
            pass

    return dash_table.DataTable(id="table",
                                columns=[{"name": "Symbol", "id": "symbol", "type": "text"}, {"name": "Trend State", "id": "trend_state", "type": "text"}, {"name": "Action", "id": "action", "type": "text"}],
                                data=data.to_dict('records'),
                                style_header=style_header,
                                style_cell=style_cell,
                                style_data_conditional=style_data_conditional,
                                style_as_list_view=True)
    

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=False)