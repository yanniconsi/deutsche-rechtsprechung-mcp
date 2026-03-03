import json
import requests
import time
import html
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Test-Konfiguration
MCP_URL = "http://localhost:8002/mcp"
RESULTS_FILE = "golden_set_results.json"
READABLE_OUTPUT_FILE = "golden_set_results_readable.txt"

# Golden Test Cases - Ihre spezifischen Fragen
GOLDEN_TEST_CASES = [
    {
        "id": "test_001",
        "question": "Unter welchen Voraussetzungen ist eine Teilwertzuschreibung bei einem Fremdwährungsdarlehen in Schweizer Franken laut Finanzgericht zulässig?",
        "expected_doknr": "NJRE001200892"
    },
    {
        "id": "test_002",
        "question": "Müssen Arbeitnehmer bei einer Massenentlassungsanzeige mitgezählt werden, wenn sie vorab einen Aufhebungsvertrag zum Übertritt in eine Transfergesellschaft unterschrieben haben?",
        "expected_doknr": "NJRE001180375"
    },
    {
        "id": "test_003",
        "question": "Hat ein Compliance-Beauftragter einer Versicherung Anspruch auf Befreiung von der Rentenversicherungspflicht, wenn er als Rechtsanwalt zugelassen ist?",
        "expected_doknr": "NJRE001131859"
    },
    {
        "id": "test_004",
        "question": "Wie wird die Gefahr einer Gruppenverfolgung für alleinstehende Frauen in Kamerun aktuell bewertet?",
        "expected_doknr": "NJRE001590735"
    },
    {
        "id": "test_005",
        "question": "Sind öffentlich-rechtliche Rundfunkanstalten bei der Erhebung von Rundfunkbeiträgen umsatzsteuerpflichtig?",
        "expected_doknr": "NJRE001291957"
    },
    {
        "id": "test_006",
        "question": "Ist ein Sachmängelausschluss in einem Vertrag von 1963 wirksam gegenüber heutigen Ausgleichsansprüchen nach dem Bundesbodenschutzgesetz?",
        "expected_doknr": "NJRE001158006"
    },
    {
        "id": "test_007",
        "question": "Können Beitragszeiten in einer sowjetischen Kolchose für die Rente anerkannt werden, wenn die Arbeitsleistung unterbrochen war?",
        "expected_doknr": "NJRE001145626"
    },
    {
        "id": "test_008",
        "question": "Welche Anforderungen gelten für die Änderung eines Versorgungsvertrags für vollstationäre Pflege in BW gemäß § 72 SGB XI?",
        "expected_doknr": "NJRE001169339"
    },
    {
        "id": "test_009",
        "question": "In welchem Fall wurde die Gesamtlaufleistung eines Pkw im Diesel-Skandal ausnahmsweise auf 400.000 km geschätzt?",
        "expected_doknr": "NJRE001450826"
    },
    {
        "id": "test_010",
        "question": "Gilt eine Reduzierung der Abgasrückführung bei Außentemperaturen zwischen +17 und +30 Grad Celsius als unzulässige Abschalteinrichtung?",
        "expected_doknr": "NJRE001578217"
    },
    {
        "id": "test_011",
        "question": "Wird dem Käufer eines Skoda Yeti mit Motor EA 189 ein deliktischer Zinsanspruch nach § 849 BGB zugesprochen?",
        "expected_doknr": "NJRE001419674"
    },
    {
        "id": "test_012",
        "question": "Wann ist ein Feststellungsantrag im Dieselskandal zulässig, wenn der Schaden noch in der Entwicklung ist?",
        "expected_doknr": "NJRE001444346"
    },
    {
        "id": "test_013",
        "question": "Kann die Zulassungsbehörde den Betrieb eines Dieselfahrzeugs untersagen, wenn der Halter das Software-Update verweigert?",
        "expected_doknr": "NJRE001416190"
    },
    {
        "id": "test_014",
        "question": "Wann wandelt sich ein Freistellungsanspruch bezüglich vorgerichtlicher Anwaltskosten in einen direkten Zahlungsanspruch um?",
        "expected_doknr": "NJRE001402973"
    },
    {
        "id": "test_015",
        "question": "Welches Urteil befasst sich mit einem Audi 3.0 Liter Diesel und der Schätzung eines Differenzschadens von 10%?",
        "expected_doknr": "NJRE001578217"
    },
    {
        "id": "test_016",
        "question": "Hat der Käufer eines Fahrzeugs mit EA 189 Motor Anspruch auf Verzinsung des Schadensersatzbetrages ab dem Zeitpunkt der Kaufpreiszahlung?",
        "expected_doknr": "NJRE001402973"
    },
    {
        "id": "test_017",
        "question": "Wird eine Schätzung der Gesamtlaufleistung auf 500.000 km abgelehnt, auch wenn das Fahrzeug weit jenseits der üblichen Grenzen noch funktionsfähig ist?",
        "expected_doknr": "NJRE001450826"
    },
    {
        "id": "test_018",
        "question": "In welchem Dokument wird die Rechtmäßigkeit der formlosen (\"bescheidlosen\") Anforderung von Rundfunkbeiträgen bestätigt?",
        "expected_doknr": "NJRE001291957"
    },
    {
        "id": "test_019",
        "question": "Unter welchem Gesichtspunkt wird die \"Verwestlichung\" bei der Beurteilung von Asylanträgen aus Kamerun abgelehnt?",
        "expected_doknr": "NJRE001590735"
    },
    {
        "id": "test_020",
        "question": "Stellt ein allgemeiner Sachmängelausschluss eine \"andere zulässige Regelung\" im Sinne des § 24 Abs. 2 BBodSchG dar?",
        "expected_doknr": "NJRE001158006"
    },
    {
        "id": "test_021",
        "question": "Welcher Fall behandelt die Tätigkeit eines Vorstandsreferenten bei einer Reiseversicherung im Kontext der Rentenversicherungspflicht?",
        "expected_doknr": "NJRE001131859"
    },
    {
        "id": "test_022",
        "question": "Spielt die ununterbrochene Beitragsentrichtung durch eine Kolchose eine Rolle für den Rentennachweis nach dem Fremdrentenrecht?",
        "expected_doknr": "NJRE001145626"
    },
    {
        "id": "test_023",
        "question": "Führt das Erlöschen der Typengenehmigung bei Verweigerung eines Software-Updates zwangsläufig zur Betriebsuntersagung nach § 5 FZV?",
        "expected_doknr": "NJRE001416190"
    },
    {
        "id": "test_024",
        "question": "Wie wird die Kostenentscheidung nach § 92 ZPO getroffen, wenn ein prozessualer Hilfsantrag Erfolg hat, der Hauptantrag aber abgewiesen wird?",
        "expected_doknr": "NJRE001444346"
    },
    {
        "id": "test_025",
        "question": "Muss sich ein Kläger im Dieselskandal die gezogenen Nutzungsvorteile auch bei vorsätzlicher sittenwidriger Schädigung anrechnen lassen?",
        "expected_doknr": "NJRE001450826"
    },
    {
        "id": "test_026",
        "question": "Finde Verwaltungsgerichtshof Urteile mit Normen § 40 Abs 1 VwGO, § 62 Abs 2 S 1 OWiG, § 68 Abs 1 S 1 OWiG",
        "expected_doknr": "NJRE001619542"
    },
    {
        "id": "test_027",
        "question": "Erfasst die Zuständigkeit der Amtsgerichte nach § 68 OWiG auch Klagen auf Feststellung der Nichtigkeit?",
        "expected_doknr": "NJRE001619542"
    },
    {
        "id": "test_028",
        "question": "Auf welche Urteile kann man sich Beziehen im Thema Nichtigkeit?",
        "expected_doknr": "NJRE001619542"
    },
    {
        "id": "test_029",
        "question": "Für wen ist eine Zuständigkeit bei Rechtschutz gegen einen Bußgeldbescheid vorgehsehen?",
        "expected_doknr": "NJRE001619542"
    },
    {
        "id": "test_030",
        "question": "Welche Normen sind Interessant bei einem Fall mit Kennzeichungspflicht bezahlter Werbung?",
        "expected_doknr": "NJRE001618880"
    },
    {
        "id": "test_031",
        "question": "Gegen welchen Paragraphen verstößt das nicht informieren über urlaubs oder krankheitsbedingte Abwesenheiten?",
        "expected_doknr": "NJRE001618980"
    },
    {
        "id": "test_032",
        "question": "Ist das EuGH dem BGH übergeordnet?",
        "expected_doknr": "NJRE001619000"
    },
    {
        "id": "test_033",
        "question": "Wer ist beschwerdeberechtigt, wenn das Grundbuchamt ein Ersuchen des Vollstreckungsgerichts zurückweist?",
        "expected_doknr": "NJRE001619954"
    },
    {
        "id": "test_034",
        "question": "Spielt es für die Anwendung des neuen GbR-Rechts eine Rolle, dass der eigentliche Eigentumsübergang (Zuschlag) bereits vor dem Inkrafttreten des MoPeG (01.01.2024) stattfand?",
        "expected_doknr": "NJRE001619954"
    }
]


def fix_encoding(text: str) -> str:
    """Repariert falsch kodierte UTF-8 Strings."""
    if not text:
        return text
    try:
        # Versuche die falsche Kodierung zu reparieren
        # Text wurde als Latin-1 interpretiert, ist aber UTF-8
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Falls das nicht klappt, HTML entities dekodieren
        return html.unescape(text)


def test_server_connection():
    """Testet die Verbindung zum MCP Server."""
    print("=" * 100)
    print("VERBINDUNGSTEST ZUM MCP SERVER")
    print("=" * 100)
    print(f"Server URL: {MCP_URL}\n")
    
    # Test 1: Einfacher HTTP GET
    print("1. HTTP GET Test...")
    try:
        response = requests.get(MCP_URL, timeout=5)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        if response.status_code == 406:
            print("   ⚠ 406 Not Acceptable - das ist normal, GET wird nicht unterstützt")
        print("   ✓ Server erreichbar\n")
    except Exception as e:
        print(f"   ✗ Fehler: {e}\n")
        return False
    
    # Test 2: Liste verfügbare Tools
    print("2. Liste verfügbare Tools...")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    
    try:
        response = requests.post(
            MCP_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Response: {response.text}")
            return False
        
        # Parse SSE response
        lines = response.text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                data = json.loads(line[6:])
                if 'result' in data:
                    tools = data['result'].get('tools', [])
                    print(f"   ✓ Gefundene Tools: {[t['name'] for t in tools]}\n")
                    return True
    except Exception as e:
        print(f"   ✗ Fehler beim Abrufen der Tools: {e}\n")
        return False
    
    return False


def call_mcp_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """Ruft das search_decisions Tool auf."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_decisions",
            "arguments": {
                "query": query,
                "limit": limit
            }
        }
    }
    
    try:
        response = requests.post(
            MCP_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        # Parse SSE response
        lines = response.text.strip().split('\n')
        
        for line in lines:
            if line.startswith('data: '):
                data_str = line[6:]
                try:
                    data = json.loads(data_str)
                    if 'result' in data:
                        return data['result']
                    elif 'error' in data:
                        return {"error": data['error']}
                except json.JSONDecodeError as e:
                    continue
        
        return {"error": "No result in response"}
    
    except requests.exceptions.Timeout:
        return {"error": "Request timeout after 30s"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {type(e).__name__}: {str(e)}"}


def extract_results_from_response(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrahiert die Suchergebnisse aus der MCP-Antwort."""
    try:
        if 'content' in result:
            content = result['content']
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get('text', '[]')
                return json.loads(text)
        elif isinstance(result, str):
            return json.loads(result)
        elif isinstance(result, list):
            return result
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  ⚠ Fehler beim Parsen: {e}")
    
    return []


def validate_test_case(test_case: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Validiert, ob die erwartete DokNr in den Top-Ergebnissen ist."""
    validation = {
        "test_id": test_case["id"],
        "question": test_case["question"],
        "expected_doknr": test_case["expected_doknr"],
        "passed": False,
        "found_at_position": None,
        "top_results": [],
        "error": None
    }
    
    # Check for errors
    if "error" in result:
        validation["error"] = result["error"]
        return validation
    
    # Extract search results
    results = extract_results_from_response(result)
    
    if not results:
        validation["error"] = "Keine Ergebnisse gefunden"
        return validation
    
    # Check if expected doknr is in results
    for idx, doc in enumerate(results[:10], 1):
        doknr = doc.get("doknr", "")
        
        # FIX ENCODING HERE
        validation["top_results"].append({
            "position": idx,
            "doknr": doknr,
            "title": fix_encoding(doc.get("title", "")),
            "score": doc.get("score", 0),
            "snippet": fix_encoding(doc.get("snippet", "")),
            "gericht": fix_encoding(doc.get("gericht", "")),
            "az": fix_encoding(doc.get("az", "")),
            "date": doc.get("date", ""),
            "normen": fix_encoding(doc.get("normen", ""))
        })
        
        if doknr == test_case["expected_doknr"]:
            validation["passed"] = True
            validation["found_at_position"] = idx
            break
    
    return validation


def write_readable_output(results: List[Dict[str, Any]], summary: Dict[str, Any]):
    """Schreibt eine lesbare Text-Datei mit allen Ergebnissen."""
    output_path = Path(READABLE_OUTPUT_FILE)
    
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        # Header
        f.write("=" * 120 + "\n")
        f.write("GOLDEN SET TEST RESULTS - Deutsche Rechtsprechung MCP Server\n")
        f.write("=" * 120 + "\n")
        f.write(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write(f"MCP Server: {MCP_URL}\n")
        f.write("=" * 120 + "\n\n")
        
        # Summary
        f.write("ZUSAMMENFASSUNG\n")
        f.write("-" * 120 + "\n")
        f.write(f"Gesamt:         {summary['total']} Tests\n")
        f.write(f"Bestanden:      {summary['passed']} ({summary['pass_rate']:.1f}%)\n")
        f.write(f"Fehlgeschlagen: {summary['failed']} ({100-summary['pass_rate']:.1f}%)\n\n")
        
        f.write("Position der korrekten Ergebnisse:\n")
        pos_stats = summary['position_stats']
        f.write(f"  Position 1:     {pos_stats[1]} ({pos_stats[1]/summary['total']*100:.1f}%)\n")
        f.write(f"  Position 2:     {pos_stats[2]} ({pos_stats[2]/summary['total']*100:.1f}%)\n")
        f.write(f"  Position 3:     {pos_stats[3]} ({pos_stats[3]/summary['total']*100:.1f}%)\n")
        f.write(f"  Position 4-5:   {pos_stats['4-5']} ({pos_stats['4-5']/summary['total']*100:.1f}%)\n")
        f.write(f"  Position 6-10:  {pos_stats['6-10']} ({pos_stats['6-10']/summary['total']*100:.1f}%)\n")
        f.write(f"  Nicht gefunden: {pos_stats['not_found']} ({pos_stats['not_found']/summary['total']*100:.1f}%)\n")
        f.write("=" * 120 + "\n\n\n")
        
        # Detailed results
        for i, test_result in enumerate(results, 1):
            f.write(f"\n{'=' * 120}\n")
            f.write(f"TEST {i}/{summary['total']}: {test_result['test_id']}\n")
            f.write(f"{'=' * 120}\n\n")
            
            # Test details
            f.write(f"FRAGE:\n{test_result['question']}\n\n")
            f.write(f"ERWARTETE DOKNR: {test_result['expected_doknr']}\n")
            
            if test_result['passed']:
                f.write(f"STATUS: ✓ PASSED (Position {test_result['found_at_position']})\n\n")
            else:
                f.write(f"STATUS: ✗ FAILED\n")
                if test_result['error']:
                    f.write(f"FEHLER: {test_result['error']}\n")
                f.write("\n")
            
            # Top 10 results with snippets
            f.write(f"\nTOP 10 SUCHERGEBNISSE:\n")
            f.write("-" * 120 + "\n\n")
            
            for result in test_result['top_results']:
                is_expected = result['doknr'] == test_result['expected_doknr']
                marker = " >>> ERWARTET <<<" if is_expected else ""
                
                f.write(f"[{result['position']}] {marker}\n")
                f.write(f"    DokNr:   {result['doknr']}\n")
                f.write(f"    Gericht: {result['gericht']}\n")
                f.write(f"    Az:      {result['az']}\n")
                f.write(f"    Datum:   {result['date']}\n")
                f.write(f"    Score:   {result['score']:.4f}\n")
                
                if result['normen']:
                    f.write(f"    Normen:  {result['normen']}\n")
                
                f.write(f"    Titel:   {result['title']}\n\n")
                
                # Snippet - relevante Textstelle
                if result['snippet']:
                    f.write(f"    RELEVANTE TEXTSTELLE:\n")
                    f.write(f"    {'-' * 110}\n")
                    # Format snippet with proper indentation
                    snippet_lines = result['snippet'].replace('<em>', '**').replace('</em>', '**').split('\n')
                    for line in snippet_lines:
                        if line.strip():
                            f.write(f"    {line.strip()}\n")
                    f.write(f"    {'-' * 110}\n")
                
                f.write("\n")
            
            f.write("\n")
    
    print(f"\n✓ Lesbare Ergebnisse gespeichert in: {output_path}")


def run_golden_set_tests():
    """Führt alle Golden Set Tests aus."""
    
    # Verbindungstest zuerst durchführen
    print("\n")
    if not test_server_connection():
        print("\n⚠ WARNUNG: Server-Verbindungstest fehlgeschlagen!")
        print("Bitte überprüfen Sie:")
        print("  1. Ist der MCP Server gestartet? (docker-compose up)")
        print("  2. Läuft der Server auf http://localhost:8002/mcp?")
        print("  3. Ist OpenSearch bereit?\n")
        response = input("Trotzdem fortfahren? (j/n): ")
        if response.lower() != 'j':
            return False
    
    print("\n")
    print("=" * 100)
    print("GOLDEN SET TESTS - Deutsche Rechtsprechung MCP Server")
    print("=" * 100)
    print(f"Anzahl Tests: {len(GOLDEN_TEST_CASES)}")
    print(f"MCP Server: {MCP_URL}")
    print("=" * 100)
    print()
    
    results = []
    passed = 0
    failed = 0
    position_stats = {1: 0, 2: 0, 3: 0, "4-5": 0, "6-10": 0, "not_found": 0}
    
    for i, test_case in enumerate(GOLDEN_TEST_CASES, 1):
        print(f"Test {i}/{len(GOLDEN_TEST_CASES)}: {test_case['id']}")
        print(f"  Frage: {test_case['question'][:80]}...")
        print(f"  Erwartete DokNr: {test_case['expected_doknr']}")
        
        # Call MCP search
        result = call_mcp_search(test_case['question'], limit=10)
        
        # Validate result
        validation = validate_test_case(test_case, result)
        results.append(validation)
        
        # Print validation
        if validation["passed"]:
            pos = validation["found_at_position"]
            print(f"  ✓ PASSED - Gefunden an Position {pos}")
            passed += 1
            
            # Statistics
            if pos == 1:
                position_stats[1] += 1
            elif pos == 2:
                position_stats[2] += 1
            elif pos == 3:
                position_stats[3] += 1
            elif pos <= 5:
                position_stats["4-5"] += 1
            else:
                position_stats["6-10"] += 1
        else:
            print(f"  ✗ FAILED - Nicht in Top 10 gefunden")
            if validation["error"]:
                print(f"    Fehler: {validation['error']}")
            else:
                print(f"    Top 3 Ergebnisse:")
                for res in validation["top_results"][:3]:
                    print(f"      {res['position']}. {res['doknr']} (Score: {res['score']:.2f})")
            failed += 1
            position_stats["not_found"] += 1
        
        print()
        time.sleep(0.3)  # Rate limiting
    
    # Summary
    print("=" * 100)
    print("ZUSAMMENFASSUNG")
    print("=" * 100)
    print(f"Gesamt:        {len(GOLDEN_TEST_CASES)} Tests")
    print(f"Bestanden:     {passed} ({passed/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print(f"Fehlgeschlagen: {failed} ({failed/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print()
    print("Position der korrekten Ergebnisse:")
    print(f"  Position 1:    {position_stats[1]} ({position_stats[1]/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print(f"  Position 2:    {position_stats[2]} ({position_stats[2]/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print(f"  Position 3:    {position_stats[3]} ({position_stats[3]/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print(f"  Position 4-5:  {position_stats['4-5']} ({position_stats['4-5']/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print(f"  Position 6-10: {position_stats['6-10']} ({position_stats['6-10']/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print(f"  Nicht gefunden: {position_stats['not_found']} ({position_stats['not_found']/len(GOLDEN_TEST_CASES)*100:.1f}%)")
    print("=" * 100)
    
    # Create summary object
    summary = {
        "total": len(GOLDEN_TEST_CASES),
        "passed": passed,
        "failed": failed,
        "pass_rate": passed/len(GOLDEN_TEST_CASES)*100,
        "position_stats": position_stats
    }
    
    # Save JSON results
    output_path = Path(RESULTS_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": summary,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ JSON-Ergebnisse gespeichert in: {output_path}")
    
    # Write readable text output
    write_readable_output(results, summary)
    
    return passed == len(GOLDEN_TEST_CASES)


if __name__ == "__main__":
    success = run_golden_set_tests()
    exit(0 if success else 1)