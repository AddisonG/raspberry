# Raspberry Pi

## Running the code

Install the python packages with the interactive installer. Some depend on each other, so it's wise to install all of them.

```
./install --install / --uninstall
```

## Getting services to work (enable/disable)

You'll need to run the enable command as root. Also see `/etc/systemd/system/`.


## Rant

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
 - It doesn't work between packages
 - Lots of `ImportError: attempted relative import with no known parent package`
 - Feels hacky

The above are all blasphemous, and I will not have them in my codebase. Imports should always look the same. Furthermore, code should work flawlessly regardless of the cwd.

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

With this, these packages are able to be used by each other, and by other packages too.
