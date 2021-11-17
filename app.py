from flask import Flask,render_template, request, session, redirect, url_for
import mysql.connector
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import gunicorn

app = Flask(__name__)
app.secret_key = "Chloe" # Needed for the session

my_db = mysql.connector.connect(
    host= "sql5.freemysqlhosting.net",
    user="sql5451738",
    password="EXQXF3Nav4",
    database ="sql5451738"
)

mycursor = my_db.cursor()
mycursor.execute("CREATE TABLE IF NOT EXISTS equipments (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), quantity VARCHAR(255), location VARCHAR(255), category VARCHAR(255),propertyType VARCHAR(255))")
mycursor.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255), password VARCHAR(255), role VARCHAR(255), roomName VARCHAR(255))")
mycursor.execute("CREATE TABLE IF NOT EXISTS requests (id INT AUTO_INCREMENT PRIMARY KEY, equipmentID INT, teacherUsername VARCHAR(255), status VARCHAR(255), quantity VARCHAR(255), roomName VARCHAR(255))")
mycursor.execute("CREATE TABLE IF NOT EXISTS analysis (id INT AUTO_INCREMENT PRIMARY KEY, teacherUsername VARCHAR(255), equipmentName VARCHAR(255), quantity VARCHAR(255), category VARCHAR(255),propertyType VARCHAR(255))")
#mycursor.execute("ALTER TABLE equipments RENAME COLUMN quantity TO availableQuantity")
#mycursor.execute("ALTER TABLE equipments ADD (totalEquipments VARCHAR(255))")

@app.route("/")
def home():
    if "username" in session: #For quick login for returning user on the same device

        if session['role'] == "teacher":
            return render_template("homeTeacher.html", user = session['username'])
        else:
            return render_template("home.html", user = session['username'])
    else:
        return render_template("login.html")

@app.route("/about")
def about():
    return render_template("about.html") 

@app.route("/addEquipment", methods=['POST', 'GET'])
def addEquipment():
    if request.method == "POST":
        name = request.form.get("equipmentName")
        quantity = request.form.get("quantity")
        totalQuantity = request.form.get("totalQuantity")
        location = request.form.get("location")
        category = request.form.get("category")
        propertyType = request.form.get("propertyType")

        sql = "INSERT INTO equipments (name,availableQuantity,location,category,propertyType,totalQuantity) VALUES (%s,%s,%s,%s,%s,%s)"
        values =[name,quantity,location,category,propertyType,totalQuantity]
        
        # Saving in the database
        mycursor.execute(sql,values) # Run database command (a sql command)
        my_db.commit() # save. commit info.

        return redirect("/")
    else:
        return render_template("addEquipment.html") 

@app.route("/search", methods=['POST', 'GET'])
def search():
    if request.method == "POST":
        name = request.form.get("searchName")

        sql = "SELECT id,name,availableQuantity,location,category,propertyType,totalQuantity FROM equipments WHERE name=%s"
        value = [name]

        mycursor.execute(sql, value)

        result = mycursor.fetchall()
        
        if len(result) > 0:
            mylist=result
        else:
            mylist=""

        if session['role'] == "teacher":
            return render_template("allEquipments.html", list=mylist)
        else:
            return render_template("allInventory.html", list=mylist)

@app.route("/searchrequest", methods=['POST', 'GET'])
def searchrequest():
    if request.method == "POST":
        name = request.form.get("searchName")

        sql = "SELECT id,name,availableQuantity,location,category,propertyType,totalQuantity FROM equipments WHERE name=%s"
        value = [name]

        mycursor.execute(sql, value)

        result = mycursor.fetchall()
        
        id_list = []

        for item in result:
            id_list.append(item[0])
        
        mylist = []
        
        if len(result) > 0:
            print("here 1")
            sql = "SELECT id,equipmentID,status,quantity FROM requests WHERE equipmentID=%s"

            requestResults = []

            for i in id_list:
                values = [i]
                mycursor.execute(sql,values)
                requestResults.append(mycursor.fetchone())

        for element in requestResults:
            for equipment in result:
                if element[1] == equipment[0]:
                    mylist.append([element[0],equipment, element[2], element[3]])

        if session['role'] == "teacher":
            return render_template("myEquipments.html", list=mylist)
        else:
            return render_template("requests.html", list=mylist)

@app.route("/editEquipment/<int:id>", methods=['POST', 'GET'])
def editEquipment(id):
    if request.method == "POST":
        name = request.form.get("equipmentName")
        quantity = request.form.get("quantity")
        originalTotalQuantity = request.form.get("originalTotalQuantity")
        newTotalQuantity = request.form.get("totalQuantity")
        location = request.form.get("location")
        category = request.form.get("category")
        propertyType = request.form.get("propertyType")

        originalTotalQuantity = float(originalTotalQuantity)
        newTotalQuantity = float(newTotalQuantity) 
        quantity = float(quantity)

        if newTotalQuantity >= (originalTotalQuantity-quantity):
            difference = newTotalQuantity - originalTotalQuantity
            quantity = quantity + difference
        else:
            return render_template("error.html", message="Total Quantity cannot be less than currently-in-use quantity.")

        sql = "UPDATE equipments SET name=%s,availableQuantity=%s,location=%s,category=%s,propertyType=%s,totalQuantity=%s WHERE id=%s"
        values =[name,quantity,location,category,propertyType,newTotalQuantity,id]
        
        # Saving in the database
        mycursor.execute(sql,values) # Run database command (a sql command)
        my_db.commit() # save. commit info.

        return redirect("/")
    else:
        sql = "SELECT id,name,availableQuantity,location,category,propertyType,totalQuantity FROM equipments WHERE id=%s"
        value = [id]
        mycursor.execute(sql, value)
        result = mycursor.fetchone()
        return render_template("edit.html", item=result) 

@app.route("/deleteEquipment/<int:id>", methods=['POST', 'GET'])
def deleteEquipment(id):
    if request.method == "POST":
        sql = "DELETE FROM equipments WHERE id=%s"
        values =[id]
        
        mycursor.execute(sql,values) # Run database command (a sql command)
        my_db.commit() # save. commit info.

        return redirect(url_for("allInventory"))
    else:
        sql = "SELECT id,name FROM equipments WHERE id=%s"
        value = [id]
        mycursor.execute(sql, value)
        result = mycursor.fetchone()
        print(result)
        return render_template("delete.html", item=result) 

@app.route("/requestEquipment/<int:id>", methods=['POST', 'GET'])
def requestEquipment(id):
    if request.method == "POST":
        teacherUsername = session['username']

        requestedQuantity = request.form.get("requestedQuantity")
        availableQuantity = request.form.get("availableQuantity")
        equipmentName = request.form.get("equipmentName")
        category = request.form.get("category")
        propertyType = request.form.get("propertyType")

        if float(requestedQuantity) < float(availableQuantity):
            
            # Create a request record
            status="Request Pending"
            roomName = session['roomName']

            sql = "INSERT INTO requests (equipmentID,teacherUsername,status,quantity,roomName) VALUES (%s,%s,%s,%s,%s)"
            values =[id,teacherUsername,status,requestedQuantity,roomName]
            
            mycursor.execute(sql,values)
            my_db.commit()

            #Update the available quantity
            newQuantity = float(availableQuantity) - float(requestedQuantity)
            sql = "UPDATE equipments SET availableQuantity=%s WHERE id=%s"
            values =[newQuantity, id]
        
            mycursor.execute(sql,values) 
            my_db.commit()

            # Track data for analysis
            sql = "INSERT INTO analysis (teacherUsername,equipmentName,quantity,category,propertyType) VALUES (%s,%s,%s,%s,%s)"
            values =[teacherUsername,equipmentName,requestedQuantity,category,propertyType]
            
            mycursor.execute(sql,values)
            my_db.commit()

            return redirect("/")
        else:
            return render_template("error.html", message="Wrong Quantity")
    else:
        sql = "SELECT id,name,availableQuantity,category,propertyType FROM equipments WHERE id= %s"
        value = [id]
        mycursor.execute(sql, value)
        result = mycursor.fetchone()
        return render_template("checkrequest.html", item=result) 

@app.route("/allInventory")
def allInventory():

    sql = "SELECT id,name,availableQuantity,location,category,propertyType,totalQuantity FROM equipments"
    mycursor.execute(sql)

    result = mycursor.fetchall()

    if len(result) > 0:
        list=result
    else:
        list=""

    return render_template("allInventory.html", list=list)

@app.route("/requests")
def requests():

    sql = "SELECT id,equipmentID,teacherUsername,status,quantity,roomName FROM requests"
    mycursor.execute(sql)
    result = mycursor.fetchall()

    equipmentList = []

    list = ""

    if len(result) > 0:
        list=result

        for item in list:
            sql = "SELECT id,name,availableQuantity,location,category,propertyType FROM equipments WHERE id=%s"
            value = [item[1]]

            mycursor.execute(sql, value)
            equipmentResult = mycursor.fetchone()

            #item[0] = request ID
            #item[2] = teacherName
            #item[3] = status
            #item[4] = quantity
            #item[5] = room
            equipmentList.append([item[0],equipmentResult,item[2],item[3],item[4],item[5]])

        list = equipmentList
    
    return render_template("requests.html", list=list)

@app.route("/manageusers")
def manageusers():

    sql = "SELECT id,username,role,roomName FROM users"
    mycursor.execute(sql)
    result = mycursor.fetchall()

    if len(result) > 0:
        return render_template("manageusers.html", list=result)
    else:
        return render_template("signup.html")

@app.route("/analysis")
def analysis():
    return render_template("analysis.html",list="")

@app.route("/datasummary", methods=['POST', 'GET'])
def datasummary():

    if request.method == "POST":
        filter = request.form.get("datafilter")
        yAxisFilter = request.form.get("yAxisFilter")

        yAxisFilter = int(yAxisFilter)

        x = []
        y = []

        if filter == "category":
            sql = "SELECT category,avg(quantity),min(quantity),max(quantity),count(id) FROM analysis group by category"
        if filter == "teacherUsername":
            sql = "SELECT teacherUsername,avg(quantity),min(quantity),max(quantity),count(id) FROM analysis group by teacherUsername"
        if filter == "propertyType":
            sql = "SELECT propertyType,avg(quantity),min(quantity),max(quantity),count(id) FROM analysis group by propertyType"

        mycursor.execute(sql)
        result = mycursor.fetchall()

        for item in result:
            x.append(item[0])
            y.append(item[yAxisFilter])

        plt.bar(x,y)
        plt.xlabel(filter)
        plt.savefig("static/images/category.png")
        plt.close()
        
        url = "static/images/category.png"

        if len(result) > 0:
            return render_template("analysis.html", list=result, url=url )
        else:
            return render_template("error.html")
    else:
        return render_template("analysis.html", list="")

@app.route("/makeAdmin/<int:id>", methods=['POST', 'GET'])
def make_admin(id):
    if request.method == "POST":
        role = "admin"

        sql = "UPDATE users SET role=%s WHERE id=%s"
        values =[role,id]
        
        mycursor.execute(sql,values) 
        my_db.commit()

    return redirect('/manageusers')

@app.route("/makeTeacher/<int:id>", methods=['POST', 'GET'])
def make_teacher(id):
    if request.method == "POST":
        role = "teacher"

        sql = "UPDATE users SET role=%s WHERE id=%s"
        values =[role,id]
        
        mycursor.execute(sql,values) 
        my_db.commit()

    return redirect('/manageusers')

@app.route("/approveRequest/<int:id>", methods=['POST', 'GET'])
def approveRequest(id):
    if request.method == "POST":
        status = "Requested Approved"

        sql = "UPDATE requests SET status=%s WHERE id=%s"
        values =[status, id]
        
        mycursor.execute(sql,values) 
        my_db.commit()

    return render_template("home.html")

@app.route("/approveReturn/<int:id>", methods=['POST', 'GET'])
def approveReturn(id):
    if request.method == "POST":

        equipmentID = request.form.get("equipmentID")
        returnedQuantity = request.form.get("availableQuantity")
        propertyType = request.form.get("propertyType")

        if propertyType == "Solid":
            sql = "UPDATE equipments SET availableQuantity=availableQuantity+%s WHERE id=%s"
            values =[returnedQuantity,equipmentID]

            mycursor.execute(sql,values) 
            my_db.commit()

        sql = "DELETE FROM requests WHERE id=%s"
        values =[id]
         
        mycursor.execute(sql,values) 
        my_db.commit()

    return render_template("home.html")

@app.route("/allEquipments")
def allEquipments():

    sql = "SELECT id,name,availableQuantity,location,category,propertyType FROM equipments"
    mycursor.execute(sql)

    result = mycursor.fetchall()

    if len(result) > 0:
        list=result
    else:
        list=""

    return render_template("allEquipments.html", list=list)

@app.route("/myEquipments") 
def myEquipments():
    teacherUsername = session["username"]

    sql = "SELECT id,equipmentID,status,quantity FROM requests WHERE teacherUsername=%s"
    values = [teacherUsername]

    mycursor.execute(sql, values)

    result = mycursor.fetchall()

    equipmentList = []

    list = ""

    if len(result) > 0:
        list=result

        for item in list:
            sql = "SELECT id,name,availableQuantity,location,category,propertyType FROM equipments WHERE id=%s"
            value = [item[1]]

            mycursor.execute(sql, value)
            result = mycursor.fetchone()

            # In below, item[0] is request ID and item[2] is request status
            equipmentList.append([item[0],result, item[2], item[3]])

        list = equipmentList
    
    return render_template("myEquipments.html", list=list)

@app.route("/returnEquipment/<int:id>", methods=['POST', 'GET'])
def returnEquipment(id):
    if request.method == "POST":
        status = "Return Pending"
        sql = "UPDATE requests SET status=%s WHERE id=%s"
        values =[status, id]
        
        mycursor.execute(sql,values) 
        my_db.commit()

    return render_template("homeTeacher.html")

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirm-password")
        roomName = request.form.get("teacherRoom")

        if password == confirmPassword:
            # check if username has been taken
            # if all good, save info in the database and go to welcome page  
              
            role = "teacher" 
            session['username'] = username
            session['roomName'] = roomName

            sql = "INSERT INTO users (username,password,role,roomName) VALUES (%s,%s,%s,%s)"
            values =[username,password,role,roomName]
        
            mycursor.execute(sql,values) # Run database command (a sql command)
            my_db.commit() # save. commit info.

            return render_template("login.html")
        else:
            return render_template("signup.html")
    else:
        return render_template("signup.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        sql = "SELECT role,roomName FROM users WHERE username=%s AND password=%s"
        values = [username,password]

        mycursor.execute(sql,values)
        result = mycursor.fetchone()

        if len(result) > 0:
            session['username'] = username 
            session['role'] = result[0]
            session['roomName'] = result[1]

            if result[0] == "teacher":
                return render_template("homeTeacher.html", user = session['username'])
            else:
                return render_template("home.html", user = session['username'])
        else:
            return render_template("login.html")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    return render_template("login.html")

if __name__ == '__main__':
    app.run()