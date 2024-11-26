from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import json, os
import mysql.connector 
from datetime import datetime, date
from openpyxl import Workbook

#app = Flask(__name__, template_folder='templates')
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

DATABASE = "database/TScouting.db"

class DatabaseConnection:
    def __init__(self):
        self.datahost = ''
        self.datauser = ''
        self.datapassword = ''
        self.dataport = 3306
        self.datadatabase = ''
        self.connection = None

    def __enter__(self):
        self.connection = mysql.connector.connect(
            host=self.datahost,
            user=self.datauser,
            password=self.datapassword,
            port=self.dataport,
            database=self.datadatabase,
            connection_timeout=10
        )
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
@app.route('/')
def home():
    return render_template('L1_Load_Session.html')

#############################################################################################################
######################################        LOAD_SESSION       ############################################
#############################################################################################################

@app.route('/inicio_sesion', methods= ["GET","POST"])
def login():
    if request.method == 'POST':
        correo = request.form["correo"].upper()
        password = request.form["password"]
        
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT password, clase, nombre_usuario FROM TUser WHERE correo_usuario = %s", (correo,))
            user_data = cursor.fetchone()

        if user_data:
            encrypted_save_password = user_data[0]
            if encrypted_save_password and check_password_hash(encrypted_save_password, password):
                
                clase = user_data[1]
                session["email_admin"] = correo
                session["class"] = user_data[1]
                session["nombre_usuario"] = user_data[2]
                return open_admin_menu()
            else:
                return render_template("L3_EW_Login.html", response=1)
        else:
            return render_template("L3_EW_Login.html", response=2)
    else:
        return home()

@app.route('/registro_sesion', methods=["GET", "POST"])
def signin():
    return render_template("L2_Create_Account.html")

@app.route('/crear_usuario', methods=["POST"])
def register_new_user():
    email = request.form["email"].upper()
    clase = "admin"
    nombre_usuario = request.form["nombre_k8s"]
    nombre_usuario = nombre_usuario.upper()
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if verificar_no_existencia(dato=email, tabla="TUser", columna="correo_usuario"):
        if review_created_password(password) and password == confirm_password:
            encrypt_password = generate_password_hash(password=password, method="pbkdf2:sha256")
            
            with DatabaseConnection() as db:
                cursor = db.cursor()
                cursor.execute("INSERT INTO TUser (correo_usuario, nombre_usuario, password, clase) VALUES (%s, %s, %s, %s)", (email, nombre_usuario, encrypt_password, clase))
                db.commit()
            
            return render_template("L3_EW_Create_Account.html", response=1)
        elif review_created_password(password) and password != confirm_password:
            return render_template("L3_EW_Create_Account.html", response=3)
        else:
            return render_template("L3_EW_Create_Account.html", response=2)
    else:
        return render_template("L3_EW_Create_Account.html", response=4)

@app.route('/Menu_Administrador', methods=["GET","POST"])
def open_admin_menu():
    email_admin = session["email_admin"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_usuario FROM TUser WHERE correo_usuario = %s", (email_admin, ))
        nombre_usuario = cursor.fetchall()[0][0]
    session["nombre_usuario"] = nombre_usuario
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute(" SELECT nombre_usuario, clase FROM TUser")
        lista_encargados = cursor.fetchall()

    return render_template('L2_Menu_Admin.html', nombre_usuario= nombre_usuario, lista_encargados=lista_encargados)

@app.route('/Menu_Administrador/Cambio_clave', methods=["POST", "GET"])
def cambio_clave():
    return render_template("L3_Change_Password.html")

@app.route('/Cambiar_mi_contraseña', methods=['POST'])
def cambiar_mi_contrasena():
    if request.method == 'POST':
        correo_usuario = session["email_admin"]
        password = request.form["actual_password"]
        new_password1 = request.form["new_password1"]
        new_password2 = request.form["new_password2"]

        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT password FROM TUser WHERE correo_usuario = %s", (correo_usuario,))
            user_data = cursor.fetchone()

        if user_data:
            encrypted_save_password = user_data[0]
            if encrypted_save_password and check_password_hash(encrypted_save_password, password):
                if new_password1==new_password2:
                    with DatabaseConnection() as db:
                        cursor = db.cursor()
                        encrypt_password = generate_password_hash(password=new_password1, method="pbkdf2:sha256")
                        cursor.execute('UPDATE TUser SET password=%s WHERE correo_usuario=%s',(encrypt_password, correo_usuario, ))
                        db.commit()
                    
                    return render_template('L3_EW_Create_Account.html', response=6)
                elif review_created_password(password) and new_password1!=new_password2:
                    return render_template('L3_EW_Create_Account.html', response=7)
                else:
                    return render_template('L3_EW_Create_Account.html', response=2)
            else:
                return render_template('L3_EW_Create_Account.html', response=5)    
        else:
            return render_template("L3_EW_Login.html", response=2)
    else:
        return home()

    return "HOLA"
#############################################################################################################
########################################        SING_OFF       ##############################################
#############################################################################################################

@app.route('/Cerrar_Sesión', methods=["GET","POST"])
def sing_off():
    return render_template('L3_EW_singoff.html')

#############################################################################################################
###################################        SCHOOL_INTERFACE       ###########################################
#############################################################################################################

@app.route('/editar/<nombre_k8s>', methods=['GET','POST'])
def load_school_data(nombre_k8s):

    email_admin = session["email_admin"]
    session["main_school_key"] = nombre_k8s

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute(" SELECT nombre_usuario, clase FROM TUser")
        lista_encargados = cursor.fetchall()
    

    dataTk8s, dataTContactos, dataTPerfil = get_school_data(nombre_k8s = nombre_k8s)


    return render_template('L2_Main_School_Page.html', nombre_k8s=nombre_k8s, dataTk8s=dataTk8s, dataTContactos=dataTContactos, dataTPerfil=dataTPerfil, email_admin = email_admin, lista_encargados = lista_encargados)

@app.route('/Actualizar_Datos', methods=['GET','POST'])
def upload_school_data():

    correo_k8s=request.form["correo_k8s"]
    correo_k8s = actualizar_correo(correo_k8s)
    nombre_k8s=request.form["nombre_k8s"]
    if session["class"]=="superadmin":
        status = request.form["status"]
    elif session["class"]=="admin":
        status = request.form["status"]
    encargado_uniandes=request.form["encargado_uniandes"]
    dir_k8s=request.form["dir_k8s"]
    tel_k8s=request.form["tel_k8s"]
    Departamento_k8s=request.form["Departamento_k8s"]
    Municipio=request.form["Municipio"]
    Web=request.form["Web"]
    Calendario=request.form["Calendario"]
    Rango_aportancia = request.form["rango_aportancia"]
    Codigo_ICFES = request.form["codigo_icfes"]
    Codigo_DANE = request.form["codigo_dane"]
    estado_k8s = request.form['status']

    encargado_k8s = request.form["encargado_k8s"]
    encargado_telefono = request.form["encargado_telefono"]
    encargado_cargo = request.form["encargado_cargo"]
    nombre_rector = request.form["nombre_rector"]

    nombre_orientador = request.form["nombre_orientador"]
    tel_orientador = request.form["tel_orientador"]
    correo_orientador = request.form["correo_orientador"]
    nota_adicional = request.form["nota_adicional"]

    if estado_k8s=='ELIMINAR':
        return render_template('L3_EW_Delete_School.html', response=0)

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE Tk8s SET correo_k8s=%s ,encargado_uniandes=%s, tel_k8s=%s, dir_k8s=%s, departamento=%s, municipio=%s, rango_aportancia=%s, cod_icfes=%s, cod_dane=%s, status=%s, nota_adicional=%s WHERE nombre_k8s=%s", (correo_k8s, encargado_uniandes, tel_k8s,dir_k8s,Departamento_k8s,Municipio, Rango_aportancia, Codigo_ICFES, Codigo_DANE, status, nota_adicional, nombre_k8s) )
        cursor.execute("UPDATE Tk8s SET nombre_contacto=%s, telefono_contacto=%s, cargo_contacto=%s, nombre_orientador=%s, correo_orientador=%s, tel_orientador=%s WHERE nombre_k8s=%s", (encargado_k8s, encargado_telefono, encargado_cargo, nombre_orientador, correo_orientador, tel_orientador, nombre_k8s) )
        cursor.execute("UPDATE Tk8s SET nombre_Rector=%s, web=%s, calendario=%s WHERE nombre_k8s=%s", (nombre_rector,Web,Calendario,nombre_k8s) )
        db.commit()

    action = request.form["action"]
    if action=="report_upload":
        actualizar_fecha(nombre_k8s=nombre_k8s)
        return render_template('L3_EW_UpdateData.html', nombre_k8s=nombre_k8s, response=0)

    return render_template('L3_EW_UpdateData.html', nombre_k8s=nombre_k8s, response=1)

@app.route('/Eliminar_k8s', methods=['GET','POST'])
def delete_school():
    nombre_k8s = session['main_school_key']
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute('DELETE FROM Tk8s WHERE nombre_k8s=%s',(nombre_k8s, ))
        cursor.execute('DELETE FROM TMONU WHERE nombre_k8s=%s',(nombre_k8s, ))
        cursor.execute('DELETE FROM TProfesores WHERE k8s_profesor=%s',(nombre_k8s, ))
        cursor.execute('DELETE FROM TUniandes_Events WHERE nombre_k8s=%s',(nombre_k8s, ))
        db.commit()

    return render_template('L3_EW_Delete_School.html', response=1)

@app.route('/Reconocimientos', methods=['GET','POST'])
def load_school_awards():
    dataawards=[]
    dataevents = []
    main_school_key = session["main_school_key"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_premios FROM Tk8s WHERE nombre_k8s LIKE %s", (main_school_key, ))
        raw_dataawards = cursor.fetchall()

    if raw_dataawards!=[]:
        dataawards = json.loads(raw_dataawards[0][0])


    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_eventos, area_eventos, descripcion_eventos FROM Tk8s WHERE nombre_k8s LIKE %s", (main_school_key, ))
        raw_dataevents = cursor.fetchall()

    if raw_dataevents!=[]:
        raw_dataevents = raw_dataevents[0]
        dataevents = [json.loads(raw_dataevents[0]),json.loads(raw_dataevents[1]),json.loads(raw_dataevents[2])]

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT modelo_ONU FROM Tk8s WHERE nombre_k8s LIKE %s", (main_school_key, ))
        modeloONU = cursor.fetchall()

    return render_template('L3_School_Page_AwardsEvents.html', nombre_k8s=main_school_key,List_Awards=dataawards, List_Events=dataevents, modeloONU = modeloONU)

@app.route('/Crear Reconocimiento', methods=['POST'])
def create_award():
    main_school_key = session["main_school_key"]
    name_award = request.form["name_award"].upper()
    list_awards = []
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_premios FROM Tk8s WHERE nombre_k8s LIKE %s", ( main_school_key,))
        raw_list_awards = cursor.fetchall()
    
    if raw_list_awards != []:
        list_awards = raw_list_awards
        list_awards = json.loads(list_awards[0][0])    

    list_awards.append(name_award)

    list_awards = json.dumps(list_awards, ensure_ascii=False)
    
    if raw_list_awards == [(None, )]:
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO Tk8s (nombre_k8s, nombre_premios) VALUES (%s, %s)",(main_school_key, list_awards))
    elif raw_list_awards != [(None, )]:
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("UPDATE Tk8s SET nombre_premios=%s WHERE nombre_k8s=%s",(list_awards, main_school_key))
            db.commit()

    return load_school_awards()

@app.route('/Eliminar_premio', methods=["POST"])
def delete_award():
    main_school_key = session["main_school_key"]
    i = int(request.form["position"])
    list_awards = []
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_premios FROM Tk8s WHERE nombre_k8s LIKE %s", ( main_school_key,))
        raw_list_awards = cursor.fetchall()
    
    list_awards = raw_list_awards[0][0]
    list_awards = json.loads(list_awards)    

    list_awards.pop(i)

    list_awards = json.dumps(list_awards, ensure_ascii=False)

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE Tk8s SET nombre_premios=%s WHERE nombre_k8s=%s",(list_awards, main_school_key))
        db.commit()

    return load_school_awards()

@app.route('/Crear Evento', methods=['POST'])
def create_event():
    main_school_key = session["main_school_key"]
    name_event = request.form["name_event"].upper()
    area = request.form["Área del k8s"].upper()
    description = request.form["description"].upper()

    list_name_events = []
    list_area_events = []
    list_description_events = []

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_eventos, area_eventos, descripcion_eventos FROM Tk8s WHERE nombre_k8s LIKE %s", (main_school_key, ))
        raw_dataevents = cursor.fetchall()

    if raw_dataevents[0][0] != [] :
        raw_dataevents = raw_dataevents[0]
        dataevents = [json.loads(raw_dataevents[0]),json.loads(raw_dataevents[1]),json.loads(raw_dataevents[2])]
        list_name_events = dataevents[0]
        list_area_events = dataevents[1]
        list_description_events = dataevents[2]
     

    list_name_events.append(name_event)
    list_area_events.append(area)
    list_description_events.append(description)

    list_name_events = json.dumps(list_name_events, ensure_ascii=False)
    list_area_events = json.dumps(list_area_events, ensure_ascii=False)
    list_description_events = json.dumps(list_description_events, ensure_ascii=False)

    if raw_dataevents[0][0] == []:
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO Tk8s (nombre_k8s, nombre_eventos, area_eventos, descripcion_eventos) VALUES (%s, %s, %s, %s)",(main_school_key, list_name_events, list_area_events, list_description_events))
    elif raw_dataevents[0][0] != []:
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("UPDATE Tk8s SET nombre_eventos=%s, area_eventos=%s, descripcion_eventos=%s  WHERE nombre_k8s = %s", (list_name_events, list_area_events, list_description_events, main_school_key))
            db.commit()
    
    return load_school_awards()

@app.route('/Eliminar_evento', methods=["POST"])
def delete_event():
    main_school_key = session["main_school_key"]
    i = int(request.form["position"])

    list_name_events = []
    list_area_events = []
    list_description_events = []

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_eventos, area_eventos, descripcion_eventos FROM Tk8s WHERE nombre_k8s LIKE %s", (main_school_key, ))
        raw_dataevents = cursor.fetchall()

    raw_dataevents = raw_dataevents[0]
    dataevents = [json.loads(raw_dataevents[0]),json.loads(raw_dataevents[1]),json.loads(raw_dataevents[2])]
    list_name_events = dataevents[0]
    list_area_events = dataevents[1]
    list_description_events = dataevents[2]
     
    list_name_events.pop(i)
    list_area_events.pop(i)
    list_description_events.pop(i)

    list_name_events = json.dumps(list_name_events, ensure_ascii=False)
    list_area_events = json.dumps(list_area_events, ensure_ascii=False)
    list_description_events = json.dumps(list_description_events, ensure_ascii=False)

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE Tk8s SET nombre_eventos=%s, area_eventos=%s, descripcion_eventos=%s  WHERE nombre_k8s = %s", (list_name_events, list_area_events, list_description_events, main_school_key))
        db.commit()
    
    return load_school_awards()

@app.route('/Edición de fechas/', methods=['POST'])
def load_dates():

    main_school_key = session["main_school_key"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_fecha,fecha FROM Tk8s WHERE nombre_k8s=%s", (main_school_key, ))
        raw_datadates = cursor.fetchall()[0]

    if raw_datadates != []:
        
        nombre_fechas = json.loads(raw_datadates[0])
        fechas = json.loads(raw_datadates[1])

        datadates = [nombre_fechas, fechas]
    
    return render_template('L3_School_Page_Dates.html', nombre_k8s=main_school_key,List_Dates=datadates)


@app.route('/Editar_fecha', methods=["POST"])
def edit_date():
    main_school_key = session["main_school_key"]
    nombre_fecha = request.form["nombre_fecha"]
    fecha = request.form["fecha"]
    position = int(request.form["position"])
    action = request.form["action"]

    if action=="update":
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT nombre_fecha, fecha FROM Tk8s WHERE nombre_k8s LIKE %s", (main_school_key, ))
            raw_datadates = cursor.fetchall()

        raw_datadates = raw_datadates[0]
        nombre_fechas = json.loads(raw_datadates[0])
        fechas = json.loads(raw_datadates[1])

        fechas[position] = fecha

        nombre_fechas = json.dumps(nombre_fechas, ensure_ascii=False)
        fechas = json.dumps(fechas, ensure_ascii=False)

        with DatabaseConnection() as db:
                cursor = db.cursor()
                cursor.execute("UPDATE Tk8s SET fecha=%s WHERE nombre_k8s = %s AND nombre_fecha = %s", (fechas, main_school_key, nombre_fechas))
                db.commit()

    if action=="delete":
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT nombre_fecha, fecha FROM Tk8s WHERE nombre_k8s LIKE %s", (main_school_key, ))
            raw_datadates = cursor.fetchall()

        raw_datadates = raw_datadates[0]
        nombre_fechas = json.loads(raw_datadates[0])
        fechas = json.loads(raw_datadates[1])

        nombre_fechas.pop(position)
        fechas.pop(position)

        nombre_fechas = json.dumps(nombre_fechas, ensure_ascii=False)
        fechas = json.dumps(fechas, ensure_ascii=False)

        with DatabaseConnection() as db:
                cursor = db.cursor()
                cursor.execute("UPDATE Tk8s SET fecha=%s, nombre_fecha=%s WHERE nombre_k8s = %s", (fechas, nombre_fechas, main_school_key))
                db.commit()

    return load_dates()

@app.route('/Crear fechas', methods=['POST'])
def create_date():
    main_school_key = session["main_school_key"]
    date = request.form["fecha"]
    nombre_fecha = request.form["nombre_fecha"]
    
    nombre_fechas = []
    fechas = []
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_fecha, fecha FROM Tk8s WHERE nombre_k8s LIKE %s ", (main_school_key, ))
        raw_datadates = cursor.fetchall()
            
    if raw_datadates[0][0] != []:
        raw_datadates = raw_datadates[0]
        datadates = [json.loads(raw_datadates[0]), json.loads(raw_datadates[1])]
        nombre_fechas = datadates[0]
        fechas = datadates[1]


    nombre_fechas.append(nombre_fecha)
    fechas.append(date)

    nombre_fechas = json.dumps(nombre_fechas, ensure_ascii=False)
    fechas = json.dumps(fechas, ensure_ascii=False)

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE Tk8s SET nombre_fecha = %s, fecha = %s WHERE nombre_k8s = %s", (nombre_fechas, fechas, main_school_key))
        db.commit()

    return load_dates()

@app.route('/Edición_de_profesores', methods=['POST','GET'])
def load_teachers_data():

    k8s_profesor = session["main_school_key"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM TProfesores WHERE k8s_profesor=%s", (k8s_profesor, ))
        datos_profesores = cursor.fetchall()

    return render_template('L3_School_Page_Teachers.html', data = datos_profesores)

@app.route('/Edición_de_profesores/Crear_profesor', methods=['POST','GET'])
def create_teacher():

    k8s_profesor = session["main_school_key"]
    nombre_profesor = request.form["teacher_name"]
    area_profesor = request.form["Area_profesor"]
    enfasis_profesor = request.form["enfasis_profesor"]
    telefono_profesor = request.form["tel_teacher"]
    correo_profesor = request.form["email_teacher"]

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("INSERT INTO TProfesores (k8s_profesor, nombre_profesor, area_profesor, enfasis_profesor, telefono_profesor, correo_profesor) VALUES (%s, %s, %s, %s, %s, %s)", (k8s_profesor, nombre_profesor, area_profesor, enfasis_profesor, telefono_profesor, correo_profesor))
        db.commit()
 
    return redirect(url_for('load_teachers_data'))

@app.route('/Edición_de_profesores/Eliminar_profesor', methods=["GET","POST"])
def delete_teacher():

    k8s_profesor = request.form['k8s_profesor']
    nombre_profesor = request.form['nombre_profesor']
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM TProfesores WHERE k8s_profesor = %s AND nombre_profesor = %s", (k8s_profesor, nombre_profesor, ))
        db.commit()

    return redirect(url_for('load_teachers_data'))

@app.route('/Información_Modelo_ONU', methods=['POST'])
def load_modelo_ONU():
    nombre_k8s = session["main_school_key"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM TMONU WHERE nombre_k8s=%s",(nombre_k8s ,))
        data = cursor.fetchall()[0]

    return render_template("L3_School_Page_ModeloONU.html", data=data)

@app.route('/modelo ONU/Actualizar data', methods=["GET","POST"])
def update_MONU_data():
    main_school_key = session["main_school_key"]
    status_MONU = request.form["MONU_SN"]
    nombre_MONU = request.form["nombre_MONU"]
    nombre_encargadoMONU = request.form["nombre_encargadoMONU"]
    tel_encargadoMONU = request.form["tel_encargadoMONU"]
    correo_encargadoMONU = request.form["correo_encargadoMONU"]
    fecha_MONU = request.form["fecha_MONU"]

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT correo_k8s FROM Tk8s WHERE nombre_k8s=%s", (main_school_key, ))
        correo_k8s = cursor.fetchall()

    correo_k8s = str(correo_k8s)
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE TMONU SET correo_k8s=%s, status_MONU=%s, nombre_MONU=%s, nombre_encargado_MONU=%s, tel_encargado_MONU=%s, correo_encargado_MONU=%s, fecha_MONU=%s  WHERE nombre_k8s LIKE %s", (correo_k8s, status_MONU, nombre_MONU, nombre_encargadoMONU, tel_encargadoMONU, correo_encargadoMONU, fecha_MONU, main_school_key, ))
        db.commit()

    return load_modelo_ONU()

@app.route('/Eventos_uniandes_k8s', methods=['POST'])
def load_uniandes_events():
    main_school_key = session["main_school_key"]
    
    data_nombre_eventos = []
    data_fecha_eventos = []
    data_descripcion_eventos = []
    
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_k8s, tipo_feria_uniandes, profesional_feria_uniandes, fecha_feria_uniandes, num_atendidos, descripcion_feria_uniandes  FROM TUniandes_Events WHERE nombre_k8s=%s", (main_school_key, ))
        data_uniandes_events = cursor.fetchall()
        cursor.execute("SELECT nombre_usuario FROM TUser")
        list_profesionales = cursor.fetchall()
    
    actualizar_ultima_atencion()

    data_official_events = get_official_events()
    return render_template("L3_School_Page_Uniandes_Events.html", data_uniandes_events = data_uniandes_events, list_profesionales=list_profesionales, data_official_events=data_official_events)

@app.route('/Crear_evento_uniandes', methods=['POST'])
def create_uniandes_event():
    main_school_key = session["main_school_key"]
    num_atendidos = request.form["numero-atendidos"]
    profesional_feria_uniandes = request.form["Profesional encargado evento"]
    nombre_feria_uniandes = request.form["Nombre de evento uniandes"]
    fecha_feria_uniandes = request.form["fecha_feria_uniandes"]
    descripcion_feria_uniandes = request.form["descripcion_feria_uniandes"]

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("INSERT INTO TUniandes_Events (nombre_k8s, num_atendidos, tipo_feria_uniandes, profesional_feria_uniandes, fecha_feria_uniandes, descripcion_feria_uniandes) VALUES (%s, %s, %s, %s, %s, %s)", (main_school_key, num_atendidos, nombre_feria_uniandes, profesional_feria_uniandes, fecha_feria_uniandes, descripcion_feria_uniandes))
        db.commit()
    
    actualizar_ultima_atencion()
    return load_uniandes_events()

@app.route('/Eliminar_evento_uniandes', methods=['POST'])
def delete_uniandes_event():

    main_school_key = session["main_school_key"]
    fecha_feria_uniandes = request.form["fecha_feria_uniandes"]
    tipo_feria_uniandes = request.form["tipo_feria_uniandes"]

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM TUniandes_Events WHERE nombre_k8s=%s AND fecha_feria_uniandes=%s AND tipo_feria_uniandes=%s", (main_school_key, fecha_feria_uniandes,tipo_feria_uniandes ,))
        db.commit()
    actualizar_ultima_atencion()
    return load_uniandes_events()

@app.route('/Historial_contacto', methods=['POST'])
def load_history_contact():
    main_school_key = session["main_school_key"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM THISTORY_CONTACT WHERE nombre_k8s = %s", (main_school_key, ))
        history_contact = cursor.fetchall()
        
    return render_template('L3_School_Page_History_Contact.html',history_contact = history_contact)

@app.route('/Historial_contacto/Crear_contacto', methods=['POST'])
def create_contact():
    main_school_key = session["main_school_key"]
    fecha_primitiva = datetime.now()
    fecha = fecha_primitiva.date()
    tipo_contacto = request.form["tipo_contacto"]
    descripcion = request.form["descripcion"]

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("INSERT INTO THISTORY_CONTACT (nombre_k8s, fecha, tipo_contacto, descripcion) VALUES (%s, %s, %s, %s)",(main_school_key, fecha, tipo_contacto, descripcion))
        db.commit()

    return load_history_contact()

@app.route('/Historial_contacto/Eliminar_contacto', methods=['POST'])
def delete_contact():
    main_school_key = session["main_school_key"]
    fecha = request.form["fecha"]
    tipo_contacto = request.form["tipo_contacto"]
    descripcion = request.form["descripcion"]

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM THISTORY_CONTACT WHERE nombre_k8s=%s AND fecha=%s AND tipo_contacto=%s AND descripcion=%s", (main_school_key, fecha, tipo_contacto, descripcion))
        db.commit()

    return load_history_contact()
#############################################################################################################
####################################        COMMON_ADMIN_FUNCTIONS       ###########################################
#############################################################################################################

@app.route('/Buscar_k8s/',methods=["GET","POST"])
def search_school():

    query = request.form['query']
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM Tk8s WHERE nombre_k8s LIKE %s", ("%" + query + "%",))
        results = cursor.fetchall()
    db.close()
    
    return render_template('L3_Result_General_Search.html', results = results, selection=1)

@app.route('/Cambiar_clase_gestor', methods = ["GET","POST"])
def change_gestor_status():
    nombre_gestor = request.form["Gestor"]
    clase = request.form["Clase_gestor"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE Tk8s SET clase=%s WHERE nombre_usuario=%s", (clase, nombre_gestor))
        db.commit()

    return render_template("L3_EW_Upload_manager_status")

@app.route('/EW_Descargar_archivo', methods = ["GET", "POST"])
def ew_descargar_excel():
    if request.method == 'POST':
        data = request.form.get('data')
    else:
        data = request.args.get('data')
    return render_template('L4_EW_DownloadExcel.html',data=data)

@app.route('/Descargar archivo', methods = ["GET", "POST"])
def descargar_excel():

    palabra_clave = request.form["keyword"]
    data_str = request.form["data"]
    name_file = request.form["name_file"]
    list_columnas = request.form["list_columnas"]

    if data_str=="":
        return render_template('L4_EW_Filter.html',response=1)

    if name_file=="":
        fecha_primitiva = str(datetime.now())
        fecha_primitiva = fecha_primitiva.replace(':',"-")
        fecha_primitiva = fecha_primitiva.replace('.',"-")
        name_file = "Resultado_Búsqueda_Filtrada-" + fecha_primitiva
    data = json.loads(data_str)
    wb = Workbook()
    ws = wb.active
    list_columnas = funtion_str_to_list(message=list_columnas)
    ws.append(list_columnas)

    for row in data:
        if palabra_clave == "k8ss":
            lista_correos = funtion_str_to_list(row[1])
            for correo in lista_correos:
                correo = correo.replace("'","")
                row[1] = correo
                ws.append(row)
        if palabra_clave == "Fechas":
            lista_correos = funtion_str_to_list(row[2])
            for correo in lista_correos:
                row[2] = correo
                ws.append(row)
        if palabra_clave == "eventos uniandes":
            with DatabaseConnection() as db:
                cursor = db.cursor()
                nombre_k8s = row[0]
                cursor.execute("SELECT correo_k8s FROM Tk8s WHERE nombre_k8s = %s", (nombre_k8s, ) )
                lista_correos = cursor.fetchall()[0][0]
            lista_correos = funtion_str_to_list(lista_correos)
            for correo in lista_correos:
                correo = correo.replace("'","")
                row.insert(1, correo)
                ws.append(row)
        elif palabra_clave=="profesores" or palabra_clave=="monitcontacto":
            ws.append(row)
        

    nombre = name_file + ".xlsx"
    downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    file_path = os.path.join(downloads_folder, nombre)
    wb.save(file_path)

    return render_template("L4_EW_DownloadExcel.html", name_file=nombre)

#############################################################################################################
#################################        SUPER_ADMIN_FUNCTIONS       ########################################
#############################################################################################################
@app.route('/Página_tranferir_k8ss', methods = ["GET","POST"])
def transferir_k8ss_page():
    data_profesionales = [False, False, False]
    list_k8ss=[]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_usuario FROM TUser")
        list_profesionales = [profesional[0] for profesional in cursor.fetchall()]
    if request.method == "POST":
        profesional1 = request.form.get("Profesional_1")
        profesional2 = request.form.get("Profesional_2")
        departamento = request.form.get("Departamento_k8s")
        if profesional1 and departamento:
            data_profesionales = [profesional1, profesional2, departamento]
            with DatabaseConnection() as db:
                cursor = db.cursor()
                if departamento == "TODOS LOS DEPARTAMENTOS":
                    cursor.execute("SELECT nombre_k8s, departamento, correo_k8s, encargado_uniandes, rango_aportancia FROM Tk8s WHERE encargado_uniandes LIKE %s", (profesional1,))
                if departamento != "TODOS LOS DEPARTAMENTOS":
                    cursor.execute("SELECT nombre_k8s, departamento, correo_k8s, encargado_uniandes, rango_aportancia FROM Tk8s WHERE encargado_uniandes = %s AND departamento = %s", (profesional1, departamento, ))
                list_k8ss = cursor.fetchall()
            response = 2
        else:
            response = 1
    else:
        response = 1
    return render_template("L3_Transfer_sheet.html", list_profesionales=list_profesionales, response=response, lista_k8ss=list_k8ss, data_profesionales=data_profesionales)

@app.route('/Transferir_k8ss_entre_profesionales', methods = ["GET","POST"])
def transferir_k8ss():
    query = request.form.get("data_cambio")
    lista_k8ss = request.form['lista_k8ss']

    action = request.form['action']
    query = json.loads(query)
    profesional1 = query[0]
    profesional2 = query[1]
    departamento = query[2]
    if action=='All':
        if profesional2 == "":
            return render_template("L4_EW_SuperAdminSupportWindow.html", profesional1=profesional1, profesional2=profesional2, departamento=departamento, response=2)

        with DatabaseConnection() as db:
            cursor = db.cursor()
            if departamento != "TODOS LOS DEPARTAMENTOS":
                cursor.execute("UPDATE Tk8s SET encargado_uniandes = %s WHERE encargado_uniandes = %s AND departamento = %s",(profesional2, profesional1, departamento))
            else:
                cursor.execute("UPDATE Tk8s SET encargado_uniandes = %s WHERE encargado_uniandes = %s",(profesional2, profesional1))
            db.commit()
    elif action=='Selected Schools':
        if profesional2 == "":
            return render_template("L4_EW_SuperAdminSupportWindow.html", profesional1=profesional1, profesional2=profesional2, departamento=departamento, response=2)

        lista_k8ss = lista_k8ss.replace('[','')
        lista_k8ss = lista_k8ss.replace(']','')
        lista_k8ss = lista_k8ss.replace('(','')
        lista_k8ss = lista_k8ss.replace("'","")
        lista_k8ss = lista_k8ss.split('), ')
        lista_k8ss_transferidos = []
        for elemento in lista_k8ss:
            elemento = elemento.split(',')
            try:
                form_answer = request.form[elemento[0]]
                with DatabaseConnection() as db:
                    cursor = db.cursor()
                    cursor.execute('UPDATE Tk8s SET encargado_uniandes = %s WHERE encargado_uniandes = %s AND nombre_k8s = %s',(profesional2, profesional1, form_answer))
                    db.commit()
                lista_k8ss_transferidos.append(form_answer)
            except:
                None
        return render_template("L4_EW_SuperAdminSupportWindow.html", profesional1=profesional1, profesional2=profesional2, departamento=departamento, response=3, lista_k8ss_transferidos= lista_k8ss_transferidos)
    return render_template("L4_EW_SuperAdminSupportWindow.html", profesional1=profesional1, profesional2=profesional2, departamento=departamento, response=1)

@app.route('/Ventana_crear_k8s', methods = ["GET","POST"])
def EW_create_school():
    return render_template("L3_EW_Create_School.html", response=1)

@app.route('/Editar_eventos_oficiales',methods = ["GET","POST"])
def edit_official_uniandes_events():
    list_official_events = get_official_events()
    return render_template("L4_Edit_official_events.html", list_official_events=list_official_events)

@app.route('/Crear_k8s', methods = ["GET","POST"])
def create_school():

    nombre_k8s = request.form.get('name_school')
    nombre_premios = json.dumps([], ensure_ascii=False)
    nombre_eventos = json.dumps([], ensure_ascii=False)
    area_eventos = json.dumps([], ensure_ascii=False)
    descripcion_eventos = json.dumps([], ensure_ascii=False)
    nombre_fecha = json.dumps([], ensure_ascii=False)
    fecha = json.dumps([], ensure_ascii=False)

    if verificar_no_existencia(dato=nombre_k8s, columna="nombre_k8s",tabla="Tk8s"):
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO Tk8s (nombre_k8s, status) VALUES (%s, %s)", (nombre_k8s, "ACTIVO", ))
            cursor.execute("UPDATE Tk8s SET nombre_premios = %s, nombre_eventos = %s, area_eventos = %s, descripcion_eventos = %s WHERE nombre_k8s = %s", (nombre_premios, nombre_eventos, area_eventos, descripcion_eventos, nombre_k8s))
            cursor.execute("UPDATE Tk8s SET nombre_fecha = %s, fecha = %s WHERE nombre_k8s = %s", (nombre_fecha, fecha, nombre_k8s))
            cursor.execute("INSERT INTO TMONU (nombre_k8s) VALUES (%s)", (nombre_k8s, ))
            db.commit()

    return render_template("L3_EW_Create_School.html", response=2, school_name=nombre_k8s)

@app.route('/Administrar_profesionales', methods=["GET", "POST"])
def manage_users_page():
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_usuario, clase FROM TUser")
        lista_encargados = cursor.fetchall()
    return render_template("L3_Management_Admins.html", lista_encargados=lista_encargados)

@app.route('/Administrar_profesionales/Acciones', methods=["GET","POST"])
def manage_professionals():
    with DatabaseConnection() as db:
        cursor = db.cursor()
        profesional = request.form['Encargado']
        action = request.form['action'] 
        if action == "Cambiar estatus":
            nuevo_status = request.form.get('Clase_gestor')
            cursor.execute("UPDATE TUser SET clase=%s WHERE nombre_usuario=%s", (nuevo_status, profesional))
            db.commit()
        elif action == "Eliminar profesional":
            return render_template('L4_EW_Delete_professional.html', profesional=profesional, response=1)
        elif action == "Restablecer contrasena":
            
            return restore_password(profesional=profesional)
    return open_admin_menu()

@app.route('/Administrar_profesionales/Eliminar_profesional', methods=['POST'])
def delete_professional():
    with DatabaseConnection() as db:
        cursor=db.cursor()
        profesional=request.form["profesional"]
        cursor.execute("DELETE FROM TUser WHERE nombre_usuario=%s", (profesional,))
        cursor.execute("UPDATE Tk8s SET encargado_uniandes=%s WHERE encargado_uniandes=%s", ('NO ASIGNADO',profesional,))
        db.commit()
    return render_template('L4_EW_Delete_professional.html', profesional=None, response=2)

@app.route('/Administrar_eventos_oficiales/Eliminar_evento_oficial', methods=["POST"])
def delete_official_uniandes_event():
    nombre_evento = request.form["nombre_evento"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM TOFFICIAL_EVENTS WHERE nombre_evento=%s", (nombre_evento,))
        db.commit()
    return render_template("L4_EW_Edit_official_events.html", nombre_evento=nombre_evento, response=1)

@app.route('/Administrar_eventos_oficiales/Crear_evento_oficial', methods=["POST"])
def create_official_uniandes_event():
    nombre_evento = request.form["official_event_name"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("INSERT INTO TOFFICIAL_EVENTS (nombre_evento) VALUES (%s)",(nombre_evento,))
        db.commit()
    return render_template("L4_EW_Edit_official_events.html", nombre_evento=nombre_evento, response=0)

@app.route('/Restablecer_contrasena/<profesional>', methods=['GET','POST'])
def restore_password(profesional):
    nombre_usuario = profesional
    contrasena = "2024*ANDES"
    encrypt_password = generate_password_hash(password=contrasena, method="pbkdf2:sha256")
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE TUser SET password = %s WHERE nombre_usuario = %s",(encrypt_password, nombre_usuario))
        db.commit()
    return render_template('L4_EW_Restore_Password.html', nombre_usuario=nombre_usuario, list_columnas=[])

@app.route('/Monitoreo_profesionales', methods=['GET','POST'])
def monitoreo_profesionales():
    clase_usuario = session["class"]
    data_monitoreo = []
    if clase_usuario=="superadmin":
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT nombre_usuario FROM TUser")
            list_nombres = cursor.fetchall()
    else: 
        list_nombres = [session["nombre_usuario"]]

    for profesional in list_nombres:
        if type(profesional) == tuple:    
           profesional = profesional[0]
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute('SELECT ultima_fecha_atencion, fecha_actualizacion, nombre_k8s, calendario FROM Tk8s WHERE encargado_uniandes = %s', (profesional, ))
            data = cursor.fetchall()
        
        contador_actualizados = 0
        contador_atendidos = 0
        cactualA = 0
        catendA = 0
        ctotalA = 0
        cactualB = 0
        catendB = 0 
        ctotalB = 0

        if session['nombre_usuario']==profesional:
            final_data = []
        for row in data:
            row = list(row)
            fecha_atencion = row[0]
            fecha_atencion = convertir_fecha(fecha_atencion)
            fecha_actualizacion = row[1]
            fecha_actualizacion = convertir_fecha(fecha_actualizacion)
            fecha_primitiva = datetime.now()
            fecha_hoy = fecha_primitiva.date()


            semestre = definir_semestre()

            row.append("")
            row.append("")
            
            if row[3] == "B":
                ctotalB += 1
                if fecha_atencion!=None:
                    if fecha_hoy.year==fecha_atencion.year and semestre=="segundo_semestre":
                        if fecha_atencion.month==7 or fecha_atencion.month==8 or fecha_atencion.month==9 or fecha_atencion.month==10 or fecha_atencion.month==11 or fecha_atencion.month==12:
                            row[4] = "ATENDIDO"
                            contador_atendidos += 1
                            catendB +=1
                    elif fecha_hoy.year==fecha_atencion.year and semestre=="primer_semestre":
                            row[4] = "ATENDIDO"
                            contador_atendidos += 1
                            catendB += 1
                    elif int(fecha_hoy.year)==int(fecha_atencion.year)+1 and semestre=="primer_semestre":
                        if fecha_atencion.month==7 or fecha_atencion.month==8 or fecha_atencion.month==9 or fecha_atencion.month==10 or fecha_atencion.month==11 or fecha_atencion.month==12:
                            row[4] = "ATENDIDO"
                            contador_atendidos += 1
                            catendB += 1

                if fecha_actualizacion!=None:
                    if fecha_hoy.year==fecha_actualizacion.year and semestre=="segundo_semestre":
                        if fecha_actualizacion.month==7 or fecha_actualizacion.month==8 or fecha_actualizacion.month==9 or fecha_actualizacion.month==10 or fecha_actualizacion.month==11 or fecha_actualizacion.month==12:
                            row[5] = "ACTUALIZADO"
                            contador_actualizados += 1
                            cactualB += 1
                    elif fecha_hoy.year==fecha_actualizacion.year and semestre=="primer_semestre":
                            row[5] = "ACTUALIZADO"
                            contador_actualizados += 1
                            cactualB += 1
                    elif int(fecha_hoy.year)==int(fecha_actualizacion.year)+1 and semestre=="primer_semestre":
                        if fecha_actualizacion.month==7 or fecha_actualizacion.month==8 or fecha_actualizacion.month==9 or fecha_actualizacion.month==10 or fecha_actualizacion.month==11 or fecha_actualizacion.month==12:
                            row[5] = "ACTUALIZADO"
                            contador_actualizados += 1
                            cactualB += 1
                    
            if row[3]=="A":
                ctotalA += 1
                if fecha_atencion!=None:
                    if fecha_hoy.year==fecha_atencion.year:
                        row[4] = "ATENDIDO"
                        contador_atendidos += 1
                        catendA += 1
                if fecha_actualizacion!=None:
                    if fecha_hoy.year==fecha_actualizacion.year:
                        row[5] = "ACTUALIZADO"
                        contador_actualizados += 1
                        cactualA+= 1
             

            if session['nombre_usuario']!='LAURA TOLE':
                final_data.append(row)
            elif session['nombre_usuario']==profesional:
                final_data.append(row)
        
        name_user = session['nombre_usuario']  

        num_k8ss = len(data)
        lista_profesional = [profesional, num_k8ss, contador_actualizados, contador_atendidos, cactualA, catendA, ctotalA, cactualB, catendB, ctotalB]
        
        if num_k8ss!=0:
            data_monitoreo.append(lista_profesional)

    return render_template('L2_Control_Profesionales.html', data_monitoreo=data_monitoreo, enumerate=enumerate, data=final_data)

@app.route('/Monitoreo_contacto', methods=['POST','GET'])
def load_monitoreo_contacto():
    list_profesionales = obtener_profesionales()
    return render_template('L3_Control_contact.html', list_profesionales=list_profesionales, response=0)

@app.route('/Monitoreo_contacto/Resultados_Busqueda', methods=['POST'])
def monitoreo_contacto():

    list_profesionales = obtener_profesionales()
    final_list_columnas = ["Nombre k8s", "Fecha de contacto","Estado" ,"Encargado", "Tipo de atención", "Descripción"]
    result_search = []
    
    nombre_k8s = request.form.get("nombre_k8s","")
    tipo_contacto = request.form.get("tipo_contacto", "")
    profesional = request.form.get("profesional", "")
    estado_actualizacion = request.form.get("estado_actualizacion", "")
    estado_atencion = request.form.get("estado_atencion", "")

    if nombre_k8s==False:
        nombre_k8s = "%"
    else:
        nombre_k8s = "%"+ nombre_k8s + "%"

    instruc_condicionales = ""
    list_columnas = ["nombre_k8s","fecha","tipo_contacto","descripcion"]
    list_condicionales = []

    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="historial", condicional=nombre_k8s, columnas='*', list_columnas=list_columnas, colum_condicional='nombre_k8s', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="historial", condicional=tipo_contacto, columnas='*', list_columnas=list_columnas, colum_condicional='tipo_contacto', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)

    query = f"SELECT * FROM THISTORY_CONTACT WHERE {instruc_condicionales}"
    tuple_condicionales = tuple(list_condicionales)

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute(query, tuple_condicionales)
        result_search = cursor.fetchall()

    if result_search==[]:
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM THISTORY_CONTACT")
            result_search = cursor.fetchall()
    
    #Construir database nueva:
    i=0
    while i<len(result_search):
        fila = list(result_search[i])
        posicion = i
        result_search[posicion] = fila
        nombrecol = fila[0] 

        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT encargado_uniandes FROM Tk8s WHERE nombre_k8s = %s",(nombrecol,))
            profesional_encargado = cursor.fetchone()[0]
            cursor.execute("SELECT estado_actualizacion FROM Tk8s WHERE nombre_k8s = %s",(nombrecol,))
            estact = cursor.fetchone()[0]
            cursor.execute("SELECT estado_atencion FROM Tk8s WHERE nombre_k8s = %s",(nombrecol,))
            estatend = cursor.fetchone()[0]       


        if estact == None:
            estact = "NO ACTUALIZADO"
        if estatend == None:
            estatend = "NO ATENDIDO"
        
        estactestatend = estact + '-' + estatend

        fila.insert(2, estactestatend)
        fila.insert(3,profesional_encargado)

        param1=1
        param2=1
        param3=1

        if profesional != "NULL":
            if profesional != profesional_encargado:
                param1 = 0
        if estado_actualizacion != "NULL":
            if estado_actualizacion != estact:
                param2 = 0
        if estado_atencion != "NULL":
            if estado_atencion != estatend:
                param3 = 0

        mult_params = param1 * param2 * param3
        if mult_params==0:
            result_search.pop(posicion)
        
        i = i + mult_params

    num_coincidences = len(result_search)

    return render_template('L3_Control_contact.html', list_profesionales=list_profesionales, list_columnas=final_list_columnas, result_search=result_search, enumerate=enumerate, response=1, num_coincidences=num_coincidences)

@app.route('/Busqueda_Filtrada', methods=["POST","GET"])
def filtered_search():
    action = request.form["action"]
    list_profesionales = obtener_profesionales()

    if action=="Busk8ss":
        return render_template('L3_Filter_Schools_Page.html', response=0, enumerate=enumerate, list_profesionales=list_profesionales)
    elif action=="BusProfesores":
        return render_template('L3_Filter_Teachers_Page.html', response = 0, enumerate=enumerate)
    elif action=="BusEventos":
        return render_template('L3_Filter_Uniandes_Events_Page.html', response = 0, enumerate=enumerate, list_profesionales=list_profesionales)
    elif action=="MonContacto":
        list_profesionales = obtener_profesionales()
        return render_template('L3_Control_contact.html', list_profesionales=list_profesionales)

@app.route('/Busqueda_filtrada/k8ss', methods=['GET','POST'])
def busqueda_filtrada_k8ss():
    Estado = request.form["status"]
    Departamento = request.form["Departamento_k8s"]
    RangoAportancia = request.form["Rango_Aportancia"]
    Calendario = request.form["Calendario"]
    Encargado = request.form["encargado_uniandes"]
    fecha_atendidos_antes = request.form["fecha_atendidos_antes"]
    fecha_atendidos_despues = request.form["fecha_atendidos_despues"]
    fecha_actualizados_antes = request.form["fecha_actualizados_antes"]
    fecha_actualizados_despues = request.form["fecha_actualizados_despues"]

    if RangoAportancia=="TODOS LOS RANGOS" and Calendario=="NULL" and Departamento=="NULL" and Encargado=="NULL" and fecha_actualizados_antes=="" and fecha_actualizados_despues=="" and fecha_atendidos_antes=="" and fecha_atendidos_despues=="" and Estado=="ACTIVO":
        return render_template('L4_EW_Filter.html', palabra_clave="k8ss", response=0)


    columnas = "nombre_k8s, correo_k8s, encargado_uniandes, tel_k8s, fecha_actualizacion, ultima_fecha_atencion"
    list_columnas = ['Nombre k8s','Correo k8s','Encargado Uniandes','Teléfono Uniandes','Fecha de actualización','Última fecha de atención']

    if RangoAportancia=="1.0 - 2.0":
            list_columnas.append("Rango")
            columnas = columnas + ", rango_aportancia"

    instruc_condicionales = ""
    list_condicionales = []
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="school", condicional=Estado, columnas=columnas, list_columnas=list_columnas, colum_condicional='status', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    if RangoAportancia != "1.0 - 2.0" and RangoAportancia != "TODOS LOS RANGOS":
        instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="school", condicional=RangoAportancia, columnas=columnas, list_columnas=list_columnas, colum_condicional='rango_aportancia', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="school", condicional=Departamento, columnas=columnas, list_columnas=list_columnas, colum_condicional='departamento', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="school", condicional=Calendario, columnas=columnas, list_columnas=list_columnas, colum_condicional='calendario', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="school", condicional=Encargado, columnas=columnas, list_columnas=list_columnas, colum_condicional='encargado_uniandes', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)

    if instruc_condicionales != "":
        query = f"SELECT {columnas} FROM Tk8s WHERE {instruc_condicionales}"
        tuple_condicionales = tuple(list_condicionales)
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute(query, tuple_condicionales)
            result_search = cursor.fetchall()
    else:
        result_search = []

    if result_search == [] and RangoAportancia == "1.0 - 2.0":
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute(f"SELECT {columnas} FROM Tk8s")
            result_search = cursor.fetchall()

    if RangoAportancia == "1.0 - 2.0":
        i=0
        while i<len(result_search):
            row = result_search[i]
            if row[6]==None:
                result_search.pop(i)
            else:
                i += 1

    fecha_atendidos_antes = convertir_fecha(fecha_atendidos_antes)
    fecha_atendidos_despues = convertir_fecha(fecha_atendidos_despues)
    fecha_actualizados_antes = convertir_fecha(fecha_actualizados_antes)
    fecha_actualizados_despues = convertir_fecha(fecha_actualizados_despues)

    if result_search == [] and (fecha_actualizados_antes!=None or fecha_actualizados_despues!=None or fecha_atendidos_antes!=None or fecha_atendidos_despues!=None):
        with DatabaseConnection() as db:
            cursor = db.cursor()
            cursor.execute(f"SELECT {columnas} FROM Tk8s")
            result_search = cursor.fetchall()

    if fecha_actualizados_antes!=None or fecha_actualizados_despues!=None or fecha_atendidos_antes!=None or fecha_atendidos_despues!=None:
        i = 0
        while i<len(result_search):
            avanzar = 1    
            row = result_search[i]
            fecha_atendidos = row[5]
            fecha_actualizados = row[4]
            fecha_atendidos = convertir_fecha(fecha_atendidos)
            fecha_actualizados = convertir_fecha(fecha_actualizados)

            if fecha_atendidos != None:
                if fecha_atendidos_antes != None :
                    if fecha_atendidos>fecha_atendidos_antes:
                        result_search.pop(i)
                        avanzar = 0
                if fecha_atendidos_despues != None:
                    if fecha_atendidos<fecha_atendidos_despues:
                        result_search.pop(i)
                        avanzar = 0
            elif fecha_atendidos==None:
                result_search.pop(i)
                avanzar = 0
            if fecha_actualizados != None:
                try:
                    if fecha_actualizados_antes != None :
                        if fecha_actualizados>fecha_actualizados_antes:
                            result_search.pop(i)
                            avanzar = 0
                    if fecha_actualizados_despues != None:
                        if fecha_actualizados<fecha_actualizados_despues:
                            result_search.pop(i)
                            avanzar = 0
                except:
                    None
            elif fecha_actualizados==None:
                try:
                    result_search.pop(i)
                    avanzar = 0
                except:
                    None
            i = i + (avanzar)        

    num_coincidences = len(result_search)
    list_profesionales = obtener_profesionales()
    return render_template('L3_Filter_Schools_Page.html', response=1, list_columnas=list_columnas, result_search = result_search, enumerate=enumerate, list_profesionales=list_profesionales, num_coincidences = num_coincidences)

@app.route('/Busqueda_filtrada/Profesores', methods=['POST','GET'])
def busqueda_filtrada_profesores():

    nombre_profesor = request.form["nombre_profesor"]
    enfasis_profesor = request.form["enfasis_profesor"]
    area_profesor = request.form["area_profesor"]
    
    if nombre_profesor==False:
        nombre_profesor = "%"
    else: 
        nombre_profesor = "%" + nombre_profesor + "%"
    
    if enfasis_profesor==False or enfasis_profesor=="":
        enfasis_profesor = "%"
    else:
        enfasis_profesor = "%" + enfasis_profesor + "%"

    instruc_condicionales = ""
    list_columnas = ["k8s", "Nombre profesor", "Área", "Énfasis", "Teléfono", "Correo"]
    list_condicionales = []

    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="teachers", condicional=nombre_profesor, columnas='*', list_columnas=list_columnas, colum_condicional='nombre_profesor', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="teachers", condicional=enfasis_profesor, columnas='*', list_columnas=list_columnas, colum_condicional='enfasis_profesor', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="teachers", condicional=area_profesor, columnas='*', list_columnas=list_columnas, colum_condicional='area_profesor', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)

    query = f"SELECT * FROM TProfesores WHERE {instruc_condicionales}"
    tuple_condicionales = tuple(list_condicionales)

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute(query, tuple_condicionales)
        result_search = cursor.fetchall()

    num_coincidences = len(result_search)

    return render_template('L3_Filter_Teachers_Page.html', response=1, list_columnas=list_columnas, result_search = result_search, enumerate=enumerate, query=query, num_coincidences=num_coincidences)


@app.route('/Busqueda_filtrada/Eventos_uniandes', methods=["POST","GET"])
def busqueda_filtrada_eventos_uniandes():
    evento_uniandes = request.form["evento_uniandes"]
    encargado_uniandes = request.form["encargado_uniandes"]

    if evento_uniandes=="NULL" and encargado_uniandes=="NULL":
        return render_template('L4_EW_Filter.html', palabra_clave="Eventos Uniandes", response=0)

    instruc_condicionales = ""
    list_columnas = ["Nombre k8s", "Num asistentes", "Tipo evento uniandes", "Profesional a cargo", "Fecha", "Descripción"]
    list_condicionales = []

    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="uniandes_events", condicional=evento_uniandes, columnas="*", list_columnas=list_columnas, colum_condicional='tipo_feria_uniandes', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)
    instruc_condicionales, list_condicionales, list_columnas, columnas = concatenar_query(selected_filter="uniandes_events", condicional=encargado_uniandes, columnas="*", list_columnas=list_columnas, colum_condicional='profesional_feria_uniandes', instruc_condicionales=instruc_condicionales, list_condicionales=list_condicionales)

    query = f"SELECT * FROM TUniandes_Events WHERE {instruc_condicionales}"
    tuple_condicionales = tuple(list_condicionales)

    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute(query, tuple_condicionales)
        result_search = cursor.fetchall()
    list_profesionales = obtener_profesionales()
    
    num_coincidences = len(result_search)

    return render_template('L3_Filter_Uniandes_Events_Page.html', response=1, list_columnas=list_columnas, result_search=result_search, enumerate=enumerate, query=query, list_profesionales=list_profesionales, num_coincidences=num_coincidences)

@app.route('/Busqueda_filtrada/Fechas de actualización', methods=['POST','GET'])
def busqueda_filtrada_fecha_actualizacion():

    start_date = request.form['start_date']
    final_date = request.form['final_date']

    with DatabaseConnection() as db:
        cursor = db.cursor()
        if start_date!="" and final_date!="":
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            final_date = datetime.strptime(final_date, '%Y-%m-%d').date()
            cursor.execute('SELECT nombre_k8s, fecha_actualizacion, correo_k8s, tel_k8s, departamento, municipio FROM Tk8s WHERE fecha_actualizacion > %s AND fecha_actualizacion < %s', (start_date, final_date, ))
        
        if start_date!="" and final_date=="":
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            cursor.execute('SELECT nombre_k8s, fecha_actualizacion, correo_k8s, tel_k8s, departamento, municipio FROM Tk8s WHERE fecha_actualizacion > %s', (start_date, ))

        if start_date=="" and final_date!="":
            final_date = datetime.strptime(final_date, '%Y-%m-%d').date()
            cursor.execute('SELECT nombre_k8s, fecha_actualizacion, correo_k8s, tel_k8s, departamento, municipio FROM Tk8s WHERE fecha_actualizacion < %s', (final_date, ))

        if start_date=="" and  final_date=="":
            return render_template('L4_EW_Filter.html', palabra_clave="Fechas de actualización", response=0)
        data = cursor.fetchall()

    num_coincidences = len(data)
    return render_template('L3_Filter_Update_Dates.html', response=1, result_search=data, enumerate=enumerate,list_columnas=['Nombre del k8s', 'Última fecha de actualización', 'Correo', 'Teléfono', 'Departamento', 'Municipio'], num_coincidences=num_coincidences)

@app.route('/descargar_database', methods=["POST"])
def descargar_tabla():

    action = request.form["action"]
    with DatabaseConnection() as db:
        cursor = db.cursor()
        if action=="k8ss" or action=="k8ss - Correos":
            cursor.execute("SELECT * FROM Tk8s")
            colum_name = ['Correo','Nombre','Profesional a cargo','Fecha de actualización','Última fecha de atención','Último tipo de atención','Teléfono del k8s','Departamento','Municipio','Dirección del k8s','Rango de aportancia','Código Icfes','Código DANE','Nombre de contacto','Teléfono del contacto','Cargo del contacto','Nombre del orientador','Correo del orientador','Teléfono del orientador','Extensión del orientador','Nombre de rector','Web','Calendario','Modelo ONU','Nombres de eventos','Áreas de eventos','Descripción de eventos','Nombre de ferias','Fechas','Estado','Notas adicionales']
        elif action=="Profesores":
            cursor.execute("SELECT * FROM TProfesores")
            colum_name = ['k8s profesor','Nombre profesor','Área de profesor','Énfasis de profesor','Teléfono de profesor','Correo de profesor']
        elif action=="Eventos":
            cursor.execute("SELECT * FROM TUniandes_Events")
            colum_name = ['Nombre k8s','Número de atendidos','Tipo de feria','Profesional que atendió','Fecha de feria','Descripción']
        data = cursor.fetchall()

    fecha_primitiva = str(datetime.now())
    fecha_primitiva = fecha_primitiva.replace(':',"-")
    fecha_primitiva = fecha_primitiva.replace('.',"-")
    name_file = "Tabla de " + str(action) + " - Fecha("+ fecha_primitiva + ")"
    wb = Workbook()
    ws = wb.active
    ws.append(colum_name)
    for row in data:
        row = list(row)
        if action == "k8ss - Correos":
            lista_correos = funtion_str_to_list(row[0])
            for correo in lista_correos:                
                correo = correo.replace("'","")
                row[0] = correo
                ws.append(row)
        else:
            ws.append(row)

    nombre = name_file + ".xlsx"
    downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    file_path = os.path.join(downloads_folder, nombre)
    wb.save(file_path)
    return render_template("L4_EW_DownloadExcel.html", name_file=nombre)


    return (data, palabra_clave)
#############################################################################################################
###################################        SUPPORT_FUNCTIONS       ##########################################
#############################################################################################################

def review_created_password(password:str)->bool:
    letters = "asdfghjklñqwertyuiopzxcvbnmQWERTYUIOPASDFGHJKLÑZXCVBNM"
    numbers = "1234567890"
    special = "°!#$%&/()=%s¡|¬¨*[];:_<>+,.-~+"

    validation_l = False
    validation_n = False
    validation_s = False

    for caracter in password:
        if caracter in letters:
            validation_l = True
        if caracter in numbers:
            validation_n = True
        if caracter in special:
            validation_s = True
        if validation_l and validation_n and validation_s:
            return True
    return False

def get_school_data(nombre_k8s:str):
    
    with DatabaseConnection() as db:
        cursor = db.cursor()
        
        cursor.execute("SELECT correo_k8s, nombre_k8s, fecha_actualizacion, encargado_uniandes, tel_k8s, departamento, municipio, dir_k8s, rango_aportancia, cod_icfes, cod_dane, ultima_fecha_atencion, ultimo_tipo_atencion, status, nota_adicional  FROM Tk8s WHERE nombre_k8s = %s", (nombre_k8s,))
        dataTk8s = cursor.fetchone()

        cursor.execute("SELECT nombre_contacto, telefono_contacto, cargo_contacto, nombre_orientador, correo_orientador, tel_orientador, extension_orientador FROM Tk8s WHERE nombre_k8s = %s", (nombre_k8s,))
        dataTContactos = cursor.fetchone()
        
        cursor.execute("SELECT nombre_rector, web, calendario FROM Tk8s WHERE nombre_k8s = %s", (nombre_k8s,))
        dataTPerfil = cursor.fetchone()
        
        fecha_actualizacion = dataTk8s[2]
        fecha_atencion = dataTk8s[11]
        calendario = dataTPerfil[2]
        fecha_primitiva = datetime.now()
        fecha_hoy = fecha_primitiva.date()
        semestre = definir_semestre()

        with DatabaseConnection() as db:
            cursor = db.cursor()
            if calendario == "B":
                if fecha_atencion!=None:
                    if fecha_hoy.year==fecha_atencion.year and semestre=="segundo_semestre":
                        if fecha_atencion.month==7 or fecha_atencion.month==8 or fecha_atencion.month==9 or fecha_atencion.month==10 or fecha_atencion.month==11 or fecha_atencion.month==12:
                            cursor.execute("UPDATE  Tk8s SET estado_atencion = %s WHERE nombre_k8s=%s", ("ATENDIDO", nombre_k8s))
                    elif fecha_hoy.year==fecha_atencion.year and semestre=="primer_semestre":
                            cursor.execute("UPDATE  Tk8s SET estado_atencion = %s WHERE nombre_k8s=%s", ("ATENDIDO", nombre_k8s))
                    elif int(fecha_hoy.year)==int(fecha_atencion.year)+1 and semestre=="primer_semestre":
                        if fecha_atencion.month==7 or fecha_atencion.month==8 or fecha_atencion.month==9 or fecha_atencion.month==10 or fecha_atencion.month==11 or fecha_atencion.month==12:
                            cursor.execute("UPDATE  Tk8s SET estado_atencion = %s WHERE nombre_k8s=%s", ("ATENDIDO", nombre_k8s))
                    else:
                        cursor.execute("UPDATE  Tk8s SET estado_atencion = %s WHERE nombre_k8s=%s", ("NO ATENDIDO", nombre_k8s))

                if fecha_actualizacion!=None:
                    if fecha_hoy.year==fecha_actualizacion.year and semestre=="segundo_semestre":
                        if fecha_actualizacion.month==7 or fecha_actualizacion.month==8 or fecha_actualizacion.month==9 or fecha_actualizacion.month==10 or fecha_actualizacion.month==11 or fecha_actualizacion.month==12:
                            cursor.execute("UPDATE  Tk8s SET estado_actualizacion = %s WHERE nombre_k8s=%s", ("ACTUALIZADO", nombre_k8s))
                    elif fecha_hoy.year==fecha_actualizacion.year and semestre=="primer_semestre":
                            cursor.execute("UPDATE  Tk8s SET estado_actualizacion = %s WHERE nombre_k8s=%s", ("ACTUALIZADO", nombre_k8s))
                    elif int(fecha_hoy.year)==int(fecha_actualizacion.year)+1 and semestre=="primer_semestre":
                        if fecha_actualizacion.month==7 or fecha_actualizacion.month==8 or fecha_actualizacion.month==9 or fecha_actualizacion.month==10 or fecha_actualizacion.month==11 or fecha_actualizacion.month==12:
                            cursor.execute("UPDATE  Tk8s SET estado_actualizacion = %s WHERE nombre_k8s=%s", ("ACTUALIZADO", nombre_k8s))
                    else:
                        cursor.execute("UPDATE  Tk8s SET estado_actualizacion = %s WHERE nombre_k8s=%s", ("NO ACTUALIZADO", nombre_k8s))
                    
            if calendario=="A":
                if fecha_atencion!=None:
                    if fecha_hoy.year==fecha_atencion.year:
                        cursor.execute("UPDATE  Tk8s SET estado_atencion = %s WHERE nombre_k8s=%s", ("ATENDIDO", nombre_k8s))                    
                    else:
                        cursor.execute("UPDATE  Tk8s SET estado_atencion = %s WHERE nombre_k8s=%s", ("NO ATENDIDO", nombre_k8s))

                if fecha_actualizacion!=None:
                    if fecha_hoy.year==fecha_actualizacion.year:
                        cursor.execute("UPDATE  Tk8s SET estado_actualizacion = %s WHERE nombre_k8s=%s", ("ACTUALIZADO", nombre_k8s))
                    else:
                            cursor.execute("UPDATE  Tk8s SET estado_actualizacion = %s WHERE nombre_k8s=%s", ("NO ACTUALIZADO", nombre_k8s))
            db.commit()



    return (dataTk8s, dataTContactos, dataTPerfil)

def obtener_profesionales()->list:
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_usuario FROM TUser")
        list_profesionales = cursor.fetchall()
    
    return list_profesionales

def verificar_no_existencia(dato:str, columna:str, tabla:str):
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {tabla} WHERE {columna}=%s", (dato,))
        response = cursor.fetchall()
    if not response:
        return True
    else:
        return False

def convertir_fecha(fecha):
    if not isinstance(fecha, date) and fecha is not None:
        try:
            fecha = fecha.split('-')
            año = int(fecha[0])
            mes = int(fecha[1])
            dia = int(fecha[2])
            fecha = date(año, mes, dia)
            return fecha
        except:
            fecha = None
            return fecha
    else:
        return fecha
        
def definir_semestre():
    fecha_primitiva = datetime.now()
    fecha = fecha_primitiva.date()
    if fecha.month==1 or fecha.month==2 or fecha.month==3 or fecha.month == 4 or fecha.month == 5 or fecha.month == 6:
        return ('primer_semestre')
    elif fecha.month == 7 or fecha.month == 8 or fecha.month == 9 or fecha.month == 10 or fecha.month == 11 or fecha.month == 12:
        return ('segundo_semestre')

def get_official_events():
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("SELECT nombre_evento FROM TOFFICIAL_EVENTS")
        raw_list_official_events = cursor.fetchall()

    list_official_events = []   
    for evento in raw_list_official_events:
        evento = evento[0]
        list_official_events.append(evento)
    return (list_official_events)

def actualizar_fecha(nombre_k8s: str):
    fecha_primitiva = datetime.now()

    fecha = fecha_primitiva.date()
    
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE Tk8s SET fecha_actualizacion=%s WHERE nombre_k8s=%s",(fecha, nombre_k8s, ))
        db.commit()
    
    return 

def actualizar_correo(correo):
    if "'" not in correo:
        correo = "['" + correo +"']"
    return correo

def actualizar_ultima_atencion():
    nombre_k8s = session['main_school_key']
    with DatabaseConnection() as db:
        cursor = db.cursor()
        cursor.execute('SELECT fecha_feria_uniandes, tipo_feria_uniandes FROM TUniandes_Events WHERE nombre_k8s = %s', (nombre_k8s ,))    
        fechas_feria = cursor.fetchall()
    
    ultima_fecha_atencion = date(2001, 12, 11)
    ultimo_evento = ""
    
    for row in fechas_feria:
        fecha = row[0].split("-")
        evento = row[1]
        for dato in fecha:
            year = int(fecha[0])
            month = int(fecha[1])
            day = int(fecha[2])
        fecha = date(year, month, day)
        
        if ultima_fecha_atencion<fecha:
            ultima_fecha_atencion = fecha
            ultimo_evento = evento
            with DatabaseConnection() as db:
                cursor = db.cursor()
                cursor.execute('UPDATE Tk8s SET ultima_fecha_atencion=%s, ultimo_tipo_atencion=%s WHERE nombre_k8s=%s',(ultima_fecha_atencion,ultimo_evento,nombre_k8s))
                db.commit()


    return

def concatenar_query(selected_filter: str, condicional: str, columnas: str, list_columnas: list, colum_condicional: str, instruc_condicionales: str, list_condicionales: list):
    # condicional es el valor a buscar en el SQL que se recibe a través del request.form
    # columnas es un str que maneja las columnas extraidas del SQL a partir de los filtros seleccionados
    # list_columnas es una lista que contiene las columnas a aparecer para mostrarlas como títulos en la tabla
    # colum_condicional es el nombre de la columna que va a evaluarse e incluirse dentro del query
    # instruc_condicionales es el str que compone la instrucción que va a pasarse al query
    # list_condicionales es la lista a transformar en tupla con los valores a replicar en la condicional
    
    if condicional != "NULL" :
        if selected_filter=="school":
            if colum_condicional != "encargado_uniandes" or colum_condicional != "status":    
           
    app.run(debug=True, host='0.0.0.0')
