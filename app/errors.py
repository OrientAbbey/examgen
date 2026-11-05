class ApiError(Exception):
    """Erreur métier convertie en réponse JSON {code, message, ...}."""

    def __init__(self, status: int, code: str, message: str = "", **extra):
        super().__init__(code)
        self.status, self.code, self.message, self.extra = status, code, message or code, extra
