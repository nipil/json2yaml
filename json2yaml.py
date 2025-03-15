#!/usr/bin/env python3

import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

import yaml


class AppError(Exception):
    pass


def load_json_file(source: Path) -> Any:
    logging.debug(f'Opening {source} for reading')
    with open(source, 'rb') as fp:
        return json.load(fp)


def write_yaml_file(destination: Path, data: Any, *, mode: str) -> None:
    logging.debug(f'Opening {destination} for writing using mode: {mode}')
    with open(destination, mode) as fp:
        yaml.dump(data, fp)


def write_yaml_file_if_not_exists_and_not_forced(data: Any, destination: Path, *, force: bool) -> None:
    mode = 'wt' if force else 'xt'
    try:
        write_yaml_file(destination, data, mode=mode)
    except FileExistsError:
        logging.warning(f'Output file {destination} already exists, skipping. Use --force to overwrite.')


class App:

    def __init__(self, sources: list[Path], *, force: bool) -> None:
        self.sources = sources
        self.force = force

    def json_to_yaml(self, source: Path) -> None:
        if not source.suffix == '.json':
            logging.warning(f'{source} does not have a json extension, skipping.')
            return
        destination = source.with_suffix('.yaml')
        logging.info(f'Converting {source} to {destination}')
        data = load_json_file(source)
        logging.debug(f'Data: {data}')
        write_yaml_file_if_not_exists_and_not_forced(data, destination, force=self.force)

    def run_source(self, source: Path) -> None:
        if source.is_file():
            self.json_to_yaml(source)
            return
        if source.is_dir():
            for file in source.glob('*.json'):
                self.run_source(file)
            return
        raise AppError(f'{source} is not a known type')

    def run_sources(self) -> None:
        if self.force:
            logging.info('Forcing overwrite of existing files')
        for source in self.sources:
            logging.debug(f'Processing {source}')
            self.run_source(source)

    def run_streams(self):
        if self.force:
            logging.warning('Forcing has no effect when working with stdin and stdout')
        data = json.load(sys.stdin)
        logging.debug(f'Data: {data}')
        yaml.dump(data, sys.stdout)

    def run(self):
        if len(self.sources) > 0:
            self.run_sources()
        else:
            self.run_streams()


def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    parser = ArgumentParser()
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error', 'critical'], default='warning')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('source', nargs='*', type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(format='%(levelname)s: %(message)s', level=getattr(logging, args.log_level.upper()))
    logging.debug(f'Args: {args}')
    try:
        app = App(args.source, force=args.force)
        app.run()
    except AppError as e:
        logging.error(str(e))


if __name__ == '__main__':
    main()
