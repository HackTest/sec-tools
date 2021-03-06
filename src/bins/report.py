import sys
import os
import argparse
import logging
import json
import socket

import binlink
import tools
import common
import morestd


def get_tpl_dirs(args):
    """
    Construct a list of directories in which to look for templates.
    """
    tpl_dirs = []

    # User specified dirs
    if args.tpl_dirs is not None:
        tpl_dirs.extend(args.tpl_dirs.split(','))

    # Current dir
    tpl_dirs.append(".")

    # 'report' dir relative to executable
    tpl_dirs.append(
        os.path.join(
            tools.abs_real_dir(sys.argv[0]),
            "reports"
        )
    )

    return tpl_dirs

@binlink.register("sec-report")
def cmdline(version):
    parser = argparse.ArgumentParser(description='Generate reports')
    common.arg_add_defaults(parser, version=version, annotate=True)
    parser.add_argument('--tpl-dirs',
                        dest="tpl_dirs",
                        action='store',
                        default=None,
                        help="Extra template dirs")
    parser.add_argument('--title',
                        dest="title",
                        action='store',
                        default=None,
                        help="Title for the report")
    parser.add_argument('--hostname',
                        dest="hostname",
                        action='store',
                        default=None,
                        help="Hostname the report is about")
    parser.add_argument('report',
                        metavar='REPORT',
                        type=str,
                        help='Mako report template')
    parser.add_argument('assets',
                        metavar='ASSETS',
                        type=str,
                        default=None,
                        nargs='*',
                        help='JSON files to be made accessible to the report.')
    args = parser.parse_args()
    common.configure_logger(args.debug)

    # data will hold all collected data (stdin, assets)
    data = {}

    # Check whether there is data on stdin
    if not sys.stdin.isatty():
        morestd.data.deepupdate(data, json.load(sys.stdin))

    # Load any data from assets provided
    for asset in args.assets:
        try:
            morestd.data.deepupdate(data, json.load(open(asset, 'r')))
        except ValueError as err:
            sys.stderr.write("Error loading asset '{}': {}\n".format(asset, err))
            if args.debug is True:
                raise
            sys.exit(1)

    # Set hostname to current host if not specified
    if args.hostname is None:
        args.hostname = socket.getfqdn()

    # Construct additional template lookup dirs
    tpl_dirs = get_tpl_dirs(args)

    logging.info("Extra template lookup dirs: {}".format(tpl_dirs))
    # User-provided dirs
    if args.tpl_dirs is not None:
        tpl_dirs.extend(args.tpl_dirs.split(','))

    # Render and output template
    sys.stdout.write(tools.tpl_file(args.report,
                                    extra_tpl_dirs=tpl_dirs,
                                    data=data,
                                    title=args.title,
                                    hostname=args.hostname))
