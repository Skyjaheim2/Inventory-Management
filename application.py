from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from datetime import date
from tempfile import mkdtemp
import hashlib
import mysql.connector
current_date = date.today()
now = current_date.strftime("%B %d, %Y")

mydb = mysql.connector.connect(host="localhost", user="root", passwd="jaheimSQL18", database="inventory")

db = mydb.cursor()


app = Flask(__name__)
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ENABLE SESSION
Session(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        user_name = request.form.get("user_name")
        user_password = request.form.get("user_password")

        # CHECKING IF USER IS REGISTERED
        sql = "SELECT * FROM user_login WHERE name = %s"
        val = (user_name, )
        db.execute(sql, val)
        result = db.fetchall()
        if len(result) == 0:
            return render_template("error.html", message = "You Are Not Registered")

        # CREATE SESSION
        session["user_id"] = result[0][0]
        # CHECKING IF PASSWORDS IS CORRECT
        sql = "SELECT password FROM user_login WHERE name = %s"
        val = (user_name, )
        db.execute(sql, val)
        hashed_password = db.fetchall()

        if not check_password_hash(user_password, hashed_password[0][0]):
            return render_template("login.html", message="Incorrect Credentials")
            # return render_template("error.html", message="Incorrect Credentials")

        return redirect("/home")



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        user_name = request.form.get("user_name")
        user_password = request.form.get("confirm_password")

        # HASH USER_PASSWORD
        user_password = hash_password(user_password)

        # CHECK IF USER IS ALREADY REGISTERED
        sql = "SELECT * FROM user_login WHERE name = %s"
        val = (user_name, )
        db.execute(sql, val)
        result = db.fetchall()
        if len(result) != 0:
            return render_template("error.html", message="You Are Already Registered")

        # REGISTER USER
        sql = "INSERT INTO user_login(name, password) VALUES (%s, %s)"
        val = (user_name, user_password)
        db.execute(sql, val)
        mydb.commit()

        session.clear()
        # ADD USER_ID TO SESSION
        sql = "SELECT id FROM user_login WHERE name = %s"
        val = (user_name, )
        db.execute(sql, val)
        result = db.fetchall()
        session["user_id"] = result[0][0]

        return redirect("/home")


# MAIN PAGE
@app.route("/home")
def index():
    # GET THE USER INVENTORY FROM DATABASE
    sql = "SELECT name, amount FROM inventory WHERE user_id = %s"
    val = (session["user_id"], )
    db.execute(sql, val)
    result = db.fetchall()

    # CALCULATING TOTAL ITEMS IN INVENTORY
    total = 0
    for i in range(len(result)):
        total += result[i][1]
    
    return render_template("index.html", items=result, num_items=len(result), total=total)


# SORT ITEMS
@app.route("/sort", methods=["GET"])
def sort_items():
    sql = "SELECT name, amount FROM inventory WHERE user_id = %s ORDER BY name"
    val = (session["user_id"], )
    db.execute(sql, val)
    result = db.fetchall()

     # CALCULATING TOTAL ITEMS IN INVENTORY
    total = 0
    for i in range(len(result)):
        total += result[i][1]

    return render_template("index.html", items=result, num_items=len(result), total=total, alert="sort")



# ADD ITEM
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("add.html")
    else:
        user_item = request.form.get("user_item")
        user_amount = int(request.form.get("user_amount"))

        
        # CHECK IF THE ITEM HAS ALREADY BEEN ADDED
        sql = "SELECT * FROM inventory WHERE user_id = %s and name = %s"
        val = (session["user_id"], user_item)
        db.execute(sql, val)
        result = db.fetchall()
        if len(result) != 0:
            new_amount = result[0][2] +int(user_amount)
            sql = "UPDATE inventory SET amount = %s WHERE user_id = %s and name = %s"
            val = (new_amount, session["user_id"], user_item)
            db.execute(sql, val)
            mydb.commit()

            sql = "SELECT name, amount FROM inventory WHERE user_id = %s"
            val = (session["user_id"], )
            db.execute(sql, val)
            result = db.fetchall()

             # CALCULATING TOTAL ITEMS IN INVENTORY
            total = 0
            for i in range(len(result)):
                total += result[i][1]

            return render_template("index.html", items=result, num_items=len(result), total=total, alert="add")
            # return redirect("/home")

        sql = "INSERT INTO inventory (user_id, name, amount) VALUES (%s, %s, %s)"
        val = (session["user_id"], user_item, user_amount)
        db.execute(sql, val)
        mydb.commit()

        sql = "SELECT name, amount FROM inventory WHERE user_id = %s"
        val = (session["user_id"], )
        db.execute(sql, val)
        result = db.fetchall()

        # CALCULATING TOTAL ITEMS IN INVENTORY
        total = 0
        for i in range(len(result)):
            total += result[i][1]

        return render_template("index.html", items=result, num_items=len(result), total=total, alert="add")

        # return redirect("/home")


# ITEMS BELOW INVENTORY
@app.route("/below", methods=["GET", "POST"])
def below_inventory():
    if request.method == "GET":
        return render_template("below_inv.html")
    else:
        inv_limit = request.form.get("user_amount")

        sql = "SELECT name, amount FROM inventory WHERE user_id = %s AND amount < %s"
        val = (session["user_id"], int(inv_limit))
        db.execute(sql, val)
        result = db.fetchall()

        # CALCULATING TOTAL ITEMS IN INVENTORY
        total = 0
        for i in range(len(result)):
            total += result[i][1]
    
        return render_template("index.html", items=result, num_items=len(result), total=total, alert="below")



# ITEMS ABOVE INVENTORY
@app.route("/above", methods=["GET", "POST"])
def above_inventory():
    if request.method == "GET":
        return render_template("above_inv.html")
    else:
        inv_limit = request.form.get("user_amount")

        sql = "SELECT name, amount FROM inventory WHERE user_id = %s AND amount > %s"
        val = (session["user_id"], int(inv_limit))
        db.execute(sql, val)
        result = db.fetchall()

        # CALCULATING TOTAL ITEMS IN INVENTORY
        total = 0
        for i in range(len(result)):
            total += result[i][1]
    
        return render_template("index.html", items=result, num_items=len(result), total=total, alert="above")


# ITEMS AT A SPECIFIC LIMIT
@app.route("/specific", methods=["GET", "POST"])
def specific_inventory():
    if request.method == "GET":
        return render_template("specific_inv.html")
    else:
        inv_limit = request.form.get("user_amount")

        sql = "SELECT name, amount FROM inventory WHERE user_id = %s AND amount = %s"
        val = (session["user_id"], int(inv_limit))
        db.execute(sql, val)
        result = db.fetchall()

        # CALCULATING TOTAL ITEMS IN INVENTORY
        total = 0
        for i in range(len(result)):
            total += result[i][1]
    
        return render_template("index.html", items=result, num_items=len(result), total=total)


# ITEMS AT A SPECIFIC LIMIT
@app.route("/delete", methods=["GET", "POST"])
def delete_inventory():
    if request.method == "GET":
        return render_template("delete_inv.html")
    else:
        item_to_delete= request.form.get("user_item")

        sql = "DELETE FROM inventory WHERE user_id = %s AND name = %s"
        val = (session["user_id"], item_to_delete)
        db.execute(sql, val)
        mydb.commit()

        sql = "SELECT name, amount FROM inventory WHERE user_id = %s"
        val = (session["user_id"], )
        db.execute(sql, val)
        result = db.fetchall()

            # CALCULATING TOTAL ITEMS IN INVENTORY
        total = 0
        for i in range(len(result)):
            total += result[i][1]

        return render_template("index.html", items=result, num_items=len(result), total=total, alert="delete")
    
        # return redirect("/home")


# FORGOT USERNAME
@app.route("/change_username", methods=["GET","POST"])
def change_username():
    if request.method == "GET":
        return render_template("change_name.html")
    else:
        pre_name  = request.form.get("pre_user_name")
        new_name = request.form.get("user_name")
        user_pwd   = request.form.get("user_password")

        # GET THEIR ID
        sql = "SELECT id FROM user_login WHERE name = %s"
        val = (pre_name, )
        db.execute(sql, val)
        user_id = db.fetchall()

        # WRONG NAME ENTERED
        if len(user_id) == 0:
            return render_template("change_name.html", message="Your previous username is incorrect")

        # CHECKING IF CORRECT PASSWORD WAS ENTERED
        sql = "SELECT password FROM user_login WHERE id = %s"
        val = (user_id[0][0], )
        db.execute(sql, val)
        hashed_pwd = db.fetchall()[0][0]

        if not check_password_hash(user_pwd, hashed_pwd):
            return render_template("change_name.html", message="Incorrect Password")

        # CHANGE THEIR USERNAME
        sql = "UPDATE user_login SET name = %s WHERE id = %s"
        val = (new_name, user_id[0][0])
        db.execute(sql, val)
        mydb.commit()

        return render_template("login.html", alert="changed_name")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        return render_template("change_pwd.html")
    else:
        user_name = request.form.get("user_name")
        pre_password = request.form.get("pre_password")
        new_password = request.form.get("new_password")

        sql = "SELECT password FROM user_login WHERE name = %s"
        val = (user_name, )
        db.execute(sql, val)
        hashed_password = db.fetchall()

        # CHECKING IF WRONG NAME WAS ENTERED
        if len(hashed_password) == 0:
            return render_template("change_pwd.html", message="Incorrect Username")

        hashed_password = hashed_password[0][0]
        # CHECKING IF WRONG PREVIOUS PASSWORD WAS ENTERED
        if not hash_password(pre_password) == hashed_password:
            return render_template("change_pwd.html", message="Incorrect Previous Password")

        
        # UPDATE THEIR PASSWORD
        changed_password = hash_password(new_password)
        sql = "UPDATE user_login SET password = %s WHERE name =%s AND password = %s"
        val = (changed_password, user_name, hashed_password)
        db.execute(sql, val)
        mydb.commit()

        return render_template("login.html", alert="changed_pwd")



        

        


        



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password_hash(password, hash):
    if hash_password(password) == hash:
        return True
    return False


if __name__ == '__main__':
    app.run(debug=True)