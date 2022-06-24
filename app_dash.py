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
import sys
import os

sys.path.append("c:\\Users\\MARIO\\Desktop\\AplicacionDash\\funciones")

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
# Defining the html contents of a URL.
xhtml = url_get_contents('https://www.meff.es/esp/Derivados-Financieros/Ficha/FIEM_MiniIbex_35').decode('utf-8')

# Defining the HTMLTableParser object
p = HTMLTableParser()

# feeding the html contents in the
# HTMLTableParser object
p.feed(xhtml)

u = p.tables[1][2:len(p.tables[1])]
u = u[0:len(u)-2]
# Para volverlos float
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

#
df1 = pd.DataFrame(futuros.values,columns = ["Vencimiento", "Tipo", "Ord.(Compra)", "Vol.(Compra)", "Precio(Compra)", "Precio(Venta)", "Vol.(Venta)", "Ord.(Venta)", "Últ.", "Vol.", "Aper.", "Máx.", "Min.", "Ant."])
df1.drop(df1.tail(1).index,inplace=True)

# Creación de la app
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
        Además, se calcula la volatilidad implícita mediante el modelo de Black-Scholes
        de las opciones PUT y CAll en la fecha de vencimiento seleccionada.
    '''], className = "descripcion" ),
     
    html.Div(children = [
        
        html.H4(children='FUTUROS',  
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
        
        html.H4(children='OPCIONES', 
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
                     figure = {},style = {"margin-top": 60})], 
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
        className = "create_container4" )
    
    ], className = "create_container1"),
    

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


if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 8080)),host='0.0.0.0',debug=True)

