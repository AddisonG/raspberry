# Raspberry Pi

## Running the code

Fuck python package managment. It enforces a structure that means importing packages from anywhere except sub-directories is impossible to do without hacky fixes, such as:

```
PYTHONPATH=/path/to/raspberry
```
 - Does not work with sudo
 - Separate code and config = confusion
 - Feels hacky

```
import sys
sys.path.append('/path/to/raspberry')
```
 - Impossible to adhere to pep8 or flake8
 - Risky to use relative paths (they fail if the script is run from elsewhere)
 - Impossible to predict absolute paths (code could be cloned anywhere)
 - Fugly
 - Feels hacky

or even:
```
from ....my_other_package import
from ...my_package import
```
 - Okay, it's not that bad, but...
 - Fuck you. IT FEELS HACKY

The above are all blasphemous, and I will not have it in my codebase. Imports should always look the same. Furthermore, code should be able to be run from any directory, wherever it is run from.

If you want this code to work, you'll have to install my code as a package.

You can install it to one of the places on your python path, such as:
 - `~/.local/lib/python3.7/site-packages/`
 - `/usr/lib/python3/dist-packages`

Find your path with:
```
import sys
print(sys.path)
```

I recommend doing this with symlinks:
```
sudo ln -siT /path/to/raspberry/projects/discord_bot /usr/lib/python3/dist-packages/discord_bot
sudo ln -siT /path/to/raspberry/projects/daemonizer /usr/lib/python3/dist-packages/daemonizer
sudo ln -siT /path/to/raspberry/projects/local_utilities /usr/lib/python3/dist-packages/local_utilities
```

With this, these packages are able to be used by each other, and any other python code which may want to


## Getting services to work (enable/disable)

You'll need to run the enable command as root. Also see `/etc/systemd/system/`.
