#!/usr/bin/python

import os
import psutil
import time
import math
import datetime
import logging
from collections import OrderedDict
import shlex
import subprocess as sp
import re
import sys
import threading

CHECK_LAPSE = 0 # time between each usage check in seconds
REPORT_LAPSE = 1 # time between each usage print in seconds

def convert_size(size_bytes):

    if (size_bytes == 0):
        return '0B'
    size_name = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes/p, 2)
    return '%s%s' % (s, size_name[i])


class VarMonitor(object):
    
    def reset_values(self):
        self.var_value = 0.0
        self.clean_report_value()
        self.summary_value = 0.0
    
    def clean_report_value(self):
        self.report_value = 0.0
        
    def __init__(self, name, proc_monitor):
        self.name = name
        self.reset_values()
        self.monitor = proc_monitor
    
    def is_parent(self, some_process):
        
        if some_process.pid == self.monitor.parent_proc.pid:
            return True
        else:
            return False
    
    '''
    def update_value(self, some_process):
        raise Exception('method not implemented!!')
    
    def update_summary_value(self):
        raise Exception('method not implemented!!')
    
    def get_var_value(self):
        raise Exception('method not implemented!!')
    
    def get_summary_value(self):
        raise Exception('method not implemented!!')
    '''


class RawVarMonitor(VarMonitor):
    
    def get_var_value(self):
        return self.var_value
    
    def get_report_value(self):
        return self.report_value
    
    def get_summary_value(self):
        return self.summary_value


class MemoryVarMonitor(VarMonitor):
    
    def get_var_value(self):
        return convert_size(self.var_value)

    def get_report_value(self):
        return convert_size(self.report_value)

    def get_summary_value(self):
        return convert_size(self.summary_value)


class MaxRSSMonitor(MemoryVarMonitor):
    
    def update_value(self, some_process):
        if self.is_parent(some_process):
            self.var_value = some_process.memory_info().rss
        else:
            self.var_value += some_process.memory_info().rss

    def update_report_value(self):
        self.report_value = max(self.var_value, self.report_value)

    def update_summary_value(self):
        self.summary_value = max(self.var_value, self.summary_value)
        

class MaxVMSMonitor(MaxRSSMonitor):
    
    def update_value(self, some_process):
        if self.is_parent(some_process):
            self.var_value = some_process.memory_info().vms
        else:
            self.var_value += some_process.memory_info().vms

class MaxUSSMonitor(MaxRSSMonitor):
    
    def update_value(self, some_process):
        if self.is_parent(some_process):
            self.var_value = some_process.memory_full_info().uss
        else:
            self.var_value += some_process.memory_full_info().uss

class MaxPSSMonitor(MaxRSSMonitor):
    
    def update_value(self, some_process):
        if self.is_parent(some_process):
            self.var_value = some_process.memory_full_info().pss
        else:
            self.var_value += some_process.memory_full_info().pss

class CumulativeVarMonitor(VarMonitor):
    
    def reset_values(self):
        self.var_value = 0.0
        self.var_value_dict = {}
        self.report_value = 0.0
        self.summary_value = 0.0
        self.backup_count = 0
    
    def get_process_value(self, some_process):
        raise Exception('Base class does not have this method implemented')
    
    def set_value_from_value_dict(self):
        # As we have accumulated data for each process
        # it's reasonable to assume that the default aggregator is the sum
        self.var_value = sum(self.var_value_dict.values())
    
    def update_value(self, some_process):
        cur_val = self.get_process_value(some_process)
        cur_pid = some_process.pid
        
        if cur_pid in self.var_value_dict and cur_val < self.var_value_dict[cur_pid]:
            # if the current value is lower than the already existent, it means
            # that the pid has been reused
            # move the old value to a backup
            bk_pid = '{}_{}'.format(cur_pid, self.backup_count)
            self.var_value_dict[bk_pid] = self.var_value_dict[cur_pid]
            self.backup_count += 1
                
        self.var_value_dict[cur_pid] = cur_val
        
        self.set_value_from_value_dict()
    
    def update_report_value(self):
        self.report_value = self.var_value
    
    def update_summary_value(self):
        self.summary_value = self.var_value


class TotalIOReadMonitor(CumulativeVarMonitor, MemoryVarMonitor):
    
    def get_process_value(self, some_process):
        return some_process.io_counters().read_chars
        
        
class TotalIOWriteMonitor(CumulativeVarMonitor, MemoryVarMonitor):
    
    def get_process_value(self, some_process):
        return some_process.io_counters().write_chars        


class TotalCpuTimeMonitor(CumulativeVarMonitor, RawVarMonitor):
    
    def get_process_value(self, some_process):
        cpu_times = some_process.cpu_times()
        return cpu_times.user + cpu_times.system 

class TotalHS06Monitor(CumulativeVarMonitor, RawVarMonitor):
    
    def __init__(self, name, proc_monitor):
        
        super(TotalHS06Monitor, self).__init__(name, proc_monitor)
        
        # Get HS06 factor
        # get the script to find the HS06 factor and run it
        HS06_factor_command_list = shlex.split(proc_monitor.kwargs.get('HS06_factor_func'))
        p = sp.Popen(HS06_factor_command_list, stdout=sp.PIPE, stderr=sp.PIPE)
        p.wait()
        
        # Capture the HS06 factor from the stdout
        m = re.search('HS06_factor=(.*)', p.stdout.read())
        self.HS06_factor = float(m.group(1))
    
    
    def get_process_value(self, some_process):
        
        # get CPU time
        cpu_times = some_process.cpu_times()
        
        # compute HS06*h
        return self.HS06_factor*(cpu_times.user + cpu_times.system)/3600.0
    def get_var_value(self):
        return '{:.4f}'.format(self.var_value)

    def get_summary_value(self):
        return '{:.4f}'.format(self.summary_value)
     

VAR_MONITOR_DICT = OrderedDict([('max_vms', MaxVMSMonitor),
            ('max_rss', MaxRSSMonitor),
            ('max_uss', MaxUSSMonitor),
            ('max_pss', MaxPSSMonitor),
            ('total_io_read', TotalIOReadMonitor),
            ('total_io_write', TotalIOWriteMonitor),
            ('total_cpu_time', TotalCpuTimeMonitor),
            ('total_HS06', TotalHS06Monitor)])


class ProcessTreeMonitor():
    
    def __init__(self, proc, var_list, **kwargs):
        
        self.parent_proc = proc
        self.kwargs = kwargs
        self.monitor_list = [VAR_MONITOR_DICT[var](var, self) for var in var_list]
        self.report_lapse = kwargs.get('report_lapse', REPORT_LAPSE)
        self.check_lapse = kwargs.get('check_lapse', CHECK_LAPSE)
        if 'log_file' in kwargs:
            if os.path.exists(kwargs['log_file']):
                raise Exception('File {} already exists'.format(kwargs['log_file']))
            self._log_file = open(kwargs['log_file'], 'a+')
        else:
            self._log_file = sys.stdout
        self.lock = threading.RLock()
    
    def update_values(self, some_process):
        for monitor in self.monitor_list:
            monitor.update_value(some_process)
    
    def update_report_values(self):
        for monitor in self.monitor_list:
            monitor.update_report_value()
    
    def update_summary_values(self):
        for monitor in self.monitor_list:
            monitor.update_summary_value()
    
    def clean_report_values(self):
        for monitor in self.monitor_list:
            monitor.clean_report_value()
    
    def get_var_values(self):
        return ', '.join(['{}, {}'.format(monit.name, monit.get_var_value()) for monit in self.monitor_list])
    
    def get_report_values(self):
        s = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ','
        return s + ','.join(['{}'.format(monit.get_report_value()) for monit in self.monitor_list]) + '\n'
    
    def get_summary_values(self):
        return ', '.join(['{}, {}'.format(monit.name, monit.get_summary_value()) for monit in self.monitor_list])
    
    def get_headers(self):
        return 'timestamp,' + ','.join([monit.name for monit in self.monitor_list]) + '\n'
    
    def update_all_values(self):
        
        # get var values from parent process
        self.update_values(self.parent_proc)

        # iterate over children and update their values
        children_process_list = self.parent_proc.children(recursive=True)
        for children_process in children_process_list:
            try:
                self.update_values(children_process)
            except:
                pass
       
        # update report values
        self.update_report_values()
        
        # update summary values
        self.update_summary_values()

    
    def write_log(self, log_message):
        
        self.lock.acquire()
        try:
            self._log_file.write(log_message)
            if hasattr(self._log_file, 'flush'):
                self._log_file.flush()
        finally:
            self.lock.release()
    
    def start(self):
        
        self._log_file.write(self.get_headers())
        
        time_report = datetime.datetime.now()
    
        while self.proc_is_running():
    
            try:
                self.update_all_values()
            except psutil.AccessDenied:
                pass
    
            # print usage if needed
            now = datetime.datetime.now()
            if (now - time_report).total_seconds() > self.report_lapse:
                self.write_log(self.get_report_values())
                self.clean_report_values()
                time_report = now
    
            time.sleep(self.check_lapse)
    
        self.parent_proc.wait()
        
        
    def proc_is_running(self):
        
        return self.parent_proc.is_running() and self.parent_proc.status() != psutil.STATUS_ZOMBIE 
    

