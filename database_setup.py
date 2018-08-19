import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """
    Registered user information
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250))
    picture = Column(String(250))


class Category(Base):
    """
    Category to group items
    """
    __tablename__ = 'category'
    name = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # one to many relationship
    # items = relationship('Item', backref = 'category', lazy = True)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'user_id': self.user_id,
        }


class Item(Base):
    """
    Detailed information of an item
    """
    __tablename__ = 'item'
    title = Column(String(80), nullable=False, unique=True)
    id = Column(Integer, primary_key=True)
    description = Column(String(5000))

    cat_id = Column(
                Integer, ForeignKey(
                    'category.id', ondelete='CASCADE'), nullable=False)
    category = relationship(Category)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'title': self.title,
            'id': self.id,
            'description': self.description,
            'cat_id': self.cat_id,
            'user_id': self.user_id,
        }


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
