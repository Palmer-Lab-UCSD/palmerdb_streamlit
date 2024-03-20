import re
import pandas as pd
import numpy as np
import os
from collections import defaultdict

def read_session_individual(s, remove_first: list = [], timestamp_measures = [] ):
    a = re.compile('[\r\n]+\s+\d*[05]:').sub
    ratd = pd.DataFrame(re.findall('([\w ]+):(.+)\n', a('', s)+'\n'), columns = ['measure', 'value']).set_index('measure')
    ratd.loc[~ratd.index.str.contains('^[A-Z]$'), 'value'] = ratd.loc[~ratd.index.str.contains('^[A-Z]$'), 'value'].apply(lambda x:  re.sub('\s+$', '', re.sub('^\s+', '',x))  )
    ratd.loc[['Start Date', 'End Date'], 'value'] = pd.to_datetime(ratd.loc[['Start Date', 'End Date'], 'value'].reset_index(drop= True) +' '
                                                               + ratd.loc[['Start Time', 'End Time'], 'value'].reset_index(drop= True), format='mixed', dayfirst=False).values
    values = ratd[ratd.index.str.contains('^[A-Z]$')]
    values = values.applymap(lambda x: np.array([float(y) for y in re.sub('\s+', ' ', x).strip(' ').split(' ')])).explode('value')
    metadata = ratd[~ratd.index.str.contains('^[A-Z]$')].drop(['Start Time', 'End Time']).value.to_dict()
    rt = values.assign(**metadata)
    rt = rt.reset_index().set_index(['Subject', 'measure'])
    
    if len(remove_first):
        rt = rt.groupby(level = ['Subject', 'measure'], group_keys=False).apply(lambda df: df.iloc[1:, :] if rt.index[0][1] in remove_first else df)

    def process_single_metric(df, timestamp_measures):
        start_time, end_time = df['Start Date'].iloc[0], df['End Date'].iloc[0]
        if df.index[0][1] in timestamp_measures:
            outdf = df[df.value.astype(float)> 0].copy()
            outdf = outdf.assign(measure_timestamp = outdf['Start Date'] + pd.to_timedelta(outdf.value.astype(float), unit ='s' ),
                                 measure_timelength_seconds = 0,order = range(len(outdf)) )
            outdf['value'] = 1
            return outdf
        return df.assign(order = range(len(df)),  measure_timestamp = pd.date_range(start=start_time, end=end_time, periods=(len(df)+1), inclusive='right'),
                                        measure_timelength_seconds = ((end_time - start_time )/len(df)).seconds )
        
    rt = rt.groupby(level = ['Subject', 'measure'], group_keys=False)\
           .apply(process_single_metric,timestamp_measures= timestamp_measures)
    return rt

def read_file(filename: str = '', remove_first: list = [], measure_name_dict = {},  subset_named_measures = False, timestamp_measures = []):
    # if not os.path.isfile(filename):
    #     raise IOError(f'Could not find file {filename}')
    # with open(filename, 'r') as f: 
        # filen = f.readline().replace('File: ', '').strip('\n').strip(' ').strip('\t')
        # t = f.read().replace('\r', '').strip('\n') + '\n'
    filen = filename.split('\n',1)[0] #.readline()
    t = filename.split('\n',1)[1].strip('\n') + '\n'
    ret =  pd.concat([read_session_individual(x, remove_first=remove_first, timestamp_measures = timestamp_measures) 
                      for x in re.split('\n\n+', t)]) \
             .assign(file = filen).reset_index()
    
    if len(measure_name_dict):
        measure_name_dict = defaultdict(lambda: 0,measure_name_dict )
        ret.measure = ret.measure.apply(lambda x: y if (y:=measure_name_dict[x]) else x)
        if subset_named_measures:
            ret= ret[ret.measure.isin(measure_name_dict.values())]    
    return ret