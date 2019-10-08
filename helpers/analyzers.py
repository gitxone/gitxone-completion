import re
import itertools

RE_PIPE = re.compile(r'\s?\|\s?')


def split(tokens_str: str):
    brackets = []
    token = ''
    tokens = []
    for s in tokens_str:
        if s == ' ' and not brackets:
            tokens += [token.strip()]
            token = ''
            continue
        
        if s == '|' and not brackets:
            tokens += [token.strip(), '|']
            token = ''
            continue

        if s == '*' and not brackets:
            tokens += [token.strip(), '*']
            token = ''
            continue

        token += s
        if s == '(':
            brackets += ['(']
        elif s == '[':
            brackets += ['[']
        elif s == '<':
            brackets += ['<']
        elif s == ')':
            brackets and brackets.pop()
            if not brackets and token[0:1] == '(':
                tokens += [token.strip()]
                token = ''
        elif s == ']':
            brackets and brackets.pop()
            if not brackets and token[0:1] == '[':
                tokens += [token.strip()]
                token = ''
        elif s == '>':
            brackets and brackets.pop()
            if not brackets and token[0:1] == '<':
                tokens += [token.strip()]
                token = ''

    if token:
        tokens.append(token.strip())
    
    while '|' in tokens:
        index = tokens.index('|')
        tokens[index + 1] = '|' + tokens[index + 1]
        del tokens[index]

    while '...' in tokens:
        index = tokens.index('...')
        tokens[index - 1] += '...'
        del tokens[index]

    while '*' in tokens:
        index = tokens.index('*')
        tokens[index - 1] += '*'
        del tokens[index]

    while '' in tokens:
        tokens.remove('')

    return tokens


def parse(token_str: str, depth: int=0, optional: bool=False):
    result = []
    for token in split(token_str):
        pipe = multiple = False
        if token.startswith('='):
            token = token[1:]
        
        if token.startswith('|'):
            pipe = True
            token = token[1:]
        
        if token.endswith('...'):
            multiple = True
            token = token[:-3]

        match = re.match(r'^<(?P<value>.+)>', token)
        if match:
            result += _process_angles(match.groupdict(), depth, optional, multiple, pipe)
            continue

        match = re.match(r'^\[(?P<value>.+)\]$', token)
        if match:
            result += _process_brackets(match.groupdict(), depth, optional, multiple, pipe)
            continue

        match = re.match(r'^\((?P<value>.+)\)(?P<astarisk>\*)?$', token)
        if match:
            result += _process_parentheses(match.groupdict(), depth, optional, multiple, pipe)
            continue

        match = re.match(
            r'^('
            r'(?P<name1>--[a-z0-9]*(\[[\-\|a-z0-9]+\])*[\-a-z0-9]*)(?P<value1>\[?=\S+\]?)?|'
            r'(?P<name2>--[a-z0-9]*(\([\-\|a-z0-9]+\))*[\-a-z0-9]*)(?P<value2>\[?=\S+\]?)?'
            r')$'
            , token)
        if match:
            result += _process_long_option(match.groupdict(), depth, optional, multiple, pipe)
            continue

        match = re.match(
            r'^('
            r'(?P<name1>-\[[\|a-zA-Z0-9]+\])(?P<value1>\[\S+\])?|'
            r'(?P<name2>-[a-zA-Z0-9])(?P<value2>\[\S+\])?|'
            r'(?P<name3>-[a-zA-Z0-9])(?P<value3>\<\S+\>)?'
            r')$', token)
        if match:
            result += _process_short_option(match.groupdict(), depth, optional, multiple, pipe)
            continue

        result += [{
            'keys': [token],
            'values': [''],
            'depth': depth,
            'optional': optional,
            'multiple': [multiple],
            'pipe': pipe,
        }]
    
    return result


def _process_angles(matching_dict: dict, depth: int, optional: bool, multiple: bool, pipe: bool):
    """ e.g. <test>
    """
    values = RE_PIPE.split(matching_dict['value'])
    return [
        {
            'keys': ['' for _ in values],
            'values': values,
            'depth': depth,
            'optional': optional,
            'multiple': [multiple for _ in values],
            'pipe': pipe,
        }
    ]


def _process_brackets(matching_dict: dict, depth: int, optional: bool, multiple: bool, pipe: bool):
    """ e.g. [-t | --test]
    """
    value = matching_dict['value']
    options = parse(value, depth + 1, True)
    if not options:
        return []

    option = {'keys': [], 'values': [], 'depth': depth + 1, 'optional': True, 'multiple': [], 'pipe': pipe}
    result = [option]

    tmp = options[0:1]
    for o in options[1:]:
        if o.get('pipe'):
            tmp.append(o)
        elif all(tmp[-1]['keys']):
            value = o['keys'][0] or o['values'][0] or ''
            
            if value and o['optional'] and o['depth'] > depth + 1:
                value += '?'
            tmp[-1]['values'] = [value for _ in tmp[-1]['values']]
        else:
            result += [o]

    # reducing options to option
    for o in tmp:
        option['keys'] += o['keys']
        option['values'] += o['values']
        option['multiple'] += [True for _ in o['multiple']] if multiple else o['multiple']

    return result


def _process_parentheses(matching_dict: dict, depth: int, optional: bool, multiple: bool, pipe: bool):
    """ e.g. (--test)
    """
    value = matching_dict['value']
    astarisk = bool(matching_dict['astarisk'])

    options = parse(value, depth + 1)
    if not options:
        return []

    option = {'keys': [], 'values': [], 'depth': depth + 1, 'optional': False, 'multiple': [], 'pipe': pipe}
    result = [option]

    tmp = options[0:1]
    for o in options[1:]:
        if o.get('pipe'):
            tmp.append(o)
        elif all(tmp[-1]['keys']):
            value = o['keys'][0] or o['values'][0] or ''
            
            if value and o['optional'] and o['depth'] > depth:
                value += '?'
            tmp[-1]['values'] = [value for _ in tmp[-1]['values']]
        else:
            result += [o]

    # reducing options to option
    for o in tmp:
        option['keys'] += o['keys']
        option['values'] += o['values']
        option['multiple'] += [True for _ in o['multiple']] if multiple else o['multiple']

    if astarisk:
        for o in result:
            o['optional'] = True
    
    return result


def _process_long_option(matching_dict: dict, depth: int, optional: bool, multiple: bool, pipe: bool):
    """ e.g. --test
    """
    name = matching_dict.get('name1') or matching_dict.get('name2')
    value = matching_dict.get('value1') or matching_dict.get('value2')
    nullable = ''
    if value and value[0] == '[' and value[-1] == ']':
        value = value[1:-1]
        nullable = '?'
    if value:
        value = value[1:]

    match1 = re.search(r'\[([\-\|a-zA-Z0-9]+)\]', name)
    match2 = re.search(r'\(([\-\|a-zA-Z0-9]+)\)', name)

    if match1:
        target = match1.group()
        replaces = ['', *RE_PIPE.split(match1.group(1))]
    elif match2:
        target = match2.group()
        replaces = RE_PIPE.split(match2.group(1))
    else:
        target = 'NO-REPLACING'
        replaces = [target]

    result = []
    for i, rep in enumerate(replaces):
        key = name.replace(target, rep)
        if key in {'--', ''}:
            continue

        option = {
            'keys': [key],
            'values': [''],
            'multiple': [multiple],
            'depth': depth,
            'optional': optional,
            'pipe': pipe or i >= 1,
        }

        if not value:
            result += [option]
        else:
            result += [
                {
                    **option,
                    'keys': option['keys'] * len(o['values']),
                    'values': [f'{v}{nullable}' for v in o['values']],
                    'multiple': option['multiple'] * len(o['values']),
                } 
                for o in parse(value, depth)
            ]
    return result


def _process_short_option(matching_dict: dict, depth: int, optional: bool, multiple: bool, pipe: bool):
    """ e.g. -T
    """
    name = matching_dict.get('name1') or matching_dict.get('name2') or matching_dict.get('name3')
    value = matching_dict.get('value1') or matching_dict.get('value2') or matching_dict.get('value3')
    
    nullable = ''
    if value and value[0] == '[' and value[-1] == ']':
        value = value[1:-1]
        nullable = '?'

    match = re.search(r'\[([\-\|a-zA-Z0-9]+)\]', name)
    if match:
        target = match.group()
        replaces = RE_PIPE.split(match.group(1))
    else:
        target = 'NO-REPLACING'
        replaces = [target]

    result = []
    for i, rep in enumerate(replaces):
        key = name.replace(target, rep)
        if key in {'-', ''}:
            continue

        option = {
            'keys': [key],
            'values': [''],
            'depth': depth,
            'optional': optional,
            'multiple': [multiple],
            'pipe': pipe or i >= 1,
        }

        if not value:
            result += [option]
        else:
            result += [
                {
                    **option,
                    'keys': option['keys'] * len(o['values']),
                    'values': [f'{v}{nullable}' for v in o['values']],
                    'multiple': option['multiple'] * len(o['values']),
                } 
                for o in parse(value, depth)
            ]
    return result
