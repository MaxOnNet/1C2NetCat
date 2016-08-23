#!/bin/sh
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

binary_mysql_mac="/Applications/MySQLWorkbench.app/Contents/MacOS";

if [ -d "${binary_mysql_mac}" ]; then
    echo "USE MySQL path: ${binary_mysql_mac}";
    export PATH=$PATH:${binary_mysql_mac};
fi;

binary_mysql="$(which mysql 2> /dev/null)";
binary_mysqldump="$(which mysqldump 2> /dev/null)";

if [ ! -x "${binary_mysql}" ]; then
    echo "mysql not install, exit.";
    exit 2;
fi;

if [ ! -x "${binary_mysqldump}" ]; then
    echo "mysqldump not install, exit.";
    exit 2;
fi;

# Проверяем, присутствует ли отладочное окружение
path_python_env="/Users/v_tatarnikov/_python_env_1c2netcat";

if [ -x "${path_python_env}/bin/python" ]; then
    echo "USE Python path: ${path_python_env}";
    path_python="${path_python_env}/bin/python";
else
    path_python="$(which python)";
fi;

# Ищем путь до программы
for path in  "/media/psf/Home/PycharmProjects/1C2NetCat/" "/home/v.tatarnikov/bin/1C2NetCat/" "/Users/v_tatarnikov/PycharmProjects/1C2NetCat/"; do
    if [ -e "${path}config.py" ]; then
        echo "USE 1C to NetCat path: ${path}";
        export PYTHONPATH=${PYTHONPATH}:${path};
        db_user="$(${path_python} ${path}/config.py get database mysql user)";
        db_password="$(${path_python} ${path}/config.py get database mysql password)";
        db_name="$(${path_python} ${path}/config.py get database mysql database)";
        db_host="$(${path_python} ${path}/config.py get database mysql server)";

        db_backup="${path}/SQL/backup/${db_name}-`date +%Y-%m-%d-%H-%M`.sql";
        db_backup_current="${path}/SQL/backup/${db_name}-current.sql";

        mkdir -p "${path}/SQL/backup/";

        echo "DROP DATABASE ${db_name}" | mysql -h${db_host} -u${db_user} -p${db_password};
        cat ${db_backup_current} | mysql -h${db_host} -u${db_user} -p${db_password} ${db_name};
        break;
    fi;
done;

