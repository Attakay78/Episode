from episode.episode import Episode
from episode.http.httpresponse import HttpResponse
from episode.http.httpstatus import HTTPStatus
from episode.model import Model, Session, DBMS, DBConnection
from episode.template_engine import render_template

file_path = "student_db.sqlite"
db_conn = DBConnection.dialect(DBMS.SQLITE)
connection = db_conn(database_path=file_path)


class Student(Model):
    first_name: str
    last_name: str
    user_name: str
    age: int


with Session(connection) as session:
    session.drop_create(Student)

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


    # Expecting a post request only with json request body as Student Model
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


    @episode.delete("/students/{username}")
    def delete_student_by_username(request, username: str):
        with Session(connection) as session:
            sql_stmt = session.select(Student).where(Student.user_name == username)
            students = list(session.exec(sql_stmt))
            student = students[0] if students else None

            if student:
                session.delete(student)
                return HttpResponse().write(
                    "Student Deleted successfully", status_code=HTTPStatus.CREATED
                )
            else:
                return HttpResponse().write(
                    f"Student with username {username} does not exist",
                    status_code=HTTPStatus.NOT_FOUND,
                )


    # Expecting path parameter 'id' and a query parameter 'q'
    @episode.route("/data/{id}/")
    def get_params(request, id: int, q: int):
        return HttpResponse().write({"id": id, "query_param": q})


    @episode.get("/index/")
    def get_index(request):
        return render_template(
            "index.html", context={"topics": ["Python", "Golang", "Java", "C++"]}
        )


    episode.start()
