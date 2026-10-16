"""Publication-size figures with explicit font sizes and no internal titles."""
from statistics import NormalDist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

WIDTH_PT, HEIGHT_PT = 493.0, 296.0
AXIS_PT, TICK_PT, BODY_PT = 10.0, 9.5, 10.5
COLORS = ['#167D8D', '#D28434', '#72589B']
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':AXIS_PT,
    'axes.labelsize':AXIS_PT, 'xtick.labelsize':TICK_PT, 'ytick.labelsize':TICK_PT,
    'legend.fontsize':TICK_PT, 'pdf.fonttype':42, 'axes.spines.top':False,
    'axes.spines.right':False, 'axes.edgecolor':'#61737c', 'axes.labelcolor':'#213343',
    'xtick.color':'#465566', 'ytick.color':'#465566'})


def canvas(xlabel,ylabel):
    fig,ax=plt.subplots(figsize=(WIDTH_PT/72,HEIGHT_PT/72),dpi=300)
    fig.subplots_adjust(left=.145,right=.98,bottom=.18,top=.97)
    ax.set_xlabel(xlabel);ax.set_ylabel(ylabel)
    ax.grid(axis='y',color='#dce4e8',linewidth=.55)
    ax.set_axisbelow(True)
    return fig,ax


def save(folder,name,fig,ax):
    assert not ax.get_title() and fig._suptitle is None
    assert ax.xaxis.label.get_fontsize()==ax.yaxis.label.get_fontsize()==AXIS_PT
    folder.mkdir(parents=True,exist_ok=True)
    fig.savefig(folder/(name+'.png'),dpi=300,facecolor='white')
    fig.savefig(folder/(name+'.pdf'),facecolor='white')
    record={'file':name+'.png','vector_file':name+'.pdf','internal_title':'',
        'width_pt':WIDTH_PT,'height_pt':HEIGHT_PT,'axis_label_pt':AXIS_PT,
        'tick_label_pt':TICK_PT,'main_text_pt':BODY_PT,'dpi':300,
        'x_label':ax.get_xlabel(),'y_label':ax.get_ylabel()}
    plt.close(fig)
    return record


def box(folder,name,groups,xlabel,ylabel):
    fig,ax=canvas(xlabel,ylabel)
    labels=[f'{label}\n(n={len(data):,})' for label,data in groups.items()]
    artists=ax.boxplot(list(groups.values()),tick_labels=labels,patch_artist=True,
        widths=.45,whis=1.5,showfliers=True,
        medianprops={'color':'#213343','linewidth':1.6},
        flierprops={'marker':'o','markersize':2.0,'markeredgewidth':0,'alpha':.55})
    for i,patch in enumerate(artists['boxes']):
        patch.set_facecolor(COLORS[i]);patch.set_alpha(.25)
        patch.set_edgecolor(COLORS[i]);patch.set_linewidth(1.2)
        artists['fliers'][i].set_markerfacecolor(COLORS[i])
    return save(folder,name,fig,ax)


def scatter(folder,name,x,y,xlabel,ylabel):
    fig,ax=canvas(xlabel,ylabel)
    ax.scatter(x,y,s=3,color='#9cafb7',alpha=.55,edgecolors='none',rasterized=True)
    bins=np.array_split(np.argsort(x,kind='stable'),10)
    points=np.array([[np.median(x[i]),np.median(y[i])] for i in bins])
    ax.plot(points[:,0],points[:,1],'-o',color=COLORS[0],linewidth=1.4,markersize=3)
    ax.margins(x=.025,y=.04)
    return save(folder,name,fig,ax)


def diagnostics(folder,z):
    residual=z['residual'];fitted=z['fit']
    fig,ax=canvas('Fitted outcome','Residual')
    ax.scatter(fitted,residual,s=3,color='#9cafb7',alpha=.55,edgecolors='none',rasterized=True)
    bins=np.array_split(np.argsort(fitted),12)
    means=np.array([[np.mean(fitted[i]),np.mean(residual[i])] for i in bins])
    ax.axhline(0,color='#61737c',linewidth=.8)
    ax.plot(means[:,0],means[:,1],color=COLORS[1],linewidth=1.5)
    first=save(folder,'diagnostic_residuals',fig,ax)
    standard=(np.sort(residual)-np.mean(residual))/np.std(residual,ddof=1)
    theory=np.array([NormalDist().inv_cdf((i+.5)/len(residual)) for i in range(len(residual))])
    fig,ax=canvas('Theoretical normal quantile','Standardized residual')
    ax.plot([theory.min(),theory.max()],[theory.min(),theory.max()],color=COLORS[1],linewidth=1)
    ax.scatter(theory,standard,s=4,color=COLORS[0],alpha=.75,edgecolors='none',rasterized=True)
    return [first,save(folder,'diagnostic_qq',fig,ax)]
