from rest_framework.exceptions import _get_error_details


class FieldError(Exception):
    default_code = "field_error"

    def __init__(self, detail, code=None):
        if code is None:
            code = self.default_code

        self.code = code
        self.detail = _get_error_details(detail, code)
        super(FieldError, self).__init__(self.detail)
