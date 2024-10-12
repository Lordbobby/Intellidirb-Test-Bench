import subprocess
import sys
from argparse import ArgumentParser
from datetime import datetime
from threading import Thread

from art import tprint


class CustomParser(ArgumentParser):
    def error(self, message):
        sys.stdout.write(f'Error: {message}\n\n')
        self.print_help()
        sys.exit(2)

def print_header():
    tprint('TestBench', 'tarty1')
    print()

def setup_argument_parser():
    arg_parser: ArgumentParser = CustomParser()

    arg_parser.add_argument('-w', dest='wordlist', required=True, help='Wordlist file.')
    arg_parser.add_argument('-t', dest='target_file', required=True, help='File containing list of targets.')
    arg_parser.add_argument('-o', dest='out_dir', required=True, help='Directory to write out to.')
    arg_parser.add_argument('-x', dest='exec_dir', required=True, help='Directory of the intellidirb.py script.')
    arg_parser.add_argument('-i', dest='iterations', type=int, default=10, help='Number of times to run each mode against each target.')

    return arg_parser

def get_targets(target_filepath):
    with open(target_filepath, 'r') as file:
        words = []
        line = file.readline()

        while line:
            words.append(line.rstrip())

            line = file.readline()

        return words

def thread_runner(cmd, transcript_file_path, target):
    with open(transcript_file_path, 'w') as transcript:
        process_start = datetime.now()
        result = subprocess.call(cmd, stdout=transcript)

        process_elapsed = datetime.now() - process_start

        print(f'{target} finished in {process_elapsed} with status code {result}.')

def run_test(cmd, transcript_file_path, target):
    thread = Thread(target=thread_runner, args=(cmd, transcript_file_path, target))
    thread.start()

    return thread

def run_testbench(args):
    wordlist_file = args.wordlist
    target_file = args.target_file
    out_dir = args.out_dir
    exec_dir = args.exec_dir
    iterations = args.iterations

    targets = get_targets(target_file)
    dirb_script = f'{exec_dir}/intellidirb.py'

    modes = ['dict', 'content', 'service', 'script', 'all']

    for iteration in range(iterations):
        print(f'==== Iteration #{iteration} ====\n')
        for mode in modes:
            print(f'==== Testing mode {mode} ====\n')

            threads = []

            for target in targets:
                site = target.replace('/', '')[-1:]
                out_name = f'out_{site}_{mode}_{iteration}.txt'
                transcript_path = f'{out_dir}/transcript_{site}_{mode}_{iteration}.txt'
                cmd = f'python {dirb_script} {target} -m {mode} -o {out_dir}/{out_name} -w {wordlist_file} -x txt,html,php'

                thread = run_test(cmd, transcript_path, target)

                threads.append(thread)

            for thread in threads:
                thread.join()



if __name__ == '__main__':
    print_header()

    parser = setup_argument_parser()
    parsed_args = parser.parse_args()
    start = datetime.now()

    run_testbench(parsed_args)

    elapsed = datetime.now() - start

    print(f'Testbench complete in {elapsed}.')