"""
The backend of the daily tracker application.
"""
import abc
from typing import ClassVar


# sourcery skip: upper-camel-case-classes
class API:
    """
    Implementation to automatically bind the integration objects to the
    ``Input`` and ``Output`` objects.
    """

    # noinspection PyUnresolvedReferences
    def __init_subclass__(cls, **kwargs) -> None:
        cls.APIS[cls.__name__.lower()] = cls
        return super().__init_subclass__(**kwargs)


class IInput(abc.ABC):
    """
    Abstract base class for objects whose methods need to be resolved before the
    form is generated.
    """

    @abc.abstractmethod
    def generate_actions(self) -> None:
        """
        The actions to perform before the form is generated.
        """
        pass


class IOutput(abc.ABC):
    """
    Abstract base class for objects whose methods need to be resolved after the
    form is closed.
    """

    @abc.abstractmethod
    def ok_actions(self) -> None:
        """
        The actions to perform after the form is closed.
        """
        pass


class Input(API, IInput):
    """
    Objects whose methods need to be resolved before the form is generated.
    """

    APIS: ClassVar = {}

    def generate_actions(self) -> None:
        """
        The actions to perform before the form is generated.
        """
        pass


class Output(API, IOutput):
    """
    Objects whose methods need to be resolved after the form is closed.
    """

    APIS: ClassVar = {}

    def ok_actions(self) -> None:
        """
        The actions to perform after the form is closed.
        """
        pass


class Outlook(Input):
    # Test the code above
    pass


print(Input.APIS["outlook"])
