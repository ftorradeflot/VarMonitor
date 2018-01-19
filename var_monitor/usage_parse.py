'''
Created on Jan 19, 2018

@author: Francesc Torradeflot
'''

import glob
import logging
from datetime import datetime, timedelta
import random

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

logger = logging.getLogger(__file__)

conversion_dict = {'K': -2, 'M': -1, 'G': 0}
def conversion(x):
    return x[-1] in conversion_dict and float(x[:-1])*1024.**conversion_dict[x[-1]] or 0.0

def save_or_show(fig, save_plot=False, plot_file=None):
    if save_plot:
        if plot_file is None:
            raise Exception('File not informed')
        
        fig.savefig(plot_file)
    else:
        plt.show()
        
def compute_df_columns(df):
    
    if len(df['timestamp']) == 0:
        return None
    
    df['timestamp'] = df['timestamp'].apply(datetime.strptime, args=('%Y-%m-%dT%H:%M:%S.%f',))
    df['time_delta_s'] = (df['timestamp'] - df['timestamp'].shift(1)).apply(lambda x: x.total_seconds())
    df['time_spent'] = df['timestamp'] - df['timestamp'][0]
    df['time_spent_s'] = df['time_spent'].apply(lambda x: x.total_seconds())
    
    if 'max_vms' in df.columns:
        df['max_vms_GB'] = df['max_vms'].apply(conversion)
    if 'max_rss' in df.columns:
        df['max_rss_GB'] = df['max_rss'].apply(conversion)
    if 'total_io_read' in df.columns:
        df['total_io_read_GB'] = df['total_io_read'].apply(conversion)
    if 'total_io_write' in df.columns:
        df['total_io_write_GB'] = df['total_io_write'].apply(conversion)
    if 'total_cpu_time' in df.columns:
        df['cpu_perc'] = 100.*(df['total_cpu_time'] - df['total_cpu_time'].shift(1))/df['time_delta_s']
    
    return df

VARLIST = ['max_vms_GB', 'max_rss_GB', 'total_io_read_GB', 'total_io_write_GB',
           'total_cpu_time', 'cpu_perc']

class UsageParser():
    
    def __init__(self):
        
        self.log_files = None 
        self.dfs = None
        self.additional_stats = None
    
    
    def load_log_files(self, wildcard_list, max_len=None):
        
        log_files = []
        
        for wildcard in wildcard_list:        
            log_files += glob.glob(wildcard)
    
        # When maximum length is fixed, get the first max_len files 
        if not max_len is None:
            log_files = log_files[:max_len]
        
        self.log_files = log_files
        
        self.load_dfs()
    
    def load_dfs(self):
        
        dfs = []
        for log_file in self.log_files:
            df = pd.read_csv(log_file, engine='python')
            compute_df_columns(df)
            dfs.append(df)
        
        self.dfs = dfs

    
    def plot_sample(self, sample_size=1, var_list=VARLIST, save_plot=False, plot_file=None):
        
        sample_dfs = random.sample(self.dfs, sample_size)
        n_vars = len(var_list)
        
        fig = plt.figure(figsize=(8*sample_size, 8*n_vars))
        
        ax_ind = 1
        for var_name in var_list:
            for sample_df in sample_dfs:
                ax = fig.add_subplot(n_vars, sample_size, ax_ind)
                ax.plot(sample_df['time_spent_s'], sample_df[var_name])
                ax.set_xlabel('Time Spent')
                ax.set_ylabel(var_name)
                ax_ind += 1
        
        save_or_show(fig, save_plot, plot_file)

    def compute_additional_stats(self, n_bins=100, hist_bins=None, max_GB=16.):
        
        if hist_bins is None:
            hist_bins = np.linspace(0., max_GB, n_bins + 1)
    
        additional_stats = {}
        
        # compute mean duration
        durations = [df['time_spent_s'].iloc[-1] for df in self.dfs]
        additional_stats['mean_duration'] = np.mean(durations)
        additional_stats['mean_duration_str'] = timedelta(seconds = additional_stats['mean_duration']).__str__()
        additional_stats['max_duration'] = np.max(durations)
        additional_stats['max_duration_str'] = timedelta(seconds = additional_stats['max_duration']).__str__()
    
        # compute mean rss histogram
        mean_rss_hist = np.zeros(n_bins)
        rss_count = 0.
        
        for df in self.dfs:
            h = np.histogram(df['max_rss_GB'], bins=hist_bins)
            rss_hist = h[0].astype(float)
            mean_rss_hist += rss_hist
            rss_count += len(df['max_rss_GB'])
        additional_stats['rss_hist'] = mean_rss_hist/rss_count
        
        # compute max RSS
        additional_stats['max_rss'] = max([df['max_rss_GB'].max() for df in self.dfs])
        
        self.additional_stats = additional_stats
    
    
    def plot_additional_stats(self, save_plot=False, plot_file=None):
        
        hist_bins = np.linspace(0., 16., 100 + 1)
        self.compute_additional_stats(hist_bins = hist_bins)
        
        hist_bins_centers = np.array((hist_bins[:-1] + hist_bins[1:])/2)
        fig = plt.figure(figsize=(16., 8.))
        ax = fig.add_subplot(1, 1, 1)
        ax.bar(hist_bins_centers, 100*self.additional_stats['rss_hist'], hist_bins_centers[1] - hist_bins_centers[0]);
        ax.set_ylabel('% of sample')
        ax.set_xlabel('GB RSS')
        
        save_or_show(fig, save_plot, plot_file)
