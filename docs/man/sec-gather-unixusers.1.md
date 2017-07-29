% SEC-GATHER-UNIXUSERS(1)
% Ferry Boender
% May 2017

<!---
Convert with pandoc to Groff man format:

pandoc this.md -s -t man > this.1
--->

# NAME

sec-gather-unixusers – Output unix users and their details

# SYNOPSIS

 **sec-gather-unixusers** [**-h**] [**--version**] [**--debug**] [**--format** *{json,html}*] [**--login**]

# DESCRIPTION

**sec-gather-unixusers** gathers information about unix user accounts from
`/etc/passwd` and their details (such as groups) and outputs it in a variety
of formats.

# OPTIONS

**-h**, **--help**
:   Display this help message and exit

**--version**
:   show program's version number and exit

**--debug**
:   Show debug info

**--format** *{json,text,html}*
:   Output format. Default is "*text*"

**--login**
:   Only users that can log in

# EXAMPLES

    $ sec-gather-unixusers --login

    {
        "unixusers": {
            "root": {
                "shell": "/bin/bash", 
                "homedir": "/root", 
                "groups": [
                    "root"
                ]
            }, 
            "fboender": {
                "shell": "/bin/bash", 
                "homedir": "/home/fboender", 
                "groups": [
                    "fboender", 
                    "adm", 
                    "cdrom", 
                    "sudo", 
                    "dip", 
                    "plugdev", 
                    "lpadmin", 
                    "sambashare", 
                    "docker"
                ]
            }
        }
    }