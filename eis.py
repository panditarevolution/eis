import sublime, sublime_plugin
import subprocess, os, sys, traceback
import json, io
import threading


######################### Entry points

class eisCommand(sublime_plugin.TextCommand):
    def run(self, edit,**kwargs):
        """Redirect calls to execute shell commands and update the menu settings."""
        # # Maybe this shouldn't be checked with every command call.....
        # if "eis_menu" in kwargs.keys():
        #     self.view.run_command("eis_create_menu",{"eis_menu_kw":kwargs})
        eis_command = kwargs["cmd"]
        self.view.run_command("exec_in_shell",{"cmd":kwargs["cmd"]})


class openShellBoxCommand(sublime_plugin.WindowCommand):
    def run(self):
        """Open an input box to allow to execute any command in the shell."""
        self.window.show_input_panel("Please enter a shell command:", '', lambda s: self.set_user_input(s), None, None)

    def set_user_input(self, text):
        panel_name = 'executeShell'
        v = self.window.get_output_panel(panel_name)
        edit = v.begin_edit()
        v.insert(edit, v.size(), text)
        v.end_edit(edit)
        self.window.run_command("exec_in_shell",{"cmd":"start "+text})

# This class is in progress
class buildEisMenu(sublime_plugin.WindowCommand):
    def run(self):
        """Checks the user key bindings for menu requests and builds them."""
        # The first part seems to work now the question is how to 
        sublime.message_dialog("Woohoo 1")
        try:
            if '/' in menu_kw["eis_menu"]:
                menu = menu_kw["eis_menu"].split("/")[::-1]
                menu_cmd = {
                "command":"eis",
                "args":menu_kw["args"],
                "caption": menu[0]
                }
            else:
                pass
        except(KeyError):
            sublime.message_dialog("There was an error creating the menu. Please check the what was given as 'args' in the key binding and how the menu tree was specified.\n\n The computer returned: \n\n"+traceback.format_exc())
        except(Exception):
            sublime.message_dialog("Don't panic!!! Something went wrong....\n\n\n"+traceback.format_exc())
        temp_list = []
        i = 1
        # Creating the dict structure for json. Following the convention that id's are lowercase captions with " " replaced by "-".
        while i in range(len(menu)):
            temp_list.append({"caption":menu[i],"id":menu[i].lower().replace(" ","-"),"children":[]})
        temp_list_copy=temp_list[::-1][:]
        n=0
        for i in temp_list[::-1][0:len(temp_list)-1]:
            i["children"]=[temp_list_copy[n+1]]
            n+=1
        # adding the last item
        temp_list[::-1][-1]["children"]=[menu_cmd]

        # Getting the current eis Menu to maintain persistancy
        try:
            cur_menu = []
            with io.open("./Data/Packages/Eis/Main.sublime-menu") as eismenu:
                cur_menu.extend(json.load(eismenu))
                sublime.message_dialog("Woohoo")
        except(Exception):
            sublime.message_dialog("Don't panic!!! Something went wrong....\n\n\n"+traceback.format_exc())


######################### Processing

class execInShellCommand(sublime_plugin.TextCommand):
    def run(self,edit,cmd):
        """This command executes 'cmd' and includes whatever is set in the settings file. This is done via eisThread."""
        # Getting the relevant setttings
        os_system   = sys.platform
        settings    = sublime.load_settings('Eis.sublime-settings')
        exec_folder = settings.get('exec_folder')
        prefix      = settings.get('prefix')
        postfix     = settings.get('postfix')
        add_start   = settings.get('add_start')
        add_pause   = settings.get('add_pause')
        verbose     = settings.get('verbose')
        cur_view    = sublime.Window.active_view(sublime.active_window())
        file_name   = cur_view.file_name()

        ########## Check the following section
        # Setting specified execution directory is specified
        if exec_folder == "$file_dir":          
            if cur_view.file_name()[-1] not in ['/','\\']:
                # This migth be superflous
                if '/' in cur_view.file_name():
                    div = '/'
                if '\\' or '\\\\' in cur_view.file_name():
                    div = '\\'
                exec_folder = '/'.join(cur_view.file_name().split(div)[0:-1])

            else: 
                exec_folder=cur_view.file_name() #this seems wrong


        # Making sure that command is a string and checking whether $file_name is called
        if type(cmd)==list:
            cmd = (' ').join(cmd)

        if "$file_name" in cmd:
            cmd = cmd.replace("$file_name",file_name)

        if "$file_dir" in cmd:
            if cur_view.file_name()[-1] not in ['/','\\']:
                # This migth be superflous
                if '/' in cur_view.file_name():
                    div = '/'
                elif '\\' or '\\\\' in cur_view.file_name():
                    div = '\\'
                file_dir = '/'.join(cur_view.file_name().split(div)[0:-1])

            else: 
                file_dir=cur_view.file_name() #this seems wrong
            cmd = cmd.replace("$file_dir","\""+file_dir+"\"")


        # Making system specific calls - 
        #####  Windows
        if os_system == 'win32':
            cmd = prefix+cmd+postfix
            if add_start:
                cmd = "start "+cmd
            if add_pause:
                cmd = cmd+" & pause"
            # call(cmd, shell=True) is replaced by thread below
            # Starting a new thread.
            eisT = eisThread(cmd,exec_folder,verbose)
            eisT.start()
        #####  Linux
        elif "linux" in os_system:
            cmd = prefix+cmd+postfix
            if add_pause:
                cmd = cmd+" read -p 'Press [Enter] key to start backup...'"
            if add_start:
                cmd = cmd+" &"
            # call(cmd, shell=True) is replaced by thread below
            # Starting a new thread.
            eisT = eisThread(cmd,exec_folder,verbose)
            eisT.start()
        #####  Mac and others - Not properly implemented relies on user input
        else:  
           cmd = prefix+cmd+postfix
           if add_start:
               cmd = "open "+cmd
           eisT = eisThread(cmd,exec_folder,verbose)
           eisT.start()


#This class is likely to be superceded by buildEisMenu
class eisCreateMenu(sublime_plugin.WindowCommand):
    def run(self, menu_kw):
        """Takes a string, unicode or dictionairy to create a new menu"""
        # The first part seems to work now the question is how to 
        try:
            if '/' in menu_kw["eis_menu"]:
                menu = menu_kw["eis_menu"].split("/")[::-1]
                menu_cmd = {
                "command":"eis",
                "args":menu_kw["args"],
                "caption": menu[0]
                }
            else:
                pass
        except(KeyError):
            sublime.message_dialog("There was an error creating the menu. Please check the what was given as 'args' in the key binding and how the menu tree was specified.\n\n The computer returned: \n\n"+traceback.format_exc())
        except(Exception):
            sublime.message_dialog("Don't panic!!! Something went wrong....\n\n\n"+traceback.format_exc())
        temp_list = []
        i = 1
        # Creating the dict structure for json
        while i in range(len(menu)):
            temp_list.append({"caption":menu[i],"id":menu[i].lower().replace(" ","-"),"children":[]})
        temp_list_copy=temp_list[::-1][:]
        n=0
        for i in temp_list[::-1][0:len(temp_list)-1]:
            i["children"]=[temp_list_copy[n+1]]
            n+=1
        # adding the last item
        temp_list[::-1][-1]["children"]=[menu_cmd]

        # Getting the current eis Menu to maintain persistancy
        try:
            with io.open("./Data/Packages/Eis/Main.sublime-menu") as eismenu:
                pass
        except:
            pass



######################### Executing

class eisThread(threading.Thread):
    def __init__(self,cmd,exec_folder,verbose):
        threading.Thread.__init__(self)
        self.cmd         = cmd
        self.exec_folder = exec_folder
        self.verbose     = verbose
    def run(self):
        try:
            # The following is trying to deal with a sublime specific requirement in regards to non shell programs. These can be called when shell=False but not otherwise. Shell programs on the other hand require shell=True. This snippet is based on http://stackoverflow.com/questions/4819402/multiple-tries-in-try-except-block.
            for i in [True,False]:
                try:
                    # sublime.message_dialog(self.cmd)
                    subprocess.call(self.cmd,shell=i)
                except(WindowsError):
                # except(RuntimeError): # Debug only
                    pass

        except(Exception):
            verb     = self.verbose
            if verb=="0":
                sublime.message_dialog("Don't panic!!! Something went wrong....")
            elif verb=="1":
                sublime.message_dialog("Don't panic!!! Something went wrong....\n\n\n"+traceback.format_exc())
            elif verb=="2":
                sublime.message_dialog("Don't panic!!! Something went wrong....\n\n\n"+str(sys.exc_info()))
            else:
                pass



######################### Misc



