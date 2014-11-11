class PutIsPatchMixin(object):
    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
