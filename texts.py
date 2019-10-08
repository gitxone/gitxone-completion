import pathlib
import re

DOCS_PATH = pathlib.Path('./git/Documentation/')


def extract(f, command):
    flag = 0
    for l in f:
        if flag == 0 and l.rstrip() == 'SYNOPSIS':
            flag += 1
        if flag == 1 and l.rstrip() == '--------':
            flag += 1
        if flag == 2 and l.rstrip() == '[verse]':
            flag += 1
        if flag == 3:
            break
    else:
        return None
    
    args_list = []

    args = None
    for l in f:
        match1 = re.search(r"^'git .+?' (.+)", l)
        match2 = re.search(r"^\s+(.+)", l)
        
        if match1:
            if args:
                args_list.append(args)
            args = match1.group(1)
        elif match2:
            args += match2.group(1)
        else:
            if args:
                args_list.append(args)
            break

    return args_list


def get():
    args_dict = {}
    for p in DOCS_PATH.glob('git-*.txt'):
        command = re.search(r'git-(.*).txt', p.name).group(1)
        with p.open() as f:
            args_list = extract(f, command)
        args_dict[command] = args_list
    return args_dict


if __name__ == '__main__':
    pass
