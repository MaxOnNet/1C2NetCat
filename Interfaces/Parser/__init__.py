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

import xml.dom.minidom
import xmltodict
import os
import logging


class Groups:
    def __init__(self, application):
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.application = application
        
        self.datatbase = self.application.database
        self.config = self.application.config
        
        self._load_xml()
        
        
    
    def _load_xml(self):
        document_file = self.config.get("import", "data", "path", "")
        
        if os.path.exists(document_file):
            self.log.debug("Загружаем фаил импорта.")
            with open(document_file) as fd:
                self.document = xmltodict.parse(fd.read().decode('utf8'))

            self.document = self.document[u'КоммерческаяИнформация'][u'Классификатор']
        else:
            self.log.critical("Фаил импорта {}, не найден.".format(document_file))

    def work(self):
        self.log.info("Начинаем анализ данных")
        if self.document:
            for group in self.document[u'Группы']:
                self._parse_group(self.document[u'Группы'][group], "")
        self.log.info("Анализ данных закончен")
        
    
    
    def _parse_group(self, group, group_parent):
        print "Root UUID: {}, UUID: {}, Name: {}".format(group_parent, group[u'Ид'], group[u'Наименование'])
        
        if u'Группы' in group:
            for index in xrange(len(group[u'Группы'][u'Группа'])):
                self._parse_group(group[u'Группы'][u'Группа'][index], group[u'Ид'])