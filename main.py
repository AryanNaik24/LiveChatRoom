
#needed imports
from flask import Flask , render_template , request,session,redirect,url_for
from flask_socketio import join_room,leave_room,send,SocketIO
import random
from string import ascii_uppercase
from dotenv import load_dotenv
import os


#loads .env file
load_dotenv('.env')

#gets passwords and username from env fole and stores in variable
key: str = os.getenv('SECRETKEY')

#initialise flask application
app = Flask(__name__)
#configure app
app.config["SECRET_KEY"] = key
#integrating soocketio
socketio = SocketIO(app)


#rooms set as a dictionary
#stores info on the different rooms made
rooms = {}

# function that generates room code
def generateCode(Length):
    while True:
        
        #sets code to empty string
        code = ""
        
        #generates random 4 capital characters letters
        for _ in range(Length):
            code += random.choice(ascii_uppercase)
        #checks if code already exists from codes
        if code not in rooms:
            break
        
    return code

#setting up home route
@app.route("/",methods=["POST","GET"])
def home():
    
    #clears the session
    session.clear()
    
    #Listens to POST requests
    if request.method == "POST":
        #saves the post request to variable
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join",False)
        create = request.form.get("create",False)

        #checks if name is entered or not
        if not name:
            return render_template("home.html",error="Please enter name!",code=code,name=name)
        
        #checks if room code entered or not
        if join != False and not code:
            return render_template("home.html",error="Please enter Room code!",code=code,name=name)
        
        
        room = code
        #if room of that code dosent exist it creats one
        if create != False:
            room = generateCode(4)
            rooms[room] = {"members":0,"messages":[]}
        
        #gives error if code is not in codes
        elif code not in rooms:
            return render_template("home.html",error="Room does not exist",code=code,name=name)
        
        #temporary data stored on server
        session["room"] = room
        session["name"] = name
        
        return redirect(url_for("room"))
            
            
    #renders home template
    return render_template("home.html")
    
#route to room
@app.route("/room")
def room():
    
    # #prevents user from directly going to /room
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))
     
                       
    #opens room . html
    return render_template("room.html",code=room,messages=rooms[room]["messages"])

#sends message to clients connected
@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

#listens to connect
@socketio.on("connect")
def connect(auth):
    
    #gets room and name input
    room = session.get("room")
    name = session.get("name")  
    
    #checks if room or name exits
    if not room or not name:
        return 
    
    #check if room exits in rooms 
    if room not in rooms:
        leave_room(room)
        return
    
    #joins the room
    join_room(room)
    #sends message to the room that person has joined room
    send({"name":name,"message":"has entered the room"},to=room)
    #keep track of how many people joined
    rooms[room]["members"] += 1
    print(f"{name} joined the {room}")
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name") 
    
    #leaves the room
    leave_room(room)
    
    #delets room if noone remaining
    if room in rooms:
        rooms[room]["members"] -=1
        if rooms[room]["members"] <=0:
            del rooms[room]
    send({"name":name,"message":"has left the room"},to=room)
    print(f"{name} left the {room}")
    

#starts the server
if __name__ == "__main__":
    socketio.run(app,debug=True)
