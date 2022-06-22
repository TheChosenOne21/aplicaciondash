__all__ = ['funciones_volatilidad', 'funciones_web_scrap']
# deprecated to keep older scripts who import this from breaking
from funciones.funciones_web_scrap import url_get_contents, filtro_opc_por_dias, obtener_call_put_data
from funciones.funciones_volatilidad import BS_CALL, BS_PUT, volat_opciones_call, volat_opciones_put 