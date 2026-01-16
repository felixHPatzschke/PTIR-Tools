### debugging
import inspect #currentframe, getframeinfo
import colorama as ca
import sys


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
        return f"<DebugLevel {self.style_setup} {self.numeric_value} '{self.name}' {self.style_reset} | traceback: {self.traceback} | {'suppressed' if self.suppressed else 'active'}>"


DEBUG_LEVELS = { dl.name.lower() : dl for dl in [
    DebugLevel( ""           , 1 , ca.Style.DIM ,                              ca.Style.RESET_ALL ,                             0,  False, False ), 
    DebugLevel( "Debug Info" , 2 , ca.Fore.BLUE ,                              ca.Fore.RESET ,                                  1,  True,  False ), 
    DebugLevel( "Trace"      , 3 , ca.Fore.BLUE ,                              ca.Fore.RESET ,                                  -1, True,  False ), 
    DebugLevel( "Success"    , 4 , ca.Fore.GREEN ,                             ca.Fore.RESET ,                                  0,  False, False ), 
    DebugLevel( "Info"       , 5 , ca.Style.DIM ,                              ca.Style.RESET_ALL ,                             1,  False, False ), 
    DebugLevel( "Warning"    , 6 , ca.Fore.YELLOW ,                            ca.Fore.RESET ,                                  1,  False, True  ), 
    DebugLevel( "Error"      , 7 , ca.Style.BRIGHT+ca.Fore.RED ,               ca.Style.RESET_ALL+ca.Fore.RESET ,               1,  False, True  ), 
    DebugLevel( "Critical"   , 8 , ca.Style.BRIGHT+ca.Back.RED+ca.Fore.WHITE,  ca.Style.RESET_ALL+ca.Back.RESET+ca.Fore.RESET , -1, False, True  ), 
    *[ DebugLevel( f"Trace{i}", 3, ca.Fore.BLUE, ca.Fore.RESET, i, True, False) for i in range(2,10) ], 
] }


def debug(*args) -> None:
    if len(args) == 0:
        msg = "✅"
        level = "debug info"
    elif len(args) == 1:
        msg = str(args[0])
        level = "debug info"
    elif len(args) > 1:
        if args[0].lower() in DEBUG_LEVELS.keys():
            level = args[0]
            msg = "\n".join( [ str(a) for a in args[1:] ] )
        else:
            level = "debug info"
            msg = "\n".join( [ str(a) for a in args ] )

    LEVEL = DEBUG_LEVELS.get(level.lower(), DEBUG_LEVELS["debug info"])
    if LEVEL.suppressed:
        return None
    
    ### initialize trackers for tabbing
    right_shift = { "traceback":0 , "level":0 }
    
    ### set terminal text display style
    print( LEVEL.style_setup, end='', file=sys.stderr )
    
    if LEVEL.print_level: 
        #right_shift["level"] = len( LEVEL.name.upper() ) + 2
        msg = f"{LEVEL.name.upper()}: " + msg
    
    if LEVEL.traceback != 0:
        cf = inspect.currentframe()
        of = inspect.getouterframes(cf)
        if LEVEL.traceback != -1:
            of = of[:LEVEL.traceback+1]
        of = of[::-1]
        traceback_lines = [ frame.filename.replace('\\','/').split('/')[-1] + " in line " + str(frame.lineno) + ":\t" for frame in of[:-1] ]
        if LEVEL.print_function:
            traceback_functions = [ f"{str(frame.function)+'():' if str(frame.function)[0] != '<' else ''}" for frame in of[:-1] ]
            for i in range(len(traceback_lines)-1):
                traceback_lines[i] += traceback_functions[i]
            msg = traceback_functions[-1] + "\n" + msg
        right_shift["traceback"] = len( traceback_lines[-1] )
        print( "\n".join( traceback_lines ), end='', file=sys.stderr )
    
    if '\n' in msg:
        indent_str = "\n"
        if right_shift["traceback"] > 0:
            indent_str += " "*right_shift["traceback"] + "\t"
        indent_str += " "*right_shift["level"]
        msg = msg.replace("\n", indent_str)
    print( msg, end='', file=sys.stderr )
    
    print( LEVEL.style_reset, file=sys.stderr )

    
def suppress_debug_levels_up_to(level:int|str) -> None:
    """
    Set up the debugging tool to only show messages over a given level of severity.
    
    :param level: Numeric value or string representation of the highest debug level to ignore
    :type level: int | str
    """
    global DEBUG_LEVELS
    if isinstance(level, str):
        level = DEBUG_LEVELS[level.lower()].numeric_value if level.lower() in DEBUG_LEVELS else 3
    for key in DEBUG_LEVELS:
        DEBUG_LEVELS[key].suppress( DEBUG_LEVELS[key].numeric_value <= level )
    
    #debug("info", "Debug Levels:", *(l.__repr__() for l in DEBUG_LEVELS.values()))


def suppress_debug_levels(*levels:list[int|str]) -> None:
    """
    Set up the debugging tool to show messages of all severities except the ones specified.
    
    :param levels: list of specifications (either numerical value or string representation) of severity levels to ignore.
    :type levels: list[int | str]
    """
    global DEBUG_LEVELS

    numerical_values = set()
    for level in levels:
        if isinstance(level, str):
            if level.lower() in DEBUG_LEVELS:
                numerical_values.add( DEBUG_LEVELS[level.lower()].numeric_value )
        elif isinstance(level, int):
            numerical_values.add( level )
        else:
            debug("warning", f"'{level}' is not a valid specification for a debug level.")

    for key in DEBUG_LEVELS:
        DEBUG_LEVELS[key].suppress( DEBUG_LEVELS[key].numeric_value in numerical_values )

    #debug("info", "Debug Levels:", *(l.__repr__() for l in DEBUG_LEVELS.values()))


### by default, only show warnings and errors
suppress_debug_levels("info")


