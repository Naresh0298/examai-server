from typing import Optional, List 
from pydantic import BaseModel 
from enum import Enum



class Gender(str, Enum):
    male = "male"
    female ="female"

class Role(str,Enum):
    admin ="admin"
    user = "user"
    student = "student"
    teacher = "teacher"

class User(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None  # Make middle name optional
    gender: Gender
    email_address: str
    phone_number: str
    roles: List[Role] # user can have several roles