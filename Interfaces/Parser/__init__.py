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

import xmltodict
import os
import logging
import sqlalchemy
import re
import pprint


from Interfaces.Parser.Utils import ucwords, transliterate

class Parser:
    _parser_xml_file = "data"
    
    def __init__(self, application):
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.application = application
        
        self.database = self.application.database
        self.config = self.application.config
        self.netcat = self.application.netcat
        
        self.data = {}
        
        self._load_xml()


    def _load_xml(self):
        document_file = self.config.get("import", self._parser_xml_file, "path", "")
        
        if os.path.exists(document_file):
            self.log.debug("Загружаем фаил импорта.")
            with open(document_file) as fd:
                self.document = xmltodict.parse(fd.read().decode('utf8'))
            
            self.document = self.document[u'КоммерческаяИнформация'][u'Классификатор']
        else:
            self.log.critical("Фаил импорта {}, не найден.".format(document_file))
    
    
    def work(self):
        self.log.info("Начинаем анализ данных")
        self.log.critical("Наследования функции Work не произошло!")
        self.log.info("Анализ данных закончен")
    
        return self.data


class Groups(Parser):
    _parser_xml_file = "data"
    
    def work(self):
        self.log.info("Начинаем анализ данных")
    
        if self.document:
            for group in self.document[u'Группы']:
                self._parse_group(self.document[u'Группы'][group])
    
        self.log.info("Анализ данных закончен")
    
        return self.data
    
    
    def _parse_group(self, group, group_parent_uuid=None):
        _group_uuid = group[u'Ид']
        _group_name = group[u'Наименование']
        _group_has_child = False
        
        if u'Группы' in group:
            if len(group[u'Группы'][u'Группа']) > 0:
                _group_has_child = True

        self.netcat.check_group_sub(_group_uuid, _group_name, group_parent_uuid, _group_has_child)

        self.data[_group_uuid] = {}
        self.data[_group_uuid]['uuid'] = _group_uuid
        self.data[_group_uuid]['name'] = _group_name
        
        self.data[_group_uuid]['subdivision_id'] = int(self.netcat.get_subdivision_row_by_source_id(_group_uuid)['Subdivision_ID'])
        self.data[_group_uuid]['class_id'] = self.netcat.get_class_id_by_source_id(_group_uuid)
        
        self.log.debug("UUID: {}, SID: {}, CID: {}, Name: {}".format(_group_uuid,self.data[_group_uuid]['subdivision_id'], self.data[_group_uuid]['class_id'], _group_name))
        
        if _group_has_child:
            for index in xrange(len(group[u'Группы'][u'Группа'])):
                self._parse_group(group[u'Группы'][u'Группа'][index], _group_uuid)
                
 

class Classificators(Parser):
    _parser_xml_file = "data"
   
    def work(self):
        self.log.info("Начинаем анализ данных")
        if self.document:
            for classificator_group in self.document[u'Свойства']:
                for classificator_index in xrange(len(self.document[u'Свойства'][classificator_group])):
                    self._parse_classificator(self.document[u'Свойства'][classificator_group][classificator_index])
        self.log.info("Анализ данных закончен")
        
        return self.data

    def _parse_classificator(self, classificator):
        _classificator = {}
        _classificator_uuid = classificator[u'Ид']
        _classificator_name = classificator[u'Наименование']
        _classificator_type = classificator[u'ТипЗначений']
        _classificator_values = {}

        if _classificator_type == u'Справочник':
            if u'ВариантыЗначений' in classificator:
                if u'ИдЗначения' in classificator[u'ВариантыЗначений'][u'Справочник']:
                    _classificator_dict = classificator[u'ВариантыЗначений'][u'Справочник']
                    _classificator_values[_classificator_dict[u'ИдЗначения']] = _classificator_dict[u'Значение']
                else:
                    for _classificator_index in xrange(len(classificator[u'ВариантыЗначений'][u'Справочник'])):
                        _classificator_dict = classificator[u'ВариантыЗначений'][u'Справочник'][_classificator_index]
                        _classificator_values[_classificator_dict[u'ИдЗначения']] = _classificator_dict[u'Значение']
        
        self.data[_classificator_uuid] = {}
        self.data[_classificator_uuid]['uuid'] = _classificator_uuid
        self.data[_classificator_uuid]['name'] = _classificator_name
        self.data[_classificator_uuid]['type'] = _classificator_type
        self.data[_classificator_uuid]['values'] = _classificator_values

        if _classificator_type == u'Справочник':
            #print pprint.PrettyPrinter(indent=4).pformat(_classificator)
    
            _classificator_table_name = self.netcat.get_list_table_name_by_source_id(_classificator_uuid)

            if not self.netcat.exist_list_table_by_source_id(_classificator_uuid):
                self.log.info("Создаем таблицу классификатора, UUID: {}, Name: {}".format(_classificator_uuid, _classificator_name))
                self.netcat.create_list_table(_classificator_uuid, _classificator_table_name, _classificator_name)
            else:
                self.log.debug("Найдена таблица классификатора, UUID: {}, Name: {}".format(_classificator_uuid, _classificator_name))
                
            if len(_classificator_values) > 0:
                pass
                #self.netcat
                #processListValues classificator_table_name  _classificator['values']
            


