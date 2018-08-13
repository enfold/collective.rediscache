import time

from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.config import getConfiguration
from App.special_dtml import DTMLFile
from OFS.Cache import Cache
from OFS.Cache import CacheManager
from OFS.SimpleItem import SimpleItem


caches = {}
DEFAULT_URL = 'redis://127.0.0.1:6379'
KEY_PREFIX = 'collective.rediscache:'


redis_cache = make_region(
    name='collective.rediscache',
    key_mangler=lambda key: KEY_PREFIX + key,
)


def init_cache():
    zope_conf = getConfiguration()
    product_conf = getattr(zope_conf, 'product_config', {})
    cache_conf = product_conf.get('collective.rediscache', {})
    redis_url = cache_conf.get('redis_url', DEFAULT_URL)
    expiration_time = cache_conf.get('expiration_time', 300)
    cache = redis_cache.configure(
        'dogpile.cache.redis',
        expiration_time=int(expiration_time),
        arguments={
            'url': redis_url,
            'distributed_lock': True,
        }
    )
    return cache


class RedisCache(Cache):
    max_age = 0

    def __init__(self):
        self.cache = redis_cache
        self.next_cleanup = 0

    def initSettings(self, kw):
        self.__dict__.update(kw)

    def get_key(self, ob, view_name, keywords):
        if not view_name:
            view_name = '__default__'
        path = ob.absolute_url_path()
        req = getattr(ob, 'REQUEST', None)
        req_vals = '|'
        for key in self.request_vars:
            if req is None:
                val = ''
            else:
                val = req.get(key, '')
            req_vals += "%s %s " % ((str(key), str(val)))
        keyword_vals = ''
        if keywords:
            keyword_vals = '|'
            for key, val in keywords.items():
                keyword_vals += "%s %s " % ((str(key), str(val)))
        return path + ':' + view_name + req_vals + keyword_vals

    def ZCache_invalidate(self, ob):
        '''
        Invalidates the cache entries that apply to ob.
        '''
        path = ob.absolute_url_path()
        regex = "%s%s*" % (KEY_PREFIX, path)
        # need to get the client because scanning for regex
        client = self.cache.backend.client
        entries = client.scan_iter(match=regex)
        for entry in entries:
            # delete goes through key mangler, so get rid of prefix
            self.cache.delete(entry[len(KEY_PREFIX):])

    def ZCache_get(self, ob, view_name='', keywords=None,
                   mtime_func=None, default=None):
        '''
        Gets a cache entry or returns default.
        '''
        key = self.get_key(ob, view_name, keywords)
        value = self.cache.get(key)
        if value is NO_VALUE:
            value = default
        return value

    def ZCache_set(self, ob, data, view_name='', keywords=None,
                   mtime_func=None):
        '''
        Sets a cache entry.
        '''
        key = self.get_key(ob, view_name, keywords)
        self.cache.set(key, data)


class RedisCacheManager(CacheManager, SimpleItem):
    """Manage a RedisCache, which stores rendered data in redis.

    This is intended to be used as a low-level cache for
    expensive Python code, not for objects published
    under their own URLs such as web pages.

    RedisCacheManager *can* be used to cache complete publishable
    pages, such as DTMLMethods/Documents and Page Templates,
    but this is not advised: such objects typically do not attempt
    to cache important out-of-band data such as 3xx HTTP responses,
    and the client would get an erroneous 200 response.

    Such objects should instead be cached with an
    AcceleratedHTTPCacheManager and/or downstream
    caching.
    """

    security = ClassSecurityInfo()
    security.setPermissionDefault('Change cache managers', ('Manager', ))

    manage_options = (
        {'label': 'Properties', 'action': 'manage_main'},
    ) + CacheManager.manage_options + SimpleItem.manage_options

    meta_type = 'Redis Cache Manager'

    def __init__(self, ob_id):
        self.id = ob_id
        self.title = ''
        self._settings = {
            'request_vars': ('AUTHENTICATED_USER', ),
            }
        self._resetCacheId()

    def getId(self):
        ' '
        return self.id

    security.declarePrivate('_remove_data')
    def _remove_data(self):
        caches.pop(self.__cacheid, None)

    security.declarePrivate('_resetCacheId')
    def _resetCacheId(self):
        self.__cacheid = '%s_%f' % (id(self), time.time())

    ZCacheManager_getCache__roles__ = ()
    def ZCacheManager_getCache(self):
        cacheid = self.__cacheid
        try:
            return caches[cacheid]
        except KeyError:
            cache = RedisCache()
            cache.initSettings(self._settings)
            caches[cacheid] = cache
            return cache

    security.declareProtected(view_management_screens, 'getSettings')
    def getSettings(self):
        'Returns the current cache settings.'
        res = self._settings.copy()
        return res

    security.declareProtected('Change cache managers', 'manage_editProps')
    def manage_editProps(self, title, settings=None, REQUEST=None):
        'Changes the cache settings.'
        if settings is None:
            settings = REQUEST
        self.title = str(title)
        request_vars = list(settings['request_vars'])
        request_vars.sort()
        self._settings = {
            'request_vars': tuple(request_vars),
            }
        cache = self.ZCacheManager_getCache()
        cache.initSettings(self._settings)
        if REQUEST is not None:
            return self.manage_main(
                self, REQUEST, manage_tabs_message='Properties changed.')

    security.declareProtected(view_management_screens, 'manage_main')
    manage_main = DTMLFile('dtml/propsRCM', globals())


InitializeClass(RedisCacheManager)


manage_addRedisCacheManagerForm = DTMLFile('dtml/addRCM', globals())


def manage_addRedisCacheManager(self, id, REQUEST=None):
    'Adds a Redis cache manager to the folder.'
    self._setObject(id, RedisCacheManager(id))
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)
