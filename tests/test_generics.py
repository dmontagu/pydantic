import sys
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

import pytest

from pydantic import BaseModel, ValidationError, validator
from pydantic.generics import GenericModel, _generic_types_cache

skip_36 = pytest.mark.skipif(sys.version_info < (3, 7), reason='generics only supported for python 3.7 and above')


@skip_36
def test_generic_name():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

    assert Result[List[int]].__name__ == 'Result[typing.List[int]]'


@skip_36
def test_double_parameterize_error():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

    with pytest.raises(TypeError) as exc_info:
        Result[int][int]

    assert str(exc_info.value) == 'Cannot parameterize a concrete instantiation of a generic model'


@skip_36
def test_methods_are_inherited():
    class CustomGenericModel(GenericModel):
        def method(self):
            return self.data

    T = TypeVar('T')

    class Model(CustomGenericModel, Generic[T]):
        data: T

    instance = Model[int](data=1)

    assert instance.method() == 1


@skip_36
def test_config_is_inherited():
    class CustomGenericModel(GenericModel):
        class Config:
            allow_mutation = False

    T = TypeVar('T')

    class Model(CustomGenericModel, Generic[T]):
        data: T

    instance = Model[int](data=1)

    with pytest.raises(TypeError) as exc_info:
        instance.data = 2

    assert str(exc_info.value) == '"Model[int]" is immutable and does not support item assignment'


@skip_36
def test_must_inherit_from_generic():
    with pytest.raises(TypeError) as exc_info:

        class Result(GenericModel):
            pass

        Result[int]

    assert str(exc_info.value) == f'Type Result must inherit from typing.Generic before being parameterized'


@skip_36
def test_parameters_must_be_typevar():
    T = TypeVar('T')
    with pytest.raises(TypeError) as exc_info:

        class Result(GenericModel[T]):
            pass

    assert str(exc_info.value) == f'Type parameters should be placed on typing.Generic, not GenericModel'


@skip_36
def test_parameter_count():
    T = TypeVar('T')
    S = TypeVar('S')

    class Model(GenericModel, Generic[T, S]):
        x: T
        y: S

    with pytest.raises(TypeError) as exc_info:
        Model[int, int, int]
    assert str(exc_info.value) == 'Too many parameters for Model; actual 3, expected 2'

    with pytest.raises(TypeError) as exc_info:
        Model[int]
    assert str(exc_info.value) == 'Too few parameters for Model; actual 1, expected 2'


@skip_36
def test_cover_cache():
    cache_size = len(_generic_types_cache)
    T = TypeVar('T')

    class Model(GenericModel, Generic[T]):
        x: T

    Model[int]  # adds both with-tuple and without-tuple version to cache
    assert len(_generic_types_cache) == cache_size + 2
    Model[int]  # uses the cache
    assert len(_generic_types_cache) == cache_size + 2


@skip_36
def test_generic_config():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

        class Config:
            allow_mutation = False

    result = Result[int](data=1)
    assert result.data == 1
    with pytest.raises(TypeError):
        result.data = 2


@skip_36
def test_generic_instantiation_error():
    with pytest.raises(TypeError) as exc_info:
        GenericModel()
    assert str(exc_info.value) == 'Type GenericModel cannot be used without generic parameters, e.g. GenericModel[T]'


@skip_36
def test_parameterized_generic_instantiation_error():
    data_type = TypeVar('data_type')

    class Result(GenericModel, Generic[data_type]):
        data: data_type

    with pytest.raises(TypeError) as exc_info:
        Result(data=1)
    assert str(exc_info.value) == 'Type Result cannot be used without generic parameters, e.g. Result[T]'


@skip_36
def test_deep_generic():
    T = TypeVar('T')
    S = TypeVar('S')
    R = TypeVar('R')

    class OuterModel(GenericModel, Generic[T, S, R]):
        a: Dict[R, Optional[List[T]]]
        b: Optional[Union[S, R]]
        c: R
        d: float

    class InnerModel(GenericModel, Generic[T, R]):
        c: T
        d: R

    class NormalModel(BaseModel):
        e: int
        f: str

    inner_model = InnerModel[int, str]
    generic_model = OuterModel[inner_model, NormalModel, int]

    inner_models = [inner_model(c=1, d='a')]
    generic_model(a={1: inner_models, 2: None}, b=None, c=1, d=1.5)
    generic_model(a={}, b=NormalModel(e=1, f='a'), c=1, d=1.5)
    generic_model(a={}, b=1, c=1, d=1.5)


@skip_36
def test_enum_generic():
    T = TypeVar('T')

    class MyEnum(Enum):
        x = 1
        y = 2

    class Model(GenericModel, Generic[T]):
        enum: T

    Model[MyEnum](enum=MyEnum.x)
    Model[MyEnum](enum=2)


@skip_36
def test_generic():
    data_type = TypeVar('data_type')
    error_type = TypeVar('error_type')

    class Result(GenericModel, Generic[data_type, error_type]):
        data: Optional[List[data_type]]
        error: Optional[error_type]
        positive_number: int

        @validator('error', always=True)
        def validate_error(cls, v: Optional[error_type], values: Dict[str, Any]) -> Optional[error_type]:
            if values.get('data', None) is None and v is None:
                raise ValueError('Must provide data or error')
            if values.get('data', None) is not None and v is not None:
                raise ValueError('Must not provide both data and error')
            return v

        @validator('positive_number')
        def validate_positive_number(cls, v: int) -> int:
            if v < 0:
                raise ValueError
            return v

    class Error(BaseModel):
        message: str

    class Data(BaseModel):
        number: int
        text: str

    success1 = Result[Data, Error](data=[Data(number=1, text='a')], positive_number=1)
    assert success1.dict() == {'data': [{'number': 1, 'text': 'a'}], 'error': None, 'positive_number': 1}
    assert str(success1) == 'Result[Data, Error] data=[<Data number=1 text=\'a\'>] error=None positive_number=1'

    success2 = Result[Data, Error](error=Error(message='error'), positive_number=1)
    assert success2.dict() == {'data': None, 'error': {'message': 'error'}, 'positive_number': 1}
    assert str(success2) == 'Result[Data, Error] data=None error=<Error message=\'error\'> positive_number=1'
    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](error=Error(message='error'), positive_number=-1)
    assert exc_info.value.errors() == [{'loc': ('positive_number',), 'msg': '', 'type': 'value_error'}]

    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](data=[Data(number=1, text='a')], error=Error(message='error'), positive_number=1)
    assert exc_info.value.errors() == [
        {'loc': ('error',), 'msg': 'Must not provide both data and error', 'type': 'value_error'},
        {'loc': ('error',), 'msg': 'value is not none', 'type': 'type_error.none.allowed'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Result[Data, Error](data=[Data(number=1, text='a')], error=Error(message='error'), positive_number=1)
    assert exc_info.value.errors() == [
        {'loc': ('error',), 'msg': 'Must not provide both data and error', 'type': 'value_error'},
        {'loc': ('error',), 'msg': 'value is not none', 'type': 'type_error.none.allowed'},
    ]
