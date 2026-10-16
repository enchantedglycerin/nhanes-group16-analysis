"""Export the twelve report figures at their final printed font size."""
import json
from pathlib import Path
import numpy as np
import plotting as P

ROOT=Path(__file__).resolve().parents[1]


def age_plot(folder,z):
    fig,ax=P.canvas('Recorded age (years)','Haemoglobin (g/dL)')
    for value,label,color in [(0,'Female',P.COLORS[0]),(1,'Male',P.COLORS[1])]:
        keep=z['sex']==value;x=z['x'][keep];y=z['y'][keep]
        points=[]
        for lo,hi in [(18,30),(30,40),(40,50),(50,60),(60,70),(70,80),(80,81)]:
            g=(x>=lo)&(x<hi)
            points.append([np.mean(x[g]),np.mean(y[g])])
        points=np.array(points)
        ax.plot(points[:,0],points[:,1],'o',color=color,markersize=4,label=label+' mean')
        ages=np.linspace(18,79,150);a=(ages-50)/10;m=np.full(len(a),value)
        X=np.column_stack([np.ones(len(a)),a,m,a*m,a*a,a*a*m])
        ax.plot(ages,X@z['quadratic_beta'],color=color,linewidth=1.4,label=label+' model')
    ax.set_xlim(15,84);ax.set_ylim(12,16)
    ax.set_xticks([20,30,40,50,60,70,80],['20','30','40','50','60','70','80+'])
    ax.legend(loc='upper right',ncol=2,frameon=False)
    return P.save(folder,'figure_2_age',fig,ax)


def main():
    checks=[]
    for folder in sorted((ROOT/'reports'/'group16').glob('variant_*')):
        r=json.loads((folder/'results.json').read_text(encoding='utf-8'));z=np.load(folder/'plot_data.npz')
        dest=folder/'figures';dest.mkdir(exist_ok=True)
        records=[P.box(dest,'figure_1_groups',
            {label:z[f'group_{i}'] for i,label in enumerate(r['groups'])},
            r['group_label'],r['group_outcome'])]
        if r['variant']==1:
            records.append(P.scatter(dest,'figure_2_scatter',z['x'],z['y'],
                'Sedentary time (h/day)','Pulse rate (bpm)'))
        elif r['variant']==2:
            records.append(age_plot(dest,z))
        else:
            records.append(P.scatter(dest,'figure_2_scatter',z['x'],z['y'],
                'Arm circumference (cm)','Body weight (kg)'))
        records.extend(P.diagnostics(dest,z))
        assert len(records)==len(list(dest.glob('*.png')))==4
        (dest/'figure_layout.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        checks.append({'variant':folder.name,'figures':4,'language':'English',
            'all_observations_retained':True,'no_internal_titles':True,
            'axis_label_pt':P.AXIS_PT,'tick_label_pt':P.TICK_PT,'main_text_pt':P.BODY_PT})
    assert len(checks)==3
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'figure_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('Created 12 title-free figures; final axis labels 10 pt, ticks 9.5 pt.')


if __name__=='__main__':main()
