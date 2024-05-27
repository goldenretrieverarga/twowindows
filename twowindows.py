import curses
import os 
from pathlib import Path
class Paginator:
    paginators = []
    
    def __init__(self,win):
        self.win = win
        self.lst = []
        self.position = 0
        self.max_lines, self.max_cols = self.win.getmaxyx()
        self.max_lines -= 1
        self.page = 0
        Paginator.paginators.append(self)
    
    def get_nlines(self):
        y,x = self.win.getmaxyx()
        return y - 2

    def get_page(self):
        begin = self.page * self.get_nlines();
        return self.lst[begin:begin  + self.get_nlines()]
    
    def get_selected(self):
        begin = self.page *  self.get_nlines()
        return self.lst[begin+self.position]
        
    def set_list(self,lst):
        self.lst = lst
    def draw(self):
        self.win.clear()
        self.win.box("*","*")
        for i,line in enumerate(self.get_page()):
            
            if i == self.position:
                self.win.addstr(i+1,0,line,curses.color_pair(1))
            else:
                self.win.addstr(i+1,0,line)
                
    def process_key(self,key):
        if key == "KEY_DOWN":
           # if self.position < self.max_lines:
           if self.position < self.get_nlines() -1:
               self.position += 1
           else:
               self.page += 1
               self.position = 0
        if key == "KEY_UP":
            if self.position > 0:
                self.position -= 1
            else:
                if self.page > 0:
                    self.page -= 1
                    self.position = self.get_nlines() -1                       
    
class DirectoryListing(Paginator):
    def __init__(self,win,dest,dir):
        super().__init__(win)
        self.dest = dest
        self.dir = dir
        self.set_list(os.listdir(self.dir))
    
    def draw(self):
        self.win.clear()
        self.win.box("*","*")
        for i,line in enumerate(self.get_page()):
            print("number of line" + str(i))
            if i == self.position:
                self.win.addstr(i+1,0,line,curses.color_pair(1))
            else:
                fullpath = os.path.join(self.dir,line)
                if os.path.isdir(fullpath):
                    self.win.addstr(i+1,0,line,curses.color_pair(2))
                else:
                    self.win.addstr(i+1,0,line)
    def process_key(self,key):
        super().process_key(key)
        if key == "KEY_RIGHT":
            fullpath = os.path.join(self.dir,self.get_selected())
            if os.path.isfile(fullpath):
                self.dest.fullpathlst.append(fullpath)
                self.dest.set_lst()
        if key == "\n" or key == "\r":
            path = os.path.join(self.dir,self.get_selected())
            if os.path.isdir(path):
                self.dir = path
                self.set_list(os.listdir(self.dir))
                self.position = 0
                self.page = 0
        if key == "\b":
            path = Path(self.dir)
            self.dir = path.parent.absolute()
            self.position = 0
            self.page = 0
            self.set_list(os.listdir(self.dir))
            #self.win.addstr(1,0,"current dir: " + str(self.dir))
            

class ListComposer(Paginator):
    def __init__(self,win):
        super().__init__(win)
        self.view = "base"
        self.fullpathlst = []
        self.set_lst()
    def set_source(self,dl):
        self.dl = dl
        
    def set_lst(self):
        if self.view == "base":
            self.set_base()
        elif self.view == "relative":
            self.set_relative()
        elif self.view == "absolute":
            self.lst = self.fullpathlst
    def draw(self):
        super().draw()
    
    def get_list(self):
        return self.lst
    
    def set_relative(self):
        rel_path = self.dl.dir
        self.lst = [ os.path.relpath(full_pth,rel_path) for full_pth in self.fullpathlst]
    def set_base(self):
        self.lst =[os.path.basename(p) for p in self.fullpathlst]
        
    def process_key(self,key):
        super().process_key(key)
        if key == "r":
            self.view = "relative"
        if key == "b":
            self.view = "base"
        if key == "a":
            self.view = "absolute"
        self.set_lst()
            
            

            
class CommandLine:
    def __init__(self,screen):
        self.y = curses.LINES-1
        self.screen = screen
    def get_y(self):
        return curses.LINES-1
    def set_source(self,source):
        self.source = source
    def print(self,string):
        self.screen.move(self.get_y(),0)
        self.screen.clrtoeol()
        self.screen.addstr(string)       
    def parse_command(self):
        self.screen.move(self.get_y(),0)
        self.screen.clrtoeol()
        curses.echo()
        command = self.screen.getstr(self.get_y(),0).decode(encoding="utf-8")
        commandandarg = command.split(" ")
        if commandandarg[0] == "w":
            self.print("Write command entered")
            
            if len(commandandarg) == 2:
                f = open(commandandarg[1],"w")
                for line in self.source.get_list():
                    line = line.replace("/","\\")
                    f.write("%s\r\n" % line)
                f.close()
def main(stdscr):
    
    curses.init_pair(1,curses.COLOR_YELLOW,curses.COLOR_BLUE)
    curses.init_pair(2,curses.COLOR_GREEN,curses.COLOR_BLACK) 
    win1 = curses.newwin(curses.LINES-1,curses.COLS // 2,0,0)
    win2 = curses.newwin(curses.LINES-1,curses.COLS //2,0,curses.COLS//2)
    
    
    win1.box('*','*')
    win2.box('|','|')
    pag2 = ListComposer(win2)
    pag1 = DirectoryListing(win1,pag2,Path.cwd())
    pag2.set_source(pag1)
    cl = CommandLine(stdscr)
    cl.set_source(pag2)
    for pag in Paginator.paginators:
        pag.draw()
    stdscr.refresh()
    
    win1.refresh()
    win2.refresh()
    
    elements = [pag1,pag2,cl]
    selected = pag1
    while True:
        #key = stdscr.getch()
        
        #cl.print("key: " + key)
        key = stdscr.getkey()
        if key == " ":
            selected = elements[(elements.index(selected)+1) % 3]
            cl.print("tab detected")
            cl.print(" %s" % pag1.dir)
            
        
        """""
        if key == curses.KEY_DOWN:
            if selected != cl:
                prev_window = selected
                selected = cl
        if key == curses.key_TBT
            if selected == cl:
                selected = prev_window
                cl.print("window selected" + prev_window)
        if key == curses.KEY_RIGHT:
            if selected == win1:
                selected = win2
        if key == curses.KEY_LEFT:
            if selected == win2:
                selected = win1
        """""       
               
        if selected == cl:
            cl.print("command line selected")
            os.chdir(pag1.dir)
            cl.parse_command()
        if selected == pag1:
            cl.print("win1 selected")
            pag1.process_key(key)
        if selected == pag2: 
            cl.print("win2 selected")
            pag2.process_key(key)
        pag1.draw()
        pag2.draw()
        win1.refresh()
        win2.refresh()
        stdscr.refresh()
    
    
    #stdscr.refresh()
        
    stdscr.getkey()

curses.wrapper(main)
