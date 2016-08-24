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


import os
import sys


reload(sys)

sys.setdefaultencoding('utf8')

import logging
import logging.handlers
import threading

import Interfaces.Parser
import Interfaces.Config
import Interfaces.MySQL as MySQL


log = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.config = Interfaces.Config.Config()
        self.database = None
    
        self._logging_init()
        
        self.parser_groups = None
        
    def _logging_init(self):
        threading.current_thread().name = 'main'
        
        logging.basicConfig(level=int(self.config.get("logging", "console", "level", "10")), stream=sys.stdout,
                            format='%(asctime)s [%(module)11s] [%(name)9s] [%(funcName)19s] [%(lineno)4d] [%(levelname)7s] [%(threadName)4s] %(message)s')
        
        log_handler_console = logging.StreamHandler()
        log_handler_console.setLevel(int(self.config.get("logging", "console", "level", "10")))
        log_handler_console.setFormatter(
            logging.Formatter('%(asctime)s [%(module)11s] [%(name)9s]  [%(funcName)19s] [%(lineno)4d] [%(levelname)7s] [%(threadName)4s] %(message)s'))
        
        if bool(int(self.config.get("logging", "", "use_file", "0"))):
            log_handler_file = logging.handlers.TimedRotatingFileHandler(self.config.get("logging", "file", "path", "4gain.log"),
                                                                         when=self.config.get("logging", "file", "when", "d"),
                                                                         interval=int(self.config.get("logging", "file", "interval", "1")),
                                                                         backupCount=int(self.config.get("logging", "file", "count", "1")))
            log_handler_file.setLevel(int(self.config.get("logging", "file", "level", "10")))
            log_handler_file.setFormatter(
                logging.Formatter('%(asctime)s [%(module)11s] [%(name)9s]  [%(funcName)19s] [%(lineno)4d] [%(levelname)7s] [%(threadName)4s] %(message)s'))
            
            logging.getLogger('').addHandler(log_handler_file)
        
        if bool(int(self.config.get("logging", "", "use_syslog", "0"))):
            log_handler_syslog = logging.handlers.SysLogHandler(address=(
            self.config.get("logging", "syslog", "address_ip", "127.0.0.1"), int(self.config.get("logging", "syslog", "address_port", "514"))))
            log_handler_syslog.setLevel(int(self.config.get("logging", "file", "level", "10")))
            log_handler_syslog.setFormatter(
                logging.Formatter('%(asctime)s [%(module)11s] [%(name)9s]  [%(funcName)19s] [%(lineno)4d] [%(levelname)7s] [%(threadName)4s] %(message)s'))
            
            logging.getLogger('').addHandler(log_handler_syslog)
        
        # logging.getLogger('').addHandler(log_handler_console)
    
    
    def _database_init(self):
        log.info("Инициализация баз данных")
        
        if bool(int(self.config.get("database", "", "use_inicialise", "0"))):
            self.database_maker = MySQL.init(self.config)
        else:
            self.database_maker = MySQL.init_fast(self.config)
        
        self.database = self.database_maker()
    
    
    def _database_close(self):
        log.info("Отключение баз данных")
        
        try:
            self.database.commit()
            self.database.flush()
            self.database.close()
        finally:
            pass
        
    def _parser_init(self):
        self.parser_groups = Interfaces.Parser.Groups(self)
    
    def _parser_work(self):
        self.parser_groups.work()
        
if __name__ == '__main__':
    app = Application()
    
    app._database_init()
    app._parser_init()
    
    app._parser_work()
    
    app._database_close()