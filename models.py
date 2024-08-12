import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


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

        class Expense(self.Base):
            __tablename__ = "expense"
            id = Column(Integer, primary_key=True)
            amount = Column(Float, nullable=False)
            date = Column(Date, nullable=False)
            category = Column(String, nullable=False)

        class Category(self.Base):
            __tablename__ = "category"
            id = Column(Integer, primary_key=True)
            amount = Column(Float, nullable=False)
            date = Column(Date, nullable=False)

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
