from sqlalchemy import Column, Integer, Table, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql.sqltypes import NullType

Base = declarative_base()
metadata = Base.metadata


class Place(Base):
    __tablename__ = 'place'

    id = Column(Integer, primary_key=True)
    city = Column(Text)
    state = Column(Text)
    latitude = Column(Text)
    longitude = Column(Text)
    url = Column(Text)


t_sqlite_sequence = Table(
    'sqlite_sequence', metadata,
    Column('name', NullType),
    Column('seq', NullType)
)