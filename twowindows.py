import curses
import os 
import random
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
        self.focused = False
        self.abs_pos = 0


    def get_nlines(self):
        y,x = self.win.getmaxyx()
        return y - 2

    def get_page(self):
        begin = self.page * self.get_nlines()
        return self.lst[begin:begin  + self.get_nlines()]
    def set_page_and_position(self):
        self.page = self.abs_pos // self.get_nlines()
        self.position = self.abs_pos % self.get_nlines()

    def get_selected(self):
        begin = self.page *  self.get_nlines()
        return self.lst[begin+self.position]

        
    def set_list(self,lst):
        if lst is not None:
            self.lst = lst
    def draw(self):
        pass
    def get_abs_pos(self):
        return self.page * self.get_nlines() + self.position
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
    


def get_all_music_files(direc):
    res = []
    for file in os.listdir(direc):
        fullpath = os.path.join(direc,file)
        #print(fullpath)
        if os.path.isdir(fullpath) and os.access(fullpath,os.R_OK):
            res += get_all_music_files(fullpath)
        elif os.path.isfile(fullpath):
            _,ext = os.path.splitext(fullpath)
            if ext in [".mp3",".m4a"]:
                res.append(fullpath)

    return res

class DirectoryListing(Paginator):
    def __init__(self,win,dest,dir):
        super().__init__(win)
        self.dest = dest
        self.dir = dir
        self.set_list(os.listdir(self.dir))
        self.full_path_list = []
        self.pos_stack = []
        self.modus = "d"
        self.refresh = True
        self.abs_pos = 0

    def get_selected_full_path(self):
        begin = self.page * self.get_nlines()
        return self.full_path_list[begin + self.position]

    def sort_alphabetically(self):
        self.full_path_list.sort(key=lambda p: os.path.basename(p).lower())

    def traverse_list(self,prefix):
        counter = 0
        for i,c in enumerate(prefix):
            while c < self[counter][i]:
                counter += 1
        return counter

    def traverse_by_char(self,char,n):
        adder = 0
        for v in self.lst[self.abs_pos:]:
            self.telex.print(v)
            if len(v) < n+1:
                continue
            elif v[n].casefold() < char.casefold():
                adder += 1
            else:
                break
        self.abs_pos += adder
        self.set_page_and_position()



    def process_key(self,key):
        super().process_key(key)
        if key == "m":
            if self.modus == "a":
                self.modus = "d"
                self.refresh = True
            else:
                self.modus = "a"
                self.refresh = True
        

        if self.modus == "a":
            if self.refresh:
                self.full_path_list = get_all_music_files(self.dir)
                self.set_list([os.path.basename(p) for p in self.full_path_list])
                self.refresh = False
                if self.telex and self.focused:
                    self.telex.print(str(len(self.lst)))
                print(len(self.lst))
            if key == "KEY_RIGHT":
                self.dest.fullpathlst.append(self.get_selected_full_path())
                self.dest.set_lst()
            if key == "s":
                self.sort_alphabetically()
                self.set_list([os.path.basename(p) for p in self.full_path_list])
            if key == "f":
                counter = 0
                self.abs_pos = 0
                self.set_page_and_position()
                while key != "\n" and key != "\r":
                    key = self.telex.get_key()
                    
                    self.traverse_by_char(key,counter)
                    print("page %d" % self.page)
                    print("position %d" % self.position)
                    self.draw()
                    counter += 1




        
        if self.modus == "d":
            if self.refresh:
                self.set_list(os.listdir(self.dir))
                self.refresh = False
            if key == "s":
                fullpath = os.path.join(self.dir,self.get_selected())
                if fullpath.endswith(".m3u"):
                    os.rename(fullpath,fullpath+".old")
                elif fullpath.endswith(".m3u.old"):
                    os.rename(fullpath,fullpath.removesuffix(".old"))
                self.set_list(os.listdir(self.dir))
            if key == "l" or key == "a":
                fullpath = os.path.join(self.dir,self.get_selected())
                if os.path.isfile(fullpath) and fullpath.endswith(".m3u"):
                    f = open(fullpath,"r")
                    if key == "l":
                        self.dest.fullpathlst = []
                    for line in f:
                        line = line.strip()
                        musicfilepath = os.path.join(self.dir,line)
                        self.dest.fullpathlst.append(musicfilepath)
                    self.dest.set_lst()
            if key == "KEY_RIGHT":
                fullpath = os.path.join(self.dir,self.get_selected())
                if os.path.isfile(fullpath):
                    self.dest.fullpathlst.append(fullpath)
                    self.dest.set_lst()
            if key == "\n" or key == "\r":
                path = os.path.join(self.dir,self.get_selected())
                if os.path.isdir(path):
                    self.pos_stack.append(self.page * self.get_nlines() + self.position)
                    self.dir = path
                    self.set_list(os.listdir(self.dir))
                    self.position = 0
                    self.page = 0
            if key == "\b" or key == "KEY_BACKSPACE":
                path = Path(self.dir)
                self.dir = path.parent.absolute()
                if len(self.pos_stack) >  0:
                    position = self.pos_stack.pop()
                    self.position = position % self.get_nlines()
                    self.page = position // self.get_nlines()
                else:
                    self.position = 0
                    self.page = 0
                self.set_list(os.listdir(self.dir))
                #self.win.addstr(1,0,"current dir: " + str(self.dir))



    def draw(self):
        self.win.clear()
        self.win.box("*","*")
        _, max_x = self.win.getmaxyx()
        for i,line in enumerate(self.get_page()):
            # print("number of line" + str(i))
            if i == self.position:
                self.win.addstr(i+1,0,line[:max_x],curses.color_pair(1))
                if self.telex and self.focused:
                    self.telex.print(line)
            else:
                fullpath = os.path.join(self.dir,line)
                if os.path.isdir(fullpath):
                    self.win.addstr(i+1,0,line[:max_x],curses.color_pair(2))
                else:
                    self.win.addstr(i+1,0,line[:max_x])

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
        
        self.win.clear()
        self.win.box("*", "*")
        _, max_x = self.win.getmaxyx()
        self.win.addstr(0,max_x-3,str(len(self.fullpathlst)),curses.color_pair(3))
        for i,line in enumerate(self.get_page()):
            if i == self.position:
                self.win.addstr(i+1,0,line[:max_x],curses.color_pair(1))
                if self.telex and self.focused:
                    self.telex.print(line)
            else:
                self.win.addstr(i+1,0,line[:max_x])
    
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
        if key == "x":
            pos = self.get_abs_pos()
            if pos >= 0 and pos < len(self.fullpathlst):
                del self.fullpathlst[self.page * self.get_nlines() + self.position]
            self.draw()
        if key == "s":
            random.shuffle(self.fullpathlst)
        if key == "u":
            pos = self.get_abs_pos()
            if pos > 0:
                self.fullpathlst[pos-1],self.fullpathlst[pos]=self.fullpathlst[pos],self.fullpathlst[pos-1]
                self.position -= 1
        if key == "d":
            pos = self.get_abs_pos()
            if pos < len(self.fullpathlst) -1:
                self.fullpathlst[pos+1],self.fullpathlst[pos]=self.fullpathlst[pos],self.fullpathlst[pos+1]
                self.position += 1
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
        _,cols = self.screen.getmaxyx();
        self.screen.move(self.get_y(),0)
        self.screen.clrtoeol()
        self.screen.addstr(string.encode(encoding="utf-8")[:cols-1])
    def get_key(self):
        return self.screen.getkey()
    def parse_command(self):
        self.screen.move(self.get_y(),0)
        self.screen.clrtoeol()
        curses.echo()
        command = self.screen.getstr(self.get_y(),0).decode(encoding="utf-8")
        commandandarg = command.split(" ")
        if commandandarg[0] == "w":
            self.print("Write command entered")
            
            if len(commandandarg) == 2 and commandandarg[1] != "":
                f = open(commandandarg[1],"w")
                for line in self.source.get_list():
                    line = line.replace("/","\\")
                    f.write("%s\r\n" % line)
                f.close()
        if commandandarg[0] == "l":
            if len(commandandarg) == 2:
                f =open(commandandarg[1],"r")
                for line in f:
                    lst = []
                    fullpath = os.path.abspath(line)
                    lst.append(fullpath)
                self.source.fullpathlst = lst
                f.close()

        if commandandarg[0] == "q":
            curses.endwin()
            exit(0)
def main(stdscr):
    
    curses.init_pair(1,curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(2,curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3,curses.COLOR_CYAN, curses.COLOR_BLACK)
    win1 = curses.newwin(curses.LINES-1, curses.COLS // 2,0,0)
    win2 = curses.newwin(curses.LINES-1, curses.COLS //2,0,curses.COLS//2)
    
    
    win1.box('*','*')
    win2.box('|','|')
    pag2 = ListComposer(win2)
    pag1 = DirectoryListing(win1,pag2,Path.cwd())
    pag2.set_source(pag1)
    cl = CommandLine(stdscr)
    cl.set_source(pag2)
    pag1.telex = cl
    pag2.telex = cl
    pag1.focused = True
    pag2.focused = False
    for pag in Paginator.paginators:
        pag.draw()
    stdscr.refresh()
    
    win1.refresh()
    win2.refresh()
    
    elements = [pag1,pag2,cl]
    selected = pag1
    pag1.focused = True
    pag2.focused = False
    prev_selected = selected
    while True:
        #key = stdscr.getch()
        
        #cl.print("key: " + key)
        key = stdscr.getkey()
       # if key == "q":
        #    curses.endwin()
         #   exit(0)
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
            if selected != prev_selected:
                cl.print("command line selected")
                try:
                    os.chdir(pag1.dir)
                except:
                    cl.print("dir not found")
                cl.parse_command()
        if selected == pag1:
            if prev_selected != selected:
                cl.print("win1 selected")
            pag1.focused = True
            pag2.focused = False
            pag1.process_key(key)
        if selected == pag2: 
            if prev_selected != selected:
                cl.print("win2 selected")
            pag1.focused = False
            pag2.focused = True
            pag2.process_key(key)
        prev_selected = selected

        pag1.draw()
        pag2.draw()
        win1.refresh()
        win2.refresh()
        stdscr.refresh()
    
    
    #stdscr.refresh()
        
    stdscr.getkey()

curses.wrapper(main)
