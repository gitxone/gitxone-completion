#!/usr/bin/env python
from collections import defaultdict

import jinja2

import texts
import fixers
import analyzers

COMMANDS_TEMPLATE = './templates/commands.go.txt'
COMMANDS_OUTPUT = '../commands.go'

OPTIONS_TEMPLATE = './templates/options.go.txt'
OPTIONS_OUTPUT = '../options.go'


def render_commands():
    commands_dict = texts.get()
    with open(COMMANDS_TEMPLATE) as f:
        template = jinja2.Template(f.read())
    
    context = {
        'commands': [
            command
            for command, args in commands_dict.items()
            if args
        ],
    }
    code = template.render(context)
    
    with open(COMMANDS_OUTPUT, 'w') as f:
        f.write(code)


def render_options():
    commands_dict = texts.get()
    options_dict = {}
    for command, args in commands_dict.items():
        if not args:
            continue

        options_dict[command] = options = []
        serial = 0
        group_keys = defaultdict(set)
        for group, arg in enumerate(args):
            text = fixers.regex_replace(arg, command)
            tmp = analyzers.parse(text)
            for order, o in enumerate(tmp):
                options += [{**o, 'group': group, 'order': order, 'serial': serial}]
                serial += 1
                group_keys[group].update(o['keys'])

        for option in options:
            invalid_serials = set()
            for group, keys in group_keys.items():
                if not keys.issuperset(option['keys']):
                    invalid_serials.update({
                        o['serial']
                        for o in options
                        if o['group'] == group
                    })
            option['invalid_serials'] = invalid_serials

    with open(OPTIONS_TEMPLATE) as f:
        template = jinja2.Template(f.read())

    context = {'options_dict': options_dict}
    code = template.render(context)
    with open(OPTIONS_OUTPUT, 'w') as f:
        f.write(code)


if __name__ == '__main__':
    render_commands()
    render_options()

