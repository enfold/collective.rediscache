from . import cachemanager


def initialize(context):
    context.registerClass(
        cachemanager.RedisCacheManager,
        constructors=(cachemanager.manage_addRedisCacheManagerForm,
                      cachemanager.manage_addRedisCacheManager),
        icon="cache.gif"
    )
    cachemanager.init_cache()
