% SEC-GATHER-LISTENPORTS(1)
% Ferry Boender
% May 2017

# NAME

sec-gather-listenports – Output listening ports

# SYNOPSIS

 **sec-gather-listenports** [**-h**] [**--version**] [**-d**] [**--annotate** *ANNOTATIONFILE*] [**--no-udp**] [**--no-local**] [**--no-verified**]

# DESCRIPTION

**sec-gather-listenports** outputs listening TCP/UDP ports on the current machine.

# OPTIONS

**-h**, **--help**
:   Display this help message and exit

**--version**
:   show program's version number and exit

**-d** / **--debug**
:   Show debug info

**--annotate** *ANNOTATIONFILE*
:   Annotation file. A JSON file who's information will be joined with the gathered results. This can be used to add custom information to results.

**--no-udp**
:   Do not include UDP ports.

**--no-verified**
:   Do not include verified services (as read from the annotations file)

**--no-local**
:   Do not include services listening on 127.0.0.1

# EXAMPLES

The default output looks like this:

    $ sec-gather-listenports
    {
        "listenports": {
            "8000": {
                "pid": 30925, 
                "remote_address": "0.0.0.0", 
                "recv_queue": 0, 
                "verified": false, 
                "service": "Unknown", 
                "remote_port": 0, 
                "proto": "tcp", 
                "local_port": 8000, 
                "state": "LISTEN", 
                "prog": "python2.7", 
                "local_address": "127.0.0.1", 
                "send_queue": 0
            }, 
            "25": {
                "pid": null, 
                "remote_address": "::", 
                "recv_queue": 0, 
                "verified": false, 
                "service": "Unknown", 
                "remote_port": 0, 
                "proto": "tcp6", 
                "local_port": 25, 
                "state": "LISTEN", 
                "prog": null, 
                "local_address": "::", 
                "send_queue": 0
            }
        }
    }

we can annotate the results by passing an annotation file. That file would
look something like:

    {
        "listenports": {
            "8000": {
                "verified": true,
                "comment": "Local python dev server"
            }
        }
    }

Calling **sec-gather-listenports** with the *--annotate* option:

    $ sec-gather-listenports --annotate listenports_annotate.json

Would result in the *verified* and *comment* fields to be added to port 8000:

    {
        "listenports": {
            "8000": {
                "pid": 30925, 
                "remote_address": "0.0.0.0", 
                "recv_queue": 0, 
                "verified": false, 
                "service": "Unknown", 
                "remote_port": 0, 
                "proto": "tcp", 
                "local_port": 8000, 
                "state": "LISTEN", 
                "prog": "python2.7", 
                "local_address": "127.0.0.1", 
                "send_queue": 0,
                "verified": true,
                "comment": "Local python dev server"
            }, 
            "25": {
            ...

# COPYRIGHT

Copyright 2017, Ferry Boender.

Licensed under the MIT license. For more information, see the LICENSE file.
