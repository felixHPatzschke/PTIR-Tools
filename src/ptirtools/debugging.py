### debugging
import inspect #currentframe, getframeinfo
import colorama as ca


class DebugLevel:
    def __init__(self, name:str, numeric_value:int, style_setup:str, style_reset:str, traceback:int, print_function:bool, print_level:bool):
        self.name = name
        self.numeric_value = numeric_value
        self.style_setup = style_setup
        self.style_reset = style_reset
        self.traceback = traceback
        self.print_level = print_level
        self.suppressed = False
        self.print_function = print_function
    
    def suppress(self, b:bool=True):
        self.suppressed = b
    
    def __repr__(self):
        return f"< DebugLevel {self.style_setup} {self.numeric_value} (\"{self.name}\") {self.style_reset} | traceback: {self.traceback} | {'suppressed' if self.suppressed else 'active'} >"


DEBUG_LEVELS = { dl.name.lower() : dl for dl in [
    DebugLevel( ""           , 1 , ca.Style.DIM ,                              ca.Style.RESET_ALL ,                             0,  False, False ), 
    DebugLevel( "Debug Info" , 2 , ca.Fore.BLUE ,                              ca.Fore.RESET ,                                  -1, True, True   ), 
    DebugLevel( "Info"       , 3 , ca.Style.DIM ,                              ca.Style.RESET_ALL ,                             1,  False, False ), 
    DebugLevel( "Success"    , 4 , ca.Fore.GREEN ,                             ca.Fore.RESET ,                                  0,  False, False ), 
    DebugLevel( "Warning"    , 5 , ca.Fore.YELLOW ,                            ca.Fore.RESET ,                                  1,  False, True  ), 
    DebugLevel( "Error"      , 6 , ca.Style.BRIGHT+ca.Fore.RED ,               ca.Style.RESET_ALL+ca.Fore.RESET ,               1,  False, True  ), 
    DebugLevel( "Critical"   , 7 , ca.Style.BRIGHT+ca.Back.RED+ca.Fore.WHITE,  ca.Style.RESET_ALL+ca.Back.RESET+ca.Fore.RESET , -1, False, True  ), 
] }


def debug(*args):
    if len(args) == 0:
        debug("✅")
        return
    elif len(args) == 1:
        msg = str(args[0])
        level = "info"
    elif len(args) > 1:
        level = args[0]
        msg = "\n".join( [ str(a) for a in args[1:] ] )

    LEVEL = DEBUG_LEVELS[level.lower()] if level.lower() in DEBUG_LEVELS else DEBUG_LEVELS["info"]
    
    right_shift = { "traceback":0 , "level":0 }
    
    if not LEVEL.suppressed:
        print( LEVEL.style_setup, end='' )
        
        if LEVEL.print_level: 
            #right_shift["level"] = len( LEVEL.name.upper() ) + 2
            msg = f"{LEVEL.name.upper()}: " + msg
        
        if LEVEL.traceback != 0:
            cf = inspect.currentframe()
            of = inspect.getouterframes(cf)
            if LEVEL.traceback != -1:
                of = of[:LEVEL.traceback+1]
            of = of[::-1]
            traceback_lines = [ f"{frame.filename.split('/')[-1]} in line {frame.lineno}:\t" for frame in of[:-1] ]
            if LEVEL.print_function:
                traceback_functions = [ f"{str(frame.function)+'():' if str(frame.function)[0] != '<' else ''}" for frame in of[:-1] ]
                for i in range(len(traceback_lines)-1):
                    traceback_lines[i] += traceback_functions[i]
                msg = traceback_functions[-1] + "\n" + msg
            right_shift["traceback"] = len( traceback_lines[-1] )
            print( "\n".join( traceback_lines ), end='' )
        
        if '\n' in msg:
            indent_str = "\n"
            if right_shift["traceback"] > 0:
                indent_str += " "*right_shift["traceback"] + "\t"
            indent_str += " "*right_shift["level"]
            msg = msg.replace("\n", indent_str)
        print( msg, end='' )
        
        print( LEVEL.style_reset )

    
def suppress_debug_levels(level:int|str):
    global DEBUG_LEVELS
    if isinstance(level, str):
        level = DEBUG_LEVELS[level.lower()].numeric_value if level.lower() in DEBUG_LEVELS else 3
    for key in DEBUG_LEVELS:
        DEBUG_LEVELS[key].suppress( DEBUG_LEVELS[key].numeric_value <= level )


### by default, only show explicit success notifications, warnings and errors
suppress_debug_levels("info")


