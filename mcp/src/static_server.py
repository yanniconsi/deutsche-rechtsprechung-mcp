from flask import Flask, render_template_string, abort
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

XML_DATA_DIR = os.environ.get('XML_DATA_DIR', '/app/mcp/data/bgh/raw')
BW_RAW_DIR = os.environ.get('BW_RAW_DIR', '/app/mcp/data/bw/raw')

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Court decision - {{ filename }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        .container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; font-size: 1.4em; margin-top: 30px; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e0e0e0; }
        p { margin-bottom: 12px; text-align: justify; }
        strong { color: #2c3e50; }
        a { color: #007bff; }
        .metadata { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 25px; font-size: 0.9em; }
        .metadata p { margin-bottom: 6px; }
        .dl-block { margin: 8px 0; display: flex; gap: 12px; align-items: flex-start; }
        .randnummer {
            min-width: 30px;
            color: #6c757d;
            font-size: 0.85em;
            font-weight: bold;
            padding-top: 2px;
            flex-shrink: 0;
        }
        .dd-content { flex: 1; }
        .dd-content p { margin-bottom: 8px; }
        .error { color: #dc3545; padding: 20px; background: #f8d7da; border-radius: 4px; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background: #f8f9fa; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <a href="javascript:history.back()" class="back-link">← Back</a>
        {{ content|safe }}
    </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# BGH: XML → HTML
# ---------------------------------------------------------------------------

def render_content_element(element):
    """Render generic XML content elements to HTML."""
    html_parts = []

    for child in element:
        tag = child.tag

        if tag == 'dl':
            html_parts.append('<div class="dl-block">')
            html_parts.append(render_content_element(child))
            html_parts.append('</div>')

        elif tag == 'dt':
            anchor = child.find('.//a')
            rd_text = ''.join(child.itertext()).strip()
            if anchor is not None and anchor.get('name'):
                rd_id = anchor.get('name')
                if rd_text:
                    html_parts.append(f'<span class="randnummer" id="{rd_id}">{rd_text}</span>')
                else:
                    html_parts.append(f'<span class="randnummer" id="{rd_id}"></span>')
            elif rd_text:
                html_parts.append(f'<span class="randnummer">{rd_text}</span>')

        elif tag == 'dd':
            html_parts.append('<div class="dd-content">')
            html_parts.append(render_content_element(child))
            html_parts.append('</div>')

        elif tag == 'p':
            text = ''.join(child.itertext()).strip()
            if text:
                html_parts.append(f'<p>{text}</p>')

        elif tag == 'div':
            html_parts.append(render_content_element(child))

        elif tag == 'table':
            html_parts.append('<table>')
            html_parts.append(render_content_element(child))
            html_parts.append('</table>')

        elif tag == 'tr':
            html_parts.append('<tr>')
            html_parts.append(render_content_element(child))
            html_parts.append('</tr>')

        elif tag in ('td', 'th'):
            text = ''.join(child.itertext()).strip()
            html_parts.append(f'<{tag}>{text}</{tag}>')

        elif tag in ('ul', 'ol'):
            html_parts.append(f'<{tag}>')
            html_parts.append(render_content_element(child))
            html_parts.append(f'</{tag}>')

        elif tag == 'li':
            text = ''.join(child.itertext()).strip()
            html_parts.append(f'<li>{text}</li>')

        else:
            text = ''.join(child.itertext()).strip()
            if text:
                html_parts.append(f'<p>{text}</p>')
            else:
                html_parts.append(render_content_element(child))

    return '\n'.join(html_parts)


def parse_xml_to_html(xml_path):
    """Parse German court decision XML (BGH) and convert to HTML"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        def get_text(tag):
            el = root.find(f'.//{tag}')
            return el.text.strip() if el is not None and el.text else None

        html_parts = []
        html_parts.append('<div class="metadata">')

        doknr = get_text('doknr')
        if doknr:
            html_parts.append(f'<p><strong>DokNr:</strong> {doknr}</p>')

        gericht = get_text('gertyp')
        if gericht:
            html_parts.append(f'<p><strong>Court:</strong> {gericht}</p>')

        datum = get_text('entsch-datum')
        if datum and len(datum) == 8:
            datum = f"{datum[6:8]}.{datum[4:6]}.{datum[0:4]}"
            html_parts.append(f'<p><strong>Date:</strong> {datum}</p>')

        az = get_text('aktenzeichen')
        if az:
            html_parts.append(f'<p><strong>Docket:</strong> {az}</p>')

        doktyp = get_text('doktyp')
        if doktyp:
            html_parts.append(f'<p><strong>Type:</strong> {doktyp}</p>')

        norm = get_text('norm')
        if norm:
            html_parts.append(f'<p><strong>Norms:</strong> {norm}</p>')

        identifier = get_text('identifier')
        if identifier:
            html_parts.append(f'<p><strong>Source:</strong> <a href="{identifier}" target="_blank">Original source (rechtsprechung-im-internet.de)</a></p>')

        html_parts.append('</div>')

        sections = [
            ('titelzeile', 'Headnote'),
            ('leitsatz', 'Headnote (official)'),
            ('tenor', 'Tenor'),
            ('tatbestand', 'Facts'),
            ('entscheidungsgruende', 'Reasons'),
            ('gruende', 'Reasons'),
            ('abwmeinung', 'Dissenting opinion'),
            ('sonstlt', 'Other'),
        ]

        for xml_tag, label in sections:
            el = root.find(f'.//{xml_tag}')
            if el is not None:
                full_text = ''.join(el.itertext()).strip()
                if full_text:
                    html_parts.append(f'<h2>{label}</h2>')
                    html_parts.append(render_content_element(el))

        return '\n'.join(html_parts)

    except ET.ParseError as e:
        logging.error(f"XML Parse Error: {e}")
        return f'<p class="error">Parse error: {e}</p>'
    except Exception as e:
        logging.error(f"Error: {e}")
        return f'<p class="error">Error: {e}</p>'


# ---------------------------------------------------------------------------
# BW: Crawled HTML → HTML
# ---------------------------------------------------------------------------

def render_bw_dl(dl_tag):
    """Convert <dl class="RspDL"> blocks into the dl-block/randnummer format."""
    html_parts = []
    for child in dl_tag.children:
        if not hasattr(child, 'name') or child.name is None:
            continue
        if child.name == 'dt':
            rd_text = child.get_text(strip=True)
            rd_id = child.get('id', '')
            if rd_id:
                html_parts.append(f'<span class="randnummer" id="{rd_id}">{rd_text}</span>')
            elif rd_text:
                html_parts.append(f'<span class="randnummer">{rd_text}</span>')
        elif child.name == 'dd':
            html_parts.append('<div class="dd-content">')
            inner_dl = child.find('dl')
            if inner_dl:
                html_parts.append('<div class="dl-block">')
                html_parts.append(render_bw_dl(inner_dl))
                html_parts.append('</div>')
            else:
                for p in child.find_all('p', recursive=False):
                    html_parts.append(f'<p>{p.get_text()}</p>')
                if not child.find('p'):
                    text = child.get_text(strip=True)
                    if text:
                        html_parts.append(f'<p>{text}</p>')
            html_parts.append('</div>')
        elif child.name == 'dl':
            html_parts.append('<div class="dl-block">')
            html_parts.append(render_bw_dl(child))
            html_parts.append('</div>')
    return '\n'.join(html_parts)


def parse_bw_html_to_html(html_path):
    """Parse a crawled state decision HTML page and return cleaned-up HTML."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        html_parts = []

        html_parts.append('<div class="metadata">')

        doc_id = os.path.splitext(os.path.basename(html_path))[0]
        html_parts.append(f'<p><strong>DokNr:</strong> {doc_id}</p>')

        doc_header = soup.find('div', class_=lambda c: c and 'documentHeader' in c)
        if doc_header:
            for table in doc_header.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).rstrip(':')
                        value = cells[1].get_text(strip=True)
                        if key and value and not 'Quelle' in key:
                            html_parts.append(f'<p><strong>{key}:</strong> {value}</p>')

        canon_link = soup.find('link', rel='canonical')
        if canon_link and canon_link.get('href'):
            href = canon_link['href']
            html_parts.append(f'<p><strong>Source:</strong> <a href="{href}" target="_blank">Original source (landesrecht-bw.de)</a></p>')

        html_parts.append('</div>')

        article = soup.find('article', attrs={'data-juris-toc': True})
        if not article:
            article = soup.find('article')

        if not article:
            return '<p class="error">No decision content found.</p>'

        content_elements = article.find_all(['h2', 'h3', 'h4', 'dl', 'p'])
        
        seen_dls = set()
        
        for element in content_elements:
            if element.name in ('h2', 'h3', 'h4') and 'unsichtbar' not in element.get('class', []):
                heading_text = element.get_text(strip=True)
                if heading_text and heading_text != 'Permalink':
                    html_parts.append(f'<h2>{heading_text}</h2>')

            elif element.name == 'dl' and 'RspDL' in element.get('class', []):
                if element in seen_dls: continue
                seen_dls.add(element)
                html_parts.append('<div class="dl-block">')
                html_parts.append(render_bw_dl(element))
                html_parts.append('</div>')

            elif element.name == 'p':
                parent_dl = element.find_parent('dl', class_='RspDL')
                if not parent_dl:
                    text = element.get_text(strip=True)
                    if text:
                        html_parts.append(f'<p>{text}</p>')

        if len(html_parts) == 2:
               html_parts.append('<p><em>Details could not be extracted reliably. Please refer to the original document.</em></p>')

        return '\n'.join(html_parts)

    except Exception as e:
        import traceback
        logging.error(f"BW HTML Parse Error: {e}\n{traceback.format_exc()}")
        return f'<p class="error">Parse error: {e}</p>'
# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

BASE_DATA_DIR = os.environ.get('BASE_DATA_DIR', '/app/mcp/data')

@app.route('/decisions/<path:filepath>')
def serve_decision(filepath):
    # Basic path traversal protection.
    filepath = filepath.replace('..', '').strip('/')
    
    # Supports e.g. "bw/xyz.html" and "bgh/xyz.xml".
    if filepath.startswith('markdown/'):
        filepath = filepath.replace('markdown/', 'bgh/', 1)
    
    parts = filepath.split('/')
    if len(parts) < 2:
        logging.error(f"Invalid filepath format: {filepath}")
        abort(404)
        
    state_or_court = parts[0]  # e.g. "bw", "by", "bgh"
    
    if state_or_court == 'bgh':
        filename = parts[-1]
        
        if filename.endswith('.md'):
            filename = filename[:-3] + '.xml'
            
        doc_id = filename.replace('.xml', '')
        
        xml_path = os.path.join(BASE_DATA_DIR, 'bgh', 'raw', doc_id, f"{doc_id}.xml")
        
        if not os.path.exists(xml_path):
            xml_path = os.path.join(BASE_DATA_DIR, 'bgh', 'raw', filename)
            
        logging.info(f"Accessing BGH file: {xml_path}")
        
        if not os.path.exists(xml_path):
            logging.error(f"File not found: {xml_path}")
            abort(404)
            
        try:
            html_content = parse_xml_to_html(xml_path)
            return render_template_string(TEMPLATE, content=html_content, filename=filename)
        except Exception as e:
            logging.error(f"Error parsing BGH XML: {str(e)}")
            abort(500)
            
    else:
        filename = parts[-1]
        html_path = os.path.join(BASE_DATA_DIR, state_or_court, 'raw', filename)
        
        logging.info(f"Accessing State ({state_or_court}) file: {html_path}")
        
        if not os.path.exists(html_path):
            logging.error(f"File not found: {html_path}")
            abort(404)
            
        try:
            html_content = parse_bw_html_to_html(html_path)
            return render_template_string(TEMPLATE, content=html_content, filename=filename)
        except Exception as e:
            logging.error(f"Error parsing State HTML: {str(e)}")
            abort(500)

@app.route('/health')
def health():
    return {"status": "ok", "service": "static-server"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)