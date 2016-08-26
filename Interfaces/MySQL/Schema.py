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

import uuid
import re
import logging

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ColumnDefault, Float, text
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.orm import relationship
from sqlalchemy.orm import object_session

from sqlalchemy_utils import URLType, CountryType, PhoneNumberType, UUIDType, IPAddressType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from Interfaces.Parser.Utils import ucwords, transliterate

log = logging.getLogger(__name__)
Base = declarative_base()


class NetCat:
    def __init__(self, application):
        self.application = application
        self.database = self.application.database
        self.config = self.application.config

        self.log = logging.getLogger(self.__class__.__name__)

    def value_one(self, query_sql, query_args=None):
        _query = sqlalchemy.text(query_sql)
        
        if query_args is not None:
            _response = self.database.execute(_query, query_args)
        else:
            _response = self.database.execute(_query)
            
        if _response:
            for _row in _response:
                return _row[0]
        else:
            self.log.warning("Error on execution SQL:{}".format(query_sql))
    
        return None


    def get_subdivision_row_by_source_id(self, source_id):
        _query = sqlalchemy.text("SELECT * FROM Subdivision WHERE SourceId = :source_id")
        _response = self.database.execute(_query, {'source_id': source_id})
    
        if _response:
            for _row in _response:
                return _row
        else:
            self.log.warning("Subdivision not found by SourceId:{}".format(source_id))
    
        return None


    def get_class_id_by_source_id(self, source_id):
        _query = sqlalchemy.text( "SELECT Class_ID FROM Class WHERE Class_Name LIKE :class_name")
        _response = self.database.execute(_query, { 'class_name': '%: {}'.format(source_id)})
    
        if _response:
            for _row in _response:
                return int(_row[0])
            else:
                self.log.warning("ClassId not found by SourceId:{}".format(source_id))
        else:
            self.log.error("ClassId not found by SourceId:{}".format(source_id))
    
        return -1


    def check_group_sub(self, group_uuid, group_name, group_parent_uuid=None, group_has_child=False):
        _subdivision = self.get_subdivision_row_by_source_id(group_uuid)
        _subdivision_parent = None
    
        if not _subdivision:
            self.create_group_sub(group_uuid, group_name, group_parent_uuid, group_has_child)
            return
    
        if group_parent_uuid is not None:
            _subdivision_parent = self.get_subdivision_row_by_source_id(group_parent_uuid)
    
        if _subdivision_parent is not None:
            if _subdivision['Parent_Sub_ID'] != _subdivision_parent['Subdivision_ID']:
                self._nc_update_group_sub(_subdivision['Parent_Sub_ID'], _subdivision_parent['Subdivision_ID'])


    def create_group_sub(self, group_uuid, group_name, group_parent_uuid=None, group_has_child=False):
        _group_name_english = re.sub("/\W+/", "", ucwords(transliterate(group_name)), re.I)
        _group_name_english_suffix = ""
        _group_parent_subdivision = None
        _group_parent_subdivision_id = None
        _group_parent_url = "/"
    
        _group_catalog_id = 1
        _group_priority = 1
    
        if group_parent_uuid is not None:
            _group_parent_subdivision = self.get_subdivision_row_by_source_id(group_parent_uuid)
            _group_parent_subdivision_id = _group_parent_subdivision['Subdivision_ID']
            _group_parent_url = _group_parent_subdivision['Hidden_URL']
    
        if _group_parent_subdivision_id is not None:
            _group_priority = int(
                self.value_one("SELECT MAX(Priority)+1 FROM Subdivision WHERE Parent_Sub_ID=:parent_sub_id;", {'parent_sub_id': _group_parent_subdivision_id}))
        
            while self.value_one(
                    "SELECT COUNT(*) FROM Subdivision WHERE Parent_Sub_ID=:parent_sub_id AND EnglishName=:english_name", {
                        'parent_sub_id': _group_parent_subdivision_id,
                        'english_name': "{}{}".format(_group_name_english, _group_name_english_suffix)
                        }) is not None:
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
        
        self.database.execute(_query,  {'group_catalog_id': _group_catalog_id,
                                        'group_parent_subdivision_id': _group_parent_subdivision_id,
                                        'group_name': group_name,
                                        'group_name_english': _group_name_english,
                                        'group_hidden_url': "{}{}".format(_group_parent_url, _group_name_english),
                                        'group_priority': _group_priority,
                                        'group_uuid': group_uuid
                                        })
    
        _group_subdivision_id = self.get_subdivision_row_by_source_id(group_uuid)
    
        self.add_group_sub_class(_group_subdivision_id, group_uuid, group_name, group_has_child)


    def add_group_sub_class(self, group_subdivision_id, group_uuid, group_name, group_has_child):
        if group_has_child:
            self.add_sub_class(group_subdivision_id, group_name, 2002)
            return
    
        _group_class_id = self.get_class_id_by_source_id(group_uuid)
    
        if not _group_class_id:
            _group_class_id = self.create_class(group_uuid, group_name)
        
            if not _group_class_id:
                self.log.error("NC: Error create class for {}".format(group_name))
                return
        
            self.add_sub_class(group_subdivision_id, group_name, _group_class_id)


    def add_sub_class(self, group_subdivision_id, group_name, group_class_id):
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
        
        self.database.execute(_query, {
                                        'group_subdivision_id': group_subdivision_id,
                                        'group_class_id': group_class_id,
                                        'group_name': group_name,
                                        'group_name_english': _group_name_english,
                                        'group_catalog_id': _group_catalog_id
                                        })


    def create_class(self, group_uuid, group_name):
        self.log.critical("NC: Function not implimented")

        # function createClass($id, $name)
        # {
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


    def get_list_table_name_by_source_id(self, source_id):
        return re.sub('/[^0-9a-z]/', '_', source_id)
    
    
    def exist_list_table_by_source_id(self, source_id):
        _query = sqlalchemy.text("""SELECT Table_Name FROM Classificator WHERE SourceId = :source_id;""")
        _response = self.database.execute(_query, {'source_id': source_id})
        
        if _response:
            for _row in _response:
                if _row[0] is not None:
                    return True
        return False
    
    
    def create_list_table(self, classificator_uuid, classificator_table_name, classificator_name):
        pass
