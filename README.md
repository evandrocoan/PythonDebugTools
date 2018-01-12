
# Python Debug Tools


Basic logger for python on the output form:
```
[DEBUG] 15:36:33:926000      0 Debugging
[DEBUG] 15:36:33:926000      0 ...
[DEBUG] 15:36:33:926000      0 ...
[DEBUG] 15:36:33:927000   1000 Entering on main(0)
[DEBUG] 15:36:33:927000      0 ( Player ) Creating the player: Player 0
[DEBUG] 15:36:33:927000      0 ( Player ) Creating the player: Player 1
[DEBUG] 15:36:33:927000      0 ( Player ) Creating the player: Player 2
[DEBUG] 15:36:33:927000      0 ( Player ) Creating the player: Player 3
[DEBUG] 15:36:33:927000      0 ( Player ) Creating the player: Player 4
[DEBUG] 15:36:33:927000      0 ( StickIntelligence ) Creating the intelligence for 5 players
[DEBUG] 15:36:33:927000      0 ( StickIntelligence ) Starting the next row of fun...
[DEBUG] 15:36:33:927000      0 ( AgentPlayer ) I am a good boy, as long as I am playing.
[DEBUG] 15:36:33:927000      0 ( AgentPlayer ) I am a good boy, as long as I am playing.
[DEBUG] 15:36:33:927000      0 ( AgentPlayer ) I am a good boy, as long as I am playing.
[DEBUG] 15:36:33:927000      0 ( AgentPlayer ) I am a good boy, as long as I am playing.
[DEBUG] 15:36:33:927000      0 ( AgentPlayer ) I am a good boy, as long as I am playing.
```


To use it:
```python
# Import the debugger
from python_debug_tools import getLogger

# Enable debug messages: (bitwise)
#
# 0   - Disabled debugging.
# 1   - Basic logging messages.
# 2   - AgentPlayer       class' notices.
# 4   - StickIntelligence class' notices.
# 127 - All debugging levels at the same time.
#
log = getLogger( 127, os.path.basename( __file__ ) )

# Later, use `log.log_level = 0` to disable the debugger, or change the level.
log( 1, "Debugging" )
log( 1, "..." )
log( 1, "..." )
```

Or something like:
```python
import os
import sys

def assert_path(module):

    if module not in sys.path:
        sys.path.append( module )

# Import the debug tools
assert_path( os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), 'PythonDebugTools/all' ) )

# Import the debugger
from python_debug_tools import getLogger

# Enable debug messages: (bitwise)
#
# 0   - Disabled debugging.
# 1   - Basic logging messages.
# 2   - AgentPlayer       class' notices.
# 4   - StickIntelligence class' notices.
# 127 - All debugging levels at the same time.
#
log = getLogger( 127, os.path.basename( __file__ ) )

# Later, use `log.log_level = 0` to disable the debugger, or change the level.
log( 1, "Debugging" )
log( 1, "..." )
log( 1, "..." )
```

If you want to reload the debug tools code on the fly, you can use this to import it:
```
import imp
from python_debug_tools.debug_tools import getLogger

imp.reload( python_debug_tools.debug_tools )
from python_debug_tools.debug_tools import getLogger
```




