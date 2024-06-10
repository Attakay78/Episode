# Episode

A python backend framework with rich features, easy to learn and fast to code.

The Key features are:

* **Fast Router**: Has a fast routing system that speeds up request to response time *
* **ORM**: Has an inbuilt ORM that supports SQLite, MySQL and MongoDB database *
* **Template Engine**: Minimalist integrated template engine for integrating your python code with html *
* **Fast to code**: Increase the speed to develop features *
* **Easy**: Designed to be easy to use and learn. Less time reading docs.
* **Short**: Minimize code duplication. Multiple features from each parameter declaration. Fewer bugs.

## Example

### Create it

* Create a file `main.py` with:

```Python
from episode.episode import Episode
from episode.httpresponse import HttpResponse
from episode.httpstatus import HTTPStatus
from episode.sqlmodel import Model, Session, DBType, DBConnection
from episode.template_engine import render_template

file_path = "student_db.sqlite"
db_conn = DBConnection.dialect(DBType.SQLITE)
connection = db_conn(database_path=file_path)

class Student(Model):
    first_name: str
    last_name: str
    user_name: str
    age: int


with Session(connection) as session:
    session.delete_and_create(Student)


if __name__ == "__main__":
    episode = Episode()

    # Expecting a get request only with path parameter 'username'
    @episode.get("/students/{username}")
    def get_student_by_username(request, username: str):
        with Session(connection) as session:
            sql_stmt = session.select(Student).where(Student.user_name == username)
            students = list(session.exec(sql_stmt))
            student = students[0] if students else None

            if student:
                context = {
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "age": student.age,
                }

                return render_template("student.html", context=context)
            else:
                return HttpResponse().write(
                    f"Student with username {username} does not exist",
                    status_code=HTTPStatus.NOT_FOUND,
                )

    # Expecting a post request only
    @episode.post("/students/add/")
    def add_student(request, student: Student):
        with Session(connection) as session:
            sql_smt = session.select(Student).where(Student.user_name == student.user_name)
            students = list(session.exec(sql_smt))

            if students:
                return HttpResponse().write(
                    f"User with username {student.user_name} already exist",
                    status_code=HTTPStatus.BAD_REQUEST,
                )

            session.save(student)

        return HttpResponse().write(
            "Data stored successfully", status_code=HTTPStatus.CREATED
        )
    
    episode.start()
```


### Run it

Run the server with:

<div class="termy">

```console
$ python main.py

INFO:   Serving at http://127.0.0.1:8880  (Press CTRL+C to quit)
```

</div>


### Check it

Open your browser at <a href="http://127.0.0.1:8880/" class="external-link" target="_blank">http://127.0.0.1:8880/</a>.

And Test any of the endpoints in the example
