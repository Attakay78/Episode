import sqlite3
from enum import Enum
from itertools import count
from typing import List, get_origin, get_args
from .logger import configure_file_logger, EPISODE_LOGGER
import mysql.connector
from mysql.connector import Error

counter = count()

 
class Condition:
    def __init__(self, op, field, value):
        self.op = op
        self.field = field
        self.value = value

    def to_sql(self, db_strategy):
        return db_strategy.condition_to_sql(self.field, self.value, self.op)

    def __or__(self, other):
        return BoolCondition("OR", self, other)

    def __and__(self, other):
        return BoolCondition("AND", self, other)


class BoolCondition:
    def __init__(self, op, cond1, cond2):
        self.op = op
        self.cond1 = cond1
        self.cond2 = cond2

    def to_sql(self, db_strategy):
        sql1, values1 = self.cond1.to_sql(db_strategy)
        sql2, values2 = self.cond2.to_sql(db_strategy)
        return (
            f"{sql1} {self.op} {sql2}",
            db_strategy.concatenate_condition_values(values1, values2)
        )


class QueryBuilder:
    def __init__(self, model, db_strategy):
        self.model = model
        self.db_strategy = db_strategy
        self._where_condition = False
        self._values = None
        self._columns = "*"
        self.row_limit = None

    def where(self, condition: Condition):
        where_sql, values = condition.to_sql(self.db_strategy)
        self._where_condition = f"WHERE {where_sql}"
        self._values = values
        return self
    
    def limit(self, limit):
        self.row_limit = limit
        return self
    
    def filter_by(self, *args):
        if len(args) > 0:
            self._columns = ", ".join(args)
        
        return self
    
    def get_sql_stmt(self):
        sql_stmt = f"SELECT {self._columns} FROM {self.model._name} {self._where_condition}"

        if self.row_limit:
            sql_stmt += f" limit {self.row_limit}"

        return sql_stmt, self._values

class Field:
    def __init__(self, name, py_type):
        self.name = name
        self.py_type = py_type
        self.is_nullable = False

    def __set__(self, instance, value):
        instance._values[self.name] = value

    def __get__(self, instance, cls):
        if instance:
            return instance._values.get(self.name, None) 
        else:
            return self

    def __eq__(self, value):
        return Condition("=", self, value)

    def __lt__(self, value):
        return Condition("<", self, value)

    def __le__(self, value):
        return Condition("<=", self, value)

    def __ne__(self, value):
        return Condition("!=", self, value)

    def __gt__(self, value):
        return Condition(">", self, value)

    def __ge__(self, value):
        return Condition(">=", self, value)

    def to_sql(self, value):
        type_args = get_args(self.py_type)
        type_origin = get_origin(self.py_type)

        if (type_origin is list) and (
            type_args[0].__base__ is Model
        ):
            return value.id

        if issubclass(self.py_type, Model):
            return value.id
        return value


class Model:
    def __init_subclass__(cls):
        cls._name = cls.__name__.lower()
        cls._cols = {
            name: Field(name, py_type) for name, py_type in cls.__annotations__.items()
        }

        cls._cols["id"] = Field("id", int)

        for name, field in cls._cols.items():
            setattr(cls, name, field)
        setattr(cls, "id", Field("id", int))

        nonetype = type(None)
        for name, field in cls._cols.items():
            type_args = get_args(field.py_type)
            if len(type_args) > 0:
                for arg in type_args:
                    if arg is nonetype:
                        field.is_nullable = True
                
                if type_args[0].__base__ is not Model:
                    field.py_type = type_args[0]
                        

    def __init__(self, **kwargs):
        self._values = {}
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if "id" not in kwargs.keys():
            self._values["id"] = None

    def __repr__(self):
        stmt = (f"{name}={getattr(self, name)}" for name in self._cols if name in self._values and self._values[name] is not None)
        return f"<{self.__class__.__name__} {', '.join(stmt)}>"


class DBType(Enum):
    MYSQL = "MYSql"
    SQLITE = "SQLite"


class MySQLConnection:
    def __init__(self, host: str, database: str, user: str, password: str):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
    
    def connect(self):
        conn = mysql.connector.connect(host=self.host, database=self.database, user=self.user, password=self.password)
        return conn
    
    def configure_cursor(self, cursor):
        return cursor(dictionary=True)
    
    def delete(self, model: Model):
        return f"DROP TABLE IF EXISTS {model._name}"
    
    def create(self, model: Model):
        return (
            f"CREATE TABLE {model._name} (id INTEGER AUTO_INCREMENT PRIMARY KEY, %s)"
            % ", ".join(
                f"{name} {self.sql_type(field)}" for name, field in model._cols.items() if name != "id"
            )
        )
    
    def sql_type(self, field):
        python_sql_type = {int: "INTEGER", str: "VARCHAR(255)"}

        null = " NULL" if field.is_nullable else " NOT NULL"
        type_args = get_args(field.py_type)
        type_origin = get_origin(field.py_type)

        if (type_origin is list) and (
            type_args[0].__base__ is Model
        ):
            return "INTEGER" + null  # For one to many relationships
        
        if (type_origin is list) and (
            type_args[0].__base__ is not Model
        ):
            return python_sql_type[type_args[0]] + null  # For one to many relationships

        # For one to one relationships
        if field.py_type.__base__ is Model:
            return "INTEGER UNIQUE" + null

        return python_sql_type[field.py_type] + null
    
    def save(self, model: Model):
        values = [
            field.to_sql(getattr(model, name))
            for name, field in model._cols.items()
        ]
        if model.id:
            stmt = f"UPDATE {model._name} SET %s " % ", ".join(
                f"{name} = %s" for name in model._cols
            )

            stmt += "WHERE id= %s"
            values.append(model.id)
            return (stmt, tuple(values))
        else:
            insert_sql = f"INSERT INTO {model._name} (%s) VALUES (%s)" % (
                ", ".join(f"{name}" for name in model._cols),
                ", ".join(f"%s" for name in model._cols),
            )
            return (insert_sql, tuple(values))
    
    def condition_to_sql(self, field, value, op):
        return (f"{field.name} {op} %s", [value])
    
    def concatenate_condition_values(self, val1, val2):
        return tuple([*val1, *val2])
        

class SQLiteConnection:
    def __init__(self, database_path):
        self.database_path = database_path
    
    def connect(self):
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def configure_cursor(self, cursor):
        return cursor()
    
    def create(self, model: Model):
        return (
            f"CREATE TABLE {model._name} (id INTEGER PRIMARY KEY, %s)"
            % ", ".join(
                f"{name} {self.sql_type(field)}" for name, field in model._cols.items() if name != "id"
            )
        )
    
    def delete(self, model: Model):
        return f"DROP TABLE IF EXISTS {model._name}"
    
    def save(self, model: Model):
        values = {
            name: field.to_sql(getattr(model, name))
            for name, field in model._cols.items()
        }
        if model.id:
            stmt = f"UPDATE {model._name} SET %s WHERE id=:id" % ", ".join(
                f"{name} = :{name}" for name in model._cols
            )

            return (stmt, {"id": model.id, **values})
        else:
            insert_sql = f"INSERT INTO {model._name} (%s) VALUES (%s)" % (
                ", ".join(f"{name}" for name in model._cols),
                ", ".join(f":{name}" for name in model._cols),
            )
            return (insert_sql, values)
    
    def sql_type(self, field):
        python_sql_type = {int: "INTEGER", str: "TEXT"}

        null = " NULL" if field.is_nullable else " NOT NULL"
        type_args = get_args(field.py_type)
        type_origin = get_origin(field.py_type)

        if (type_origin is list) and (
            type_args[0].__base__ is Model
        ):
            return "INTEGER" + null  # For one to many relationships
        
        if (type_origin is list) and (
            type_args[0].__base__ is not Model
        ):
            return python_sql_type[type_args[0]] + null  # For one to many relationships

        # For one to one relationships
        if field.py_type.__base__ is Model:
            return "INTEGER UNIQUE" + null

        return python_sql_type[field.py_type] + null
    
    def condition_to_sql(self, field, value, op):
        placeholder = f"var{next(counter)}"
        return (
            f"{field.name} {op} :{placeholder}",
            {placeholder: value},
        )
    
    def concatenate_condition_values(self, val1, val2):
        return {**val1, **val2}


class DBConnection:
    @staticmethod
    def dialect(db_type):
        if db_type == DBType.MYSQL:
            return MySQLConnection
        elif db_type == DBType.SQLITE:
            return SQLiteConnection


class Session:
    def __init__(self, db_strategy, log=False):
        self.log = log
        self.db_strategy = db_strategy
        if self.log:
            configure_file_logger(filename="episodeDB.log")
        self.conn = self.db_strategy.connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def sql_run(self, sql_stmt, values=None):
        self.log_sql_stmt(f"Running '{sql_stmt}', with, {values}")
        cur = self.db_strategy.configure_cursor(self.conn.cursor)
        cur.execute(sql_stmt, values or {})
        self.conn.commit()
        return cur.lastrowid

    def create(self, model: Model):
        sql_statement = self.db_strategy.create(model)
        return self.sql_run(sql_statement)

    def delete(self, model: Model):
        sql_statement = self.db_strategy.delete(model)
        self.sql_run(sql_statement)

    def delete_and_create(self, model: Model):
        # Delete if table exists and create table after
        self.delete(model)
        self.create(model)

    def save(self, model: Model):
        sql_statement, values = self.db_strategy.save(model)
        row_id = self.sql_run(sql_statement, values)

        if row_id:
            model.id = row_id

    def sql_select(self, sql_stmt, values=None):
        self.log_sql_stmt(f"Selecting '{sql_stmt}' with {values}")
        cur = self.db_strategy.configure_cursor(self.conn.cursor)
        cur.execute(sql_stmt, values or ())
        yield from cur.fetchall()
    
    def log_sql_stmt(self, sql_stmt):
        if self.log:
            EPISODE_LOGGER.debug(sql_stmt)
    
    def process_row_data(self, row, query_builder: QueryBuilder):
        row_data = {}
        for name, value in dict(row).items():
            sql_stmt = f"SELECT * FROM {name} WHERE id = :id"
            column = query_builder.model._cols.get(name, None)
            if (
                column != None
                and (get_origin(column.py_type) is list)
                and (issubclass(get_args(column.py_type)[0], Model))
            ):
                row_data[name] = get_args(column.py_type)[0](
                    **dict(next(self.sql_select(sql_stmt, {"id": value})))
                )
            elif column != None and column.py_type.__base__ is Model:
                row_data[name] = column.py_type(
                    **dict(next(self.sql_select(sql_stmt, {"id": value})))
                )
            else:
                row_data[name] = value
        
        return row_data

    def exec(self, query_builder: QueryBuilder):
        sql_stmt, values = query_builder.get_sql_stmt()
        for row in self.sql_select(sql_stmt, values):
            row_data = self.process_row_data(row, query_builder)
            yield query_builder.model(**row_data)
 
    def close(self):
        self.conn.close()
    
    def select(self, model):
        return QueryBuilder(model, connection)


if __name__ == "__main__":
    #  Example
    class Department(Model):
        name: str
        employees_number: int
        courses: int

    class Student(Model):
        first_name: str
        last_name: str
        age: int | None
        department: List[Department]

    db_connect = DBConnection.dialect(DBType.SQLITE)
    connection = db_connect(database_path="testdb.sqlite")

    # db_connect = DBConnection.dialect(DBType.MYSQL)
    # connection = db_connect(host="********", user="******", password="******", database="*******")

    with Session(connection, log=True) as session:
        session.delete_and_create(Department)
        session.delete_and_create(Student)

        dp1 = Department(name="Science", employees_number=2900, courses=20)
        dp2 = Department(name="Art", employees_number=2100, courses=10)

        session.save(dp1)
        session.save(dp2)

        dp2.name = "Programming"
        session.save(dp2)

        obed = Student(first_name="obed", last_name="Clon", age=45, department=dp1)
        kwame = Student(first_name="Kwame", last_name="Klan", age=31, department=dp2)
        session.save(obed)
        session.save(kwame)

    with Session(connection, log=True) as session:
        statement = session.select(Student).where((Student.department == 1) | (Student.department == 2) & (Student.department == 2)).filter_by("first_name", "id", "age").limit(4)
        rows = session.exec(statement)
        for row in rows:
            print(row)
    

    class LectureHall(Model):
        name: str
        capacity: int
        location: str
    
    class Student(Model):
        first_name: str
        last_name: str
        age: int
    
    class StudentLectureHall(Model):
        lecture_halls: List[LectureHall]
        students: List[Student]
    

    with Session(connection) as session:
        for table in (LectureHall, Student, StudentLectureHall):
            session.delete_and_create(table)

        john = Student(first_name="John", last_name="Doe", age=34)
        lin = Student(first_name="Lin", last_name="Hally", age=35)

        lh1 = LectureHall(name="LH1", capacity=2300, location="Angel street")
        lh2 = LectureHall(name="LH2", capacity=4500, location="Cornor point")

        slh1 = StudentLectureHall(students=john, lecture_halls=lh1)
        slh2 = StudentLectureHall(students=john, lecture_halls=lh2)
        slh3 = StudentLectureHall(students=lin, lecture_halls=lh2)

        for data in (john, lin, lh1, lh2, slh1, slh2, slh3):
            session.save(data)
