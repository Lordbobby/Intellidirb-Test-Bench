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
    tprint('Grapher', 'tarty1')
    print()

def setup_argument_parser():
    arg_parser: ArgumentParser = CustomParser()

    arg_parser.add_argument('-d', dest='directory', required=True, help='Directory to read summaries from.')

    return arg_parser

def get_summary_results(directory):
    file_path =  join(directory, 'summary.csv')
    df = pd.read_csv(file_path, header=0)

    for index in range(1, 10):
        df = df.replace(f'site{index}', f'Site {index}')

    df = df.replace('all', 'Enhanced')
    df = df.replace('dict', 'Dictionary')

    return df

def generate_total_exec_graph(summary, graphs):
    exec_times = summary[['Mode', 'Site', 'Total Time']]

    exec_times = exec_times.pivot(columns='Mode', index='Site')

    exec_time_ax = exec_times.plot.bar(title='Total Execution Time By Site And Mode', ylabel='Total Execution Time (min)')
    exec_time_ax.legend(['Dictionary', 'Enhanced'])

    graphs['exec_times'] = exec_time_ax

def generate_total_exec_diff_graph(summary, graphs):
    exec_times = summary[['Mode', 'Site', 'Total Time']]
    exec_times = exec_times.pivot(columns='Site', index='Mode')

    exec_times.loc['Difference'] = exec_times.loc['Dictionary'] - exec_times.loc['Enhanced']

    exec_times = pd.DataFrame({'Site': [f'Site {i}' for i in range(1, 10)], 'Difference': exec_times.loc['Difference']})
    exec_time_ax = exec_times.plot.bar(title='Difference in Execution Time (Dictionary - Enhanced)', ylabel='Difference (min)', x='Site', legend=False)

    for p in exec_time_ax.patches:
        height = 1

        if p.get_height() > 0:
            height = -8

        coords = (p.get_x(), height)

        exec_time_ax.annotate(f'{p.get_height():.1f}', coords)

    graphs['exec_time_diffs'] = exec_time_ax

def generate_total_valid_by_parser(summary, graphs):
    summary = summary[summary.Mode == 'Enhanced']
    summary['Dictionary'] = summary['Dict Valid Responses']
    summary['Service'] = summary['Service Valid Responses']
    summary['Content'] = summary['Href Valid Responses'] + summary['Src Valid Responses'] + summary['Link Valid Responses'] + summary['Redirect Valid Responses'] + summary['Index Valid Responses']
    summary['Script'] = summary['Script Valid Responses']
    summary = summary[['Site', 'Dictionary', 'Service', 'Content', 'Script']]

    summary_ax = summary.plot.bar(x='Site', stacked=True, title='Total Valid Responses by Parser Type')

    graphs['valid_by_parser'] = summary_ax

def generate_total_valid_by_parser_no_index(summary, graphs):
    summary = summary[summary.Mode == 'Enhanced']
    summary['Dictionary'] = summary['Dict Valid Responses']
    summary['Service'] = summary['Service Valid Responses']
    summary['Content'] = summary['Href Valid Responses'] + summary['Src Valid Responses'] + summary['Link Valid Responses'] + summary['Redirect Valid Responses']
    summary['Script'] = summary['Script Valid Responses']
    summary = summary[['Site', 'Dictionary', 'Service', 'Content', 'Script']]

    summary_ax = summary.plot.bar(x='Site', stacked=True, title='Total Valid Responses by Parser Type Without Index')

    graphs['valid_by_parser_no_index'] = summary_ax

def graph_data(directory):
    summary = get_summary_results(directory)
    print(summary)
    out_dir = join(directory, 'graphs')

    if not exists(out_dir):
        os.makedirs(out_dir)

    graphs = {}

    generate_total_exec_graph(summary, graphs)
    generate_total_exec_diff_graph(summary, graphs)
    generate_total_valid_by_parser(summary, graphs)
    generate_total_valid_by_parser_no_index(summary, graphs)

    for name, graph in graphs.items():
        fig = graph.get_figure()
        out_file = join(out_dir, f'{name}.jpg')

        fig.savefig(out_file)

if __name__ == '__main__':
    print_header()

    parser = setup_argument_parser()
    parsed_args = parser.parse_args()

    graph_data(parsed_args.directory)