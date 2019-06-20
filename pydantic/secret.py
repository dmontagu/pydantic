from typing import TypeVar, Generic, Type, Union, Any, Tuple, TYPE_CHECKING

from pydantic import ValidationError
from pydantic.generics import GenericModel

T = TypeVar("T")
S = TypeVar("S")
SecretT = TypeVar("SecretT", bound="Secret[Any]")


class GenericSecret(GenericModel, Generic[T]):  # type
    secret_value: T

    def __init__(self, value: T):
        super().__init__(secret_value=value)

    def __repr__(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__repr__()

    def display(self) -> str:
        return '**********'

    def get_secret_value(self) -> T:
        return self.secret_value


class Secret(Generic[T]):
    if TYPE_CHECKING:
        def __init__(self, value: T):
            ...

        def __repr__(self) -> str:
            ...

        def __str__(self) -> str:
            ...

        def display(self) -> str:
            ...

        def get_secret_value(self) -> T:
            ...

    def __class_getitem__(  # type: ignore
        cls: Type["Secret[T]"], param: Union[Type[Any], Tuple[Type[Any], ...]]
    ) -> Type["GenericSecret[T]"]:
        if isinstance(param, tuple):
            assert len(param) == 1
            param = param[0]
        param_str = param.__name__ if hasattr(param, "__name__") else str(param)

        class _Secret(GenericSecret[param]):  # type: ignore
            def __repr__(self) -> str:
                return f'Secret[{param_str}](\'**********\')'

        return _Secret


str_secret = Secret[str]("a")
print(f"{str_secret}: secret_value = {str_secret.get_secret_value()}")
int_secret = Secret[int](1)
print(f"{int_secret}: secret_value = {int_secret.get_secret_value()}")
try:
    print(Secret[int]("a"))
except ValidationError as e:
    print(e)

"""
Secret[str]('**********')
a
Secret[int]('**********')
1 validation error
secret_value
  value is not a valid integer (type=type_error.integer)
"""

"""
mypy output:
generic_secret.py:68: error: Argument 1 to "Secret" has incompatible type "str"; expected "int"
"""
