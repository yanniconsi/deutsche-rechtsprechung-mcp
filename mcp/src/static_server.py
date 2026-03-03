from flask import Flask, render_template_string, abort
import os
import xml.etree.ElementTree as ET
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

XML_DATA_DIR = os.environ.get('XML_DATA_DIR', '/app/prepare_data/data/extracted')


def render_content_element(element):
    """Rendert beliebige XML-Inhaltselemente generisch zu HTML"""
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
            # Generisch: einfach den Text ausgeben falls vorhanden
            text = ''.join(child.itertext()).strip()
            if text:
                html_parts.append(f'<p>{text}</p>')
            else:
                html_parts.append(render_content_element(child))

    return '\n'.join(html_parts)


def parse_xml_to_html(xml_path):
    """Parse German court decision XML and convert to HTML"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Metadaten
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
            html_parts.append(f'<p><strong>Gericht:</strong> {gericht}</p>')

        datum = get_text('entsch-datum')
        if datum and len(datum) == 8:
            datum = f"{datum[6:8]}.{datum[4:6]}.{datum[0:4]}"
            html_parts.append(f'<p><strong>Datum:</strong> {datum}</p>')

        az = get_text('aktenzeichen')
        if az:
            html_parts.append(f'<p><strong>Aktenzeichen:</strong> {az}</p>')

        doktyp = get_text('doktyp')
        if doktyp:
            html_parts.append(f'<p><strong>Typ:</strong> {doktyp}</p>')

        norm = get_text('norm')
        if norm:
            html_parts.append(f'<p><strong>Normen:</strong> {norm}</p>')

        identifier = get_text('identifier')
        if identifier:
            html_parts.append(f'<p><strong>Quelle:</strong> <a href="{identifier}" target="_blank">Originalquelle (rechtsprechung-im-internet.de)</a></p>')

        html_parts.append('</div>')

        # Alle Inhaltssektionen dynamisch rendern
        sections = [
            ('titelzeile', 'Leitsatz'),
            ('leitsatz', 'Leitsatz (amtlich)'),
            ('tenor', 'Tenor'),
            ('tatbestand', 'Tatbestand'),
            ('entscheidungsgruende', 'Entscheidungsgründe'),
            ('gruende', 'Gründe'),
            ('abwmeinung', 'Abweichende Meinung'),
            ('sonstlt', 'Sonstiges'),
        ]

        for xml_tag, label in sections:
            el = root.find(f'.//{xml_tag}')
            if el is not None:
                # Prüfe ob Element irgendeinen Inhalt hat
                full_text = ''.join(el.itertext()).strip()
                if full_text:
                    html_parts.append(f'<h2>{label}</h2>')
                    html_parts.append(render_content_element(el))

        return '\n'.join(html_parts)

    except ET.ParseError as e:
        logging.error(f"XML Parse Error: {e}")
        return f'<p class="error">Fehler beim Parsen: {e}</p>'
    except Exception as e:
        logging.error(f"Error: {e}")
        return f'<p class="error">Fehler: {e}</p>'


@app.route('/decisions/<path:filepath>')
def serve_decision(filepath):
    filepath = filepath.replace('..', '').strip('/')

    if filepath.startswith('markdown/'):
        filepath = filepath[9:]
    if filepath.endswith('.md'):
        filepath = filepath[:-3] + '.xml'

    if not filepath.endswith('.xml'):
        doc_id = filepath.strip('/')
        xml_path = os.path.join(XML_DATA_DIR, doc_id, f"{doc_id}.xml")
    else:
        xml_path = os.path.join(XML_DATA_DIR, filepath)

    logging.info(f"Accessing file: {xml_path}")

    if not os.path.exists(xml_path):
        logging.error(f"File not found: {xml_path}")
        abort(404)

    try:
        html_content = parse_xml_to_html(xml_path)

        template = """
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Gerichtsentscheidung - {{ filename }}</title>
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
                <a href="javascript:history.back()" class="back-link">← Zurück</a>
                {{ content|safe }}
            </div>
        </body>
        </html>
        """

        filename = os.path.basename(filepath)
        return render_template_string(template, content=html_content, filename=filename)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        abort(500)


@app.route('/health')
def health():
    return {"status": "ok", "service": "static-server"}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)