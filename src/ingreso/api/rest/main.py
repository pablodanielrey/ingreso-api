import logging
logging.getLogger().setLevel(logging.INFO)
import sys
import base64
import hashlib
import os
import uuid
from flask import Flask, abort, make_response, jsonify, url_for, request, json, send_from_directory, send_file
from flask_jsontools import jsonapi
from rest_utils import register_encoder
from .API import API
from .UserCache import UserCache
from ingreso.model.MailsModel import MailsModel

VERIFY_SSL = bool(int(os.environ.get('VERIFY_SSL',0)))
OIDC_URL = os.environ['OIDC_URL']
client_id = os.environ['OIDC_CLIENT_ID']
client_secret = os.environ['OIDC_CLIENT_SECRET']

API_BASE=os.environ['API_BASE']
api = API()

USUARIOS_URL = os.environ['USERS_API_URL']
LOGIN_URL = os.environ['LOGIN_API_URL']
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

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

"""
    /////////// los getters de la cache //////////
"""

def _get_user_uuid(uuid, token=None):
    query = '{}/usuarios/{}'.format(USUARIOS_URL, uuid)
    r = api.get(query, token=token)
    if not r.ok:
        return None
    usr = r.json()        
    return usr

def _ingresante_getter_sesion(sid, token=None):
    return None

cache = UserCache(REDIS_HOST, REDIS_PORT, _get_user_uuid, _ingresante_getter_sesion)


def _parsear_usuario(usr):
    return {
        'id': usr['id'],
        'nombre': usr['nombre'],
        'apellido': usr['apellido'],
        'dni': usr['dni'],
        'genero': usr['genero'],
        'correos': usr['mails']

    }

@app.route(API_BASE + '/verificar_dni/<dni>', methods=['GET'], provide_automatic_options=False)
@jsonapi
def verificar_dni(dni):

    query = '{}/usuario_por_dni/{}'.format(USUARIOS_URL, dni)
    r = api.get(query, token=None)
    if not r.ok:
        return r
    usr = r.json()
    if ((usr is None) or ('tipo' not in usr) or (usr['tipo'] is None) or (usr['tipo'] != 'ingresante')):
        return ('no permitido', 401)

    '''
    Verifico de que no tenga correo
    '''
    query = '{}/usuarios/{}/precondiciones'.format(USUARIOS_URL, usr['id']) 
    r = api.get(query, token=None)
    if not r.ok:
        return r
    pre_json = r.json()
    if 'correo' in pre_json and pre_json['correo']:
        return ('el usuario ya fue registrado', 401)
    

    sid = str(uuid.uuid4())[:8]
    u = _parsear_usuario(usr)
    cache._setear_usuario_cache(u, sid)    
    return {
        'estado': 'ok',
        'sesion': sid
    }


@app.route(API_BASE + '/datos/<sesion>', methods=['GET'], provide_automatic_options=False)
@jsonapi
def obtener_datos(sesion):
    usr = cache.obtener_usuario_por_sesion(sesion)
    if usr is None: 
        return ('usuario no encontrado', 404)    
    
    return {
        'sesion': sesion,
        'usuario': usr
    }


@app.route(API_BASE + '/datos/<sesion>', methods=['POST'], provide_automatic_options=False)
@jsonapi
def actualizar_datos(sesion):
    """
    usr: {
        'clave': contraseña ingresada,
        'correo': correo ingresado,
        'genero': genero de la persona
    }
    """
    usr = request.get_json()
    usuario = cache.obtener_usuario_por_sesion(sesion)
    if usuario is None:
        return ('usuario no encontrado', 404)    
    
    codigo = str(uuid.uuid4())[:5]
    usuario['genero'] = usr['genero']
    cache._setear_usuario_cache(usuario, sesion)    
    cache.actualizar_datos_sesion(sid=sesion, correo=usr['correo'], clave=usr['clave'], codigo=codigo)    

    
    '''
    Enviar correo con el codigo de confirmacion
    '''

    mail = usr['correo']
    nombre = usuario['nombre'] + ' ' + usuario['apellido']
    tmpl = cuerpo = MailsModel.obtener_template('confirmar_correo.tmpl')
    cuerpo = tmpl.render(nombre=nombre, codigo=codigo)
    MailsModel.enviar_correo('sistemas@econo.unlp.edu.ar', mail, 'Ingreso FCE', cuerpo)    

    return {
        'estado': 'ok'
    }

@app.route(API_BASE + '/sesion/<sesion>/correo', methods=['GET'], provide_automatic_options=False)
@jsonapi
def obtner_correo_sesion(sesion):

    info = cache.obtener_ingresante_por_sesion(sesion)
    if info is None:
        return ('inválido',401) 

    if 'correo' in info:
        return info['correo']

    return None   

@app.route(API_BASE + '/datos/<sesion>/confirmar', methods=['POST'], provide_automatic_options=False)
@jsonapi
def confirmar_cambios(sesion):

    datos = request.get_json()
    codigo = datos['codigo']

    info = cache.obtener_ingresante_por_sesion(sesion)

    if info is None:
        return ('inválido',401)

    if 'codigo' not in info or info['codigo'] != codigo:
        return ('código incorrecto',401)

    # persistir usuario
    usr = cache.obtener_usuario_por_sesion(sesion)
    if usr is None:
        return ('inválido',401)

    query = '{}/usuarios/{}'.format(USUARIOS_URL, usr['id']) 
    r = api.post(query, data=usr)

    if not r.ok:
        return r

    # persistir clave
    query = '{}/usuario/{}/clave'.format(LOGIN_URL, info['uid']) 
    r = api.post(query, data={'clave':info['clave']})

    if not r.ok:
        return r
        
    # persistir correo
    query = '{}/usuarios/{}/correos/sin_confirmacion'.format(USUARIOS_URL, info['uid']) 
    r = api.post(query, data={'email':info['correo']})

    if not r.ok:
        return r

    """
    enviar correo de finalización
    """
    
    mail = info['correo']
    usuario = usr['dni']
    clave = info['clave']
    nombre = usr['nombre'] + ' ' + usr['apellido']
    tmpl = cuerpo = MailsModel.obtener_template('finalizacion.tmpl')
    cuerpo = tmpl.render(nombre=nombre, codigo=codigo, usuario=usuario, clave=clave)
    MailsModel.enviar_correo('sistemas@econo.unlp.edu.ar', mail, 'Bienvenido a FCE', cuerpo)    
    

    return { 'estado': 'ok' }

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
