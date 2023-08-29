from topshelfsoftware_util.exceptions import ModuleError


class WorksheetNotFoundError(ModuleError):
    """Raised to indicate an Excel worksheet was not found."""
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return(repr(self.value))
