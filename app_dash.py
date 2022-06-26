import dash
from dash import dcc
from dash import html
import plotly.express as px
from dash import dash_table
from dash.dependencies import Input,Output
import json
from bs4 import BeautifulSoup
import pandas as pd
import requests
import numpy as np
import datetime
from datetime import date
from html_table_parser.parser import HTMLTableParser
import mibian
import urllib3
import plotly.graph_objects as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot
from plotly.graph_objs import *

from funciones.funciones_web_scrap import url_get_contents, filtro_opc_por_dias, obtener_call_put_data
from funciones.funciones_volatilidad import BS_CALL, BS_PUT, volat_opciones_call, volat_opciones_put 
import collections
collections.Callable = collections.abc.Callable


# Obtención de los datos del futuro 
url = 'https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35'
web_content = pd.read_html(url,thousands='.', decimal=',')
futuros = web_content[0]
datos_futuro = futuros.iloc[:,[0,futuros.shape[1]-1]]
datos_futuro = datos_futuro.iloc[0,:]

# Obtención de las fechas de ejercicio
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
dias = soup.find('select', attrs={'class': 'form-control', 'id': 'OpStrike'})
dias_opciones = []
for i in range(0,len(dias.text),10):
    dias_opciones.append(dias.text[i:i+10])
dias_opc = pd.unique(dias_opciones[0:len(dias_opciones)-2])


# Obtención de la tabla de datos de las opciones put y call
# Obteniendo el html content de la URL.
xhtml = url_get_contents('https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35').decode('utf-8')

# Defining the HTMLTableParser object
p = HTMLTableParser()

# feeding the html contents in the
# HTMLTableParser object
p.feed(xhtml)

u = p.tables[1][2:len(p.tables[1])]
u = u[0:len(u)-2]
# Para que los datos aparezcan como float
for i in range(len(u)):
    for j in range(len(u[i])):
        if type(u[i][j]) != float and u[i][j] != "-" :
            u[i][j] = u[i][j].replace(".", "")
            u[i][j] = u[i][j].replace(",", ".")
            u[i][j] = float(u[i][j])      

headers = ['Strike',
'Ord.Comp',
'Vol.Comp',
'Precio Comp',
'Precio Vent',
'Vol.Vent',
'Ord.Vent',
'Últ.',
'Vol.',
'Aper.',
'Máx.',
'Min.',
'Ant.']
precios_opc = pd.DataFrame(u,columns = headers)

# Se establecen los datos de las opciones para la fecha de ejercicio correspondiente
precios_dias = filtro_opc_por_dias (precios_opc, dias_opc)

# Limpieza de datos y clasificación de las opciones en put y call
datos_completos = obtener_call_put_data (precios_dias,datos_futuro)

# Calcular la volatilidad implicita de las opciones
volat_put = volat_opciones_put(datos_completos,datos_futuro,tasa_interes=0)
volat_call = volat_opciones_call(datos_completos,datos_futuro,tasa_interes=0)

# Se prepara el df de futuros para la tabla de dash
df1 = pd.DataFrame(futuros.values,columns = ["Vencimiento", "Tipo", "Ord.(Compra)", "Vol.(Compra)", "Precio(Compra)", "Precio(Venta)", "Vol.(Venta)", "Ord.(Venta)", "Últ.", "Vol.", "Aper.", "Máx.", "Min.", "Ant."])
df1.drop(df1.tail(1).index,inplace=True)

call_22 = pd.read_csv("datos_antig_opc/call_22-06-2022.csv").drop("Unnamed: 0",axis = 1)
call_23 = pd.read_csv("datos_antig_opc/call_23-06-2022.csv").drop("Unnamed: 0",axis = 1)
call_24 = pd.read_csv("datos_antig_opc/call_24-06-2022.csv").drop("Unnamed: 0",axis = 1)
put_22 = pd.read_csv("datos_antig_opc/put_22-06-2022.csv").drop("Unnamed: 0",axis = 1)
put_23 = pd.read_csv("datos_antig_opc/put_23-06-2022.csv").drop("Unnamed: 0",axis = 1)
put_24 = pd.read_csv("datos_antig_opc/put_24-06-2022.csv").drop("Unnamed: 0",axis = 1)

volat_call_diaria = {"22/06/2022":call_22,"23/06/2022":call_23,"24/06/2022":call_24}
volat_put_diaria = {"22/06/2022":put_22,"23/06/2022":put_23,"24/06/2022":put_24}

lista_opciones = []
for dia in volat_call_diaria.keys():
    lista_opciones.extend(volat_call_diaria[dia]["Fecha"].unique())
for dia in volat_put_diaria.keys():
    lista_opciones.extend(volat_put_diaria[dia]["Fecha"].unique())
    
lista_opciones.extend(volat_call.keys())
lista_opciones.extend(volat_put.keys())
lista_opc_uniq = list(dict.fromkeys(lista_opciones))

app = dash.Dash('Volatilidad Implícita opciones MINI-IBEX-35',
               external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

app.layout = html.Div(children=[
    
    html.Div([
        
        html.H1(children='Volatilidad Implícita opciones MINI-IBEX-35')],    
            className = 'banner'
            ),
    
    html.Div(children=['''
        En esta página se encuentan los datos de futuros y de opciones europeas
        del MINI IBEX. Estos datos se han obtenido de la página de derivados 
        financieros de MEFF perteneciente al BME. 
        Se calcula la volatilidad implícita mediante el modelo de Black-Scholes
        de las opciones PUT y CAll en la fecha de vencimiento seleccionada junto
        con la superficie de volatilidad asociada a estas opciones.
        Además, al final de la página se encuentra un comparador de skews de 
        volatilidad que permite comparar los gráficos de volatilidad implícita
        de una opción dada en días distintos.
    ''']),
     
    html.Div(children = [
        
        html.H3(children='FUTUROS',  
                className = "title_sub",
               )
    ]),
    
    html.Div([

        dash_table.DataTable(data = df1.to_dict("records"),
                             columns = [{"name": i, "id": i} for i in df1.columns],
                             merge_duplicate_headers = True, 
                             style_cell = {'padding': '5px'},
                             style_header = {'backgroundColor': '#00072D',
                                           'fontWeight': 'bold',
                                           'color': 'white',
                                           'text-align': 'center',
                                           },
                             style_data = {'backgroundColor': 'white',
                                         'color': '#00072D'}                          
                            )

             ], className = 'create_container3'),

    
    html.Div([
        
        html.H3(children='OPCIONES', 
                className = "title_sub")
    ]),

    html.Div([
    
        html.Div([

            html.Div([
                html.P('Selecciona la fecha de ejercicio de la opción', 
                       className = 'fix_label', 
                       style={'color':'black', 'margin-top': '2px'}
                      ),

                dcc.Dropdown(id = 'fecha_de_ejercicio',
                             options = [{'label': i, 'value': i} for i in volat_call.keys()],
                             value = list(volat_call.keys())[0]
                            ),


                html.P('Selecciona el tipo de opción',
                       className = 'fix_label',
                       style={'color':'black', 'margin-top': '2px'}
                      ),

                dcc.RadioItems(id = 'call_put_radioitems',
                               labelStyle = {'display': 'inline-block'},
                               options = [
                                   {'label' : 'CALL', 'value' : 'CALL'},
                                   {'label' : 'PUT', 'value' : 'PUT'}
                               ], 
                               value = 'CALL',
                               style = {'text-aling':'center', 'color':'black'},
                               className = 'dcc_compon')
            ],
            className = 'create_container2',
            style = {'margin-bottom': '20px'})
            
        ],className = 'row flex-display'),

        html.Div([  
            
            html.Div([
                
                dcc.Graph(id='my_graph',
                     figure = {},style = {"margin-top": 5})], 
                className = "create_container5", 
                style={'width': '49%', 'display': 'inline-block'}),
            
            html.Div([

                dash_table.DataTable( data=[{}],columns = [],merge_duplicate_headers=True,
                                     id = 'my_table',
                                     style_cell = {'padding': '5px'},
                                     style_header = {'backgroundColor': '#00072D',
                                                     'fontWeight': 'bold',
                                                     'color': 'white',
                                                     'text-align': 'center'
                                                    },
                                     style_data = {'backgroundColor': 'white',
                                                   'color': '#00072D'
                                                  }  

                )],
        style={'width': '49%', 'display': 'inline-block'})],
        className = "create_container4" ),
        
        html.Div([  
            
            html.Div([

                dcc.Graph(id='my_graph2',
                     figure = {},
                         )
            ], 
                className = "create_container5", 
                style={'width': '100%',"justify-content": "center"}),
            ],
        className = "create_container4",style={'width': '90%',"justify-content": "center"}),    
  
    ], className = "create_container1"),
    
    
    html.Div([
        
        html.H3(children='Comparación de skews en distintos días', 
                className = "title_sub")
            ]),
    
    html.Div([
    
        html.Div([

            html.Div([
                html.P('Selecciona la fecha de ejercicio de la opción', 
                       className = 'fix_label', 
                       style={'color':'black', 'margin-top': '2px'}
                      ),

                dcc.Dropdown(id = 'fecha_de_ejercicio2',
                             options = [{'label': i, 'value': i} for i in lista_opc_uniq],
                             value = lista_opc_uniq[1]
                            ),


                html.P('Selecciona el tipo de opción',
                       className = 'fix_label',
                       style={'color':'black', 'margin-top': '2px'}
                      ),

                dcc.RadioItems(id = 'call_put_radioitems2',
                               labelStyle = {'display': 'inline-block'},
                               options = [
                                   {'label' : 'CALL', 'value' : 'CALL'},
                                   {'label' : 'PUT', 'value' : 'PUT'}
                               ], 
                               value = 'CALL',
                               style = {'text-aling':'center', 'color':'black'},
                               className = 'dcc_compon'),
                
                html.P('Selecciona los días a comparar', 
                       className = 'fix_label', 
                       style={'color':'black', 'margin-top': '2px'}
                      ),

                dcc.Dropdown(id = 'fecha_de_comparacion1',
                             options = {},
                            ),
                dcc.Dropdown(id = 'fecha_de_comparacion2',
                             options = {},
                            ),
            ],
            className = 'create_container2',
            style = {'margin-bottom': 'auto'}),
        ],className = 'row flex-display'),
        
        html.Div([    
            
            html.Div([
                
                dcc.Graph(id='my_graph3',
                     figure = {},style = {"margin": "auto"})], 
                className = "create_container5", 
                style={'width': '49%', 'display': 'inline-block'}),
            
            html.Div([
                
                dcc.Graph(id='my_graph4',
                     figure = {},style = {"margin": "auto"})], 
                className = "create_container5", 
                style={'width': '49%', 'display': 'inline-block'})
        ],className = 'create_container4')
    ],className = "create_container1")
])
    
@app.callback(
    Output('my_graph', component_property='figure'),
    [Input('fecha_de_ejercicio', component_property='value'),
    Input('call_put_radioitems', component_property='value')])

def update_graph(val1,val2):

    select_values = {"fecha_de_ejercicio": val1, "call_put_radioitems": val2}    
    df_call = volat_call[val1]
    df_put = volat_put[val1]
    
    if val2 == "CALL":
        
        fig = px.line(df_call, 
                      x=df_call.index, 
                      y=df_call.iloc[:,0], 
                      title = "Volatilidad implícita en función del Strike (Call)"
                     )
    
    else:
        
        fig = px.line(df_put,
                      x=df_put.index,
                      y=df_put.iloc[:,0],
                      title = "Volatilidad implícita en función del Strike (Put)"
                     )
    
    fig.update_layout(xaxis_title="Strike", 
                      yaxis_title="Volatilidad implícita",
                      plot_bgcolor= "white",
                      paper_bgcolor = "#F2F2F2",
                      font_color = "#00072D",
                      title_x = 0.5,
                      title_y = 0.85,
                      title_font_family="Times New Roman",
                      title_font_color="#00072D"
                     )
    
    fig.update_traces(line_color='#333957')
    fig.update_xaxes(linecolor='black', gridcolor='silver')
    fig.update_yaxes(linecolor='black', gridcolor='silver')
    return fig

@app.callback(
    [Output('my_table', component_property='data'), Output('my_table', component_property='columns')],
    [Input('fecha_de_ejercicio', component_property='value'),
    Input('call_put_radioitems', component_property='value')])

def update_table(val1,val2):

    select_values = {"fecha_de_ejercicio": val1, "call_put_radioitems": val2}    
    df = datos_completos[val1][val2]
    
    return df.to_dict("records"), [{"name": i, "id": i} for i in df.columns]

@app.callback(
    Output('my_graph2', component_property='figure'),
    [Input('fecha_de_ejercicio', component_property='value'),
    Input('call_put_radioitems', component_property='value')])

def update_graph2(val1,val2):

    select_values = {"fecha_de_ejercicio": val1, "call_put_radioitems": val2}    
    df_call = volat_call[val1]
    df_put = volat_put[val1]
    precio_strike = []

    if val2 == "CALL":
        
        dias_datos = []
        datos_superf = pd.DataFrame()
        for dia in volat_call_diaria.keys():

            if volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                datos_superf = pd.concat([datos_superf,volat_dia])

        datos_superf = datos_superf.drop(["Fecha"],axis = 1)
        datos_superf_hoy = pd.concat([pd.DataFrame(volat_call[val1].index,columns = ["Strike"]),pd.DataFrame(volat_call[val1].values,columns = ["volat impli"])],axis = 1)
        datos_superf_hoy.index = [val1]*datos_superf_hoy.shape[0]
        datos_superf = pd.concat([datos_superf,datos_superf_hoy])
        datos_superf = datos_superf.reset_index()
        

        
        z1 = datos_superf["volat impli"].values
        y = datos_superf["Strike"].values
        for i in range(datos_superf["index"].shape[0]):
            datos_superf["index"][i] = (datetime.datetime.strptime(val1, '%d/%m/%Y')-datetime.datetime.strptime(datos_superf["index"][i], '%d/%m/%Y')).days
        x = datos_superf["index"].values
        z = np.array([x,z1])

        trace0= Surface(z=z,x=x,y=y)
        data=[trace0]
        fig = go.Figure(dict(data=data))
    
    else:
        
        dias_datos = []
        datos_superf = pd.DataFrame()
        for dia in volat_put_diaria.keys():

            if volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                datos_superf = pd.concat([datos_superf,volat_dia])

        datos_superf = datos_superf.drop(["Fecha"],axis = 1)
        datos_superf_hoy = pd.concat([pd.DataFrame(volat_put[val1].index,columns = ["Strike"]),pd.DataFrame(volat_put[val1].values,columns = ["volat impli"])],axis = 1)
        datos_superf_hoy.index = [val1]*datos_superf_hoy.shape[0]
        datos_superf = pd.concat([datos_superf,datos_superf_hoy])
        datos_superf = datos_superf.reset_index()
        

        
        z1 = datos_superf["volat impli"].values
        y = datos_superf["Strike"].values
        for i in range(datos_superf["index"].shape[0]):
            datos_superf["index"][i] = (datetime.datetime.strptime(val1, '%d/%m/%Y')-datetime.datetime.strptime(datos_superf["index"][i], '%d/%m/%Y')).days
        x = datos_superf["index"].values
        z = np.array([x,z1])

        trace0= Surface(z=z,x=x,y=y)
        data=[trace0]
        fig = go.Figure(dict(data=data))
    
    fig.update_layout(scene = dict(
                xaxis=dict(title='Días hasta vencimiento', 
                           range = [0,x.max()]
                          ),
                yaxis_title='Strike',
                zaxis_title='Volatilidad implícita',
                bgcolor = "#F2F2F2"),
                width=550,
                title='Superficie de Volatilidad',
                paper_bgcolor = "#F2F2F2",
                font_color = "#00072D",
                title_font_family="Times New Roman",
                title_font_color="#00072D",
                title_x = 0.5,
                title_y = 0.85,
                autosize=False,
                height=550,
                margin=dict(l=65, r=50, b=65, t=90))
    return fig

@app.callback(
    Output('fecha_de_comparacion1', component_property='options'),
    [Input('fecha_de_ejercicio2', component_property='value'),
    Input('call_put_radioitems2', component_property='value')]
)
    
def update_dropdown2 (val1,val2):
    
    select_values = {"fecha_de_ejercicio2": val1, 
                     "call_put_radioitems2": val2}
    
    df_call = volat_call[val1]
    df_put = volat_put[val1]
    
    if val2 == "CALL":
        dias_datos = []
        df = pd.DataFrame()
    
        for dia in volat_call_diaria.keys():

            if volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_call[val1].index,columns = ["Strike"]),pd.DataFrame(volat_call[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()
    else:
    
        dias_datos = []
        df = pd.DataFrame()
        for dia in volat_put_diaria.keys():

            if volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_put[val1].index,columns = ["Strike"]),pd.DataFrame(volat_put[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()

    
    
    return [{'label': i, 'value': i} for i in df["index"].unique()]

@app.callback(
    Output('fecha_de_comparacion2', component_property='options'),
    [Input('fecha_de_ejercicio2', component_property='value'),
    Input('call_put_radioitems2', component_property='value')])
    
def update_dropdown2 (val1,val2):
    
    select_values = {"fecha_de_ejercicio2": val1, 
                     "call_put_radioitems2": val2}
    
    df_call = volat_call[val1]
    df_put = volat_put[val1]
    
    if val2 == "CALL":
        dias_datos = []
        df = pd.DataFrame()
    
        for dia in volat_call_diaria.keys():

            if volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_call[val1].index,columns = ["Strike"]),pd.DataFrame(volat_call[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()
    else:
    
        dias_datos = []
        df = pd.DataFrame()
        for dia in volat_put_diaria.keys():

            if volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_put[val1].index,columns = ["Strike"]),pd.DataFrame(volat_put[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()
    
    return [{'label': i, 'value': i} for i in df["index"].unique()]

@app.callback(
    Output('my_graph3', component_property='figure'),
    Input('fecha_de_ejercicio2', component_property='value'),
    Input('call_put_radioitems2', component_property='value'),
    Input('fecha_de_comparacion1', component_property='value')
)

def update_graph3(val1,val2,val3):

    select_values = {"fecha_de_ejercicio2": val1, 
                     "call_put_radioitems2": val2,
                     'fecha_de_comparacion1': val3
                    }    
    df_call = volat_call[val1]
    df_put = volat_put[val1]
    

    if val2 == "CALL":
        dias_datos = []
        df = pd.DataFrame()

        for dia in volat_call_diaria.keys():

            if volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_call[val1].index,columns = ["Strike"]),pd.DataFrame(volat_call[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()
        df = df.loc[df.loc[:, 'index'] == val3]



        fig = px.line(df, 
              x=df.iloc[:,1], 
              y=df.iloc[:,2], 
              title = "Volatilidad implícita en función del Strike (Call)"
             )
    else:

        dias_datos = []
        df = pd.DataFrame()
        for dia in volat_put_diaria.keys():

            if volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_put[val1].index,columns = ["Strike"]),pd.DataFrame(volat_put[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()
        df = df.loc[df.loc[:, 'index'] == val3]

        fig = px.line(
              x=df.iloc[:,1], 
              y=df.iloc[:,2], 
              title = "Volatilidad implícita en función del Strike (Put)"
             )

    
    fig.update_layout(xaxis_title="Strike", 
                      yaxis_title="Volatilidad implícita",
                      plot_bgcolor= "white",
                      paper_bgcolor = "#F2F2F2",
                      font_color = "#00072D",
                      title_x = 0.5,
                      title_y = 0.85,
                      title_font_family="Times New Roman",
                      title_font_color="#00072D"
                     )
    
    fig.update_traces(line_color='#333957')
    fig.update_xaxes(linecolor='black', gridcolor='silver')
    fig.update_yaxes(linecolor='black', gridcolor='silver')
    return fig

@app.callback(
    Output('my_graph4', component_property='figure'),
    [Input('fecha_de_ejercicio2', component_property='value'),
    Input('call_put_radioitems2', component_property='value'),
    Input('fecha_de_comparacion2', component_property='value')])

def update_graph4(val1,val2,val3):

    select_values = {"fecha_de_ejercicio2": val1, 
                     "call_put_radioitems2": val2,
                     'fecha_de_comparacion2': val3
                    }    
    df_call = volat_call[val1]
    df_put = volat_put[val1]

    if val2 == "CALL":
        dias_datos = []
        df = pd.DataFrame()
    
        for dia in volat_call_diaria.keys():

            if volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_call_diaria[dia].loc[volat_call_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_call[val1].index,columns = ["Strike"]),pd.DataFrame(volat_call[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()
        df = df.loc[df.loc[:, 'index'] == val3]
    
        fig = px.line(df, 
              x=df.iloc[:,1], 
              y=df.iloc[:,2], 
              title = "Volatilidad implícita en función del Strike (Call)"
             )
        
    else:
    
        dias_datos = []
        df = pd.DataFrame()
        
        for dia in volat_put_diaria.keys():

            if volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1].empty == False:
                dias_datos.append(dia)
                volat_dia = volat_put_diaria[dia].loc[volat_put_diaria[dia].loc[:, 'Fecha'] == val1]
                volat_dia.index = [dia]*volat_dia.shape[0]
                df = pd.concat([df,volat_dia])

        df = df.drop(["Fecha"],axis = 1)
        df_dia = pd.concat([pd.DataFrame(volat_put[val1].index,columns = ["Strike"]),pd.DataFrame(volat_put[val1].values,columns = ["volat impli"])],axis = 1)
        df_dia.index = [date.today().strftime('%d/%m/%Y')]*df_dia.shape[0]
        df = pd.concat([df,df_dia])
        df = df.reset_index()
        df = df.loc[df.loc[:, 'index'] == val3]
    
        fig = px.line(df, 
              x=df.iloc[:,1], 
              y=df.iloc[:,2], 
              title = "Volatilidad implícita en función del Strike (Put)"
             )

    
    fig.update_layout(xaxis_title="Strike", 
                      yaxis_title="Volatilidad implícita",
                      plot_bgcolor= "white",
                      paper_bgcolor = "#F2F2F2",
                      font_color = "#00072D",
                      title_x = 0.5,
                      title_y = 0.85,
                      title_font_family="Times New Roman",
                      title_font_color="#00072D"
                     )
    
    fig.update_traces(line_color='#333957')
    fig.update_xaxes(linecolor='black', gridcolor='silver')
    fig.update_yaxes(linecolor='black', gridcolor='silver')
    return fig


if __name__ == '__main__':
    app.run(port= 8080,host='0.0.0.0',debug=True)
