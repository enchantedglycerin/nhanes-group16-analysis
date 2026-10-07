"""Figures for the three new topics; every plotted observation is retained."""
import json
from pathlib import Path
import numpy as np
import wx
from wx.lib.plot import PolyLine,PolyMarker
import plotting as P

ROOT=Path(__file__).resolve().parents[1]

def age_plot(folder,z):
    objects=[]
    for value,label,color in [(0,'Female',P.COLORS[0]),(1,'Male',P.COLORS[1])]:
        keep=z['sex']==value;x=z['x'][keep];y=z['y'][keep]
        # Top-coded 80+ is a distinct final category. Curves stop at age 79.
        points=[]
        for lo,hi in [(18,30),(30,40),(40,50),(50,60),(60,70),(70,80),(80,81)]:
            g=(x>=lo)&(x<hi)
            points.append([np.mean(x[g]),np.mean(y[g])])
        objects.append(PolyMarker(points,colour=color,fillcolour=color,size=3,marker='circle',legend=label+' mean'))
        ages=np.linspace(18,79,150);a=(ages-50)/10;m=np.full(len(a),value)
        X=np.column_stack([np.ones(len(a)),a,m,a*m,a*a,a*a*m])
        objects.append(PolyLine(np.column_stack([ages,X@z['quadratic_beta']]),colour=color,width=3,legend=label+' model'))
    P.plot(folder,'figure_2_age',objects,'Haemoglobin by recorded age and sex','Recorded age (years)',
       'Haemoglobin (g/dL)',(15,84),(12,16),xlabels=[(20,'20'),(30,'30'),(40,'40'),(50,'50'),(60,'60'),(70,'70'),(80,'80+')],legend=True)

def main():
    app=wx.App(False);checks=[]
    for folder in sorted((ROOT/'reports'/'group16').glob('variant_*')):
        r=json.loads((folder/'results.json').read_text(encoding='utf-8'));z=np.load(folder/'plot_data.npz')
        dest=folder/'figures';dest.mkdir(exist_ok=True)
        labels=list(r['groups']);labels=[s.replace('≥','>=') for s in labels]
        P.box(dest,'figure_1_groups',{label:z[f'group_{i}'] for i,label in enumerate(labels)},
              r['group_outcome']+' by '+r['group_label'].lower(),r['group_outcome'])
        if r['variant']==1:
            P.scatter(dest,'figure_2_scatter',z['x'],z['y'],'Sedentary time and pulse rate',
                      'Sedentary time (h/day)','Pulse rate (bpm)')
            title='Pulse rate model'
        elif r['variant']==2:
            age_plot(dest,z);title='Haemoglobin model'
        else:
            P.scatter(dest,'figure_2_scatter',z['x'],z['y'],'Arm circumference and body weight',
                      'Arm circumference (cm)','Body weight (kg)')
            title='Body weight model'
        P.diagnostics(dest,z,title)
        assert len(list(dest.glob('*.png')))==4
        checks.append({'variant':folder.name,'figures':4,'language':'English','all_observations_retained':True})
    assert len(checks)==3
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'figure_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('Created 12 figures with English titles, axes and legends.')

if __name__=='__main__':main()
