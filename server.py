#imports
from socket import socket, AF_INET, SOCK_STREAM, gethostbyname, gethostname
from threading import Thread
from tkinter import DISABLED, E, NORMAL, W, Button, Entry, Frame, Label, Text, Tk, messagebox

#server setup
FORMAT = 'utf-8'

#colors and font
fore = '#FFFFFF'
back = '#0000FF'
FONT = ('Consolas',15)

global PORT
global ADDRESS
global server
global SERVER
global con_count
global password
all_clients = []

class PassError(OSError):
    pass

#function to get input from fields and start server
def submit():
    global PORT
    global ADDRESS
    global server
    global SERVER
    global con_count
    global password
    try:
        password = pass_entry.get() #get password
        if not password:    raise PassError #check if password is empty ('') and raise error if it is
        SERVER = gethostbyname(gethostname()) #get IP
        PORT = int(port_entry.get()) #get port from input, if port is not an integer, ValueError will be raised
        if PORT<0:  raise ValueError # ensure port is positive
        
        #binding server
        ADDRESS = (SERVER,PORT)        
        server = socket(AF_INET, SOCK_STREAM)
        server.bind(ADDRESS)
        con_count = 0 #initialize connection_count to 0 and close window
        window.destroy()

    except ValueError:
        messagebox.showerror("Error",'Invalid Port')
    except PassError:
        messagebox.showerror("Error",'Invalid Password')
    except OSError:
        messagebox.showerror("Error",'Port already in use')

#function to close window and terminate program
def endall():
    try:
        window.destroy()
        quit()
    except Exception as e:
        print(e)

#Make 1st window - to start server
window = Tk()
window.title("IntraText - Server")
window.config(bg=back)
window.protocol(name="WM_DELETE_WINDOW",func=endall)
window.bind('<Return>',lambda anony: submit())
window.geometry('450x90')
window.maxsize(450,90)
window.minsize(450,90)

top = Frame(window,bg=back)
top.pack()

#port text
text = Label(top,text='Enter Server Port   ',font=FONT,fg=fore,bg=back)
text.grid(row=0,column=0,sticky=W)
text.config(width=20)
#port entry field
port_entry = Entry(top,font=FONT,bg=back,fg=fore)
port_entry.focus_set()
port_entry.config(width=20)
port_entry.grid(row=0,column=1,sticky=E)

#password text
text2 = Label(top,text='Password', font=FONT,bg=back,fg=fore,)
text2.grid(row=1,column=0,sticky=W)
text.config(width=20)
#password entry field
pass_entry = Entry(top,font=FONT,bg=back,fg=fore)
pass_entry.config(width=20)
pass_entry.grid(row=1,column=1,sticky=E)

#'make' button to start server
make = Button(window,bg=back,fg=fore,command=submit,text='Make Server',width=40,font=FONT)
make.pack()

window.mainloop()



HEAD_BYTES = 16
DISCONNECT = 'dc'
# PROTOCOL

# Client to Server communication:
# Client types a message and sends it
# Let the string length of the message be 'L'
# Client sends a signal with set length - HEAD_BYTES
# This signal contains integer data - equal to 'L'
# The server now knows the length of the incoming string/text message so knows how many bytes need to be processed
# Client sends the string of the message
# Server processes appropriate amount of bytes
# 'dc' means termination of connection
# If server receives this string, the client is disconnected and connection_count updated


# Initializing connection between new Client and Server
# Connection request sent to server using same protocol as mentioned above
# Request packet has password as data
# If received password matches with stored password, connection is made
# '1' is sent back to client and client then sends the username else if password is incorrect, '0' is sent back
# For each client connection, a thread is made to handle the client so all clients can be dhandles simeultaneously


# Server to Client
# When server recives a message from the client, the message is to be displayed on all other clinets screen as well
# To process this event, the server sends the data of the message to all other clients
# Data needs to have actual message string content as well as username
# Formed data is '{username}&&&{msg}'
# This is sent to all other clients with same length protocol

def handle(con,add):

    pass_len = con.recv(HEAD_BYTES).decode(FORMAT) #receive incoming password length and decode it
    received_password = con.recv(int(pass_len)).decode(FORMAT) #receive actual password
    if received_password!=password:
        reply = '0'
    else:
        reply = '1'
    con.send(reply.encode(FORMAT))
    if reply=='0':# close connection if password was incorrect
        con.close()
        return

    #username receiving
    username_len = int(con.recv(HEAD_BYTES).decode(FORMAT)) #receive username_len
    username = con.recv(username_len).decode(FORMAT) #receive actual username

    global con_count
    con_count+=1
    count.config(text=str(con_count)) #increment connection_count and increment it
    
    msg = ('{} connected'.format(username)).encode(FORMAT) # Message "{username} connected" to be sent to all other clients
    len_msg = str(len(msg)).encode(FORMAT)
    len_msg += b' '*(HEAD_BYTES-len(len_msg)) #make len_msg
    for c in all_clients: #sent len_msg and msg
        c.send(len_msg)
        c.send(msg)
    all_clients.append(con) #add this specific connection to clients array

    try:
        # start while loop to constantly listen for incoming messages
        while True:
            msg_len = int(con.recv(HEAD_BYTES).decode(FORMAT)) #receive message length and message from client
            actual_msg = con.recv(msg_len).decode(FORMAT)
            if actual_msg==DISCONNECT: #exit while loop if client wishes to disconnect
                break

            # data to be sent to all other clients
            msg = (f'{username}&&&{actual_msg}').encode(FORMAT)
            len_msg = str(len(msg)).encode(FORMAT)
            len_msg += b' '*(HEAD_BYTES-len(len_msg))

            # send to all other clients
            for c in all_clients:
                if c==con:   continue
                c.send(len_msg)
                c.send(msg)
        
        # is user disconnects, send the disconnection message to all other clients
        for c in all_clients:
            if c==con:   continue
            msg = (f'{username} disconnected').encode(FORMAT)
            len_msg = str(len(msg)).encode(FORMAT)
            len_msg += b' '*(HEAD_BYTES-len(len_msg))
            c.send(len_msg)
            c.send(msg)
        
        # decrement con_count and close connection
        con_count-=1
        count.config(text=str(con_count))
        all_clients.remove(con)
        con.close()
    except ConnectionResetError: #if connection is closed unexpectedly, con_count is decremented
        con_count-=1
        count.config(text=str(con_count))

def start():
    global server
    server.listen() #start listening for connections
    while True:
        # server.accept() will only return values when server receives a connection request
        # these values (args) are passed to the 'handle' function
        # A thread is started which runs this function
        client_thread = Thread(target=handle,args=server.accept())
        client_thread.daemon = True #ensures thread can end individually
        client_thread.start()

#thread to listen for connections
new_cons = Thread(target=start)
new_cons.daemon = True
new_cons.start() #start server

# make GUI window to display server stats
window = Tk()
window.title("IntraText - Server")
window.config(bg=back)
window.protocol(name="WM_DELETE_WINDOW",func=endall)
window.geometry('338x160')
window.maxsize(338,160)
window.minsize(338,160)

content = f'Server Live\nIP:\t{SERVER}\nPort:\t{PORT}'

info = Text(window,bg=back,fg=fore,font=FONT,width=25,height=3,border=0)
info.config(state=NORMAL)
info.insert(1.0,content)
info.config(state=DISABLED)
info.grid(row=0,column=0,sticky=W)


pFrame = Frame(window,bg=back)
pFrame.grid(row=1,column=0)

text3 = Text(pFrame,bg=back,fg=fore,width=30,height=1,font=FONT,border=0)
text3.insert(1.0,f'Password:\t{password}')
text3.config(state=DISABLED)
text3.grid(row=0,column=0,sticky=E)

bottom = Frame(window,bg=back)
bottom.grid(row=2,column=0,sticky=W)

cons = Label(bottom,bg=back,fg=fore,font=FONT,width=24,height=1)
cons.config(text="Active Connections:\t")
cons.grid(row=0,column=0,sticky=W)

count = Label(bottom,bg=back,fg=fore,width=4,height=1,border=0,font=FONT)
count.config(text='0')
count.grid(row=0,column=1,sticky=E)

close_button = Button(window,bg=back,fg='red',text='Close Server',font=FONT,width=30,command=endall,border=1)
close_button.grid(row=3,column=0)

window.mainloop()