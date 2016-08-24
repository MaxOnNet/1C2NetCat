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
import logging

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ColumnDefault, Float, text
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.orm import relationship
from sqlalchemy.orm import object_session

from sqlalchemy_utils import URLType, CountryType, PhoneNumberType, UUIDType, IPAddressType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method


log = logging.getLogger(__name__)
Base = declarative_base()


class Classificator(Base):
    __tablename__ = 'Classificator'
    __table_args__ = {'mysql_engine': 'MyISAM', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': 'Таблица с группами свойств'}
    Classificator_ID = Column(Integer(), primary_key=True, autoincrement=True, nullable=False, doc="")
    Classificator_Name = Column(String(64), nullable=False, default="", doc="")

    Table_Name = Column(String(64), nullable=False, default="", doc="")
    
    System = Column(Integer(), default=0, nullable=False)
    Sort_Type = Column(Integer(), default=0, nullable=False)
    Sort_Direction = Column(Integer(), default=0, nullable=False)
    SourceId = Column(String(255), nullable=False, doc="")
    

    @staticmethod
    def parse(database, classificator_hash):
        classificator_hash_test = {
            'uuid': "uuid",
            'name': "Text",
            'items': {
                {'uudi': "uuid", 'name': "Name"},
                {'uudi': "uuid1", 'name': "Name"}
            }
        }
        
        if 'uuid' in classificator_hash and 'name' in classificator_hash:
            query = database.query(Classificator)
            query = query.filter(Classificator.SourceId == classificator_hash['uuid'])
            
            for row in query.all():
                pass
            else:
                pass
            
            