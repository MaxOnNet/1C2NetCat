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

from functools import wraps
import xml.dom.minidom
import os


class Config:
    """
        Класс отвечаюший за сохранение и загрузку конфигурации
    """

    def __init__(self):
        self.xml_file = "{0}/config.xml".format(os.path.abspath(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '..')))
        self.xml = xml.dom.minidom.parse(self.xml_file)
        self.configuration = self.xml.getElementsByTagName("configuration")[0]


    def fix_parms(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            value_o = str(fn(*args, **kwargs))
            value_n = ""

            value_n = str.replace(value_o, "$path", str(os.path.abspath(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), '..'))))

            return value_n
        return wrapped

    @fix_parms
    def get(self, group, item, attribute, value=""):
        for group in self.configuration.getElementsByTagName(group):
            if item == "":
                if group.hasAttribute(attribute):
                    return group.getAttribute(attribute)
                else:
                    return value
            else:
                for item in group.getElementsByTagName(item):
                    if item.hasAttribute(attribute):
                        return item.getAttribute(attribute)
                    else:
                        return value

    def set(self, group, item, attribute, value):
        if len(self.configuration.getElementsByTagName(group)) == 0:
            self.configuration.appendChild(self.xml.createElement(group))

        for group in self.configuration.getElementsByTagName(group):
            if item == "":
                group.setAttribute(attribute, value)
            else:
                if len(group.getElementsByTagName(item)) == 0:
                    group.appendChild(self.xml.createElement(item))

                for item in group.getElementsByTagName(item):
                    item.setAttribute(attribute, value)

        self.save()

    def remove(self, group, item, attribute):
        for group in self.configuration.getElementsByTagName(group):
            if item == "" and attribute != "":
                if group.hasAttribute(attribute):
                    group.removeAttribute(attribute)

            elif item == "" and attribute == "":
                self.configuration.removeChild(group)

            else:
                for item in group.getElementsByTagName(item):
                    if attribute != "":
                        if item.hasAttribute(attribute):
                            item.removeAttribute(attribute)
                    else:
                        group.removeChild(item)

        self.save()

    def save(self):
        io_writer = open(self.xml_file, "w")
        io_writer.writelines(self.xml.toprettyxml(indent="", newl="", encoding="UTF-8"))
        io_writer.close()

