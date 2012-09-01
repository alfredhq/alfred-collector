import argparse
import yaml
from .process import CollectorProcess


def get_config(path):
    with open(path) as file:
        return yaml.load(file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')

    args = parser.parse_args()
    config = get_config(args.config)

    processes = []
    database_uri = config['database_uri']
    for socket_address in config['collectors']:
        process = CollectorProcess(database_uri, socket_address)
        process.start()
        processes.append(process)

    for process in processes:
        process.join()


if __name__ == '__main__':
    main()
