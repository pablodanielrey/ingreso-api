
import redis

class UserCache:

    def __init__(self, host, port, users_getter, ingresante_getter_sesion, timeout=60 * 60):
        self.redis_ = redis.StrictRedis(host=host, port=port, decode_responses=True)
        self.getter_usuario = users_getter
        self.getter_ingresante_sesion = ingresante_getter_sesion
        self.timeout = timeout

    def _setear_usuario_cache(self, usr, sid):
        uk = 'usuario_uid_{}'.format(usr['id'])
        self.redis_.hmset(uk, usr)
        self.redis_.expire(uk, self.timeout)
        
        uk = 'ingresante_sesion_{}'.format(sid)
        self.redis_.hset(uk, 'uid', usr['id'])
        self.redis_.expire(uk, self.timeout)

    def obtener_usuario_por_uid(self, uid, token=None):
        usr = self.redis_.hgetall('usuario_uid_{}'.format(uid))
        if len(usr.keys()) > 0:
            return usr

        usr = self.getter_usuario(uid, token=token)
        if not usr:
            return None
        self._setear_usuario_cache(usr)
        return usr

    def obtener_usuario_por_sesion(self, sid, token=None):
        key = 'ingresante_sesion_{}'.format(sid)
        if self.redis_.hexists(key,'uid'):
            uid = self.redis_.hget(key,'uid')
            return self.obtener_usuario_por_uid(uid, token=token)

        usr = self.getter_ingresante_sesion(sid, token=token)
        if not usr:
            return None
        self._setear_usuario_cache(usr)
        return usr

    def actualizar_datos_sesion(self, sid, correo, clave, codigo):
        key = 'ingresante_sesion_{}'.format(sid)
        self.redis_.hset(key, 'correo', correo)
        self.redis_.hset(key, 'clave', clave)
        self.redis_.hset(key, 'codigo', codigo)

    
    def obtener_ingresante_por_sesion(self, sid, token=None):
        info = self.redis_.hgetall('ingresante_sesion_{}'.format(sid))
        if len(info.keys()) > 0:
            return info
        else:
            return None        
