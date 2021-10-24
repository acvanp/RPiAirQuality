# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as dates
from StringIO import StringIO
import pandas as pd


df = pd.read_csv(r'AQMOct_23_2021.csv')#,error_bad_lines=False )#.iloc[-10000:,:] or .iloc[-100000:-90000,:]
df = df.reset_index()

def flyers(dfcol, window):
    # take out any bad data pionts where the signal instantaneously and unrealistically jumps
    temp = [dfcol[0]]
    for i in range(1,len(dfcol)):
        if (abs(dfcol[i] - temp[-1]) > (window * temp[-1])) or  (abs(dfcol[i] - temp[-1]) > 150):
            temp.append(temp[-1])
        else: temp.append(dfcol[i])
    return temp
    
df['Temperature'] = flyers(df['Temperature'].tolist(), 0.2)
df['MQ2_VCs'] = flyers(df['MQ2_VCs'].tolist(), 0.5)
df['Humidity'] = flyers(df['Humidity'].tolist(), 0.3)
df['Pressure'] = flyers(df['Pressure'].tolist(), 0.2)

#print(df.index.tolist())
check1 = df[(df['Indoor_Outdoor'] == 1) & (df['Sample_Conditioning']==0)]
check2 = df[(df['Indoor_Outdoor'] == 1) & (df['Sample_Conditioning']==1)]

def remove_samples(check):
    # makes list of samples to remove on the basis of not having enough rows to make a data point using the smooth function below
    # this may be necessary if your analyzer errors out and restarts several times, thus not fully completing the analytical cycles
    
    temp=[int(check.index[0])]
    remove = []
    for i in range(1, check.shape[0]):
        k = i
        i = int(check.index[i])
        #print(i)
        if (i == (temp[-1] + 1)) or (i == (temp[-1])):
            temp.append(i)
        else:
            if len(temp) > 35:
                temp = [int(check.index[k+1])]                
            else:
                remove = remove + temp
                temp = [int(check.index[k+1])]
    return remove

remove = remove_samples(check1)
remove = remove + remove_samples(check2)
#print(remove)
df.drop(df.index[remove])
#pd.read_pickle('AQdata.pkl')
df['Temperature(F)'] = [i*9/5 + 32 for i in df['Temperature'].tolist()]
df['Humidity(%)'] = df['Humidity']
indoor = df[(df['Indoor_Outdoor'] == 1) & (df['Sample_Conditioning']==1)]
outdoor = df[(df['Indoor_Outdoor'] == 0) & (df['Sample_Conditioning']==1)]
params = ['Temperature(F)', 'Humidity(%)', 'MQ2_VCs', 'Pressure', 'PM10_std', 'PM25_std']
concs = ['P03', 'P05', 'P1', 'P25', 'P5', 'P10' ]

smooth = [i + '_smooth' for i in params]

def smooth(df, params):
    # average every 30 rows of the sampled data for indoor or outdoor data
    mydict = {}
    for param in params:
        temp = []
        agg=[]
        c=0
        mqpct = df['MQ2_VCs'].tolist()[0]
        for entry in df[param]:
           if (param == 'MQ2_VCs') and (entry >1150): entry = temp[-1] 
           if param == 'MQ2_VCs':
               agg.append(100*(entry - mqpct) / mqpct)#normalize MQ VC data
           else: agg.append(int(entry))
           if c%30==0: #2 seconds per entry means 30*2seconds or 1 minute per aggregate
              temp.append(np.mean(agg)+0.1)
              agg = []
           c+=1
        mydict[param] = temp
    c=0
    timestamps = []
    for t in df['Timestamp'].tolist():
        if c%30==0: timestamps.append(t)
        c+=1
    mydict['Timestamp']=timestamps
    return mydict

indoor_smooth = smooth(indoor, params)
outdoor_smooth = smooth(outdoor, params)

#print(outdoor_smooth['Humidity(%)'])

templl = indoor_smooth['Temperature(F)']
indoor_ticks = []
indoor_ticklabels = []
c = 0
for t in indoor_smooth['Timestamp']:
    if c%np.floor(0.2*len(templl))==0:
        indoor_ticks.append(dates.datestr2num(t))
        indoor_ticklabels.append(t[:-3])
    c+=1
    #print(c)
    
mydatetimes = dates.datestr2num(indoor_smooth['Timestamp'])
fig = plt.figure(figsize=(14, 10), dpi=80)
fig.subplots_adjust(hspace=0.1, wspace=0.4)
   
for i in range(1,(len(params)+1)):
    #fig,ax1 = plt.subplots()
    param = params[i-1]
    print(param)
    ax1 = fig.add_subplot(3,3, i)
    l1,=ax1.plot(mydatetimes, indoor_smooth[param], color='purple',label='indoors')
    plt.xticks(rotation=90)
    ax2 = ax1.twinx()
    l2,=ax2.plot(dates.datestr2num(outdoor_smooth['Timestamp']), outdoor_smooth[param], color='blue',label='outdoors', alpha=0.4)
    if param == 'Temperature(F)':
        myrange = [60, 100]
    elif param == 'Humidity(%)':
        myrange = [10, 100]
        #print(df[param])
    elif param == 'MQ2_VCs':
        myrange = [-30, 30]
    elif param == 'Pressure':
        myrange = [99700, 102200]
    elif param == 'P03':
        myrange = [0.1,4000]
    else:
        myrange = [0.1,100]
    
    ax1.set_ylim(myrange)
    ax2.set_ylim(myrange)
    ax1.set_ylabel(param)
    ax1.set_xticks(indoor_ticks)
    ax1.set_xticklabels(['']*len(indoor_ticklabels))
    ax1.set_xlim(mydatetimes.min(), mydatetimes.max())
    ax2.set_xlim(mydatetimes.min(), mydatetimes.max())
    
    if param.startswith('PM'):
        ax1.set_yscale('log')
        ax2.set_yscale('log')
    
    if i == 1:
        plt.legend([l1,l2],['inside','outside'],fontsize=8)
        #ax2.legend(['out'],fontsize=8)

indoor_concs = smooth(indoor, concs)
outdoor_concs = smooth(outdoor, concs)

ax1 = fig.add_subplot(3,3, 7)
for conc in concs:
    ax1.plot(mydatetimes, indoor_concs[conc], label=conc)
    ax1.set_yscale('log')
    plt.xticks(rotation=90)
    ax1.set_xticks(indoor_ticks)
    ax1.set_xticklabels(indoor_ticklabels)
    ax1.set_ylabel('ug/m3')  # Add a y-label to the axes.
    ax1.set_title("Indoor Particle Conc.",fontsize=8, y=1.0, pad=-14)  # Add a title to the axes.
    ax1.legend(fontsize=7)  # Add a legend.

ax1 = fig.add_subplot(3,3, 8)
for conc in concs:
    ax1.plot(dates.datestr2num(outdoor_smooth['Timestamp']), outdoor_concs[conc], label=conc)
    ax1.set_yscale('log')
    plt.xticks(rotation=90)
    ax1.set_xticks(indoor_ticks)
    ax1.set_xticklabels(indoor_ticklabels)
    ax1.set_ylabel('ug/m3')  # Add a y-label to the axes.
    ax1.set_title("Outdoor Particle Conc.", fontsize=8,y=1.0, pad=-14)  # Add a title to the axes.
    ax1.legend(fontsize=7)  # Add a legend.

ax1 = fig.add_subplot(3,3, 9)
minlen = min(len(indoor_smooth['Timestamp']), len(outdoor_smooth['Timestamp']))
# use this for comparing indoor and outdoor concs
# comparing the indoor and outdoor concs is hard because they are lists of values that are not the same length
cols = ['blue', 'orange', 'green', 'red', 'purple', 'brown']
c=0
for conc in concs:
    ratios = []
    for i in range(minlen):
        ratios.append((indoor_concs[conc][i])/(outdoor_concs[conc][i]))# add 0.000001 in the ratio'd values so as to not divide by zero
    ax1.plot(mydatetimes, ratios, label=conc, linewidth=1, alpha=0.3, color=cols[c])
    ax1.set_yscale('log')
    plt.xticks(rotation=90)
    ax1.set_xticks(indoor_ticks)
    ax1.set_xticklabels(indoor_ticklabels)
    ax1.set_ylabel('ug/m3')  # Add a y-label to the axes.
    ax1.set_title("Indoor/Outdr Part. Conc. Ratios", fontsize=8,y=1.0, pad=-14)  # Add a title to the axes.
    ax1.legend(fontsize=7)  # Add a legend.
    ax1.set_ylim(0.001, 1000)
    ax1.hlines(1, mydatetimes[0], mydatetimes[-1], linewidth=0.55, alpha=0.7, linestyle='--', color='black')
    c+=1

fig.savefig('Air_Quality_panel.png', bbox_inches='tight')



# use this for comparing indoor and outdoor concs
# comparing the indoor and outdoor concs is hard because they are lists of values that are not the same length
cols = ['blue', 'orange', 'green', 'red', 'purple', 'brown']
c=0
fig = plt.figure(figsize=(6,6), dpi=80)
fig.subplots_adjust(hspace=0.1, wspace=0.4)
for conc in concs:
    plt.scatter(indoor_concs[conc][-minlen:], outdoor_concs[conc][-minlen:], label=conc, linewidth=1, alpha=0.3, color=cols[c])
    plt.xticks(rotation=90)
    plt.xlabel('indoor conc. ug/m3')  # Add a x-label to the axes.
    plt.ylabel('outdoor conc. ug/m3')  # Add a y-label to the axes.
    plt.title("Indoor/Outdr Part. Conc. Scatter", fontsize=8,y=1.0, pad=-14)  # Add a title to the axes.
    plt.legend(fontsize=7)  # Add a legend.
    plt.xlim(0.1,100000)
    plt.ylim(0.1,100000)
    plt.xscale('log')
    plt.yscale('log')
    c+=1
plt.plot([0.1,400000],[0.1,400000], color='black', ls="--")
    
fig.savefig('conc_scatter.png', bbox_inches='tight')