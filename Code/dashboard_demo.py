from dash import Dash, html, dcc, Input, Output, State, callback, dash_table

from model.LocationScraper import LocationScraper
from model.FlightScraper import FlightScraper
from model.UserAgent import UserAgent
from model.Cookie import Cookie, solve_captcha_with_link

from requests import Session
from dateutil.relativedelta import relativedelta
from pandas import DataFrame, concat
from datetime import date, datetime, timedelta
import plotly.express as px
from time import sleep

import json

#############################
time_out = 5
max_check = 3
change_cookie_rate = 45 # change cookie per 45 requests
#############################

request_ct = 0

def get_ticket(scraper:FlightScraper, origin_id:str, dest_id:str,
               go_year:int, go_month:int, go_day:int,
               back_year:int=None, back_month:int=None, back_day:int=None,
               ):
    global request_ct
    if request_ct>0 and request_ct%change_cookie_rate==0:
        new_cookie = Cookie()
        scraper.cookie = new_cookie
    request_ct+=1
    
    ct = 0
    data = None
    while ct<max_check and data is None:
        if back_year is None:
            raw_data = scraper.get_data(origin_entity_id=origin_id,
                                        destination_entity_id=dest_id,
                                        go_year=go_year,
                                        go_month=go_month,
                                        go_day=go_day)
        else:
            raw_data = scraper.get_data(origin_entity_id=origin_id,
                                        destination_entity_id=dest_id,
                                        go_year=go_year,
                                        go_month=go_month,
                                        go_day=go_day,
                                        back_year=back_year,
                                        back_month=back_month,
                                        back_day=back_day)
          
        if "reason" in raw_data:
            print("[WARNING] Bad cookies. Changing cookie...")
            captcha_link = raw_data["redirect_to"]
            solve_captcha_with_link(captcha_link)
            sleep(60)
            new_cookie = Cookie()
            scraper.cookie = new_cookie
            request_ct = 1
            
            if back_year is None:
                raw_data = scraper.get_data(origin_entity_id=origin_id,
                                            destination_entity_id=dest_id,
                                            go_year=go_year,
                                            go_month=go_month,
                                            go_day=go_day)
            else:
                raw_data = scraper.get_data(origin_entity_id=origin_id,
                                            destination_entity_id=dest_id,
                                            go_year=go_year,
                                            go_month=go_month,
                                            go_day=go_day,
                                            back_year=go_year,
                                            back_month=go_month,
                                            back_day=go_day)
        
        
        try:
            if ct+1==max_check:
                data = scraper.clean_data(raw_data, skip_complete=True)
            else:
                data = scraper.clean_data(raw_data)
                            
            if data is None: 
                print(f"Incomplete Data. Waiting {time_out//60} minutes for the server to give complete  data. Trial {ct+1}/{max_check}")
                sleep(time_out)
            ct+=1
        except:
            with open("error.json", "w") as file:
                json.dump(raw_data, file, indent=4)
            raise ValueError("cannot find raw data")
        
    return data

ua = UserAgent()
s = Session()
cookie = Cookie()
flight_scraper = FlightScraper(user_agent=ua, cookie=cookie, session=s)
location_scraper = LocationScraper(ua, s)
today = date.today()
max_day = today + relativedelta(months=+8)
time_format = "%Y-%m-%d"
result_dic = dict()

def lookup_place(name: str):
    if not name.strip(): return
    raw_data = location_scraper.getData(name.strip())
    return location_scraper.getDescription(raw_data) if raw_data else raw_data

def getDataFrame(result_dic:dict, go_day_string_list:list, back_day_string_list:list, day_dic:dict):
    df_list = []
    if back_day_string_list is None:
        for go_string in go_day_string_list:
            df_list.append(result_dic[go_string])
        return concat(df_list, ignore_index=True, copy=False)
    else:
        for go_string in go_day_string_list:
            go_day = day_dic[go_string]
            for back_string in back_day_string_list:
                back_day = day_dic[back_string]
                if back_day<go_day: continue
                df_list.append(result_dic[go_string][back_string])
        return concat(df_list, ignore_index=True, copy=False)
        
def checklist(checklist_info:dict):
    if checklist_info["trip_type"]=="direct":
        return html.Div([
                    html.Label("Go Days"),
                    html.Br(),
                    dcc.Checklist(
                            id="go-day-checklist-selector",
                            options=checklist_info["go_day_string_list"],
                            labelStyle={"display": "flex", "alignItems": "center", "fontSize": "18px", "color": "white"}
                    )
                ])
    else:
        return html.Div([
                    html.Div(
                        [
                            html.Label("Go Day(s)"),
                            html.Br(),
                            dcc.Checklist(
                                    id="go-day-checklist-selector",
                                    options=checklist_info["go_day_string_list"],
                                    labelStyle={"display": "flex", "alignItems": "center", "fontSize": "18px", "color": "white"}
                            )
                        ], style={"marginRight": "40px"}
                    ),
                    
                    html.Div(
                        [
                            html.Label("Back Day(s)"),
                            html.Br(),
                            dcc.Checklist(
                                    id="back-day-checklist-selector",
                                    options=checklist_info["back_day_string_list"],
                                    labelStyle={"display": "flex", "alignItems": "center", "fontSize": "18px", "color": "white"}
                            )
                        ], style={"marginRight": "40px"}
                    )
                ],
                style={"display": "flex"})        

def info_page():
    global result_dic
    result_dic.clear()
    return html.Div(
    [
        # title
        html.Div(
            html.H1("Flight Ticket Search"),
            style={
                "textAlign": "center",
                "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                "color": "white",
                "padding": "30px",
                "borderRadius": "15px",
                "boxShadow": "0px 8px 20px rgba(0,0,0,0.5)",
                "fontFamily": "Verdana, sans-serif"
            }
        ),
        html.Br(),
        
        # Origin input
        html.Div(
            [
                html.Label("Origin:   ", style={"color": "white", "fontWeight": "bold", "fontFamily": "Verdana, sans-serif"}),
                dcc.Input(
                    id="origin-input", 
                    type="text", 
                    placeholder="Enter origin city/airport",
                    style={
                        "width": "20%", 
                        "padding": "10px", 
                        "borderRadius": "5px",
                        "border": "none"                    }
                ),
                html.Div(id="origin-output", style={"color": "white", "marginTop": "20px"})
            ],
            style={
                "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                "padding": "20px",
                "borderRadius": "10px",
                "marginBottom": "20px",
                "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)"
            }
        ),
        html.Br(),
        
        # Destination input
        html.Div(
            [
                html.Label("Destination:   ", style={"color": "white", "fontWeight": "bold", "fontFamily": "Verdana, sans-serif"}),
                dcc.Input(
                    id="dest-input", 
                    type="text", 
                    placeholder="Enter destination city/airport",
                    style={
                        "width": "20%", 
                        "padding": "10px", 
                        "borderRadius": "5px",
                        "border": "none"
                    }
                ),
                html.Div(id="dest-output", style={"color": "white", "marginTop": "20px"})
            ],
            style={
                "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                "padding": "20px",
                "borderRadius": "10px",
                "marginBottom": "20px",
                "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)"
            }
        ),
        html.Br(),
        
        # Trip type
        html.Div(
            [
                # First row: label + radio buttons
                html.Div(
                    [
                        html.Label(
                            "Trip type:",
                            style={"color": "white", "marginRight": "15px", "fontWeight": "bold", "fontFamily": "Verdana, sans-serif"}
                        ),
                        dcc.RadioItems(
                            id="trip-type",
                            options=[{"label": opt, "value": opt} for opt in ["Direct", "Round"]],
                            value="Direct",
                            inline=True,
                            style={"color": "white", "fontFamily": "Verdana, sans-serif"}
                        )
                    ],
                    style={"display": "flex", "alignItems": "center"}  # keep these in one row
                ),

                html.Br(),

                # Second row: date picker container
                html.Div(id="date-picker-container")
            ],
            style={
                "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                "padding": "20px",
                "borderRadius": "10px",
                "marginBottom": "20px",
                "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)"
            }
        ),
        html.Br(),
        
        # Range Slider
        html.Div([
            html.Div(id="range-slider-container")
        ],
        style={
                "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                "width": "20%",
                "padding": "20px",
                "borderRadius": "10px",
                "marginBottom": "20px",
                "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)"
            }
        ),
        html.Br(),
        
        # Confirm Button
        html.Button(
            "Confirm",
            id="confirm-btn",
            n_clicks=0,
        ),
        html.Br(),
        
        # Confirm Output Display
        html.Div(
            id="confirm-output",
            style={
                "width": "40%",
                "marginTop": "15px",
                "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                "color": "white",
                "padding": "15px",
                "borderRadius": "8px",
                "boxShadow": "0px 4px 6px rgba(0,0,0,0.2)",
                "fontSize": "20px",
                "minHeight": "40px"  # keeps box visible even if empty,
            }
        ),
        html.Br(),

        # Find Ticket Button
        html.Button(
            "Find Ticket",
            id="find-btn",
            n_clicks=0,
            disabled=True
        )
        
    ], style={"backgroundColor": "#FFFFFFFF"})
    
def dashboard_page(data_dic:dict):
    # data_dic = {
    #         "origin_id": origin_info["entity_code"],
    #         "dest_id": dest_info["entity_code"],
    #         "go": single_date if single_date is not None else start_date,
    #         "back": end_date,
    #         "goRange": direct_range if direct_range is not None else go_range,
    #         "backRange": back_range
    #     }
    check_list_info_dic = dict()
    trip_type = "direct" if data_dic["back"] is None else "round"
    check_list_info_dic["trip_type"] = trip_type
    day_dic = {}
    global result_dic
    
    if trip_type=="direct":
        go_day_list = []
        go_day_string_list = []
        goDay = datetime.strptime(data_dic["go"], time_format)
        goRange = data_dic["goRange"]
        for day_range in range(-goRange, goRange+1):
            day = goDay + relativedelta(days=day_range)
            string = day.strftime(time_format)
            day_dic[string] = day
            go_day_list.append(day)
            go_day_string_list.append(string)
            
        check_list_info_dic["day_dic"] = day_dic
        check_list_info_dic["go_day_string_list"] = go_day_string_list
            
        for day in go_day_list:
            results = get_ticket(flight_scraper, data_dic["origin_id"], data_dic["dest_id"], day.year, day.month, day.day)
            df = DataFrame([result.to_dict() for result in results])
            result_dic[day.strftime(time_format)] = df
    else:
        go_day_list = []
        go_day_string_list = []
        goDay = datetime.strptime(data_dic["go"], time_format)
        goRange = data_dic["goRange"]
        
        back_day_list = []
        back_day_string_list = []
        backDay = datetime.strptime(data_dic["back"], time_format)
        backRange = data_dic["backRange"]
        
        for day_range in range(-goRange, goRange+1):
            day = goDay + relativedelta(days=day_range)
            string = day.strftime(time_format)
            day_dic[string] = day
            go_day_list.append(day)
            go_day_string_list.append(string)
            
        for day_range in range(-backRange, backRange+1):
            day = backDay + relativedelta(days=day_range)
            string = day.strftime(time_format)
            day_dic[string] = day
            back_day_list.append(day)
            back_day_string_list.append(string)
        
        check_list_info_dic["go_day_string_list"] = go_day_string_list
        check_list_info_dic["back_day_string_list"] = back_day_string_list
        check_list_info_dic["day_dic"] = day_dic
                
        for gd, gds in zip(go_day_list, go_day_string_list):
            for bd, bds in zip(back_day_list, back_day_string_list):
                if bd<gd: continue
                results = get_ticket(flight_scraper, data_dic["origin_id"], data_dic["dest_id"], gd.year, gd.month, gd.day, bd.year, bd.month, bd.day)
                df = DataFrame([result.to_dict() for result in results])
                if gds not in result_dic: result_dic[gds] = dict()
                result_dic[gds][bds] = df
        # print(day_dic)
    return html.Div(
        [
            # title
            html.Div(
                html.H1("Ticket Dashboard"),
                style={
                    "textAlign": "center",
                    "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                    "color": "white",
                    "padding": "30px",
                    "borderRadius": "15px",
                    "boxShadow": "0px 8px 20px rgba(0,0,0,0.5)",
                    "fontFamily": "Verdana, sans-serif"
                }
            ),
            html.Br(),

            # confirm output
            html.Div(
                data_dic["confirm_output"],
                # str(data_dic),
                style={
                    "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginBottom": "20px",
                    "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)",
                    "color": "white",          
                    "fontSize": "20px",        
                    "fontWeight": "bold",
                    "fontFamily": "Verdana, sans-serif"
                }
            ),
            html.Br(),

            # days checklist
            html.Div(
                [
                    checklist(check_list_info_dic)
                ],
                style={
                    "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginBottom": "20px",
                    "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)",
                    "color": "white",
                    "fontSize": "20px",
                    "fontWeight": "bold",
                    "fontFamily": "Verdana, sans-serif"
                }
            ),
            html.Br(),
            
            # Dashboard
            dcc.Store("trip-type-dashboard", data=trip_type),
            html.Div(
                [
                    html.Div(id="axis-dropdown-container")
                ],
                style={
                    "width": "50%",
                    "background": "linear-gradient(135deg, #1E1E2F, #3E3E5E)",
                    "padding": "10px",
                    "borderRadius": "5px",
                    "marginBottom": "10px",
                    "boxShadow": "0px 4px 10px rgba(0,0,0,0.3)",
                    "color": "white",
                    "fontSize": "13px",
                    "fontWeight": "bold",
                    "fontFamily": "Verdana, sans-serif"
                }
            ),
            html.Br(),
            
            # plot graph button
            html.Button(
                "Plot",
                id="plot-btn",
                n_clicks=0
            ),
            html.Br(),
            
            dcc.Store("day-dic", data=day_dic),
            # dashboard section
            html.Div(id="dashboard"),
            html.Br(),
            
            # ticket table section
            html.Div(id="table"),
            html.Br(),

            # back button
            html.Button(
                "Back",
                id="back-btn",
                n_clicks=0
            )
            
        ],style={"padding": "20px"})
    
app = Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Store(id="page-store", data="info"),
    dcc.Store(id="data-dic"),
    html.Div(id="page-container", children=info_page())
])

# --- Callbacks ---
@callback(
    Output("page-container", "children"),
    Input("page-store", "data"),
    State("data-dic", "data", allow_optional=True),
    prevent_initial_call=True
)
def render(page, data_dic):
    if page=="info": return info_page()
    else: return dashboard_page(data_dic)
    
@callback(
    Output("date-picker-container", "children"),
    Input("trip-type", "value")
)
def toggle_date_picker(trip_type):
    if trip_type == "Direct":
        return dcc.DatePickerSingle(
            id="date-single",
            min_date_allowed=today,
            max_date_allowed=max_day,
            date=today,
            clearable=True,
            reopen_calendar_on_clear=True
        )
    else:  # Round trip
        return dcc.DatePickerRange(
            id="date-range",
            min_date_allowed=today,
            max_date_allowed=max_day,
            start_date=today,
            end_date=date.today() + timedelta(weeks=1),
            clearable=True,
            reopen_calendar_on_clear=True,
            minimum_nights=0
        )
        
@callback(
    Output("range-slider-container", "children"),
    Input("trip-type", "value")
)
def toggle_range_slider(trip_type):
    if trip_type == "Direct":
        return html.Div([
            html.Label("Range:", style={"color": "white", "marginBottom": "10px", "fontFamily": "Verdana, sans-serif"}),
            dcc.Slider(
                id="direct-range-slider",
                min=0,
                max=3,
                step=1,
                value=0,
                marks={i: str(i) for i in range(4)}
            )
        ])
    else:  # Round trip
        return html.Div([
            html.Label("Go Range", style={"color": "white", "marginBottom": "10px", "fontFamily": "Verdana, sans-serif"}),
            dcc.Slider(
                id="go-range-slider",
                min=0,
                max=3,
                step=1,
                value=0,
                marks={i: str(i) for i in range(4)}
            ),
            html.Label("Back Range", style={"color": "white", "marginBottom": "10px", "fontFamily": "Verdana, sans-serif"}),
            dcc.Slider(
                id="back-range-slider",
                min=0,
                max=3,
                step=1,
                value=0,
                marks={i: str(i) for i in range(4)}
            )
        ])

@callback(
    Output("origin-output", "children"),
    Output("dest-output", "children"),
    Output("confirm-output", "children"),
    Output("find-btn", "disabled"),
    Output("data-dic", "data"),
    Input("confirm-btn", "n_clicks"),
    State("origin-input", "value"),
    State("dest-input", "value"),
    State("trip-type", "value"),
    State("date-picker-container", "children"),
    State("direct-range-slider", "value", allow_optional=True),
    State("go-range-slider", "value", allow_optional=True),
    State("back-range-slider", "value", allow_optional=True)
)
def confirm_inputs(n_clicks, origin, dest, trip_type, date_picker_children, direct_range, go_range, back_range):
    if n_clicks > 0:
        # --- Basic origin/destination checks ---
        if not origin or not dest:
            return "", "", "❌ Empty origin or destination", True, {}
        if origin == dest:
            return "", "", "❌ Origin and destination cannot be the same", True, {}

        # --- Lookup airport info ---
        origin_info = lookup_place(origin)
        dest_info = lookup_place(dest)
        
        if not origin_info or not dest_info: return "", "", "❌ Invalid origin or destination", True, {}
            
        origin_text = f"Airport Code: {origin_info['airport_code']} | Airport Name: {origin_info['airport_name']} | Country: {origin_info['country']}"
        dest_text = f"Airport Code: {dest_info['airport_code']} | Airport Name: {dest_info['airport_name']} | Country: {dest_info['country']}"

        # --- Extract dates from dynamic date picker ---
        start_date = None
        end_date = None
        single_date = None

        if date_picker_children and isinstance(date_picker_children, dict):
            props = date_picker_children.get("props", {})
            if "date" in props:
                single_date = props["date"]  # Direct trip
            elif "start_date" in props and "end_date" in props:
                start_date = props["start_date"]  # Round trip
                end_date = props["end_date"]    
        
        # --- Validate dates ---
        if trip_type == "Direct":
            if not single_date:
                return origin_text, dest_text, "❌ Please select a departure date", True, {}
            confirm_text = f"✅ {origin_info['airport_code']} → {dest_info['airport_code']}  |  {single_date}"
        else:  # Round trip
            if not start_date or not end_date:
                return origin_text, dest_text, "❌ Please select both departure and return dates", True, {}
            if end_date < start_date:
                return origin_text, dest_text, "❌ Return date cannot be earlier than departure date", True, {}
            confirm_text = f"✅ {origin_info['airport_code']} → {dest_info['airport_code']}  |  {start_date} → {end_date}"
                
        data_dic = {
            "origin_id": origin_info["entity_code"],
            "dest_id": dest_info["entity_code"],
            "go": single_date if single_date is not None else start_date,
            "back": end_date,
            "goRange": direct_range if direct_range is not None else go_range,
            "backRange": back_range,
            "confirm_output": confirm_text
        }

        return origin_text, dest_text, confirm_text, False, data_dic
    
    return "", "", "", True, {}

@callback(
    Output("page-store", "data"),
    Input("find-btn", "n_clicks"),
    prevent_initial_call=True
)
def loadDashboard(n_clicks:int):
    return "dashboard"

@callback(
    Output("page-store", "data", allow_duplicate=True),
    Input("back-btn", "n_clicks"),
    prevent_initial_call=True
)
def loadInfo(n_clicks:int):
    return "info"
    
@callback(
    Output("axis-dropdown-container", "children"),
    Input("go-day-checklist-selector", "value"),
    Input("back-day-checklist-selector", "value", allow_optional=True),
    State("trip-type-dashboard", "data"),
    prevent_initial_call=True
)
def get_axis_dropdown(go_checklist:list, back_checklist:list, trip_type:str):
    global result_dic
    if go_checklist is None or len(go_checklist)==0: return html.Div()
    if trip_type=="direct":
        df = next(iter(result_dic.values()))
        axis_list = df.columns.tolist()
        axis_list.remove("url")
    else:
        if back_checklist is None or len(back_checklist)==0: return  html.Div()
        df = next(iter(next(iter(result_dic.values())).values()))
        axis_list = df.columns.tolist()
        axis_list.remove("url")
        
    dropdown_container = html.Div(
        [
            html.Div(
                [
                    html.Label("X-axis"),
                    dcc.Dropdown(
                        id="x-axis-dropdown",
                        options=axis_list,
                        clearable=False,
                        style={"color": "black", "backgroundColor": "white"}
                    )
                ],
                style={"flex": "1", "margin-right": "10px"}
            ),
            
            html.Div(
                [
                    html.Label("Y-axis"),
                    dcc.Dropdown(
                        id="y-axis-dropdown",
                        options=axis_list,
                        clearable=False,
                        style={"color": "black", "backgroundColor": "white"}
                    )
                ],
                style={"flex": "1"}
            )
        ],
        style={"display": "flex", "flex-direction": "row", "margin": "10px 0"}
    )
    
    return dropdown_container

@callback(
    Output("dashboard", "children"),
    Output("table", "children"),
    Input("plot-btn", "n_clicks"),
    State("x-axis-dropdown", "value", allow_optional=True),
    State("y-axis-dropdown", "value", allow_optional=True),
    State("trip-type-dashboard", "data"),
    State("go-day-checklist-selector", "value"),
    State("back-day-checklist-selector", "value", allow_optional=True),
    State("day-dic", "data"),
    prevent_initial_call=True
)
def get_dashboard(_, x_axis, y_axis, trip_type, go_day_check_list, back_day_check_list, day_dic):
    if not x_axis or not y_axis: return html.Div()
    if x_axis==y_axis: return html.Div()
    
    global result_dic
    df_list = []
    
    if trip_type=="direct":
        for day in go_day_check_list:
            df_list.append(result_dic[day])
    else:
        for go_day_string in go_day_check_list:
            for back_day_string in back_day_check_list:
                if day_dic[back_day_string]<day_dic[go_day_string]: continue
                # print(go_day_string, back_day_string)
                df_list.append(result_dic[go_day_string][back_day_string])
                
    if len(df_list)==0: return html.Div(), html.Div()
    
    combined = concat(df_list, ignore_index=True, copy=False)
    combined = combined.reset_index() # move index to a col named "index"
    col_list = []
    for col in combined.columns:
        if col=="url":continue
        col_list.append(col)
    col_list.append("url")
    combined = combined[col_list]
    
    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in combined.columns],
        data=combined.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'padding': '6px', 'textAlign': 'left'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
    )
    
    try:
        fig = px.scatter(combined, x=x_axis, y=y_axis, size="price",
                        trendline="lowess", trendline_options=dict(frac=0.1),
                        hover_data=['price', 'agent', 'index'])
    except ValueError as e:
        msg = str(e)
        if "Could not convert value of 'y'" in msg:
            fig = px.scatter(
                combined, x=x_axis, y=y_axis, size="price",
                hover_data=['price', 'agent', 'index']
            )
            fig.update_yaxes(type="category")
        elif "Could not convert value of 'x'" in msg:
            fig = px.scatter(
                combined, x=x_axis, y=y_axis, size="price",
                hover_data=['price', 'agent', 'index']
            )
            fig.update_xaxes(type="category")
        else:
            raise e  # re-raise unexpected ValueErrors
        
    return dcc.Graph(figure=fig), table


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

