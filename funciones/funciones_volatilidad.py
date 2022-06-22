import datetime
import pandas as pd
import mibian
from datetime import date
import sys


def BS_CALL(k, s, t, r, p):
    """ 
    BS - Black-Scholes        
    Used for pricing European options on stocks without dividends
    k: Underlying price. ANT
    s: Strike Price. Precio de strike
    r: Interest Rate. Tasa de interes
    t: Days to expiration. Delta tiempo
    p: Call price. Precio subyacente ANT Futuro
   
    """
    #Returns the implied volatility from the call price
    volatilidad = mibian.BS([k, s, r, t], callPrice=p)
    return volatilidad.impliedVolatility

def BS_PUT(k, s, t, r, p):
    """ 
    BS - Black-Scholes        
    Used for pricing European options on stocks without dividends
    k: Underlying price. ANT
    s: Strike Price. Precio de strike
    r: Interest Rate. Tasa de interes
    t: Days to expiration. Delta tiempo
    p: Put price. Precio subyacente ANT Futuro
   
    """
    #Returns the implied volatility from the put price
    volatilidad = mibian.BS([k, s, r, t], putPrice = p)
    
    return volatilidad.impliedVolatility

def volat_opciones_call(datos_completos,datos_futuro,tasa_interes=0):
    
    volat_opc_call = {}
    for dia in datos_completos.keys():
        
        r = tasa_interes
        k = datos_futuro["Ant."].values[0]
        t = (datetime.datetime.strptime(dia,"%d/%m/%Y").date() - date.today()).days
        datos_necesarios = datos_completos[dia]["CALL"][["Strike","Ant."]]
        volat_impl = []
        strike_index = []
        
        for i in range(datos_necesarios.shape[0]):
            p = datos_necesarios["Ant."][i]
            s = datos_necesarios["Strike"][i]
            if p != "-" and t > 0:
                volat_impl.append(BS_CALL(k, s, t, r, p))
                strike_index.append(s)
            if pd.DataFrame(volat_impl,index = strike_index).empty == False:            
                volat_opc_call[dia] = pd.DataFrame(volat_impl,index = strike_index)

    return volat_opc_call

def volat_opciones_put(datos_completos,datos_futuro,tasa_interes=0):
    
    volat_opc_put = {}
    for dia in datos_completos.keys():
        
        r = tasa_interes
        k = datos_futuro["Ant."].values[0]
        t = (datetime.datetime.strptime(dia,"%d/%m/%Y").date() - date.today()).days
        datos_necesarios = datos_completos[dia]["PUT"][["Strike","Ant."]]
        volat_impl = []
        strike_index = []
        
        for i in range(datos_necesarios.shape[0]):
            p = datos_necesarios["Ant."][i]
            s = datos_necesarios["Strike"][i]
            if p != "-" and t > 0:
                volat_impl.append(BS_PUT(k, s, t, r, p))
                strike_index.append(s)
        if pd.DataFrame(volat_impl,index = strike_index).empty == False:            
            volat_opc_put[dia] = pd.DataFrame(volat_impl,index = strike_index)

    return volat_opc_put
