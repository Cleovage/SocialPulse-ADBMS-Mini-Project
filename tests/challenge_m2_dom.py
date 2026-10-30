import re
from bs4 import BeautifulSoup

def main():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    with open("app/static/js/app.js", "r", encoding="utf-8") as f:
        js_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    all_html_ids = {tag["id"] for tag in soup.find_all(attrs={"id": True})}

    # Extract all getElementById in js_content
    js_ids = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", js_content))

    print(f"Total IDs found in index.html: {len(all_html_ids)}")
    print(f"Total IDs referenced via getElementById in app.js: {len(js_ids)}")

    # Check Instagram related IDs
    ig_related_in_js = {i for i in js_ids if any(k in i.lower() for k in ["ig", "instagram", "settings"])}
    print("\n=== Instagram-related IDs referenced in app.js ===")
    missing_ig = []
    for ig_id in sorted(ig_related_in_js):
        present = ig_id in all_html_ids
        print(f"  [{'PASS' if present else 'FAIL'}] {ig_id}: {'Found in HTML' if present else 'MISSING FROM HTML'}")
        if not present:
            missing_ig.append(ig_id)

    print(f"\nMissing Instagram IDs: {missing_ig}")

    # Check all missing IDs across entire app.js
    missing_all = sorted([i for i in js_ids if i not in all_html_ids])
    print(f"\nAll missing IDs across app.js: {missing_all}")

if __name__ == "__main__":
    main()
