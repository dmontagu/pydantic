from typing import Generic, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel


class Model(BaseModel):
    x: float
    y: str

    class Config:
        orm_mode = True

    class NotConfig:
        allow_mutation = False


class SelfReferencingModel(BaseModel):
    submodel: Optional['SelfReferencingModel']

    @property
    def prop(self) -> None:
        ...


model = Model(x=1, y='y')
Model(x=1, y='y', z='z')
model.x = 2
Model.from_orm(model)

self_referencing_model = SelfReferencingModel(submodel=SelfReferencingModel(submodel=None))

T = TypeVar('T')


class Response(GenericModel, Generic[T]):
    data: T
    error: Optional[str]


response = Response[Model](data=model, error=None)


class InheritingModel(Model):
    z: int = 1


InheritingModel.from_orm(model)


class ForwardReferencingModel(Model):
    future: 'FutureModel'


class FutureModel(Model):
    pass


future_model = FutureModel(x=1, y='a')
forward_model = ForwardReferencingModel(x=1, y='a', future=future_model)


class NoMutationModel(BaseModel):
    x: int

    class Config:
        allow_mutation = False


class MutationModel(NoMutationModel):
    a = 1

    class Config:
        allow_mutation = True
        orm_mode = True


MutationModel(x=1).x = 2
MutationModel.from_orm(model)


class OverrideModel(Model):
    x: int


OverrideModel(x=1.5, y='b')


class Mixin:
    def f(self) -> None:
        pass


class MultiInheritanceModel(BaseModel, Mixin):
    pass


MultiInheritanceModel().f()
