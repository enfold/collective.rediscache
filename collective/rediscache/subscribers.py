def cloned(obj, event):
    """
    Reset the Id of the module level cache so the clone gets a different cache
    than its source object
    """
    obj._resetCacheId()


def removed(obj, event):
    obj._remove_data()
