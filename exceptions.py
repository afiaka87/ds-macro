# exceptions.py
class DSControllerError(Exception):
    """Base exception for DS controller errors"""

    pass


class MouseMovementError(DSControllerError):
    """Raised when mouse movement fails"""

    pass


class KeyboardError(DSControllerError):
    """Raised when keyboard input fails"""

    pass


class XdotoolError(DSControllerError):
    """Raised when xdotool command fails"""

    pass
