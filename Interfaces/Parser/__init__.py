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

def ucwords (s):
    """Returns a string with the first character of each word in str
    capitalized, if that character is alphabetic."""
    return " ".join([w[0].upper() + w[1:] for w in re.split('\s*', s)])

def transliterate(string):

    capital_letters = {u'А': u'A',
                       u'Б': u'B',
                       u'В': u'V',
                       u'Г': u'G',
                       u'Д': u'D',
                       u'Е': u'E',
                       u'Ё': u'E',
                       u'З': u'Z',
                       u'И': u'I',
                       u'Й': u'Y',
                       u'К': u'K',
                       u'Л': u'L',
                       u'М': u'M',
                       u'Н': u'N',
                       u'О': u'O',
                       u'П': u'P',
                       u'Р': u'R',
                       u'С': u'S',
                       u'Т': u'T',
                       u'У': u'U',
                       u'Ф': u'F',
                       u'Х': u'H',
                       u'Ъ': u'',
                       u'Ы': u'Y',
                       u'Ь': u'',
                       u'Э': u'E',}

    capital_letters_transliterated_to_multiple_letters = {u'Ж': u'Zh',
                                                          u'Ц': u'Ts',
                                                          u'Ч': u'Ch',
                                                          u'Ш': u'Sh',
                                                          u'Щ': u'Sch',
                                                          u'Ю': u'Yu',
                                                          u'Я': u'Ya',}


    lower_case_letters = {u'а': u'a',
                       u'б': u'b',
                       u'в': u'v',
                       u'г': u'g',
                       u'д': u'd',
                       u'е': u'e',
                       u'ё': u'e',
                       u'ж': u'zh',
                       u'з': u'z',
                       u'и': u'i',
                       u'й': u'y',
                       u'к': u'k',
                       u'л': u'l',
                       u'м': u'm',
                       u'н': u'n',
                       u'о': u'o',
                       u'п': u'p',
                       u'р': u'r',
                       u'с': u's',
                       u'т': u't',
                       u'у': u'u',
                       u'ф': u'f',
                       u'х': u'h',
                       u'ц': u'ts',
                       u'ч': u'ch',
                       u'ш': u'sh',
                       u'щ': u'sch',
                       u'ъ': u'',
                       u'ы': u'y',
                       u'ь': u'',
                       u'э': u'e',
                       u'ю': u'yu',
                       u'я': u'ya',}

    for cyrillic_string, latin_string in capital_letters_transliterated_to_multiple_letters.iteritems():
        string = re.sub(ur"%s([а-я])" % cyrillic_string, ur'%s\1' % latin_string, string)

    for dictionary in (capital_letters, lower_case_letters):

        for cyrillic_string, latin_string in dictionary.iteritems():
            string = string.replace(cyrillic_string, latin_string)

    for cyrillic_string, latin_string in capital_letters_transliterated_to_multiple_letters.iteritems():
        string = string.replace(cyrillic_string, latin_string.upper())

    return string

class Groups:
    def __init__(self, application):
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.application = application
        
        self.database = self.application.database
        self.config = self.application.config
        self.data = {}
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
                self._parse_group(self.document[u'Группы'][group])
        self.log.info("Анализ данных закончен")
        
    
    
    def _parse_group(self, group, group_parent_uuid=None):
        _group_uuid = group[u'Ид']
        _group_name = group[u'Наименование']
        _group_has_child = False
        _group_ncdata = {}
        
        if u'Группы' in group:
            if len(group[u'Группы'][u'Группа']) > 0:
                _group_has_child = True

        self._nc_check_group_sub(_group_uuid, _group_name, group_parent_uuid, _group_has_child)

        self.data[_group_uuid] = {}
        self.data[_group_uuid]['uuid'] = _group_uuid
        self.data[_group_uuid]['name'] = _group_name
        
        self.data[_group_uuid]['subdivision_id'] = int(self._db_subdivision_get_by_source_id(_group_uuid)['Subdivision_ID'])
        self.data[_group_uuid]['class_id'] = self._db_class_id_by_source_id(_group_uuid)
        
        self.log.debug("UUID: {}, SID: {}, CID: {}, Name: {}".format(_group_uuid,self.data[_group_uuid]['subdivision_id'], self.data[_group_uuid]['class_id'], _group_name))
        
        if _group_has_child:
            for index in xrange(len(group[u'Группы'][u'Группа'])):
                self._parse_group(group[u'Группы'][u'Группа'][index], _group_uuid)
                
    def _db_value1(self, query_sql):
        _query = self.database.execute(sqlalchemy.text(query_sql))
    
        if _query:
            for _row in _query:
                return _row[0]
        else:
            self.log.warning("NC: Subdivision not found by SourceId:{}".format(data))
    
        return None

    def _db_subdivision_get_by_source_id(self, data):
        _query_sql = "SELECT * FROM Subdivision WHERE SourceId = '{}'".format(data)
        _query = self.database.execute(sqlalchemy.text(_query_sql))
        
        if _query:
            for row in _query:
                return row
        else:
            self.log.warning("NC: Subdivision not found by SourceId:{}".format(data))

        return None
    
    def _db_class_id_by_source_id(self, data):
        _query_sql = "SELECT Class_ID FROM Class WHERE Class_Name LIKE '%: {}'".format(data)
        _query = self.database.execute(sqlalchemy.text(_query_sql))

        if _query:
            for row in _query:
                return int(row[0])
            else:
                self.log.warning("NC: ClassId not found by SourceId:{}".format(data))
        else:
            self.log.error("NC: ClassId not found by SourceId:{}".format(data))
            
        return -1

    def _nc_check_group_sub(self, group_uuid, group_name, group_parent_uuid=None, group_has_child=False):
        _subdivision = self._db_subdivision_get_by_source_id(group_uuid)
        _subdivision_parent = None
        
        if not _subdivision:
            self._nc_create_group_sub(group_uuid, group_name, group_parent_uuid, group_has_child)
            return
        
        if group_parent_uuid is not None:
            _subdivision_parent = self._db_subdivision_get_by_source_id(group_parent_uuid)
        
        if _subdivision_parent is not None:
            if _subdivision['Parent_Sub_ID'] != _subdivision_parent['Subdivision_ID']:
                self._nc_update_group_sub(_subdivision['Parent_Sub_ID'], _subdivision_parent['Subdivision_ID'])

    def _nc_create_group_sub(self, group_uuid, group_name, group_parent_uuid=None, group_has_child=False):
        _group_name_english = re.sub("/\W+/", "", ucwords(transliterate(group_name)), re.I)
        _group_name_english_suffix = ""
        _group_parent_subdivision = None
        _group_parent_subdivision_id = None
        _group_parent_url = "/"

        _group_catalog_id = 1
        _group_priority = 1
        
        if group_parent_uuid is not None:
            _group_parent_subdivision = self._db_subdivision_get_by_source_id(group_parent_uuid)
            _group_parent_subdivision_id = _group_parent_subdivision['Subdivision_ID']
            _group_parent_url = _group_parent_subdivision['Hidden_URL']
            
        if _group_parent_subdivision_id is not None:
            _group_priority = int(self._db_value1("SELECT MAX(Priority)+1 FROM Subdivision WHERE Parent_Sub_ID={}".format(_group_parent_subdivision_id)))
            
            while self._db_value1("SELECT COUNT(*) FROM Subdivision WHERE Parent_Sub_ID={} AND EnglishName='{}'".format(_group_parent_subdivision_id, "{}{}".format(_group_name_english, _group_name_english_suffix))) is not None:
                if _group_name_english_suffix == "":
                    _group_name_english_suffix = str(1)
                else:
                    _group_name_english_suffix = str(int(_group_name_english_suffix) + 1)

        _group_name_english = "{}{}".format(_group_name_english, _group_name_english_suffix)
        _query = sqlalchemy.text("""
            INSERT INTO Subdivision
            SET
                Catalogue_ID = :group_catalog_id,
                Parent_Sub_ID = :group_parent_subdivision_id,
                Subdivision_Name = :group_name,
                Template_ID = 0,
                EnglishName = :group_name_english,
                LastUpdated = NOW(),
                Created = NOW(),
                Hidden_URL = :group_hidden_url,
                Priority = :group_priority,
                SourceId = :group_uuid,
                Checked = 1;
            """)
        _query.bindparams(group_catalog_id=_group_catalog_id, group_parent_subdivision_id=_group_parent_subdivision_id, group_name=group_name, group_name_english=_group_name_english,group_hidden_url=("{}{}".format(_group_parent_url,_group_name_english)), group_priority=_group_priority, group_uuid=group_uuid)
        
        
        self.database.execute(_query)

        _group_subdivision_id = self._db_subdivision_get_by_source_id(group_uuid)
        
        self._nc_add_group_sub_class(_group_subdivision_id, group_uuid, group_name, group_has_child)
        
        
    def _nc_add_group_sub_class(self, group_subdivision_id, group_uuid, group_name, group_has_child):
        if group_has_child:
            self._nc_add_sub_class(group_subdivision_id, group_name, 2002)
            return
        
        _group_class_id = self._db_class_id_by_source_id(group_uuid)
        
        if not _group_class_id:
            _group_class_id = self._nc_create_class(group_uuid, group_name)

            if not _group_class_id:
                self.log.error("NC: Error create class for {}".format(group_name))
                return
            
            self._nc_add_sub_class(group_subdivision_id, group_name, _group_class_id)
            
    def _nc_add_sub_class(self, group_subdivision_id, group_name, group_class_id):
        _group_name_english = re.sub("/\W+/", "", ucwords(transliterate(group_name)), re.I)
        _group_catalog_id = 1
        
        _query = sqlalchemy.text("""
            INSERT INTO Sub_Class
            SET
                Subdivision_ID = :group_subdivision_id,
                Class_ID = :group_class_id,
                Sub_Class_Name = :group_name,
                EnglishName = :group_name_english,
                Priority = 0,
                Checked = 1,
                Catalogue_ID = :group_catalog_id,
                DefaultAction = 'index',
                Created = NOW(),
                LastUpdated = NOW();
              """)
        _query.bindparams(group_subdivision_id=group_subdivision_id, group_class_id=group_class_id, group_name=group_name, group_name_english=_group_name_english, group_catalog_id=_group_catalog_id)
        
        self.database.execute(_query)
    
    def _nc_create_class(self, group_uuid, group_name):
        self.log.critical("NC: Function not implimented")
        
#function createClass($id, $name)
#{
#    global $nc_core, $db;
    
#    $className = $name . ": " . $id;
#    $baseClassID = 2002;
#    $nc_core->input->_POST = array();
#    $nc_core->input->_POST['Class_Name'] = $className;
#    $nc_core->input->_POST['Class_Group'] = 'Энерго';
#    $_REQUEST['fs'] = 1;
    
#    $newID = ActionClassComleted(1, $baseClassID);
#    InsertActionsFromBaseClass($baseClassID, $newID);
#    InsertFieldsFromBaseClass($baseClassID, $newID);
    
#    $baseClassSettings = $db->get_row("SELECT SortBy, TitleTemplate FROM Class WHERE Class_ID = {$baseClassID}", ARRAY_A);
#    $db->query("UPDATE Class SET SortBy = '{$baseClassSettings['SortBy']}', TitleTemplate = '{$baseClassSettings['TitleTemplate']}' WHERE Class_ID =
#          {$newID}");
    
#    return $newID;
