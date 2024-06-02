from flask import Flask, render_template, flash, redirect, url_for, request,session
from wtforms import Form, StringField, PasswordField, validators, EmailField, TextAreaField
import hashlib
from flaskext.mysql import MySQL
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))  # return ifadesini ekle
    return decorated_function


class RegistrationForm(Form):
    name = StringField("Name", [validators.Length(min=1, max=50)])
    username = StringField("Username", [validators.Length(min=4, max=25)])
    email = EmailField("EMAIL", [validators.Length(min=6, max=50)])
    password = PasswordField("Password", [
        validators.DataRequired(),
        validators.EqualTo(fieldname="confirm", message="Parolalar eslesmiyor")
    ])
    confirm = PasswordField("Password Again")

class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

app = Flask(__name__) # Flask app

app.config['SECRET_KEY'] = 'arda123'

app.config["MYSQL_DATABASE_HOST"] = "localhost"
app.config["MYSQL_DATABASE_USER"] = "root"
app.config["MYSQL_DATABASE_DB"] = "algoritma"
app.config["MYSQL_DATABASE_PORT"] = 3307
app.config["MYSQL_DATABASE_CHARSET"] = "utf8mb4"

mysql = MySQL()
mysql.init_app(app)

@app.route("/")
def index():
    number = 10
    name = "John"
    article = {
        "title": "My article",
        "author": "Me",
        "body": "This is my article"
    }

    return render_template("index.html", number=number, name=name, article=article)

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.get_db().cursor()

    basliklar = "SELECT * FROM articles where author = %s"

    result1 = cursor.execute(basliklar, (session["username"],))

    if result1 > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = hashlib.sha256(form.password.data.encode("utf-8")).hexdigest()

        cursor = mysql.get_db().cursor()

        sorgu = "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)"

        cursor.execute(sorgu, (name, email, username, password))

        mysql.get_db().commit()
        cursor.close()

        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.get_db().cursor()

        sorgu = "SELECT password FROM users WHERE username = %s"
        
        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data[0]  # Demetin sırasını kullanarak parolayı al
            if real_password == hashlib.sha256(password_entered.encode("utf-8")).hexdigest():

                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                return redirect(url_for("login"))

        else:
            return redirect(url_for("login"))

    return render_template("login.html", form=form)

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.get_db().cursor()

    sorgu = "SELECT * FROM articles WHERE id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/articles")
def articles():
    cursor = mysql.get_db().cursor()

    basliklar = "SELECT * FROM articles"

    result1 = cursor.execute(basliklar)

    if result1  > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")

@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.get_db().cursor()

        sorgu = "Select * from articles where id = %s and author = %s"

        result = cursor.execute(sorgu, (id, session["username"]))

        if result == 0:
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article[1]
            form.content.data = article[3]
            return render_template("update.html", form=form)
    else:
        form = ArticleForm(request.form)

        newtitle = form.title.data
        newcontent = form.content.data

        sorgu2 = "update articles set title = %s, content = %s where id = %s"

        cursor = mysql.get_db().cursor()

        cursor.execute(sorgu2, (newtitle, newcontent, id))

        mysql.get_db().commit()
        cursor.close()

        return redirect(url_for("dashboard"))  # Return a redirect after updating the article


@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.get_db().cursor()

    basliklar = "SELECT * FROM articles where author = %s and id = %s"

    result1 = cursor.execute(basliklar, (session["username"], id))

    if result1 > 0:
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.get_db().commit()
        return redirect(url_for("dashboard"))    
    else:
        return redirect(url_for("index"))  
    

@app.route("/addarticle", methods=["GET", "POST"])
@login_required
def addarticle():
    form  = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.get_db().cursor()

        sorgu = "INSERT INTO articles(title, author, content) VALUES(%s, %s, %s)"   

        cursor.execute(sorgu, (title, session["username"], content))

        mysql.get_db().commit()
        cursor.close()

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form = form)



class ArticleForm(Form):
    title = StringField("Baslik", [validators.Length(min=5, max=100)])
    content = TextAreaField("Icerik", [validators.Length(min=10)])

if __name__ == "__main__":
    app.run(debug=True)
