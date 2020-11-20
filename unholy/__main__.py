import logging

import typechecker
import unholy

if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('file', metavar='FILE', type=open)
    p.add_argument('-o', '--output', metavar='FILE', type=str, default='-', dest='output')
    p.add_argument('-q', '--quiet', '--stfu', default=0, action='count', dest='quiet')
    p.add_argument('--safe', action='store_true', dest='safe',
                   help='Enables debugging types returned by functions in the transpiler. Leads to slight slow down of '
                        'the compilation but gives more detailed error information where possible.')
    program_arguments = p.parse_args()
    typechecker.enable_typecheck = not program_arguments.safe

    if program_arguments.file:
        logging.basicConfig(format='%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)s] %(message)s',
                            level=(logging.INFO if program_arguments.quiet else logging.DEBUG))
        result = unholy.jsify(''.join(program_arguments.file.readlines()))
        if program_arguments.output == '-':
            print(result[0].compile([]))
        else:
            with open(program_arguments.output, 'w') as f:
                f.write(unholy.START_COMMENT)
                f.write(result[0].compile([]))

            if program_arguments.quiet < 2:
                print(f'Written result to {program_arguments.output}')
