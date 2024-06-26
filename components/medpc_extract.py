import streamlit as st
import re
import pandas as pd
import numpy as np
import os
from collections import defaultdict


def coerce_float(x):
    try:    return float(re.sub('\\s+', '', str(x)))
    except: return np.nan

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

def sorted_day_experiment(df):
    day_conv = {val:num+1 for num, val in enumerate(sorted(df['Start Date'].dt.floor('D').unique())) }
    df['sorted_day'] = df['Start Date'].dt.floor('D').map(lambda x: day_conv[x]) #df.measure.iloc[0]+'_day'+
    return df

def add_final_order(df):
    return df.groupby(['Subject', 'measure'],group_keys = False )\
            .apply(lambda x: sorted_day_experiment(x.sort_values('measure_timestamp'))\
            .assign(final_order = range(1, len(x)+1)))\
            .sort_values(['Subject','measure_timestamp','measure']).reset_index(drop = True)

def read_file(filename: str = '', remove_first: list = [], measure_name_dict = {},  subset_named_measures = False, timestamp_measures = []):

    if 'File' in filename:
        filen = filename.split('\n',1)[0] #.readline()
        t = filename.split('\n',1)[1].strip('\n').replace('\n\n\n', '')
        t = t.rstrip()
    else:
        filen = filename
        t = filename.strip('\n').replace('Start Date', '\nStart Date').replace('Start Time: 21:00:00', 'Start Time: 9:00:00')
    
    try:
        ret =  pd.concat([read_session_individual(x, remove_first=remove_first, timestamp_measures = timestamp_measures) 
                  for x in re.split('\n{2,}', t)]).assign(file = filen).reset_index()
    except:
        print(f'{filename} separation by "\\n\\n+" failed trying by "Start Date:"')
        ret =  pd.concat([read_session_individual('Start Date:'+x, remove_first='', timestamp_measures = timestamp_measures) 
                  for x in re.split('Start Date:', t) if len(x)]).assign(file = filename).reset_index()
    
    if len(measure_name_dict):
        measure_name_dict = defaultdict(lambda: 0,measure_name_dict )
        ret.measure = ret.measure.apply(lambda x: y if (y:=measure_name_dict[x]) else x)
        if subset_named_measures:
            ret= ret[ret.measure.isin(measure_name_dict.values())]    
    return ret

def read_session_individual_oldformat(text):
    if not len(text): return pd.DataFrame()
    rat = pd.DataFrame(re.findall('([^\n]+)\s([^\n]+)', text), columns = ['measure', 'value']).set_index('measure')
    metadata =  rat[(~rat.value.str.contains('__') | rat.value.str.contains('[A-Za-z]')) &~rat.index.str.contains('Total|^fr$') ].value.to_dict()
    try:rat.loc['IRItype'] = rat.loc['IRItype'].str.split('__')
    except:
        return pd.DataFrame()
    ts = rat.loc[['IRI', 'IRICode'], :]
    ts = ts.value.str.split('__', expand= True).iloc[:, 2:]
    ts.loc['IRI', :] = ts.loc['IRI', :].astype(int).cumsum()/100
    ts.loc['IRICode'] = ts.loc['IRICode'].apply( lambda x: rat.loc['IRItype', 'value'][int(x)])
    ts = ts.rename({'IRI': 'value', 'IRICode': 'measure'}).T.set_index('measure')
    ts.columns = ['value']
    ts = ts.assign(date=pd.to_datetime(metadata['date']),measure_timelength_seconds =0 	)
    ts['measure_timestamp'] = ts.date + pd.to_timedelta(ts.value.astype(int), unit ='s' )
    ts['value'] = 1
    ts = ts.groupby('measure', group_keys= False).apply(lambda df : df.sort_values('measure_timestamp')\
                                                        .assign(order = range(len(df))))\
                                                        .assign(**{'Start Date': pd.to_datetime(metadata['date']), 
                                                                   'End Date':pd.to_datetime(metadata['date']) + 
                                                                   pd.to_timedelta(int(metadata['Sessionlength']), unit ='h' ) })
    totals = rat.loc[rat.index.str.lower().str.contains('total|^fr$')].astype(int)
    if ('TotalResponses' in totals.index) and ('TotalTOResponses' in totals.index):
        totals.loc['TotalActive', 'value'] =  totals.loc['TotalResponses', 'value'] + totals.loc['TotalResponses', 'value']
    if ('TotalRspInAct' in totals.index) and ('TotalTORspInAct' in totals.index):
        totals.loc['TotalInactive', 'value'] =  totals.loc[['TotalRspInAct', 'TotalTORspInAct'], 'value'].sum() 
    #totals = totals.assign(date=pd.to_datetime(metadata['date']),)
    totals= totals.assign(date=pd.to_datetime(metadata['date']), order= 0,
                          measure_timelength_seconds=int(metadata['Sessionlength'])*3600,
                          measure_timestamp=pd.to_datetime(metadata['date']) + pd.to_timedelta(int(metadata['Sessionlength']), unit ='h' ) )
    totals = totals.assign(**{'Start Date': pd.to_datetime(metadata['date']), 
                              'End Date':pd.to_datetime(metadata['date']) + pd.to_timedelta(int(metadata['Sessionlength']), unit ='h' ) })
    start_time = pd.to_datetime(metadata['date'])
    end_time = pd.to_datetime(metadata['date']) + pd.to_timedelta(int(metadata['Sessionlength']), unit ='h' )
    rt = rat[rat.value.str.contains('__') & ~rat.index.str.contains('^IRI')]\
            .applymap(lambda x: np.array([float(y) for y in x.split('__')][1:]))\
            .explode('value').assign(date=pd.to_datetime(metadata['date']))\
           .assign(**{'Start Date': start_time, 'End Date':end_time })
    rt = rt.groupby('measure', group_keys= False) \
           .apply(lambda df: df.assign(order = range(len(df)), 
                             measure_timestamp = pd.date_range(start=start_time, end=end_time, periods=(len(df)+1), inclusive='right'),
                             measure_timelength_seconds = ((end_time - start_time )/len(df)).seconds ))
    #ts = ts[ts.index !='EndOfSession']
    out = pd.concat([totals, rt, ts]).assign(**metadata).rename({'FileName': 'file', 
                                                                 'BoxNumber':'Box', 'RatNumber': 'Subject'}, axis = 1).drop('date', axis = 1)
    
    return out.reset_index().set_index(['Subject', 'measure', 'value']).reset_index()


def read_file_old_format(filename, measure_name_dict = {},  subset_named_measures = False, verbose = False):
    # if not os.path.isfile(filename): raise IOError(f'Could not find file {filename}')
    # with open(filename) as f:
    s = filename.replace('\r', '').replace('Rewarf', 'Reward').replace('false', 'False').replace('totalRewards', 'TotalRewards').split('\n', 2)[-1]
    s= s.replace('\n\n', '\nUNK\n')
    #s= s.replace('Treatment\n\n', 'Treatment\nUNK').replace('Drug\n\n', 'Drug\nUNK')#.replace('EndSubject\n', '')
    #s = re.sub('(Drug\n0.5coc)',  lambda x: re.sub(r'\n', '_', x.group(1)), s)
    #s = re.sub('(Drug\n.*)\nfr',  lambda x: re.sub(r'\n', '_', x.group(1))+ '\nfr', s)
    s = re.sub('list\n([\d\w\n]*?)\nendl', lambda x: re.sub(r'\n', '__', x.group(1)), s)
    s = re.sub('(True\nFalse)', lambda x: re.sub(r'\n', '|', x.group(1)), s)
    s = re.sub('(False\nTrue)', lambda x: re.sub(r'\n', '|', x.group(1)), s)
    splited = s.split('EndSubject\n')
    out = pd.concat([read_session_individual_oldformat(i) for i in splited])
    if len(measure_name_dict):
        measure_name_dict = defaultdict(lambda: 0, measure_name_dict)
        out.measure = out.measure.apply(lambda x: y if (y:=measure_name_dict[x]) else x)
        if subset_named_measures:
            out= out[out.measure.isin(measure_name_dict.values())]    
    if not verbose:
        out = out.loc[:, ~out.columns.str.contains('^RewardPrimary|^RewardSecondary|^BackGround|^StartingPrimary|^StartingSecondary|^IRItype|^binNumber')]
    
    return out

def read_medpc_files(filenames, remove_first: list = [], measure_name_dict = {},  subset_named_measures = False, timestamp_measures = []):
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    out = []
    if type(filenames)== str: filenames= [filenames]
    for file in (filenames) if len(filenames)>10 else filenames:
        # if not os.path.isfile(file): print(f'Could not find file {file}')
        try:  
            # with open(file) as f: test = f.read()
            if 'Start Date:' in file.split('\n',1)[0]:
                
                try: out += [read_file(filename=file, remove_first=remove_first, measure_name_dict=measure_name_dict, 
                          subset_named_measures=subset_named_measures, timestamp_measures=timestamp_measures).assign(fmt = 'new', real_filename = file)]
                except: 
                    print(f'{file}: tried new format, didnt work rerunning with old format')
                    out += [read_file_old_format(filename=file, measure_name_dict=measure_name_dict, subset_named_measures=subset_named_measures).assign(fmt = 'old', real_filename = file)]
            else:
                try: out += [read_file_old_format(filename=file,  measure_name_dict=measure_name_dict, subset_named_measures=subset_named_measures).assign(fmt = 'old', real_filename = file)]
                except: 
                    print(f'{file}: tried old format, didnt work rerunning with new format')
                    out += [read_file(filename=file, remove_first=remove_first, measure_name_dict=measure_name_dict, 
                          subset_named_measures=subset_named_measures, timestamp_measures=timestamp_measures).assign(fmt = 'new', real_filename = file)]
        except: print(f"{file}: didn't work with either format")
    if not len(out): 
        print(f"{'|'.join(filenames)}: no files were read return empty df")
        return pd.DataFrame(columns = ['Subject','measure','measure_timestamp', 'final_order'])
    out = pd.concat(out)
    out = add_final_order(out)
    # out = out.groupby(['Subject', 'measure'],group_keys = False )\
    #         .apply(lambda x: sorted_day_experiment(x.sort_values('measure_timestamp')).assign(final_order = range(len(x))))
    return out.sort_values(['Subject','measure_timestamp', 'measure']).reset_index(drop = True)