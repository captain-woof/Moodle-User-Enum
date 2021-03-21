# Moodle-User-Enum
A python script that lets you dump the entire personal user data (short of the passwords)  or search for a particular user, by taking advantage of the fact that Moodle is vulnerable to a simple user enumeration scan by id incrementation, given that you are authenticated.

```
 __  __              _ _       _   _               ___                
|  \/  |___  ___  __| | |___  | | | |___ ___ _ _  | __|_ _ _  _ _ __  
| |\/| / _ \/ _ \/ _` | / -_) | |_| (_-</ -_) '_| | _|| ' \ || | '  \ 
|_|  |_\___/\___/\__,_|_\___|  \___//__/\___|_|   |___|_||_\_,_|_|_|_|

usage: moodle_user_enum.py [-h] -m {S,D} -u URL [-ids ID_RANGE] [-t THREADS] [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  -m {S,D}, --mode {S,D}
                        Search for single user/Dump all users (S/D)
  -u URL, --url URL     Moodle CMS's homepage url (prepended with http/s)
  -ids ID_RANGE, --id_range ID_RANGE
                        ID range to search in (default: '0-10000')
  -t THREADS, --threads THREADS
                        Max number of concurrent threads to use
  -o OUTPUT, --output OUTPUT
                        Output directory ('cur' for current-directory):

```

### Author
***CaptainWoof***

[@realCaptainWoof](https://www.twitter.com/realCaptainWoof)