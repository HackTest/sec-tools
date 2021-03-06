import os
import sys
import argparse
import logging
import json

import binlink
import tools
import common


text_tpl = """\
% for change in changes:
<%
path_text = " -> ".join(change["path"])
%>
% if change["action"] == 'added':
  - Added to "${path_text}":\

    % if change["type"] == 'dict':
    ${format_value({change["key"]:change["value"]})}
    % else:
    ${format_value(change["value"])}
    % endif

% elif change["action"] == 'removed':
  - Removed from "${path_text}":\

    % if change["type"] == 'dict':
    ${format_value({change["key"]:change["value"]})}
    % else:
    ${format_value(change["value"])}
    % endif

% elif change["action"] == 'changed':
  - Changed for "${path_text}"\

    from:

      ${format_value(change["old_value"])}

    to:

      ${format_value(change["new_value"])}
% endif
% endfor
"""

html_tpl = """\
<ul>
% for change in changes:
    <%
    path_html = "&rarr; ".join(change["path"])
    %>
    <li>
        % if change["action"] == "added":
            <b>Added</b> to
            <code>${path_html}</code>:
            % if change["type"] == 'dict':
            <b>${change["key"]}</b>
            % endif
            <code>${change["value"]}</code>.
        % elif change["action"] == "removed":
            <b>Removed</b> from
            <code>${path_html}</code>:
            % if change["type"] == 'dict':
            <b>${change["key"]}</b>
            % endif
            <code>${change["value"]}</code>.
        % elif change["action"] == "changed":
            <b>Changed</b> for
            <code>${path_html}</code> from
            % if change["type"] == 'dict':
            <b>${change["key"]}</b>
            % endif
            <code>${change["old_value"]}</code> to
            <code>${change["value"]}</code>.
        % endif
    </li>
% endfor
</ul>
"""


def format_value(value, left_indent=2):
    """
    Return a pretty version of `value` (list, dict, etc) with indenting.
    """
    pretty = json.dumps(value, indent=2)
    if type(value) == dict:
        pretty = pretty.lstrip('{').rstrip('}')
    pretty_indent = pretty.replace("\n", "\n" + left_indent * ' ')
    return pretty_indent


def diff_list(old, new, cur_path=[]):
    """
    Compare two lists and return a list of additions and deletions in the old
    and new list.

    We don't need to recurse into the lists, because Python can deep-compare
    lists automatically.
    """
    changes = []

    # Go through new values, figure out what's been added
    for i in range(len(new)):
        new_v = new[i]
        logging.debug("Checking if {}::'{}' has been added.".format(cur_path,
                                                                    new_v))

        if new_v not in old:
            changes.append(
                {
                    "action": "added",
                    "type": "list",
                    "path": cur_path,
                    "value": new_v
                }
            )

    # Go through old values, figure out what's been removed
    for i in range(len(old)):
        old_v = old[i]
        logging.debug("Checking if {}::'{}' has been removed.".format(cur_path,
                                                                      old_v))

        if old_v not in new:
            changes.append(
                {
                    "action": "removed",
                    "type": "list",
                    "path": cur_path,
                    "value": old_v
                }
            )

    return changes


def diff_dict(old, new, cur_path=[]):
    """
    Compare two dicts and return a list of key additions and deletions in the
    old and new dict. For any keys that haven't changed between the dicts, we
    recurse into those keys to do a deep compare.

    Returns a flat list of changes, where each entry in the list is a dict that
    looks like:

        {
            "action": "added/deleted",
            "type": "dict",
            "path": ["groups", "students", "firstyear"],
            "key": "John McFirstyearStudent",
            "value": {"firstname": "John", .....etc}
        }
    """
    changes = []

    logging.debug("diff_dict: cur path: {}".format(cur_path))
    logging.debug("keys in old: {}".format(old.keys()))
    logging.debug("keys in new: {}".format(new.keys()))

    added_keys = set(new.keys()) - set(old.keys())
    removed_keys = set(old.keys()) - set(new.keys())
    same_keys = set(old.keys()).intersection(set(new.keys()))

    logging.debug("diff_dict: added keys: {}".format(added_keys))
    logging.debug("diff_dict: same keys: {}".format(same_keys))
    logging.debug("diff_dict: removed keys: {}".format(removed_keys))

    for added_key in added_keys:
        added_value = new[added_key]
        changes.append(
            {
                "action": "added",
                "type": "dict",
                "path": cur_path,
                "key": added_key,
                "value": added_value
            }
        )

    for removed_key in removed_keys:
        removed_value = old[removed_key]
        changes.append(
            {
                "action": "removed",
                "type": "dict",
                "path": cur_path,
                "key": removed_key,
                "value": removed_value
            }
        )

    # Go through keys that are in both old and new, and recurse into them if
    # required.
    for same_key in same_keys:
        new_v = new[same_key]
        old_v = old[same_key]
        if type(new_v) == list:
            # Recurse
            changes.extend(diff_list(old_v,
                                     new_v,
                                     cur_path=cur_path + [same_key]))
        elif type(new_v) == dict:
            # Recurse
            changes.extend(diff_dict(old_v,
                                     new_v,
                                     cur_path=cur_path + [same_key]))
        elif new_v != old_v:
            # Value has changed
            changes.append(
                {
                    "action": "changed",
                    "type": "dict",
                    "path": cur_path + [same_key],
                    "key": same_key,
                    "old_value": old_v,
                    "new_value": new_v
                }
            )

    return changes


def diff(old, new, cur_path=[]):
    """
    Compare two python dicts or lists and return their difference.
    """
    if type(new) == list:
        return diff_list(old, new, cur_path)
    elif type(new) == dict:
        return diff_dict(old, new, cur_path)


def exclude_match(change, match):
    """
    Check if the path in `match` matches the path in `change`.

    Return True if `match` matches the path of `change`. Otherwise return
    `False`.
    """
    change_path = change['path']
    for change_index in range(len(match)):
        try:
            if match[change_index] == '*':
                # Match any key. Compare the rest.
                continue
            elif match[change_index] != change_path[change_index]:
                # Paths are not the same, so it doesn't match
                return False
        except IndexError:
            return False

    return True


def exclude_list(change, matches):
    """
    Apply a list of matches to a change. If any of them match, return True.
    Otherwise, return False.
    """
    for match in matches:
        if exclude_match(change, match):
            return True
    return False


@binlink.register("sec-diff")
def cmdline(version):
    formats = ['json', 'text', 'html']
    parser = argparse.ArgumentParser(
        description='Diff JSON from stdin against JSON from file.'
    )
    common.arg_add_defaults(parser, version=version, annotate=True)
    parser.add_argument('--format',
                        dest="format",
                        choices=formats,
                        type=str,
                        default="text",
                        help="Output format")
    parser.add_argument('--exclude',
                        dest="exclude",
                        type=str,
                        help="Exclude keys")
    parser.add_argument('--include-init',
                        dest="include_init",
                        action="store_true",
                        default=False,
                        help="Output initial results as 'added'")
    parser.add_argument('statefile',
                        metavar='STATEFILE',
                        type=str,
                        help='File on disk to check stdin against.')
    args = parser.parse_args()
    common.configure_logger(args.debug)

    if not os.path.exists(args.statefile) and \
       args.include_init is False:
        # First time diff, write previous scan to disk
        with open(args.statefile, 'w') as f:
            f.write(sys.stdin.read())
        sys.exit(0)

    # Compare old from disk with new from stdin
    try:
        old_c = json.load(open(args.statefile, 'r'))
    except FileNotFoundError:
        if args.include_init is True:
            old_c = {}
        else:
            raise
    except ValueError as err:
        sys.stderr.write("Invalid state file '{}': {}\n".format(args.statefile, err))
        sys.exit(1)

    new_c = json.load(sys.stdin)
    changes = diff(old_c, new_c)

    # filter out changes
    if args.exclude:
        # build a list of exclude paths
        exclude_paths = []
        filtered_changed = []
        for exclude in args.exclude.split(','):
            exclude_path = exclude.split('.')
            exclude_paths.append(exclude_path)

        # Test each change to see if its path (e.g. listenports -> 53 -> proto)
        # is in the exclude list. Replaces original `changes` list.
        filtered_changes = []
        for change in changes:
            if not exclude_list(change, exclude_paths):
                filtered_changes.append(change)
        changes = filtered_changes

    if args.format == 'json':
        sys.stdout.write(json.dumps(changes))
        sys.stdout.write("\n")
    elif args.format == 'text':
        sys.stdout.write(tools.tpl_str(text_tpl,
                                       changes=changes,
                                       format_value=format_value))
    elif args.format == 'html':
        sys.stdout.write(tools.tpl_str(html_tpl, changes=changes))

    # Write new contents to key file.
    with open(args.statefile, 'w') as f:
        json.dump(new_c, f, indent=4)
