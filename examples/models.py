from episode.model import Model, DBConnection, DBMS, Session

if __name__ == "__main__":
    #  Example
    class Department(Model):
        name: str
        employees_number: int
        courses: int

    class Student(Model):
        first_name: str
        last_name: str
        age: int
        department: Department

    # SQLite Connection
    db_connect = DBConnection.dialect(DBMS.SQLITE)
    connection_ = db_connect(database_path="testdb.sqlite")
 
    # MongoDB Connection
    # db_connect = DBConnection.dialect(DBMS.MONGODB)
    # connection_ = db_connect(database="school_system")

    # MySQL Connection
    # db_connect = DBConnection.dialect(DBMS.MYSQL)
    # connection_ = db_connect(host="localhost", user="root", password="ftpiptf0", database="school_system")
 
    with Session(connection_, log=True) as session:
        session.drop_create(Department)
        session.drop_create(Student)

        dp1 = Department(name="Science", employees_number=2900, courses=20)
        dp2 = Department(name="Art", employees_number=2100, courses=10)

        session.save(dp1)
        session.save(dp2)

        dp2.name = "Programming"
        session.save(dp2)

        obed = Student(first_name="obed", last_name="kobby", age=45, department=dp1)
        kwame = Student(first_name="Kwame", last_name="Klan", age=31, department=dp2)
        session.save(obed)
        session.save(kwame)

    with Session(connection_, log=True) as session:
        query_statement = session.select(Student).where((Student.department == 1)).OR(Student.department == 2).AND((Student.department == 2)).filter_by("first_name", "id", "age").limit(4)

        rows = session.exec(query_statement)
        for row in rows:
            print(row)
