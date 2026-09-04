from pydantic import BaseModel, ConfigDict, EmailStr


class InstructorCreate(BaseModel):
    name: str
    email: EmailStr
    specialty: str | None = None
    bio: str | None = None


class InstructorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    specialty: str | None = None
    bio: str | None = None
