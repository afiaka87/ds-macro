# exceptions.py
class DSControllerError(Exception):
    """Base exception for DS controller errors"""

    pass


class RoutineError(DSControllerError):
    """Raised when a routine cannot be executed properly"""

    pass


class RegistryError(DSControllerError):
    """Raised when there's an issue with the routine registry"""

    pass


class ActionError(DSControllerError):
    """Base exception for action execution errors"""

    pass


class MouseMovementError(ActionError):
    """Raised when mouse movement fails"""

    pass


class KeyboardError(ActionError):
    """Raised when keyboard input fails"""

    pass


class XdotoolError(ActionError):
    """Raised when xdotool command fails"""

    pass


class ConfigurationError(DSControllerError):
    """Raised when there's an issue with configuration"""

    pass


class ParallelExecutionError(ActionError):
    """Raised when parallel execution of actions fails"""

    pass
