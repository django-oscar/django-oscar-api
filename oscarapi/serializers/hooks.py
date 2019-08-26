def entity_internal_value(attribute, value):
    raise NotImplementedError(
        "Writable Entity support requires a manual implementation, "
        "because it is not possible to guess how the value "
        "sent should be interpreted. You can override "
        "'oscarapi.serializers.hooks.entity_internal_value' to provide an implementation"
    )
