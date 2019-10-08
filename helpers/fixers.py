import re

RULES = {
    '*': {
        r"'": r'',
        r'>/': r'/>',
        r'_': r'-',
        r'\|\(\|\)': r'',
        r'\[<([\-a-zA-Z0-9]+?)\]': r'[<\1>]',
        r'\<([a-z]+)\s+([a-z]+)\>': r'<\1-\2>',
        r'\<([a-z]+)\s([a-z]+)\s+([a-z]+)\>': r'<\1-\2-\3>',
        r'\\--': r'',
    },
    'add': {
        r'--chmod=\(\+\|-\)x': r'--chmod=(<=+x>|<=-x>)',
    },
    'archimport': {
        r'<archive/branch>\[:<git-branch>\] ...': r'<archive/branch:git-branch>...',
    },
    'blame': {
        r'<rev>\.\.<rev>': r'<rev..rev>',
    },
    'config': {
        r'name-regex': r'<name-regex>',
        r'value-regex': r'<value-regex>',
        r'default': r'<default>',
        r'stdout-is-tty': r'<stdout-is-tty>',
        r'URL': r'<URL>',
        r'new-name': r'<new-name>',
        r'old-name': r'<old-name>',
        r' name': r' <name>',
        r' value': r' <value>',
        r'value ': r'<value> ',
    },
    'stash': {
        r'\[push (.*)\]': r'push \1',
    },
    'push': {
        r'\(true\|false\|if-asked\)': r'<=true|=false|=if-asked>',
    },
    'range-diff': {
        r'<range1> <range2>': r'<range1 range2>',
        r'<rev1>\.\.\.<rev2>': r'<rev1...rev2>',
        r'<base> <rev1> <rev2>': r'<base rev1 rev2>',
    },
    'pack-redundant': {
        r'\< --all \| \.pack filename \.\.\. \>': r'( --all | <.pack-filename>... )',
    },
    'show-branch': {
        r'\(-g\|--reflog\)\[=<n>\[,<base>\]\]': r'(-g [<n>[<base>]]|--reflog [<n> [<base>]])',
    },
    'send-pack': {
        r'<host>:': r'<host>',
    },
}


def regex_replace(s, command=None):
    for target, rules in RULES.items():
        for rule, after in rules.items():
            if command == target or target == '*':
                s = re.sub(rule, after, s)
    return s
