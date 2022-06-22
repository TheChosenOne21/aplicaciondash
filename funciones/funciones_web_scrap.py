# Opens a website and read its
# binary contents (HTTP Response Body)
import pandas as pd
import urllib3
import math
import urllib.request


def url_get_contents(url):

    # Opens a website and read its
    # binary contents (HTTP Response Body)

    #making request to the website
    req = urllib.request.Request(url=url)
    f = urllib.request.urlopen(req)

    #reading contents of the website
    return f.read()

def filtro_opc_por_dias (precios_opc, dias_opc):
    
    precios_dias = {}
    lst = [0]
    
    # Se obtienen los índices que dividen los datos de las opciones por días
    for i in range(1,len(precios_opc["Strike"])):
        anterior = precios_opc["Strike"][i-1]
        if precios_opc["Strike"][i] < anterior:
            lst.append(i)
    lst.append(len(precios_opc["Strike"])-1)
    
    # Con los .indices se indexan los datos y se guardan en un diccionario
    # Se obtiene un diccionario donde la clave es el dia 
    # y tiene asociado los datos de las opciones correspondientes a ese día
    for i in range(len(dias_opc)-1):
        if (precios_opc.iloc[lst[i]:lst[i+1],:].empty == False) and (len(precios_opc.iloc[lst[i]:lst[i+1],:]) >= 3)  :
            precios_dias[dias_opc[i]] = precios_opc.iloc[lst[i]:lst[i+1],:]
    
    return precios_dias

def round_up(n, decimals = 0):  
    multiplier = 10 ** decimals  
    return math.ceil(n * multiplier) / multiplier
def round_down(n, decimals=0): 
    multiplier = 10 ** decimals 
    return math.floor(n * multiplier) / multiplier 

def obtener_call_put_data (precios_dias,datos_futuro):
    datos_call_put = {}
    datos_completos = {}
    precio_fut = round_up(datos_futuro["Ant."].values[0], decimals = -2)
    for dia in precios_dias.keys():
        
        strike_index = precios_dias[dia]["Strike"].unique()
        contador = 0
        put = []
        call = []
        datos_call_put = {}
        
        for valor in strike_index:

            if valor < precio_fut:

                datos = precios_dias[dia][precios_dias[dia]["Strike"] == valor]

                if datos.shape[0] == 1:

                    if datos.iloc[0,12] == "-":
                        put.append(datos)

                    elif datos.iloc[0,12] <= 75 :
                        put.append(datos)
                    else:
                        call.append

                elif datos.shape[0] >= 2:

                    if (datos.iloc[0,12] == "-"):

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([1],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([0],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)

                    elif (datos.iloc[1,12] == "-") :

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([0],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([1],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)

                    elif datos.iloc[0,12] <= datos.iloc[1,12] :

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([1],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([0],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)

                    elif datos.iloc[0,12] > datos.iloc[1,12] :

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([0],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([1],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)

            elif valor >= precio_fut:

                datos = precios_dias[dia][precios_dias[dia]["Strike"] == valor]

                if datos.shape[0] == 1:

                    if datos.iloc[0,12] == "-":

                        call.append(datos)
                    
                    elif datos.iloc[0,12] <= 75 :
                        call.append(datos)
                    else:
                        put.append

                elif datos.shape[0] >= 2:

                    if (datos.iloc[0,12] == "-"):

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([0],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([1],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)

                    elif (datos.iloc[1,12] == "-"):

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([1],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([0],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)        


                    elif datos.iloc[0,12] <= datos.iloc[1,12] :

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([0],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([1],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)    

                    elif datos.iloc[0,12] > datos.iloc[1,12] :

                        datos_put = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_put = datos_put.drop([1],axis=0)

                        datos_call = datos.reset_index(inplace=False, drop=False).drop("index",axis = 1)
                        datos_call = datos_call.drop([0],axis=0)

                        put.append(datos_put)
                        call.append(datos_call)  
            contador +=1
        datos_put = pd.DataFrame(columns = ['Strike',
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
                                    'Ant.'])                           
        datos_call = pd.DataFrame(columns = ['Strike',
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
                                    'Ant.'])

        datos_call_put["CALL"] = datos_call.append(call).reset_index().drop("index",axis = 1)        
        datos_call_put["PUT"] = datos_put.append(put).reset_index().drop("index",axis = 1)
        datos_completos[dia] = datos_call_put
    return datos_completos