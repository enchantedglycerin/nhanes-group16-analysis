"""Export standalone scientific plots with the installed wxPython plotting library."""
from statistics import NormalDist
import numpy as np
import wx
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker

COLORS=['#167D8D','#D28434','#72589B']
np.random.seed(4101)  # deterministic boxplot outlier jitter; no data changes


class Canvas(PlotCanvas):
    xlabels=None
    ylabels=None
    def _xticks(self,*args):
        return self.xlabels if self.xlabels is not None else super()._xticks(*args)
    def _yticks(self,*args):
        return self.ylabels if self.ylabels is not None else super()._yticks(*args)


def plot(folder,name,objects,title,xlabel,ylabel,xrange=None,yrange=None,xlabels=None,ylabels=None,legend=False):
    frame=wx.Frame(None,size=(1500,900))
    canvas=Canvas(frame)
    canvas.SetSize((1500,900))
    canvas.fontSizeAxis=17
    canvas.fontSizeTitle=21
    canvas.fontSizeLegend=14
    canvas.enableGrid=(False,True)
    canvas.enableLegend=legend
    canvas.xlabels=xlabels
    canvas.ylabels=ylabels
    canvas.Draw(PlotGraphics(objects,title,xlabel,ylabel),xAxis=xrange,yAxis=yrange)
    assert canvas.SaveFile(str(folder/f'{name}.png'))
    frame.Destroy()


def scatter(folder,name,x,y,title,xlabel,ylabel):
    objects=[PolyMarker(np.column_stack([x,y]),colour='#AABBC1',fillcolour='#AABBC1',size=.9,marker='circle')]
    bins=np.array_split(np.argsort(x,kind='stable'),10)
    points=np.array([[np.median(x[i]),np.median(y[i])] for i in bins])
    objects.extend([PolyLine(points,colour=COLORS[0],width=4,legend='Median in 10 equal-count bins'),
                    PolyMarker(points,colour=COLORS[0],fillcolour=COLORS[0],size=3,marker='circle')])
    dx=(x.max()-x.min())*.025
    dy=(y.max()-y.min())*.04
    plot(folder,name,objects,title,xlabel,ylabel,(float(x.min()-dx),float(x.max()+dx)),
         (float(y.min()-dy),float(y.max()+dy)),legend=False)


def box(folder,name,groups,title,ylabel):
    objects=[]
    labels=[]
    for i,(label,data) in enumerate(groups.items(),1):
        color=COLORS[i-1]
        q1,median,q3=np.quantile(data,[.25,.5,.75])
        iqr=q3-q1
        low=np.min(data[data>=q1-1.5*iqr])
        high=np.max(data[data<=q3+1.5*iqr])
        objects.extend([
            PolyLine([(i-.25,q1),(i+.25,q1),(i+.25,q3),(i-.25,q3),(i-.25,q1)],colour=color,width=3),
            PolyLine([(i-.25,median),(i+.25,median)],colour=color,width=5),
            PolyLine([(i,low),(i,q1)],colour=color,width=2),
            PolyLine([(i,q3),(i,high)],colour=color,width=2),
            PolyLine([(i-.12,low),(i+.12,low)],colour=color,width=2),
            PolyLine([(i-.12,high),(i+.12,high)],colour=color,width=2),
        ])
        outliers=data[(data<low)|(data>high)]
        jitter=np.random.uniform(-.04,.04,len(outliers))
        objects.append(PolyMarker(np.column_stack([i+jitter,outliers]),colour=color,fillcolour=color,size=1.6))
        labels.append((i,f'{label} (n={len(data):,})'))
    all_y=np.concatenate(list(groups.values()))
    padding=(all_y.max()-all_y.min())*.055
    plot(folder,name,objects,title,'Group',ylabel,(.35,len(groups)+.65),
         (float(all_y.min()-padding),float(all_y.max()+padding)),xlabels=labels)


def diagnostics(folder,z,title):
    residual=z['residual']
    fitted=z['fit']
    bins=np.array_split(np.argsort(fitted),12)
    means=np.array([[np.mean(fitted[i]),np.mean(residual[i])] for i in bins])
    objects=[PolyMarker(np.column_stack([fitted,residual]),colour='#9EAEB8',fillcolour='#9EAEB8',size=.8),
             PolyLine([(float(fitted.min()),0),(float(fitted.max()),0)],colour='#465566',width=2),
             PolyLine(means,colour='#CB7334',width=3,legend='Binned mean residual')]
    plot(folder,'diagnostic_residuals',objects,title+' | residuals','Fitted outcome','Residual',legend=False)
    standard=(np.sort(residual)-np.mean(residual))/np.std(residual,ddof=1)
    theory=np.array([NormalDist().inv_cdf((i+.5)/len(residual)) for i in range(len(residual))])
    objects=[PolyLine([(float(theory.min()),float(theory.min())),(float(theory.max()),float(theory.max()))],colour='#CB7334',width=3),
             PolyMarker(np.column_stack([theory,standard]),colour=COLORS[0],fillcolour=COLORS[0],size=1.1)]
    plot(folder,'diagnostic_qq',objects,title+' | normal Q-Q','Theoretical normal quantile','Standardized residual')
