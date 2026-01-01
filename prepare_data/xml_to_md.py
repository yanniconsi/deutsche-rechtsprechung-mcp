import os
import re
import sys
import xml.etree.ElementTree as ET


def clean_text(text):
    if text:
        # Replace newlines and multiple spaces with a single space
        return re.sub(r'\s+', ' ', text)
    return ""

def parse_element_to_markdown(element, context=None):
    """
    Recursively converts an XML element and its children to Markdown.
    """
    if context is None:
        context = {}
    
    md = ""
    
    # Handle text content of the current element (before children)
    if element.text:
        md += clean_text(element.text)
        
    for child in element:
        tag = child.tag
        
        # Dispatch based on tag
        if tag == 'p':
            # Add newlines before paragraphs
            md += "\n\n" + parse_element_to_markdown(child, context).strip()
        elif tag in ['b', 'strong']:
            md += "**" + parse_element_to_markdown(child, context) + "**"
        elif tag in ['i', 'em']:
            md += "*" + parse_element_to_markdown(child, context) + "*"
        elif tag == 'u' or (tag == 'span' and 'underline' in child.get('style', '')):
             md += "<u>" + parse_element_to_markdown(child, context) + "</u>"
        elif tag == 'br':
            md += "  \n"
        elif tag == 'table':
            md += "\n\n" + parse_table(child) + "\n\n"
        elif tag == 'dl':
             md += parse_dl(child, context)
        elif tag == 'a':
             text_content = parse_element_to_markdown(child, context)
             href = child.get('href')
             if href:
                 md += f"[{text_content}]({href})"
             else:
                 # Just an anchor name or similar
                 md += text_content
        elif tag == 'div':
             md += parse_element_to_markdown(child, context)
        elif tag in ['ul', 'ol']:
            # Basic list support if encountered
            md += "\n" + parse_list(child, context) + "\n"
        elif tag == 'li':
             md += "\n- " + parse_element_to_markdown(child, context)
        else:
             # Fallback: process children transparently
             md += parse_element_to_markdown(child, context)
             
        # Handle tail text (text after the child tag but before the next child or end of parent)
        if child.tail:
            md += clean_text(child.tail)
            
    return md

def parse_dl(dl, context):
    """
    Parses <dl> lists, specifically targeting the margin number structure 
    (dt -> number, dd -> content)
    """
    md = ""
    # We iterate manually to handle the dt/dd relationship
    for child in dl:
        if child.tag == 'dt':
            dt_text = parse_element_to_markdown(child, context).strip()
            if dt_text:
                # Margin number (Randnummer)
                md += f"\n\n**{dt_text}** "
            else:
                # Empty dt, just ensure spacing
                md += "\n\n"
        elif child.tag == 'dd':
            # Definition/Content
            content = parse_element_to_markdown(child, context).strip()
            md += content
    return md

def parse_list(list_elem, context):
    md = ""
    is_ordered = list_elem.tag == 'ol'
    for i, child in enumerate(list_elem):
        if child.tag == 'li':
            item_content = parse_element_to_markdown(child, context).strip()
            if is_ordered:
                md += f"{i+1}. {item_content}\n"
            else:
                md += f"- {item_content}\n"
    return md

def parse_table(table):
    """
    Basic table parser. Attempts to create a Markdown table.
    """
    rows = table.findall('.//tr')
    if not rows:
        return ""
    
    grid = []
    max_cols = 0
    
    # First pass: Extract data into a grid
    for tr in rows:
        row_cells = []
        for cell in tr.findall('.//td') + tr.findall('.//th'):
            cell_content = parse_element_to_markdown(cell).strip()
            # Replace newlines in cells with <br> or space to keep table structure
            cell_content = cell_content.replace('\n', '<br>')
            row_cells.append(cell_content)
            
            # Simple colspan handling: add empty cells
            colspan = int(cell.get('colspan', 1))
            for _ in range(colspan - 1):
                row_cells.append("")
                
        grid.append(row_cells)
        if len(row_cells) > max_cols:
            max_cols = len(row_cells)
            
    if not grid:
        return ""

    
    # Second pass: Remove empty columns
    if grid:
        num_cols = len(grid[0])
        cols_to_keep = []
        for c in range(num_cols):
            # Check if column is empty in all rows
            if any(row[c].strip() for row in grid):
                cols_to_keep.append(c)
        
        if cols_to_keep:
            new_grid = []
            for row in grid:
                new_grid.append([row[c] for c in cols_to_keep])
            grid = new_grid
            max_cols = len(cols_to_keep)
        else:
            # All empty?
            return ""

    # Third pass: Construct Markdown lines
    lines = []
    
    # 1. Header Row
    header = grid[0]
    # Pad header
    while len(header) < max_cols:
        header.append("")
    lines.append("| " + " | ".join(header) + " |")
    
    # 2. Separator Row
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    
    # 3. Data Rows
    for row in grid[1:]:
        while len(row) < max_cols:
            row.append("")
        lines.append("| " + " | ".join(row) + " |")
        
    return "\n".join(lines)

def convert_xml_to_md_text(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
        
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Error parsing XML: {e}")
        
    md_output = []

    # --- Metadata Extraction ---
    doknr = root.findtext('doknr') or ""
    ecli = root.findtext('ecli') or ""
    datum = root.findtext('entsch-datum') or ""
    aktenzeichen = root.findtext('aktenzeichen') or ""
    gertyp = root.findtext('gertyp') or ""
    gerort = root.findtext('gerort') or ""
    spruchkoerper = root.findtext('spruchkoerper') or ""
    norm = root.findtext('norm') or ""
    
    # Vorinstanz might contain markup, use parser
    vorinstanz_node = root.find('vorinstanz')
    vorinstanz = ""
    if vorinstanz_node is not None:
        vorinstanz = parse_element_to_markdown(vorinstanz_node).strip()
    
    titel_elem = root.find('.//titelzeile')
    if titel_elem is not None:
        titel_text = parse_element_to_markdown(titel_elem).strip()
    else:
        titel_text = "Urteil" # Fallback title
        
    metadata = {
        "title": titel_text,
        "doknr": doknr,
        "ecli": ecli,
        "datum": datum,
        "aktenzeichen": aktenzeichen,
        "gertyp": gertyp,
        "gerort": gerort,
        "spruchkoerper": spruchkoerper,
        "norm": norm,
        "vorinstanz": vorinstanz
    }

    # Output Header
    md_output.append(f"# {titel_text}")
    md_output.append(f"\n**Gericht:** {gertyp} {gerort} | **Spruchkörper:** {spruchkoerper}")
    md_output.append(f"**DokNr:** {doknr} | **ECLI:** {ecli} | **Datum:** {datum} | **Az:** {aktenzeichen}")
    if norm:
        md_output.append(f"**Normen:** {norm}")
    if vorinstanz:
        md_output.append(f"**Vorinstanz:** {vorinstanz}")
    md_output.append("\n---\n")
    
    # --- Main Sections ---
    # Define sections to process in order
    sections = [
        ('leitsatz', 'Leitsatz'),
        ('sonstosatz', 'Sonstosatz?'),
        ('tenor', 'Tenor'),
        ('tatbestand', 'Tatbestand'),
        ('entscheidungsgruende', 'Entscheidungsgründe'),
        ('gruende', 'Gründe'),
        ('abwmeinung', 'Abwmeinung?'),
        ('sonstlt', 'Sonstlt?')
    ]
    
    for tag_name, display_name in sections:
        node = root.find(tag_name)
        if node is not None:
            content = parse_element_to_markdown(node).strip()
            if content:
                # Add to markdown output
                md_output.append(f"## {display_name}\n")
                md_output.append(content)
                md_output.append("\n---\n")
                
                # Add to metadata/JSON output
                # Use the tag name as key for cleaner JSON structure
                metadata[tag_name] = content
    
    return "\n".join(md_output), metadata

def main():
    if len(sys.argv) < 2:
        print("Usage: python xml_to_md.py <path_to_xml>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    print(convert_xml_to_md_text(file_path))

if __name__ == "__main__":
    main()
