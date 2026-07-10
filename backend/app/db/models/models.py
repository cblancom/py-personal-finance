import os
from dotenv import load_dotenv
from datetime import date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy import create_engine, String, Integer, Date, ForeignKey, select, delete
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, List
from fastapi import FastAPI, Depends, HTTPException


load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

## Database contectiion
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# SQL models
class Base(DeclarativeBase):
    pass


class CategoriaIngresoEnum(str, Enum):
    TRABAJO_1 = "TRABAJO1"
    TRABAJO_2 = "TRABAJO2"
    ARRIENDO = "Arriendo"


class CategoriaGastoEnum(str, Enum):
    NECESARIO = "NECESARIO"
    NO_NECESARIO = "NO_NECESARIO"
    INVERSION = "INVERSION"


class IngresoTabla(Base):
    __tablename__ = "ingresos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date)
    valor: Mapped[int] = mapped_column(Integer)
    categoria: Mapped[CategoriaIngresoEnum] = mapped_column(
        SQLEnum(CategoriaIngresoEnum)
    )
    descripcion: Mapped[str] = mapped_column(String(200))


class GastoTabla(Base):
    __tablename__ = "gastos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha: Mapped[date] = mapped_column(Date)
    valor: Mapped[int] = mapped_column(Integer)
    categoria: Mapped[CategoriaGastoEnum] = mapped_column(SQLEnum(CategoriaGastoEnum))
    descripcion: Mapped[str] = mapped_column(String(200))


class InversionTabla(Base):
    __tablename__ = "inversiones"
    id: Mapped[int] = mapped_column(ForeignKey("gastos.id"), primary_key=True)
    fecha: Mapped[date] = mapped_column(Date)
    valor: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(String(200))


## Pydantic models
### Ingreso
class IngresoBase(BaseModel):
    fecha: date
    valor: int = Field(gt=0)
    categoria: CategoriaIngresoEnum
    descripcion: Annotated[str, Field(max_length=200)]


class IngresoWrite(IngresoBase):
    pass


class IngresoRead(IngresoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class IngresoUpdate(BaseModel):
    fecha: date | None = None
    valor: int | None = Field(gt=0)
    categoria: CategoriaIngresoEnum | None = None
    descripcion: str | None = Field(default=None, max_length=200)


### Gasto
class GastoBase(BaseModel):
    fecha: date
    valor: int
    categoria: CategoriaGastoEnum
    descripcion: Annotated[str, Field(max_length=200)]


class GastoWrite(GastoBase):
    pass


class GastoRead(GastoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class GastoUpdate(BaseModel):
    fecha: date | None = None
    valor: int | None = Field(gt=0)
    categoria: CategoriaGastoEnum | None = None
    descripcion: str | None = Field(default=None, max_length=200)


### Inversion
class InversionBase(BaseModel):
    fecha: date
    valor: int
    descripcion: Annotated[str, Field(max_length=200)]


class InversionWrite(InversionBase):
    pass


class InversionRead(InversionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InversionUpdate(BaseModel):
    fecha: date | None = None
    valor: int | None = Field(gt=0)
    descripcion: str | None = Field(default=None, max_length=200)


app = FastAPI()


@app.post("/ingresos", response_model=IngresoRead)
def add_ingreso(ingreso: IngresoWrite, db: Session = Depends(get_db)):
    ingreso_nuevo = IngresoTabla(**ingreso.model_dump())
    db.add(ingreso_nuevo)
    db.commit()
    db.refresh(ingreso_nuevo)
    return ingreso_nuevo


@app.get("/ingresos/{ingreso_id}", response_model=IngresoRead)
def get_ingreso(ingreso_id: int, db: Session = Depends(get_db)):
    query = select(IngresoTabla).where(IngresoTabla.id == ingreso_id)
    ingreso = db.execute(query).scalar_one_or_none()
    if ingreso is None:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    return ingreso


@app.get("/ingresos/", response_model=List[IngresoRead])
def get_ingreso_all(db: Session = Depends(get_db)):
    ingresos = db.scalars(select(IngresoTabla)).all()
    return ingresos


@app.delete("/ingresos/{ingreso_id}", response_model=IngresoRead)
def delete_ingreso(ingreso_id: int, db: Session = Depends(get_db)):
    query = select(IngresoTabla).where(IngresoTabla.id == ingreso_id)
    ingreso = db.execute(query).scalar_one_or_none()
    if ingreso is None:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    else:
        query = delete(IngresoTabla).where(IngresoTabla.id == ingreso_id)
        db.execute(query)
        db.commit()
    return ingreso
