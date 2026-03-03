import re
from typing import Optional, Tuple


def extract_structured_data(query: str) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extract structured data from query string using regex patterns.
    
    Args:
        query: Search query potentially containing structured data (e.g. 'BGH IX ZB 72/08 § 850c ZPO').
    
    Returns:
        Tuple of (cleaned_query, az, datum_von, datum_bis, normen, gericht)
    """
    cleaned_query = query
    extracted_az = None
    extracted_datum_von = None
    extracted_datum_bis = None
    extracted_normen = None
    extracted_gericht = None
    
    # Extract case reference numbers (Aktenzeichen)
    # Examples: "IX ZB 72/08", "1 BvR 123/20", "VIII ZR 1/19", "2 StR 45/21"
    az_patterns = [
        r'\b([IVX]+\s+[A-Z]+\s+\d+/\d+)\b',  # Roman numerals: IX ZB 72/08
        r'\b(\d+\s+[A-Z][a-z]*\s+\d+/\d+)\b',  # Arabic: 1 BvR 123/20
        r'\b(\d+\s+[A-Z]+\s+\d+/\d+)\b',  # Arabic: 2 StR 45/21
    ]
    
    for pattern in az_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            extracted_az = match.group(1)
            cleaned_query = cleaned_query.replace(match.group(0), '').strip()
            break
    
    # Extract dates
    # Full date (DD.MM.YYYY)
    date_full_match = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', query)
    if date_full_match:
        day, month, year = date_full_match.groups()
        extracted_datum_von = f"{year}{month.zfill(2)}{day.zfill(2)}"
        extracted_datum_bis = extracted_datum_von
        cleaned_query = cleaned_query.replace(date_full_match.group(0), '').strip()
    
    # Month name with year (e.g. "Januar 2010")
    month_names = {
        'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
        'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
        'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
    }
    date_month_match = re.search(
        r'\b(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember)\s+(\d{4})\b', 
        query, 
        re.IGNORECASE
    )
    if date_month_match and not extracted_datum_von:
        month_name, year = date_month_match.groups()
        month_num = month_names[month_name.lower()]
        extracted_datum_von = f"{year}{month_num}01"
        # Last day of month
        if month_num in ['01', '03', '05', '07', '08', '10', '12']:
            last_day = '31'
        elif month_num in ['04', '06', '09', '11']:
            last_day = '30'
        else:  # February
            last_day = '28'  # Simplified, ignoring leap years
        extracted_datum_bis = f"{year}{month_num}{last_day}"
        cleaned_query = cleaned_query.replace(date_month_match.group(0), '').strip()
    
    # Year only (e.g. "2010", "aus 2010")
    year_match = re.search(r'\b(aus\s+|vom\s+Jahr\s+)?(\d{4})\b', query)
    if year_match and not extracted_datum_von:
        year = year_match.group(2)
        # Only interpret as date if between 1990-2030
        if 1990 <= int(year) <= 2030:
            extracted_datum_von = f"{year}0101"
            extracted_datum_bis = f"{year}1231"
            cleaned_query = cleaned_query.replace(year_match.group(0), '').strip()
    
    # Relative date expressions
    if re.search(r'\b(nach|ab|seit)\s+(\d{4})\b', query):
        match = re.search(r'\b(nach|ab|seit)\s+(\d{4})\b', query)
        year = match.group(2)
        extracted_datum_von = f"{year}0101"
        cleaned_query = cleaned_query.replace(match.group(0), '').strip()
    
    if re.search(r'\b(vor|bis)\s+(\d{4})\b', query):
        match = re.search(r'\b(vor|bis)\s+(\d{4})\b', query)
        year = match.group(2)
        extracted_datum_bis = f"{year}1231"
        cleaned_query = cleaned_query.replace(match.group(0), '').strip()
    
    # Extract legal norms
    # Examples: "§ 536 BGB", "§§ 133, 157 BGB", "Art. 14 GG"
    normen_patterns = [
        r'(§§?\s*\d+[a-z]?(\s+Abs\.\s*\d+)?(\s+[A-Z]+))',  # § 536 BGB, § 536 Abs. 1 BGB
        r'(Art\.\s*\d+[a-z]?(\s+Abs\.\s*\d+)?(\s+[A-Z]+))',  # Art. 14 GG
    ]
    
    for pattern in normen_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            extracted_normen = match.group(1)
            cleaned_query = cleaned_query.replace(match.group(0), '').strip()
            break
    
    # Extract court names
    # Examples: "BGH", "BVerfG", "OLG Hamburg", "AG München"
    gericht_patterns = [
        r'\b(BGH|BVerfG|BAG|BFH|BSG|BVerwG)\b',  # Federal courts
        r'\b(OLG|LG|AG|VG|OVG|LSG|SG)\s+([A-ZÄÖÜ][a-zäöüß]+)\b',  # Regional courts with location
    ]
    
    for pattern in gericht_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            extracted_gericht = match.group(0)
            cleaned_query = cleaned_query.replace(match.group(0), '').strip()
            break
    
    # Cleanup: Remove multiple spaces
    cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
    
    return cleaned_query, extracted_az, extracted_datum_von, extracted_datum_bis, extracted_normen, extracted_gericht