#imports
from signal import SIGINT
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from tkinter import DISABLED, E, END, LEFT, NORMAL, RIGHT, W, Button, Text, Tk, Entry, Frame, Label, messagebox
from os import kill

#client setup
FORMAT = 'utf-8'
HEAD_BYTES = 16
DISCONNECT = 'dc'
global run 
run = True
global success
success = False
global other_clients
class PassError(OSError):
    pass

# to send message to client
def send():
    data = inp.get()
    if not data:    return #doesn't work if empty message is attempted to be sent
    inp.delete(0,END) #empty text input

    # prepare length and message to be sent
    msg = data.encode(FORMAT)
    msg_len = str(len(msg)).encode(FORMAT)
    msg_len += b' '*(HEAD_BYTES-len(msg_len))

    # send to server
    client.send(msg_len)
    client.send(msg)
    
    # if client wishes to disconnect, close everything
    if data == DISCONNECT:
        endall()
        return
    
    # add the message sent to chatlog
    addtochat(f"you:\t{data}")

# to receive incoming message from the server (to receive messages that other clients sent)
def listen():
    global run

    try:
        while True:
            if not run: endall()
            incoming = client.recv(HEAD_BYTES).decode(FORMAT)
            if incoming: #process only if received data is not empty (0)

                msg_len = int(incoming)
                data = client.recv(msg_len).decode(FORMAT) # receive message data
                try:
                    name,message = data.split('&&&') # separate username and message based on protocol
                    addtochat(f"{name}:\t{message}")
                except ValueError:
                    addtochat(data)
    
    except ConnectionResetError: #arror raised when connection is closed unexpectedly
        run = False
        messagebox.showinfo('Disconnected',message='Server was closed')
        endall()

# try to establish connection
def submit():
    global username
    global PORT
    global SERVER
    global ADDRESS
    global client
    global success
    try:
        username = username_entry.get() # get username, port, server IP and attempted password from entry text fields
        PORT = int(port_entry.get())
        SERVER = server_entry.get()
        entered = pass_entry.get()
        if '' in [username,SERVER,entered]: # make sure none of them are empty
            raise ValueError
        
        ADDRESS = (SERVER,PORT)
        client = socket(AF_INET, SOCK_STREAM)
        client.connect(ADDRESS) # connect to client

        # send password length message
        pass_len = str(len(entered)).encode(FORMAT)
        pass_len += b' '*(HEAD_BYTES-len(pass_len))
        client.send(pass_len)
        # send actual password
        client.send(entered.encode())
        reply = client.recv(1).decode(FORMAT)
        # if reply is 0, password was wrong
        if reply=='0':
            raise PassError
        
        # if password was correct, close current window
        window.destroy()
        success = True

    except WindowsError as e: # error raised if connection could not be made
        if e.winerror==10061:
            messagebox.showerror(title='Error',message='Invalid IP or Port')
        else:
            messagebox.showerror(title='Error',message='Could not connect')
    except ValueError:
        messagebox.showerror(title='Error',message='Invalid Data')
    except PassError:
        messagebox.showerror(title='Error',message='Invalid Password')
    except Exception as e:
        messagebox.showerror(title='Error',message=e)

# add text/data to chatlog
def addtochat(txt):
    chatbox.config(state=NORMAL)
    chatbox.insert(END,'\n'+txt)
    chatbox.config(state=DISABLED)
    chatbox.see(END)

# to close everything and terminate program
def endall():
    try:
        window.destroy()
        global other_clients
        if other_clients.is_alive():    kill(other_clients.native_id,SIGINT)
    except OSError:
        pass
    except NameError:
        quit()
    except Exception:
        pass

# make window to attempt connection
fore = '#FFFFFF'
back = '#0000FF'

window = Tk()
window.title("IntraText - Client")
window.config(bg=back)
window.protocol(name="WM_DELETE_WINDOW",func=endall)
window.bind('<Return>',lambda lolz: submit())
window.geometry('510x185')
window.maxsize(510,185)
window.minsize(510,185)

top = Frame(window,bg=back)
top.pack()

# entry fields
text = Label(top,text='Enter Username   ',font=('Consolas',18),fg=fore,bg=back)
text.grid(row=0,column=0,sticky=W)
text.config(width=18)

username_entry = Entry(top,font=("Consolas",18),bg=back,fg=fore)
username_entry.focus_set()
username_entry.config(width=20)
username_entry.grid(row=0,column=1,sticky=E)

text2 = Label(top,text='Enter Server IP  ',font=('Consolas',18),fg=fore,bg=back)
text2.grid(row=1,column=0,sticky=W)
text2.config(width=18)

server_entry = Entry(top,font=("Consolas",18),bg=back,fg=fore)
server_entry.config(width=20)
server_entry.grid(row=1,column=1,sticky=E)

text3 = Label(top,text='Enter Server Port',font=('Consolas',18),fg=fore,bg=back)
text3.grid(row=2,column=0,sticky=W)
text3.config(width=18)

port_entry = Entry(top,font=("Consolas",18),bg=back,fg=fore)
port_entry.config(width=20)
port_entry.grid(row=2,column=1,sticky=E)

text4 = Label(top,text='Enter Password   ',font=('Consolas',18),fg=fore,bg=back)
text4.grid(row=3,column=0,sticky=W)
text4.config(width=18)

pass_entry = Entry(top,font=("Consolas",18),bg=back,fg=fore)
pass_entry.config(width=20)
pass_entry.grid(row=3,column=1,sticky=E)

submit_name = Button(window,text='Connect',command=submit,font=("Consolas",18),bg=back,fg=fore,border=1)
submit_name.config(width=38,height=1)
submit_name.pack()

window.mainloop()


# when window is terminated, it was either due to ending the program or if connection was made
# is connection was made, success will be True
# program terminates if success if false

if success:

    # send username to server
    msg = username.encode(FORMAT)
    msg_len = str(len(msg)).encode(FORMAT)
    msg_len += b' '*(HEAD_BYTES-len(msg_len))
    client.send(msg_len)
    client.send(msg)

    # thread to listen to server for other clients' messages
    other_clients = Thread(target=listen)
    other_clients.daemon = True
    other_clients.start()

    # make window
    window = Tk()
    window.title("IntraText - Client")
    window.config(bg=back)
    window.protocol(name="WM_DELETE_WINDOW",func=endall)
    window.bind('<Return>',lambda _: send())
    window.geometry('570x590')

    chatframe = Frame(window,bg=back)
    chatframe.grid(row=0,column=0)

    chatbox = Text(chatframe,width=50,fg=fore,bg=back,border=0,font=('Consolas', 15),borderwidth=0)
    chatbox.config(state=DISABLED)
    chatbox.grid(row=0,column=0)

    bottom = Frame(chatframe,bg=back)
    bottom.grid(row=1,column=0)

    inp = Entry(bottom,fg=fore,bg=back,width=45,font=('Consolas', 15),border=1,borderwidth=3)
    inp.focus_set()
    inp.pack(side=LEFT)

    send_button = Button(bottom,fg=fore,bg=back,text='send',command=send,width=5,font=('Consolas', 15))
    send_button.pack(side=RIGHT)

    window.mainloop()