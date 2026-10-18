"""Stable error codes for the implemented kernel foundation."""


class KernelError(Exception):
    """A stable code and read-only scientific context; preserve backend causes."""

    code = "kernel_error"

    def __init__(self, message, *, provider=None, object_key=None, time=None, resource=None):
        super().__init__(message)
        self._context = (str(message), provider, object_key, time, resource)

    def __setattr__(self, name, value):
        if name in {"code", "message", "provider", "object_key", "time", "resource"}:
            raise AttributeError("kernel error context is read-only")
        if name == "_context" and hasattr(self, "_context"):
            raise AttributeError("kernel error context is read-only")
        super().__setattr__(name, value)

    message = property(lambda self: self._context[0])
    provider = property(lambda self: self._context[1])
    object_key = property(lambda self: self._context[2])
    time = property(lambda self: self._context[3])
    resource = property(lambda self: self._context[4])


class InvalidQuery(KernelError):
    code = "invalid_query"


class UnknownObject(KernelError):
    code = "unknown_object"


class UnsupportedCapability(KernelError):
    code = "unsupported_capability"


class IncompatibleContract(KernelError):
    code = "incompatible_contract"


class ResourceMismatch(KernelError):
    code = "resource_mismatch"


class OutsideCoverage(KernelError):
    code = "outside_coverage"


class TimeConversionUnavailable(KernelError):
    code = "time_conversion_unavailable"


class AccuracyUnavailable(KernelError):
    code = "accuracy_unavailable"


class ProviderEvaluationError(KernelError):
    code = "provider_evaluation_error"


class InvalidProviderResult(KernelError):
    code = "invalid_provider_result"


class ProviderBusy(KernelError):
    code = "provider_busy"


class ClosedSession(KernelError):
    code = "closed_session"
