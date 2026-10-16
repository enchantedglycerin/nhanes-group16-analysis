"""Report blocks, CSV tables and the shared Word exporter."""

import csv
import html
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

def plain(text):
    return re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',text)

class Report:

    def __init__(self,folder,title,short_title,variant):
        self.folder=Path(folder)
        self.title=title
        self.short_title=short_title
        self.variant=variant
        self.blocks=[]

    def h(self,text,level=2,main=False):
        self.blocks.append(dict(type='heading',text=text,level=level,main=main))

    def p(self,text,main=True,style=''):
        self.blocks.append(dict(type='paragraph',text=text,main=main,style=style))

    def table(self,title,headers,rows,filename):
        self.blocks.append(dict(type='table',title=title,headers=headers,rows=rows))
        with (self.folder/filename).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(headers);writer.writerows(rows)

    def fig(self,filename,caption):
        self.blocks.append(dict(type='figure',filename=filename,caption=caption))

    def page(self):
        self.blocks.append(dict(type='break'))

    def _docx(self,wc):
        # Minimal standard Office Open XML keeps Word output dependency-free.
        W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
        A='http://schemas.openxmlformats.org/drawingml/2006/main'
        PIC='http://schemas.openxmlformats.org/drawingml/2006/picture'
        for prefix,uri in [('w',W),('r',R),('wp',WP),('a',A),('pic',PIC)]:ET.register_namespace(prefix,uri)
        def el(parent,tag,attrs=None,text=None):
            ns,local=tag.split(':');mapping={'w':W,'r':R,'wp':WP,'a':A,'pic':PIC}
            converted={('{'+mapping[k.split(':')[0]]+'}'+k.split(':')[1] if ':' in k else k):str(v) for k,v in (attrs or {}).items()}
            node=ET.SubElement(parent,'{'+mapping[ns]+'}'+local,converted)
            if text is not None:node.text=str(text)
            return node
        doc=ET.Element('{'+W+'}document');body=el(doc,'w:body')
        external_links=[]
        def paragraph(text,style=None):
            p=el(body,'w:p')
            if style:el(el(p,'w:pPr'),'w:pStyle',{'w:val':style})
            cursor=0
            for match in re.finditer(r'\[([^\]]+)\]\((https?://[^)]+)\)',text):
                if match.start()>cursor:
                    t=el(el(p,'w:r'),'w:t',text=text[cursor:match.start()]);t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
                rid=f'rIdLink{len(external_links)+1}';external_links.append((rid,match.group(2)))
                hyperlink=el(p,'w:hyperlink',{'r:id':rid});run=el(hyperlink,'w:r');props=el(run,'w:rPr')
                el(props,'w:color',{'w:val':'126580'});el(props,'w:u',{'w:val':'single'});el(run,'w:t',text=match.group(1))
                cursor=match.end()
            if cursor<len(text):
                t=el(el(p,'w:r'),'w:t',text=text[cursor:]);t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
            return p
        paragraph(self.title,'Title')
        paragraph(f'NHANES 2021–2023 teaching extract | Variant {self.variant} | Main text: {wc:,} words','Subtitle')
        paragraph(f'กลุ่มที่ {self.group_number}','Subtitle')
        images=[]
        for b in self.blocks:
            if b['type']=='heading':paragraph(b['text'],'Heading'+str(min(b['level']-1,2)))
            elif b['type']=='paragraph':paragraph(b['text'],'Caption' if b['style']=='caption' else None)
            elif b['type']=='break':el(el(el(body,'w:p'),'w:r'),'w:br',{'w:type':'page'})
            elif b['type']=='table':
                caption=paragraph(b['title'],'Caption')
                el(caption.find('{'+W+'}pPr'),'w:keepNext')
                table=el(body,'w:tbl');pr=el(table,'w:tblPr')
                el(pr,'w:tblStyle',{'w:val':'TableGrid'});el(pr,'w:tblW',{'w:w':'0','w:type':'auto'})
                grid=el(table,'w:tblGrid')
                width=int(9360/len(b['headers']))
                for _ in b['headers']:el(grid,'w:gridCol',{'w:w':width})
                for index,row in enumerate([b['headers']]+b['rows']):
                    tr=el(table,'w:tr')
                    if index==0:el(el(tr,'w:trPr'),'w:tblHeader')
                    for value in row:
                        cell=el(tr,'w:tc');cp=el(cell,'w:tcPr');el(cp,'w:tcW',{'w:w':width,'w:type':'dxa'})
                        if index==0:el(cp,'w:shd',{'w:fill':'E3EFF3'})
                        p=el(cell,'w:p');run=el(p,'w:r')
                        if index==0:el(el(run,'w:rPr'),'w:b')
                        el(run,'w:t',text=plain(str(value)))
                paragraph('')
            elif b['type']=='figure':
                image_id=len(images)+1;rid=f'rIdImage{image_id}';images.append((rid,self.folder/b['filename']))
                p=el(body,'w:p');el(el(p,'w:pPr'),'w:keepNext')
                drawing=el(el(p,'w:r'),'w:drawing');inline_node=el(drawing,'wp:inline',{'distT':0,'distB':0,'distL':0,'distR':0})
                cx,cy=493*12700,296*12700
                el(inline_node,'wp:extent',{'cx':cx,'cy':cy});el(inline_node,'wp:docPr',{'id':image_id,'name':f'Figure {image_id}'})
                graphic=el(inline_node,'a:graphic');gd=el(graphic,'a:graphicData',{'uri':PIC});pic=el(gd,'pic:pic')
                nv=el(pic,'pic:nvPicPr');el(nv,'pic:cNvPr',{'id':image_id,'name':f'image{image_id}.png'});el(nv,'pic:cNvPicPr')
                fill=el(pic,'pic:blipFill');el(fill,'a:blip',{'r:embed':rid});el(el(fill,'a:stretch'),'a:fillRect')
                props=el(pic,'pic:spPr');trans=el(props,'a:xfrm');el(trans,'a:off',{'x':0,'y':0});el(trans,'a:ext',{'cx':cx,'cy':cy})
                el(el(props,'a:prstGeom',{'prst':'rect'}),'a:avLst')
                paragraph(b['caption'],'Caption')
        section=el(body,'w:sectPr');el(section,'w:pgSz',{'w:w':11906,'w:h':16838})
        el(section,'w:pgMar',{'w:top':1080,'w:bottom':1080,'w:left':1000,'w:right':1000,'w:header':360,'w:footer':360})
        relationships='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdStyles" Type="'+R+'/styles" Target="styles.xml"/>'+''.join(f'<Relationship Id="{rid}" Type="{R}/image" Target="media/image{i}.png"/>' for i,(rid,_) in enumerate(images,1))+''.join(f'<Relationship Id="{rid}" Type="{R}/hyperlink" Target="{html.escape(url,quote=True)}" TargetMode="External"/>' for rid,url in external_links)+'</Relationships>'
        styles=f'''<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:sz w:val="40"/><w:b/><w:color w:val="12566C"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:rPr><w:sz w:val="20"/><w:color w:val="52697A"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="100"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="12566C"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:pPr><w:keepNext/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="Caption"/><w:rPr><w:sz w:val="18"/><w:color w:val="455B6A"/></w:rPr></w:style><w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders>{''.join(f'<w:{x} w:val="single" w:sz="4" w:color="C6D3DA"/>' for x in ['top','left','bottom','right','insideH','insideV'])}</w:tblBorders></w:tblPr></w:style></w:styles>'''
        content_types='''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
        root_rels='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="'+R+'/officeDocument" Target="word/document.xml"/></Relationships>'
        with zipfile.ZipFile(self.folder/'report.docx','w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('[Content_Types].xml',content_types);archive.writestr('_rels/.rels',root_rels)
            archive.writestr('word/document.xml',ET.tostring(doc,encoding='utf-8',xml_declaration=True))
            archive.writestr('word/styles.xml',styles);archive.writestr('word/_rels/document.xml.rels',relationships)
            for i,(_,path) in enumerate(images,1):archive.write(path,f'word/media/image{i}.png')
