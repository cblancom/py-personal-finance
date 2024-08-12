import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    MetaData,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, sessionmaker


class CreateDB:

    def __init__(self) -> None:
        db_path = os.path.join(os.path.abspath(os.getcwd()), "py_personal_finance.db")
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Base = declarative_base()
        self.create_tables()

        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        self.table = metadata.tables.keys()

    def create_tables(
        self,
    ):

        class Income(self.Base):
            __tablename__ = "income"
            id = Column(Integer, primary_key=True)
            amount = Column(Float, nullable=False)
            date = Column(Date, nullable=False)

        class Category(self.Base):
            __tablename__ = "category"
            id = Column(Integer, primary_key=True)
            name = Column(String, nullable=False)
            expenses = relationship("Expense", back_populates="category")

        class Expense(self.Base):
            __tablename__ = "expense"
            id = Column(Integer, primary_key=True)
            amount = Column(Float, nullable=False)
            category_id = Column(Integer, ForeignKey("category.id"), nullable=False)
            date = Column(Date, nullable=False)
            category = relationship("Category", back_populates="expenses")

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
