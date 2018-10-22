import logging
logging.getLogger().setLevel(logging.INFO)
import sys
import base64
import hashlib
import os

from flask import Flask, abort, make_response, jsonify, url_for, request, json, send_from_directory, send_file
from flask_jsontools import jsonapi

from rest_utils import register_encoder
from .API import API

VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))
OIDC_URL = os.environ['OIDC_URL']
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']

API_BASE=os.environ['API_BASE']
api = API()

USUARIOS_URL = os.environ['USERS_API_URL']


app = Flask(__name__)
app.debug = True
register_encoder(app)

DEBUGGING = bool(int(os.environ.get('VSC_DEBUGGING',0)))
def configurar_debugger():
    """
    para debuggear con visual studio code
    """
    if DEBUGGING:
        print('Iniciando Debugger PTVSD')
        import ptvsd
        #secret = os.environ.get('VSC_DEBUG_KEY',None)
        port = int(os.environ.get('VSC_DEBUGGING_PORT', 5678))
        ptvsd.enable_attach(address=('0.0.0.0',port))

configurar_debugger()



@app.route(API_BASE + '/<path:path>', methods=['OPTIONS'])
def options(path=None):
    if request.method == 'OPTIONS':
        return ('',204)
    return ('',204)



@app.route(API_BASE + '/verificar_dni/<dni>', methods=['GET'], provide_automatic_options=False)
@jsonapi
def verificar_dni(dni):

    query = '{}/usuarios/'.format(USUARIOS_URL) 
    r = api.get(query, params={'q':dni}, token=None)
    if not r.ok:
        return r
    usrs = r.json()
    usr = usrs[0] if len(usrs) else None
    if usr is None or 'tipo' not in usr or usr['tipo'] is None or usr['tipo'] != 'ingresante':
        return ('no permitido', 401)
    """
        setear cache redis con los datos del usuario y clave ingrsante_sesion : datos
    """
    
    return {
        'estado': ok,
        'sesion': 'dsfgdfgdfgdfgfdgfgdfg'
    }


@app.route(API_BASE + '/datos/<sesion>', methods=['GET'], provide_automatic_options=False)
@jsonapi
def obtener_datos(sesion):

    
    """
        se chequea redis por la existencia de los datos de usuario y se retorna junto con un id de sesion nuevo

        session = str(uuid.uuid4())



        datos = request.get_json()
        datos['sesion']
        datos['dni']
        datos[.....]
    """
    
    return {
        estado: ok,
        usuario: {dni:'',nombre:''}
    }


@app.route(API_BASE + '/datos/<sesion>', methods=['POST'], provide_automatic_options=False)
@jsonapi
def actualizar_datos(sesion):

    
    """
        datos = request.get_json()
        usuario = datos['usuario']
    """
    
    return {
        estado: ok        
    }

@app.route(API_BASE + 'datos/<sesion>/confirmar', methods=['POST'], provide_automatic_options=False)
@jsonapi
def confirmar_cambios(sesion):
    """
        datos = request.get_json()
        codigo = datos['codigo']
    """
    return {
        estado: ok
    }




@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET','POST','PUT','PATCH'])
def catch_all(path):
    return ('no permitido', 401)


def cors_after_request(response):
    if not response.headers.get('Access-Control-Allow-Origin',None):
        response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.after_request
def add_header(r):
    r = cors_after_request(r)
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'

    return r


'''
@app.route('/rutas', methods=['GET'])
@jsonapi
def rutas():
    links = []
    for rule in app.url_map.iter_rules():
        url = url_for(rule.endpoint, **(rule.defaults or {}))
        links.append(url)
    return links
'''

def main():
    app.run(host='0.0.0.0', port=10102, debug=False)

if __name__ == '__main__':
    main()
