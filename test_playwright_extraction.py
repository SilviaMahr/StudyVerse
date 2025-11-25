"""
Test um zu pruefen ob die Playwright-basierte Semester-Extraktion funktioniert
"""

import sys
sys.path.append(".")

from data_ingestion.extractor import extract_win_bsc_info_with_semester


def test_playwright_extraction():
    """Testet die Playwright-basierte Extraktion fuer WS und SS."""
    print("=" * 80)
    print("TEST: PLAYWRIGHT SEMESTER-EXTRAKTION")
    print("=" * 80)

    # Test WS
    print("\n1. Teste WS-Extraktion...")
    print("-" * 80)
    (ws_html, ws_url) = extract_win_bsc_info_with_semester("WS")

    if ws_html:
        print(f"[OK] WS-Daten erfolgreich extrahiert!")
        print(f"   URL: {ws_url}")
        print(f"   HTML-Laenge: {len(ws_html)} Zeichen")
        print(f"   HTML-Vorschau (erste 300 Zeichen):")
        print(f"   {ws_html[:300]}...")

        # Pruefe ob "2025W" oder aehnliches im HTML ist
        if "W" in ws_html[:500] or "Winter" in ws_html[:500]:
            print(f"   [+] Wintersemester-Indikator gefunden!")
    else:
        print(f"[ERROR] Konnte WS-Daten nicht extrahieren!")

    # Test SS
    print("\n2. Teste SS-Extraktion...")
    print("-" * 80)
    (ss_html, ss_url) = extract_win_bsc_info_with_semester("SS")

    if ss_html:
        print(f"[OK] SS-Daten erfolgreich extrahiert!")
        print(f"   URL: {ss_url}")
        print(f"   HTML-Laenge: {len(ss_html)} Zeichen")
        print(f"   HTML-Vorschau (erste 300 Zeichen):")
        print(f"   {ss_html[:300]}...")

        # Pruefe ob "2025S" oder aehnliches im HTML ist
        if ("S" in ss_html[:500] and "W" not in ss_html[:100]) or "Sommer" in ss_html[:500]:
            print(f"   [+] Sommersemester-Indikator gefunden!")
    else:
        print(f"[ERROR] Konnte SS-Daten nicht extrahieren!")

    print("\n" + "=" * 80)
    print("TEST ABGESCHLOSSEN!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_playwright_extraction()
    except KeyboardInterrupt:
        print("\n\nTest abgebrochen durch User.")
    except Exception as e:
        print(f"\n\nFATALER FEHLER: {e}")
        import traceback
        traceback.print_exc()
