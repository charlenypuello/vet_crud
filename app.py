from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "clave-super-secreta"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clinica.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ------------ MODELOS ------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)


class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50), nullable=False)
    dueno = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)


# ------------ INICIALIZAR BD ------------

def inicializar_bd():
    """Crea tablas y usuario admin si no existe."""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            user = User(username="admin", password="1234")
            db.session.add(user)
            db.session.commit()


# ------------ DECORADOR LOGIN ------------

def login_requerido(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


# ------------ RUTAS DE AUTENTICACIÓN ------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("lista_pacientes"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for("lista_pacientes"))
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("login"))


# ------------ RUTAS CRUD PACIENTES ------------

@app.route("/pacientes")
@login_requerido
def lista_pacientes():
    pacientes = Paciente.query.all()
    return render_template("pacientes.html", pacientes=pacientes)


@app.route("/pacientes/nuevo", methods=["GET", "POST"])
@login_requerido
def crear_paciente():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        especie = request.form.get("especie")
        dueno = request.form.get("dueno")
        telefono = request.form.get("telefono")

        if not nombre or not especie or not dueno:
            flash("Nombre, especie y dueño son obligatorios", "danger")
            return render_template("paciente_form.html", accion="Crear", paciente=None)

        nuevo = Paciente(
            nombre=nombre,
            especie=especie,
            dueno=dueno,
            telefono=telefono
        )
        db.session.add(nuevo)
        db.session.commit()
        flash("Paciente creado correctamente", "success")
        return redirect(url_for("lista_pacientes"))

    # GET – mostrar formulario vacío
    return render_template("paciente_form.html", accion="Crear", paciente=None)


@app.route("/pacientes/<int:paciente_id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_paciente(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)

    if request.method == "POST":
        nombre = request.form.get("nombre")
        especie = request.form.get("especie")
        dueno = request.form.get("dueno")
        telefono = request.form.get("telefono")

        if not nombre or not especie or not dueno:
            flash("Nombre, especie y dueño son obligatorios", "danger")
            return render_template("paciente_form.html", accion="Editar", paciente=paciente)

        paciente.nombre = nombre
        paciente.especie = especie
        paciente.dueno = dueno
        paciente.telefono = telefono
        db.session.commit()
        flash("Paciente actualizado correctamente", "success")
        return redirect(url_for("lista_pacientes"))

    return render_template("paciente_form.html", accion="Editar", paciente=paciente)


@app.route("/pacientes/<int:paciente_id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_paciente(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    db.session.delete(paciente)
    db.session.commit()
    flash("Paciente eliminado correctamente", "info")
    return redirect(url_for("lista_pacientes"))


# ------------ ARRANCAR APLICACIÓN ------------

if __name__ == "__main__":
    inicializar_bd()
    app.run(debug=True)


