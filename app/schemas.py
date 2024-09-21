from pydantic import BaseModel, EmailStr, Field, StringConstraints
from typing import Optional, List, Union
from datetime import datetime, date
from app.core.permission import Permission
from typing_extensions import Annotated


# User Schemas
class UserCreate(BaseModel):
    username: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
    ]
    email: EmailStr
    name: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
    ] = Field(default=None)
    is_active: bool = Field(default=True)


class UserUpdate(BaseModel):
    username: Optional[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
        ]
    ] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    name: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
    ] = Field(default=None)


# Role Schemas
class RoleBase(BaseModel):
    name: str = Field(..., example="admin")
    description: Optional[str] = Field(
        None, example="Administrator role with full permissions."
    )


class RoleCreate(RoleBase):
    permissions: Optional[List[Permission]] = Field(
        default_factory=list, example=[Permission.CREATE_PRODUCT]
    )


class RoleRead(RoleBase):
    id: int
    permissions: List[Permission] = []


# Person Schemas
class NaturalPersonDetailsBase(BaseModel):
    curp: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=18, max_length=18)
    ] = Field(..., example="CURP12345678901234")
    rfc: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=12, max_length=13)
    ] = Field(..., example="RFC1234567890")
    name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] = (
        Field(..., example="John")
    )
    first_last_name: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=100)
    ] = Field(..., example="Doe")
    second_last_name: Optional[
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
    ] = Field(None, example="Smith")
    date_of_birth: Optional[date] = Field(None, example="1990-01-01")


class JuridicalPersonDetailsBase(BaseModel):
    rfc: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=12, max_length=13)
    ] = Field(..., example="RFC1234567890")
    legal_name: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=200)
    ] = Field(..., example="ACME Corporation")
    incorporation_date: Optional[date] = Field(None, example="2000-05-20")


class PersonCreateBase(BaseModel):
    type: Annotated[str, StringConstraints(strip_whitespace=True)] = Field(
        ..., example="natural"
    )  # or "juridical"
    # Common fields
    active: Optional[bool] = Field(True)


class PersonCreateNatural(PersonCreateBase):
    type: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern="^(natural)$")
    ]  # Ensures type is 'natural'
    details: NaturalPersonDetailsBase


class PersonCreateJuridical(PersonCreateBase):
    type: Annotated[
        str, StringConstraints(strip_whitespace=True, pattern="^(juridical)$")
    ]  # Ensures type is 'juridical'
    details: JuridicalPersonDetailsBase


PersonCreate = Union[PersonCreateNatural, PersonCreateJuridical]


class NaturalPersonDetailsRead(NaturalPersonDetailsBase):
    person_id: int
    created_at: datetime
    full_name: str


class JuridicalPersonDetailsRead(JuridicalPersonDetailsBase):
    person_id: int
    created_at: datetime


class PersonBase(BaseModel):
    id: int
    type: str
    active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class PersonReadNatural(PersonBase):
    details: NaturalPersonDetailsRead


class PersonReadJuridical(PersonBase):
    details: JuridicalPersonDetailsRead


PersonRead = Union[PersonReadNatural, PersonReadJuridical]


class PersonFilter(BaseModel):
    type: Optional[str] = Field(None, example="natural")
    active: Optional[bool] = Field(None, example=True)
    name: Optional[str] = Field(None, example="John")


class Pagination(BaseModel):
    skip: int = Field(0, ge=0, example=0)
    limit: int = Field(10, ge=1, le=100, example=10)


class PersonList(BaseModel):
    total: int
    items: List[PersonRead]
