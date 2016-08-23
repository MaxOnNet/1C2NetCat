#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright [2016] Tatarnikov Viktor [viktor@tatarnikov.org]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

reload(sys)

sys.setdefaultencoding('utf8')

import argparse
import Interfaces.Config


def config_read(arguments):
    """Эта функция будет вызвана для создания пользователя"""
    config = Interfaces.Config.Config()
    print config.get(arguments.group, arguments.item, arguments.attribute, "")


def parse_args():
    """Настройка argparse"""
    arg_parser = argparse.ArgumentParser(description='4Gain Утилита по работе с конфигом и инициализации базы данных')

    arg_subparsers = arg_parser.add_subparsers()

    arg_config = arg_subparsers.add_parser('get', help='Получение информации из конфигурационного файла')
    arg_config.add_argument('group', help='Group name')
    arg_config.add_argument('item', help='Item name')
    arg_config.add_argument('attribute', help='Attribute name')
    arg_config.set_defaults(func=config_read)

    # код для других аргументов

    return arg_parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    args.func(args)
