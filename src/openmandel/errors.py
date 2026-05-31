class OpenmandelError(Exception):
    pass


class ValidationError(OpenmandelError):
    pass


class PathSecurityError(OpenmandelError):
    pass


class RenderError(OpenmandelError):
    pass
