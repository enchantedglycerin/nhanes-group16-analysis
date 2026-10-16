"""Thai report exports with Thai word breaks, embedded fonts and Unicode text."""
import html
import io
import os
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import pymupdf

from report_io import Report, plain

ROOT=Path(__file__).resolve().parents[1]
FONT_DIR=Path(os.environ.get('THAI_FONT_DIR', 'C:/Windows/Fonts'))
CSS='''
@font-face {font-family: Thai;src:url(tahoma.ttf);}
@font-face {font-family: Thai;src:url(tahomabd.ttf);font-weight:bold;}
body {font-family:Thai,Tahoma,sans-serif;font-size:10.5pt;line-height:1.52;color:#213343;margin:0;}
h1 {font-size:19pt;line-height:1.42;color:#12566c;margin:0 0 8pt;}
h2 {font-size:13pt;line-height:1.45;color:#12566c;margin:12pt 0 5pt;}
h3 {font-size:11pt;line-height:1.45;color:#12566c;margin:9pt 0 4pt;}
p {margin:0 0 8pt;}
table {border-collapse:collapse;width:100%;font-size:8.5pt;line-height:1.48;margin:5pt 0;}
td,th {border:0.5pt solid #c6d3da;padding:4pt;text-align:left;vertical-align:top;}
th {background-color:#e3eff3;color:#163d4d;font-weight:bold;}
.caption {font-size:8.5pt;line-height:1.5;color:#455b6a;margin-bottom:9pt;}
.meta {font-size:9pt;color:#52697a;}
.reference {font-size:8.5pt;line-height:1.35;margin-bottom:7pt;}
.break {page-break-before:always;}
a {color:#126580;}
img {width:493pt;height:296pt;}
'''


def fix_tahoma_unicode(document):
    """Add missing Thai glyph mappings emitted by MuPDF's Tahoma shaping.

    Tahoma's positioned tone-mark glyphs 0x477..0x47b (in this installed font)
    were omitted from the generated ToUnicode table. The glyphs draw correctly,
    but copying text otherwise yields their CID values as Cyrillic characters.
    The mappings cover the font's five base tone/cancellation glyphs and the
    alternate bold mai tho glyph found in the generated Thai headings.
    This changes text extraction only, never the page's drawn glyphs.
    """
    seen=set()
    for page in document:
        for xref,_,_,name,*_ in page.get_fonts():
            if 'Tahoma' not in name:
                continue
            kind,value=document.xref_get_key(xref,'ToUnicode')
            if kind!='xref':continue
            target=int(value.split()[0])
            if target in seen:continue
            seen.add(target)
            stream=document.xref_stream(target)
            # Confirm the installed Tahoma glyph order before applying the fix.
            assert b'<0434> <046d> <0e01>' in stream
            mappings={0x477+i:0xe48+i for i in range(5)}
            if 'Bold' in name:mappings[0x49f]=0xe49
            mappings.update({0x3:0x20,0x10:0x2d,0x1e:0x3b})
            addition=f'{len(mappings)} beginbfchar\n'+''.join(f'<{g:04x}> <{u:04x}>\n' for g,u in mappings.items())+'endbfchar\n'
            document.update_stream(target,stream.replace(b'endcmap',addition.encode()+b'endcmap'))


class ThaiReport(Report):
    edition=4

    def prepare_segmentation(self):
        texts={self.title}
        texts.update(getattr(self,'title_lines',[]))
        for block in self.blocks:
            for key in ['text','title','caption']:
                if key in block:texts.add(plain(block[key]))
            if block['type']=='table':
                texts.update(map(str,block['headers']))
                for row in block['rows']:texts.update(map(str,row))
        inp=self.folder/'_segment_input.json';out=self.folder/'_segment_output.json'
        inp.write_text(json.dumps(sorted(texts),ensure_ascii=False),encoding='utf-8')
        subprocess.run(['node',str(ROOT/'tools'/'segment_thai.mjs'),str(inp),str(out)],check=True,capture_output=True)
        self.segments=json.loads(out.read_text(encoding='utf-8'))
        inp.unlink();out.unlink()

    def inline(self,text):
        text=str(text)
        if '[' in text and re.search(r'\]\(https?://',text):
            # Bibliographic English requires no Thai word segmentation.
            escaped=html.escape(text)
            return re.sub(r'\[([^\]]+)\]\((https?://[^ ]+)\)',r'<a href="\2">\1</a>',escaped)
        rendered=self.segments.get(text,{}).get('display',text)
        return html.escape(rendered)

    def table_html(self,headers,rows):
        widths=[24,38,38] if headers==['ชื่อสมาชิก','หน้าที่หลัก','งานร่วมและการตรวจทาน'] else None
        head=''.join(('<th style="width:'+str(widths[i])+'%;">' if widths else '<th>')+self.inline(c)+'</th>' for i,c in enumerate(headers))
        return '<table><tr>'+head+'</tr>'+''.join(
            '<tr>'+''.join('<td>'+self.inline(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</table>'

    def save(self):
        self.prepare_segmentation()
        wc=sum(self.segments[plain(b['text'])]['count'] for b in self.blocks if b.get('main'))
        assert wc<=2500,(self.variant,'Thai main-text word count',wc)
        self.word_count=wc
        assert self.document_status=='final' and self.group_number==16
        meta='รายงาน Medical Data Analysis Using Python | NHANES ค.ศ. 2021–2023'
        detail=f'กลุ่มที่ {self.group_number} | เนื้อหาหลัก {wc:,} คำ'
        title_html='<br/>'.join(self.inline(line) for line in getattr(self,'title_lines',[self.title]))
        parts=[f'<h1>{title_html}</h1>',f'<p class="meta">{meta}<br/>{detail}</p>']
        md=[f'# {self.title}','',meta,'',detail,'']
        chunks=[{'html':'\n'.join(parts)}]
        for b in self.blocks:
            kind=b['type']
            if kind=='heading':
                fragment=f'<h{b["level"]}>{self.inline(b["text"])}</h{b["level"]}>'
                md.extend(['#'*b['level']+' '+b['text'],''])
            elif kind=='paragraph':
                fragment=f'<p class="{b["style"]}">{self.inline(b["text"])}</p>'
                md.extend([b['text'],''])
            elif kind=='table':
                fragment='<p class="caption"><b>'+self.inline(b['title'])+'</b></p>'+self.table_html(b['headers'],b['rows'])
                md.extend([f'**{b["title"]}**','','| '+' | '.join(map(str,b['headers']))+' |','| '+' | '.join('---' for _ in b['headers'])+' |'])
                md.extend('| '+' | '.join(map(str,row))+' |' for row in b['rows']);md.append('')
            elif kind=='figure':
                fragment=f'<img src="{b["filename"]}"/><p class="caption">{self.inline(b["caption"])}</p>'
                md.extend([f'![{b["caption"]}]({b["filename"]})',''])
            elif kind=='break':
                parts.append('<div class="break"></div>');chunks.append({'break':True});continue
            parts.append(fragment);chunks.append({'html':fragment,'heading':kind=='heading'})
        browser_css=CSS.replace('url(tahoma.ttf)','local("Tahoma")').replace('url(tahomabd.ttf)','local("Tahoma Bold")')
        (self.folder/'report.html').write_text('<!doctype html><html lang="th"><head><meta charset="utf-8"><title>'+html.escape(self.title)+'</title><style>'+browser_css+'</style></head><body>'+'\n'.join(parts)+'</body></html>',encoding='utf-8')
        (self.folder/'report.md').write_text('\n'.join(md),encoding='utf-8')
        self.pdf(chunks)
        self.docx(wc,meta,detail)
        (self.folder/'report_metadata.json').write_text(json.dumps({
            'title':self.title,'language':'th','edition':self.edition,'main_word_count':wc,
            'word_count_method':'Node Intl.Segmenter(th, word), isWordLike; approximate and software-dependent',
            'word_count_scope':'Introduction through Conclusion prose and headings; excludes tables, captions, references and appendices',
            'group_number':getattr(self,'group_number',None),
            'group_details_pending':getattr(self,'group_number',None) is None,
            'font':'Tahoma, embedded in PDF; local Windows font files not redistributed',
            'authors':getattr(self,'authors',[]),'student_ids_pending':getattr(self,'student_ids_pending',True),
            'student_ids_displayed':getattr(self,'student_ids_displayed',False),
            'document_status':getattr(self,'document_status','draft'),
            'contribution_status':getattr(self,'contribution_status','unfilled'),
            'technical_terms_language':getattr(self,'technical_terms_language','th'),
        },ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'Thai variant {self.variant}: {wc} segmented main-text words.',flush=True)

    def pdf(self,chunks):
        combined=[];i=0
        while i<len(chunks):
            c=chunks[i].copy()
            if c.get('heading') and i+1<len(chunks) and not chunks[i+1].get('break'):
                c['html']+=chunks[i+1]['html'];i+=1
            combined.append(c);i+=1
        archive=pymupdf.Archive(str(self.folder));archive.add(str(FONT_DIR))
        buffer=io.BytesIO();writer=pymupdf.DocumentWriter(buffer)
        rect=pymupdf.paper_rect('a4');content=pymupdf.Rect(50,51,rect.width-50,rect.height-47)
        device=writer.begin_page(rect);y=content.y0;pages=1
        for c in combined:
            if c.get('break'):
                if y>content.y0:writer.end_page();device=writer.begin_page(rect);y=content.y0;pages+=1
                continue
            story=pymupdf.Story(html=c['html'],user_css=CSS,archive=archive)
            more,filled=story.place(pymupdf.Rect(content.x0,y,content.x1,content.y1))
            if more:
                writer.end_page();device=writer.begin_page(rect);y=content.y0;pages+=1
                story.reset();more,filled=story.place(content)
            assert not more,('Thai block exceeds one page',c['html'][:160])
            story.draw(device);y=filled[3]+4
            assert pages<30
        writer.end_page();writer.close()
        document=pymupdf.open(stream=buffer.getvalue(),filetype='pdf')
        fix_tahoma_unicode(document)
        urls=[url for b in self.blocks if b.get('style')=='reference' for url in re.findall(r'\[ต้นฉบับ\]\((https?://[^)]+)\)',b['text'])]
        linked=0
        for i,page in enumerate(document):
            # Reference entries may continue beyond the page with their heading.
            for area in page.search_for('ต้นฉบับ'):
                assert linked<len(urls), ('Unexpected source-link label', i)
                page.insert_link({'kind':pymupdf.LINK_URI,'from':area,'uri':urls[linked]});linked+=1
            page.draw_line((50,34),(rect.width-50,34),color=(.08,.34,.42),width=.7)
            page.insert_font(fontname='ThaiFooter',fontfile=str(FONT_DIR/'tahoma.ttf'))
            header=f'กลุ่มที่ {self.group_number} | Medical Data Analysis Using Python'
            page.insert_text((50,26),header,fontname='ThaiFooter',fontsize=8,color=(.25,.35,.42))
            footer='NHANES | Teaching dataset | Unweighted analysis'
            page.insert_text((50,rect.height-27),footer,fontname='ThaiFooter',fontsize=8,color=(.3,.4,.45))
            page.insert_text((rect.width-93,rect.height-27),f'{i+1} / {len(document)}',fontsize=8,color=(.3,.4,.45))
        assert linked==len(urls) and linked>=3,(self.variant,linked,len(urls))
        subject=f'Medical statistics report | Group {self.group_number}'
        document.set_metadata({'title':self.title,'subject':subject,
                               'author':'; '.join(self.authors),
                               'creator':'Python report builder'})
        document.subset_fonts()
        document.save(self.folder/'report.pdf',garbage=4,deflate=True)
        document.close()

    def docx(self,wc,meta,detail):
        super()._docx(wc)
        path=self.folder/'report.docx'
        with zipfile.ZipFile(path) as z:contents={name:z.read(name) for name in z.namelist()}
        W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        doc=ET.fromstring(contents['word/document.xml']);body=doc.find('{'+W+'}body')
        paragraphs=body.findall('{'+W+'}p')
        if getattr(self,'title_lines',None):
            for child in list(paragraphs[0]):
                if child.tag=='{'+W+'}r':paragraphs[0].remove(child)
            for index,line in enumerate(self.title_lines):
                run=ET.SubElement(paragraphs[0],'{'+W+'}r')
                if index:ET.SubElement(run,'{'+W+'}br')
                ET.SubElement(run,'{'+W+'}t').text=line
        paragraphs[1].find('.//{'+W+'}t').text=meta
        paragraphs[2].find('.//{'+W+'}t').text=detail
        styles=ET.fromstring(contents['word/styles.xml'])
        for font in styles.findall('.//{'+W+'}rFonts'):
            for attr in ['ascii','hAnsi','eastAsia','cs']:font.set('{'+W+'}'+attr,'Tahoma')
        for props in styles.findall('.//{'+W+'}rPr'):
            lang=ET.SubElement(props,'{'+W+'}lang');lang.set('{'+W+'}val','th-TH');lang.set('{'+W+'}eastAsia','th-TH')
            size=props.find('{'+W+'}sz')
            if size is not None:
                cs=ET.SubElement(props,'{'+W+'}szCs');cs.set('{'+W+'}val',size.get('{'+W+'}val'))
        for spacing in styles.findall('.//{'+W+'}spacing'):
            if '{'+W+'}line' in spacing.attrib:spacing.set('{'+W+'}line','360')
        contents['word/document.xml']=ET.tostring(doc,encoding='utf-8',xml_declaration=True)
        contents['word/styles.xml']=ET.tostring(styles,encoding='utf-8',xml_declaration=True)
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for name,data in contents.items():z.writestr(name,data)
