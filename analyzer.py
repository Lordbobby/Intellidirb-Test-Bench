import sys
from argparse import ArgumentParser
from art import tprint
from os import listdir
from os.path import isfile, join

class CustomParser(ArgumentParser):
    def error(self, message):
        sys.stdout.write(f'Error: {message}\n\n')
        self.print_help()
        sys.exit(2)

def print_header():
    tprint('Analyzer', 'tarty1')
    print()

def setup_argument_parser():
    arg_parser: ArgumentParser = CustomParser()

    arg_parser.add_argument('-d', dest='directory', required=True, help='Directory to read results from.')
    arg_parser.add_argument('-o', dest='out_dir', required=True, help='Directory to output analysis into.')

    return arg_parser

class Stat:
    def __init__(self):
        self.valid = 0
        self.total = 0

class RunSummary:
    def __init__(self):
        self.requests = Stat()
        self.total_min = 0
        self.parser_stats = {
            'Dict': Stat(),
            'Link': Stat(),
            'Href': Stat(),
            'Service': Stat(),
            'Redirect': Stat(),
            'Index': Stat(),
            'Src': Stat(),
            'Script': Stat(),
        }

class RunData:
    def __init__(self, input_file):
        details = input_file.split('\\')[-1].split('.')[0].split('_')

        self.site = details[2]
        self.mode = details[1]
        self.iteration = details[3]
        self.start = 0
        self.responses = {}
        self.summary = RunSummary()

    def add_response(self, time, parser_type, status_code, url):
        time = time - self.start
        self.responses[url] = (time, parser_type, status_code)

    def set_finish(self, total, valid, total_min):
        self.summary.requests.total = int(total)
        self.summary.requests.valid = int(valid)
        self.summary.total_min = float(total_min)

    def set_parser_stat(self, parser_type, valid, total):
        self.summary.parser_stats[parser_type].valid = valid
        self.summary.parser_stats[parser_type].total = total

def read_data(input_file):
    data = RunData(input_file)

    with open(input_file, 'r') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines]

        for line in lines:
            fields = line.split(',')
            entry_type = fields[1]

            if entry_type == 'Start':
                data.start = int(fields[0])

            if entry_type == 'Response':
                data.add_response(int(fields[0]), fields[2], int(fields[3]), fields[5])

            if entry_type == 'Finish':
                data.set_finish(fields[2], fields[3], fields[4])

            if entry_type == 'ParserStat':
                data.set_parser_stat(fields[2], int(fields[3]), int(fields[4]))

    return data

def build_run_data_map(input_files):
    run_data = {}

    for input_file in input_files:
        data = read_data(input_file)

        if data.mode not in run_data:
            run_data[data.mode] = {}

        if data.site not in run_data[data.mode]:
            run_data[data.mode][data.site] = []

        run_data[data.mode][data.site].append(data)

    return run_data

class Summary:
    def __init__(self, site, mode):
        self.site = site
        self.mode = mode

        self.responses = []
        self.summary = RunSummary()

    def add_response(self, avg_time, parser_type, status_code, url):
        self.responses.append((avg_time, parser_type, status_code, url))

    def set_finish(self, total, valid, total_min):
        self.summary.requests.total = int(total)
        self.summary.requests.valid = int(valid)
        self.summary.total_min = float(total_min)

    def set_parser_stat(self, parser_type, valid, total):
        self.summary.parser_stats[parser_type].valid = valid
        self.summary.parser_stats[parser_type].total = total


def summarize_iterations(mode, site, iteration_data):
    summary = Summary(site, mode)

    avg_total = sum([data.summary.requests.total for data in iteration_data]) / len(iteration_data)
    avg_valid = sum([data.summary.requests.valid for data in iteration_data]) / len(iteration_data)
    avg_total_min = sum([data.summary.total_min for data in iteration_data]) / len(iteration_data)

    summary.set_finish(avg_total, avg_valid, avg_total_min)

    for parser_type in summary.summary.parser_stats.keys():
        avg_total = sum([data.summary.parser_stats[parser_type].total for data in iteration_data]) / len(iteration_data)
        avg_valid = sum([data.summary.parser_stats[parser_type].valid for data in iteration_data]) / len(iteration_data)

        summary.set_parser_stat(parser_type, avg_valid, avg_total)

    # TODO Summarize response times

    return summary

def summarize_site_summaries (summaries):
    # TODO Summarize site summaries to get full mode picture
    return []

def summarize_run_data(run_data):
    result_map = {
        'Summary': {}
    }

    for mode, site_data in run_data.items():
        result_map[mode] = {}

        for site, iteration_data in site_data.items():
            result_map[mode][site] = summarize_iterations(mode, site, iteration_data)

        result_map['Summary'][mode] = summarize_site_summaries(result_map[mode])

    return result_map

def get_out_file_list(input_dir):
    file_paths =  [join(input_dir, file) for file in listdir(input_dir) if 'out' in file]

    return [file_path for file_path in file_paths if isfile(file_path)]

def generate_header(first_column):
    columns = [
        first_column,
        'Total Time',
        'Total Requests',
        'Total Valid Responses',
    ]

    for parser_type in ['Dict', 'Link', 'Href', 'Service', 'Redirect', 'Index', 'Src', 'Script']:
        columns.append(f'{parser_type} Requests')
        columns.append(f'{parser_type} Valid Responses')

    return ','.join(columns) + '\n'

def generate_summary_line(first_column, summary):
    columns = [
        first_column,
        summary.summary.total_min,
        summary.summary.requests.total,
        summary.summary.requests.valid,
    ]

    for parser_type in ['Dict', 'Link', 'Href', 'Service', 'Redirect', 'Index', 'Src', 'Script']:
        columns.append(summary.summary.parser_stats[parser_type].total)
        columns.append(summary.summary.parser_stats[parser_type].valid)

    columns = [str(column) for column in columns]

    return ','.join(columns) + '\n'

def write_results(output_dir, result_map):
    site_data = {}

    for mode, site_map in result_map.items():
        if mode == 'Summary':
            continue

        with open(join(output_dir, f'{mode}_summary.csv'), 'w+') as file:
            file.write(generate_header('Site'))

            for site, summary in site_map.items():
                file.write(generate_summary_line(site, summary))

                if site not in site_data:
                    site_data[site] = {}

                site_data[site][mode] = summary

    for site, mode_map in site_data.items():
        with open(join(output_dir, f'{site}_summary.csv'), 'w+') as file:
            file.write(generate_header('Mode'))

            for mode, summary in mode_map.items():
                file.write(generate_summary_line(mode, summary))

    with open(join(output_dir, f'summary.csv'), 'w+') as file:
        file.write(generate_header('Mode,Site'))
        for site, mode_map in site_data.items():
            for mode, summary in mode_map.items():
                file.write(generate_summary_line(f'{mode},{site}', summary))

def analyze(input_dir, output_dir):
    input_files = get_out_file_list(input_dir)
    print(f'Found {len(input_files)} files to analyze.')

    run_data = build_run_data_map(input_files)
    print(f'Finished building run data map.')

    result_map = summarize_run_data(run_data)
    print(f'Built result map.')

    write_results(output_dir, result_map)
    print(f'Wrote results to output directory.')

if __name__ == '__main__':
    print_header()

    parser = setup_argument_parser()
    parsed_args = parser.parse_args()

    analyze(parsed_args.directory, parsed_args.out_dir)
