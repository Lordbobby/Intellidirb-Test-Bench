import os
import sys
from argparse import ArgumentParser
from os import listdir
from os.path import join, isfile, exists

import pandas as pd
from art import tprint


class CustomParser(ArgumentParser):
    def error(self, message):
        sys.stdout.write(f'Error: {message}\n\n')
        self.print_help()
        sys.exit(2)

def print_header():
    tprint('Run Grapher', 'tarty1')
    print()

def setup_argument_parser():
    arg_parser: ArgumentParser = CustomParser()

    arg_parser.add_argument('-d', dest='directory', required=True, help='Directory to read run from.')
    arg_parser.add_argument('-o', dest='out_dir', required=True, help='Directory to write graph to.')

    return arg_parser

def get_run_results_for_mode(directory, mode):
    results = {}

    for index in range(1, 10):
        file_path = join(directory, f'out_{mode}_site{index}_1.txt')
        df = pd.read_csv(file_path, names=['Time', 'Type', 'Parser', 'StatusCode', 'Size', 'URL'])
        start_time = int(df[df.Type == 'Start']['Time'][0])
        df['Time'] = df['Time'].apply(lambda t: int(t) - start_time)
        finish_time = int(df[df.Type == 'Finish']['Time'].reset_index(drop=True)[0])
        df = df[df.Type == 'Response']
        df['TimeOfFinish'] = df['Time'].apply(lambda t: int(t) / finish_time)
        df['Time'] = df['Time'].apply(lambda t: t / 1e9)
        df['Total'] = range(len(df))

        results[f'Site {index}'] = df

    return results

def generate_run_graph(all_runs, dict_runs, graphs):
    for i in range(1, 10):
        summary_ax = all_runs[f'Site {i}'].plot.line(x='Time', y='Total', ylabel='Total Valid Responses', title=f'Site {i}')
        dict_runs[f'Site {i}'].plot.line(ax=summary_ax, x='Time', y='Total')

        summary_ax.legend(['Enhanced', 'Dictionary'])

        graphs[f'site{i}_run_over_time'] = summary_ax


def graph_data(directory, out_dir):
    all_runs = get_run_results_for_mode(directory, 'all')
    dict_runs = get_run_results_for_mode(directory, 'dict')

    if not exists(out_dir):
        os.makedirs(out_dir)

    graphs = {}

    generate_run_graph(all_runs, dict_runs, graphs)

    for name, graph in graphs.items():
        fig = graph.get_figure()
        out_file = join(out_dir, f'{name}.jpg')

        fig.savefig(out_file)

if __name__ == '__main__':
    print_header()

    parser = setup_argument_parser()
    parsed_args = parser.parse_args()

    graph_data(parsed_args.directory, parsed_args.out_dir)