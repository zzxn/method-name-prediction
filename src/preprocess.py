#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from typing import List
import os
import platform
import multiprocessing
import time

compile_cmd = ''
move_cmd = ''

if platform.system() == 'Windows':
    compile_cmd = 'javac -cp src/features-javac-extractor-latest.jar -Xplugin:FeaturePlugin %s 2>nul 1>nul'
    move_cmd = 'move %s.proto %s 2>nul 1>nul'
else:
    compile_cmd = 'javac -cp src/features-javac-extractor-latest.jar -Xplugin:FeaturePlugin %s >/dev/null 2>&1'
    move_cmd = 'mv %s.proto %s >/dev/null 2>&1'


def get_file_paths_in_dir(dir_path: str) -> List[str]:
    # get all file paths in this dir
    return [os.path.join(root, file) for (root, dirs, files) in os.walk(dir_path) for file in files
            if os.path.splitext(file)[1] == '.java']


def process_file(input_path: str, output_path: str):
    r1 = os.system(compile_cmd % input_path)
    r2 = os.system(move_cmd % (input_path, output_path))
    return input_path, r1, r2


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('input_dir')
    parser.add_argument('output_dir')
    parser.add_argument('--num', '-n', dest='num', type=int, required=False, default=-1)
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.exists(input_dir):
        raise FileNotFoundError('No such dir:' + input_dir)

    if os.path.exists(output_dir):
        if os.path.isfile(output_dir):
            raise RuntimeError('Given output_dir is a file, but directory required')
    else:  # if no such dir, create it
        os.mkdir(output_dir)

    print('Scanning .java files...')
    file_paths = get_file_paths_in_dir(args.input_dir)[:args.num]
    print('Got %d .java files' % len(file_paths))

    process_pool = multiprocessing.Pool()
    curr = 0

    def incr_curr(res):
        # if (res[1] | res[2]) != 0:
        #     raise RuntimeError("Fail to process file " + res[0])
        global curr
        curr += 1

    print('Start to transform .java files to .proto files')
    start = time.time()
    for path in file_paths:
        process_pool.apply_async(process_file, args=(path, output_dir), callback=incr_curr)

    while curr < len(file_paths):
        print('%d / %d  %3.2f %%  %d secs' % (curr, len(file_paths), curr / len(file_paths) * 100,
                                                    time.time() - start))
        time.sleep(10)

    print('Finish processing %d files. Time cost: %d secs' % (len(file_paths), time.time() - start))
