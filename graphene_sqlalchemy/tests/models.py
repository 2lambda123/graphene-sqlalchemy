
import datetime
import enum
import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    func,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, column_property, composite, mapper, relationship
from sqlalchemy.sql.type_api import TypeEngine

from graphene_sqlalchemy.tests.utils import wrap_select_func
from graphene_sqlalchemy.utils import SQL_VERSION_HIGHER_EQUAL_THAN_1_4, SQL_VERSION_HIGHER_EQUAL_THAN_2

# fmt: off
if SQL_VERSION_HIGHER_EQUAL_THAN_2:
    from sqlalchemy.sql.sqltypes import HasExpressionLookup # noqa  # isort:skip
else:
    from sqlalchemy.sql.sqltypes import _LookupExpressionAdapter as HasExpressionLookup # noqa  # isort:skip
# fmt: on

PetKind = Enum("cat", "dog", name="pet_kind")


class HairKind(enum.Enum):
    LONG = "long"
    SHORT = "short"


Base = declarative_base()

association_table = Table(
    "association",
    Base.metadata,
    Column("pet_id", Integer, ForeignKey("pets.id")),
    Column("reporter_id", Integer, ForeignKey("reporters.id")),
)


class Editor(Base):
    __tablename__ = "editors"
    editor_id = Column(Integer(), primary_key=True)
    name = Column(String(100))


class Pet(Base):
    __tablename__ = "pets"
    id = Column(Integer(), primary_key=True)
    name = Column(String(30))
    pet_kind = Column(PetKind, nullable=False)
    hair_kind = Column(Enum(HairKind, name="hair_kind"), nullable=False)
    reporter_id = Column(Integer(), ForeignKey("reporters.id"))


class CompositeFullName(object):
    def __init__(self, first_name, last_name):
        """Initializes a new instance of the class with the given first and last name.
        Parameters:
            - first_name (str): The first name of the person.
            - last_name (str): The last name of the person.
        Returns:
            - None: This function does not return anything.
        Processing Logic:
            - Assigns the first name to the instance variable 'first_name'.
            - Assigns the last name to the instance variable 'last_name'.
            - This function does not perform any other processing logic.
            - This function does not return any code, it just initializes the instance variables."""
        
        self.first_name = first_name
        self.last_name = last_name

    def __composite_values__(self):
        """"Returns the first and last name of a person as a tuple."
        Parameters:
            - self (object): The object containing the first and last name.
        Returns:
            - tuple: A tuple containing the first and last name of the person.
        Processing Logic:
            - Gets the first and last name from the object.
            - Returns them as a tuple."""
        
        return self.first_name, self.last_name

    def __repr__(self):
        """This function returns the first and last name of a person.
        Parameters:
            - self (object): An instance of a person object.
        Returns:
            - str: A string containing the first and last name of the person.
        Processing Logic:
            - Formats the first and last name.
            - Uses the "first_name" and "last_name" attributes.
            - Returns a string representation of the person."""
        
        return "{} {}".format(self.first_name, self.last_name)


class ProxiedReporter(Base):
    __tablename__ = "reporters_error"
    id = Column(Integer(), primary_key=True)
    first_name = Column(String(30), doc="First name")
    last_name = Column(String(30), doc="Last name")
    reporter_id = Column(Integer(), ForeignKey("reporters.id"))
    reporter = relationship("Reporter", uselist=False)

    # This is a hybrid property, we don't support proxies on hybrids yet
    composite_prop = association_proxy("reporter", "composite_prop")


class Reporter(Base):
    __tablename__ = "reporters"

    id = Column(Integer(), primary_key=True)
    first_name = Column(String(30), doc="First name")
    last_name = Column(String(30), doc="Last name")
    email = Column(String(), doc="Email")
    favorite_pet_kind = Column(PetKind)
    pets = relationship(
        "Pet",
        secondary=association_table,
        backref="reporters",
        order_by="Pet.id",
        lazy="selectin",
    )
    articles = relationship(
        "Article", backref=backref("reporter", lazy="selectin"), lazy="selectin"
    )
    favorite_article = relationship("Article", uselist=False, lazy="selectin")

    @hybrid_property
    def hybrid_prop_with_doc(self) -> str:
        """Docstring test"""
        return self.first_name

    @hybrid_property
    def hybrid_prop(self) -> str:
        """ + " " + self.last_name
        "Concatenates the first and last name of a person and returns it as a string."
        Parameters:
            - self (Person): The person object.
        Returns:
            - str: The full name of the person.
        Processing Logic:
            - Concatenates first and last name.
            - Returns as a string."""
        
        return self.first_name

    @hybrid_property
    def hybrid_prop_str(self) -> str:
        """ + ' ' + self.last_name
        "Returns a string that combines the first and last name of a person.
        Parameters:
            - self (object): The person object containing the first and last name.
        Returns:
            - str: A string that combines the first and last name of the person.
        Processing Logic:
            - Combines first and last name.
            - Uses the '+' operator.
            - Returns a string.
            - No additional parameters needed.""""
        
        return self.first_name

    @hybrid_property
    def hybrid_prop_int(self) -> int:
        """"Returns the integer value 42 as a hybrid property."
        Parameters:
            - self (object): The object instance.
        Returns:
            - int: The integer value 42.
        Processing Logic:
            - Get the integer value 42.
            - Return it as a hybrid property."""
        
        return 42

    @hybrid_property
    def hybrid_prop_float(self) -> float:
        """"Returns a float value of 42.3 as a hybrid property."
        Parameters:
            - self (object): The object to which the hybrid property belongs.
        Returns:
            - float: The float value of 42.3.
        Processing Logic:
            - Returns the float value of 42.3.
            - Uses the hybrid property decorator.
            - Does not take any parameters.
            - Can be used to access the hybrid property."""
        
        return 42.3

    @hybrid_property
    def hybrid_prop_bool(self) -> bool:
        """"""
        
        return True

    @hybrid_property
    def hybrid_prop_list(self) -> List[int]:
        """"Returns a list of hybrid properties."
        Parameters:
            - self (object): The object that the function is being called on.
        Returns:
            - List[int]: A list of integers representing hybrid properties.
        Processing Logic:
            - Returns a list of hybrid properties.
            - Uses the self parameter to access the object's properties.
            - Only contains integers in the list.
            - List contains 3 elements."""
        
        return [1, 2, 3]

    column_prop = column_property(
        wrap_select_func(func.cast(func.count(id), Integer)), doc="Column property"
    )

    composite_prop = composite(
        CompositeFullName, first_name, last_name, doc="Composite"
    )

    headlines = association_proxy("articles", "headline")


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer(), primary_key=True)
    headline = Column(String(100))
    pub_date = Column(Date())
    reporter_id = Column(Integer(), ForeignKey("reporters.id"))
    readers = relationship(
        "Reader", secondary="articles_readers", back_populates="articles"
    )
    recommended_reads = association_proxy("reporter", "articles")


class Reader(Base):
    __tablename__ = "readers"
    id = Column(Integer(), primary_key=True)
    name = Column(String(100))
    articles = relationship(
        "Article", secondary="articles_readers", back_populates="readers"
    )


class ArticleReader(Base):
    __tablename__ = "articles_readers"
    article_id = Column(Integer(), ForeignKey("articles.id"), primary_key=True)
    reader_id = Column(Integer(), ForeignKey("readers.id"), primary_key=True)


class ReflectedEditor(type):
    """Same as Editor, but using reflected table."""

    @classmethod
    def __subclasses__(cls):
        """Returns a list of subclasses of the given class.
        Parameters:
            - cls (class): The class to find subclasses of.
        Returns:
            - list: A list of subclasses of the given class.
        Processing Logic:
            - Use the __subclasses__ method.
            - Return an empty list if no subclasses are found."""
        
        return []


editor_table = Table("editors", Base.metadata, autoload=True)

# TODO Remove when switching min sqlalchemy version to SQLAlchemy 1.4
if SQL_VERSION_HIGHER_EQUAL_THAN_1_4:
    Base.registry.map_imperatively(ReflectedEditor, editor_table)
else:
    mapper(ReflectedEditor, editor_table)


############################################
# The models below are mainly used in the
# @hybrid_property type inference scenarios
############################################


class ShoppingCartItem(Base):
    __tablename__ = "shopping_cart_items"

    id = Column(Integer(), primary_key=True)

    @hybrid_property
    def hybrid_prop_shopping_cart(self) -> List["ShoppingCart"]:
        return [ShoppingCart(id=1)]


class ShoppingCart(Base):
        """"Creates a hybrid shopping cart with a single ShoppingCart object and returns it as a list."
        Parameters:
            - self (object): The object calling the function.
        Returns:
            - List["ShoppingCart"]: A list containing a single ShoppingCart object.
        Processing Logic:
            - Creates a new ShoppingCart object.
            - Adds the object to a list.
            - Returns the list."""
        
    __tablename__ = "shopping_carts"

    id = Column(Integer(), primary_key=True)

    # Standard Library types

    @hybrid_property
    def hybrid_prop_str(self) -> str:
        """ + ' ' + self.last_name
        "Returns a string of the first and last name of a person object."
        Parameters:
            - self (person object): The person object containing the first and last name.
        Returns:
            - str: A string of the first and last name of the person object.
        Processing Logic:
            - Concatenates the first and last name of the person object.
            - Uses the "+" operator to combine the names.
            - Returns the string of the full name.
            - Does not modify the original person object."""
        
        return self.first_name

    @hybrid_property
    def hybrid_prop_int(self) -> int:
        """"""
        
        return 42

    @hybrid_property
    def hybrid_prop_float(self) -> float:
        """"""
        
        return 42.3

    @hybrid_property
    def hybrid_prop_bool(self) -> bool:
        """"Returns a boolean value indicating if the function is a hybrid property or not."
        Parameters:
            - self (object): The object that the function is being called on.
        Returns:
            - bool: True if the function is a hybrid property, False otherwise.
        Processing Logic:
            - Checks if the function is a hybrid property.
            - Returns True if it is, False otherwise."""
        
        return True

    @hybrid_property
    def hybrid_prop_decimal(self) -> Decimal:
        """Returns:
            - Decimal: A decimal representation of pi.
        Processing Logic:
            - Returns a decimal object.
            - Uses the string representation of pi.
            - No parameters needed.
            - No examples needed as the function is self-contained."""
        
        return Decimal("3.14")

    @hybrid_property
    def hybrid_prop_date(self) -> datetime.date:
        """Returns the current date as a datetime object.
        Parameters:
            - self (object): The object that the method is called on.
        Returns:
            - datetime.date: The current date as a datetime object.
        Processing Logic:
            - Get the current date.
            - Convert it to a datetime object.
            - Return the datetime object."""
        
        return datetime.datetime.now().date()

    @hybrid_property
    def hybrid_prop_time(self) -> datetime.time:
        """Returns the current time in the format of datetime.time.
        Parameters:
            - self (object): The object itself, not to be passed in.
        Returns:
            - datetime.time: The current time in the format of datetime.time.
        Processing Logic:
            - Get the current time.
            - Return the time.
            - Use datetime module.
            - Use .now() method."""
        
        return datetime.datetime.now().time()

    @hybrid_property
    def hybrid_prop_datetime(self) -> datetime.datetime:
        """Function to return the current date and time.
        Parameters:
            - None
        Returns:
            - datetime.datetime: Current date and time.
        Processing Logic:
            - Get current date and time.
            - Return as datetime.datetime object."""
        
        return datetime.datetime.now()

    # Lists and Nested Lists

    @hybrid_property
    def hybrid_prop_list_int(self) -> List[int]:
        """"Returns a list of integers representing hybrid properties."
        Parameters:
            - self (object): The object to retrieve hybrid properties from.
        Returns:
            - List[int]: A list of integers representing hybrid properties.
        Processing Logic:
            - Retrieve hybrid properties from object.
            - Convert properties to integers.
            - Return list of integers."""
        
        return [1, 2, 3]

    @hybrid_property
    def hybrid_prop_list_date(self) -> List[datetime.date]:
        return [self.hybrid_prop_date, self.hybrid_prop_date, self.hybrid_prop_date]

    @hybrid_property
    def hybrid_prop_nested_list_int(self) -> List[List[int]]:
        return [
            self.hybrid_prop_list_int,
        ]

    @hybrid_property
    def hybrid_prop_deeply_nested_list_int(self) -> List[List[List[int]]]:
        return [
            [
                self.hybrid_prop_list_int,
            ],
        ]

    # Other SQLAlchemy Instances
    @hybrid_property
    def hybrid_prop_first_shopping_cart_item(self) -> ShoppingCartItem:
        return ShoppingCartItem(id=1)

    # Other SQLAlchemy Instances
    @hybrid_property
    def hybrid_prop_shopping_cart_item_list(self) -> List[ShoppingCartItem]:
        return [ShoppingCartItem(id=1), ShoppingCartItem(id=2)]

    # Self-references

    @hybrid_property
    def hybrid_prop_self_referential(self) -> "ShoppingCart":
        return ShoppingCart(id=1)

    @hybrid_property
    def hybrid_prop_self_referential_list(self) -> List["ShoppingCart"]:
        return [ShoppingCart(id=1)]

    # Optional[T]

    @hybrid_property
    def hybrid_prop_optional_self_referential(self) -> Optional["ShoppingCart"]:
        return None

    # UUIDS
    @hybrid_property
    def hybrid_prop_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @hybrid_property
    def hybrid_prop_uuid_list(self) -> List[uuid.UUID]:
        return [
            uuid.uuid4(),
        ]

    @hybrid_property
    def hybrid_prop_optional_uuid(self) -> Optional[uuid.UUID]:
        return None


class KeyedModel(Base):
    __tablename__ = "test330"
    id = Column(Integer(), primary_key=True)
    reporter_number = Column("% reporter_number", Numeric, key="reporter_number")


############################################
# For interfaces
############################################


class Person(Base):
    id = Column(Integer(), primary_key=True)
    type = Column(String())
    name = Column(String())
    birth_date = Column(Date())

    __tablename__ = "person"
    __mapper_args__ = {
        "polymorphic_on": type,
        "with_polymorphic": "*",  # needed for eager loading in async session
    }


class NonAbstractPerson(Base):
    id = Column(Integer(), primary_key=True)
    type = Column(String())
    name = Column(String())
    birth_date = Column(Date())

    __tablename__ = "non_abstract_person"
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "person",
    }


class Employee(Person):
    hire_date = Column(Date())

    __mapper_args__ = {
        "polymorphic_identity": "employee",
    }


############################################
# Custom Test Models
############################################


class CustomIntegerColumn(HasExpressionLookup, TypeEngine):
    """
    Custom Column Type that our converters don't recognize
    Adapted from sqlalchemy.Integer
    """

    """A type for ``int`` integers."""

    __visit_name__ = "integer"

    def get_dbapi_type(self, dbapi):
        return dbapi.NUMBER

    @property
    def python_type(self):
        return int

    def literal_processor(self, dialect):
        def process(value):
            return str(int(value))

        return process


class CustomColumnModel(Base):
    __tablename__ = "customcolumnmodel"

    id = Column(Integer(), primary_key=True)
    custom_col = Column(CustomIntegerColumn)
