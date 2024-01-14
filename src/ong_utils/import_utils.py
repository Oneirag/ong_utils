"""
Exception and a function to deal with lack of imports
"""


class AdditionalRequirementException(Exception):
    """Class for exceptions for lack or extras install (missing dependencies)"""
    pass


def raise_extra_exception(extras: str):
    """Raises exception for the user to install some extras"""
    raise AdditionalRequirementException(
        f"Missing dependencies. Please install extra requirements with 'pip install ong_utils[{extras}]'")


def raise_extra_install(extras: str):
    """Function to raise exception for the user to install some extras. Used to replace original function
    when dependencies are not met"""
    def f(*args, **kwargs):
        raise_extra_exception(extras)
    return f
