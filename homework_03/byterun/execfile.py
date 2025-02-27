import logging
from .pyobj import VirtualMachine

def run_python_file(file_path, args):
    # Инициализация виртуальной машины и загрузка файла
    vm = VirtualMachine()
    vm.run_file(file_path, args)

def run_python_module(module_name, args):
    # Инициализация виртуальной машины и загрузка модуля
    vm = VirtualMachine()
    vm.run_module(module_name, args)