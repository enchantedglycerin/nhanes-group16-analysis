"""Validate the new Thai PDFs and Word files and render review previews."""
import hashlib
import json
import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import pymupdf
from PIL import Image,ImageDraw
from report_io import plain

ROOT=Path(__file__).resolve().parents[1]

def normalize(text):
    text=unicodedata.normalize('NFKC',text).replace('\u0e33','\u0e4d\u0e32')
    return re.sub(r'[\s\u200b\u00ad]+','',text)

def main():
    results=[]
    group=json.loads((ROOT/'group_members.json').read_text(encoding='utf-8'))
    names=[m['name'] for m in group['members']]
    group_number=group['group_number']
    forbidden=['กรอก','ชื่อกลุ่ม','รหัสนักศึกษา','[add','placeholder','Proposed work allocation','เบื้องต้น','ก่อนส่ง','ฉบับภาษาไทย v4']
    forbidden.extend(['รันตามลำดับ', 'tools/', 'font files', 'ZIP'])
    expected_sections=['บทนำ','วิธีดำเนินการศึกษา','ผลการศึกษา','อภิปรายผล','สรุปผล','เอกสารอ้างอิง',
       'Appendix A. Contribution statement','Appendix B. Missing data and selection',
       'Appendix C. Assumptions and program output','Appendix D. Regression diagnostic figures',
       'Appendix E. Sensitivity analyses and reproducibility']
    for folder in sorted((ROOT/'reports'/'group16').glob('variant_*')):
        blocks=json.loads((folder/'report_blocks.json').read_text(encoding='utf-8'))
        meta=json.loads((folder/'report_metadata.json').read_text(encoding='utf-8'))
        r=json.loads((folder/'results.json').read_text(encoding='utf-8'))
        pdf=pymupdf.open(folder/'report.pdf');pages=[];thumbs=[]
        for i,page in enumerate(pdf):
            txt=page.get_text();pages.append(txt)
            assert len(txt.strip())>50,(folder.name,i,'empty page')
            assert '\ufffd' not in txt and not re.search(r'[\u0400-\u052f]',txt),(folder.name,i,'Unicode mapping')
            for b in page.get_text('dict')['blocks']:
                if b['type']!=0:continue
                x0,y0,x1,y1=b['bbox']
                assert 0<=x0 and 0<=y0 and x1<=page.rect.width+.5 and y1<=page.rect.height+.5,(folder.name,i,'clipped text',b['bbox'])
            pix=page.get_pixmap(matrix=pymupdf.Matrix(.6,.6),alpha=False)
            thumbs.append(Image.frombytes('RGB',(pix.width,pix.height),pix.samples))
            if i<2 or any(phrase in normalize(txt) for phrase in map(normalize,['อภิปรายผล','Figures ประกอบผลการศึกษา','Appendix A.','Table 3.'])):
                page.get_pixmap(matrix=pymupdf.Matrix(1.35,1.35),alpha=False).save(folder/f'preview_page_{i+1}.png')
        whole=normalize('\n'.join(pages))
        assert all(normalize(h) in whole for h in expected_sections)
        for b in blocks:
            if b['type'] in ['paragraph','heading']:
                assert normalize(plain(b['text'])) in whole,(folder.name,'text absent',b['text'][:160])
            elif b['type']=='table':
                for value in [b['title'],*b['headers'],*[x for row in b['rows'] for x in row]]:
                    assert normalize(str(value)) in whole,(folder.name,'table cell absent',value)
            elif b['type']=='figure':assert normalize(b['caption']) in whole,(folder.name,'caption absent')
        urls=[url for b in blocks if b.get('style')=='reference' for url in re.findall(r'\[ต้นฉบับ\]\((https?://[^)]+)\)',b['text'])]
        actual=[l['uri'] for p in pdf for l in p.get_links() if l['kind']==pymupdf.LINK_URI]
        assert actual==urls and len(urls)>6
        assert sum(len(p.get_images()) for p in pdf)==4
        assert 0<meta['main_word_count']<=2500 and meta['technical_terms_language']=='en'
        assert meta['authors']==names and not meta['student_ids_pending']
        assert meta['group_number']==group_number==16 and not meta['group_details_pending']
        assert meta['document_status']=='final'
        assert all(normalize(f'กลุ่มที่ {group_number}') in normalize(p) for p in pages)
        for name in names:assert normalize(name) in normalize(pages[0])
        tables=[b for b in blocks if b['type']=='table' and b['title']=='Member responsibilities']
        assert len(tables)==1 and len(tables[0]['rows'])==4
        assert [row[0] for row in tables[0]['rows']]==names
        for phrase in forbidden:assert normalize(phrase) not in whole,(folder.name,'unfinished text',phrase)
        for path in [folder/'report.md',folder/'report.html',folder/'report_blocks.json',*folder.glob('table_*.csv')]:
            text=normalize(path.read_text(encoding='utf-8-sig'))
            for phrase in forbidden:assert normalize(phrase) not in text,(path.name,'unfinished text',phrase)
        main_text='\n'.join(b['text'] for b in blocks if b.get('main'))
        for term in ['ช่วงความเชื่อมั่น','ส่วนเบี่ยงเบนมาตรฐาน','สหสัมพันธ์','สัมประสิทธิ์','การถดถอย','ข้อมูลสูญหาย','ฮีโมโกลบิน','รอบเอว','ความดันโลหิต']:
            assert term not in main_text,('Thai technical term',term)
        for question in r['config']['questions']:assert question in main_text
        with zipfile.ZipFile(folder/'report.docx') as z:
            assert z.testzip() is None
            for path in z.namelist():
                if path.endswith(('.xml','.rels')):ET.fromstring(z.read(path))
            doc=ET.fromstring(z.read('word/document.xml'))
            txt=''.join(n.text or '' for n in doc.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
            for b in blocks:
                if b['type'] in ['paragraph','heading']:assert plain(b['text']) in txt,(folder.name,'Word text absent',b['text'][:80])
            for name in names:assert name in txt
            assert f'กลุ่มที่ {group_number}' in txt
            for phrase in forbidden:assert normalize(phrase) not in normalize(txt),(folder.name,'Word unfinished text',phrase)
            assert sum(p.startswith('word/media/') for p in z.namelist())==4
            rel=ET.fromstring(z.read('word/_rels/document.xml.rels'))
            assert [v.attrib['Target'] for v in rel if v.attrib.get('TargetMode')=='External']==urls
            assert b'Tahoma' in z.read('word/styles.xml') and b'th-TH' in z.read('word/styles.xml')
        width,height=thumbs[0].size;columns=3;rows=(len(thumbs)+2)//3
        sheet=Image.new('RGB',(columns*(width+12)+12,rows*(height+34)+12),'#dce4e8');draw=ImageDraw.Draw(sheet)
        for i,im in enumerate(thumbs):
            x=12+i%3*(width+12);y=12+i//3*(height+34)
            draw.text((x,y),f'Page {i+1}',fill='black');sheet.paste(im,(x,y+20))
        sheet.save(folder/'preview_contact_sheet.png')
        results.append({'variant':folder.name,'pages':len(pdf),'main_words':meta['main_word_count'],'figures':4,'reference_links':len(urls),
          'all_text_tables_captions_in_pdf':True,'all_prose_in_word':True,'four_named_members':True,
          'group_number':group_number,'document_status':'final','no_placeholders':True,
          'contribution_status':group['contribution_status'],
          'no_build_instructions_in_report':True,
          'english_technical_terms':True,'result_sha256':hashlib.sha256((folder/'results.json').read_bytes()).hexdigest()})
        pdf.close()
    assert len(results)==3
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'report_validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
