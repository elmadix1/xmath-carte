#!/usr/bin/env python3
"""
Splits carte.html into db.js + index.html
Run: python3 split.py carte.html
"""
import sys, re

src = open(sys.argv[1], encoding='utf-8').read()

# Find the big script block (after topojson CDN)
# Extract const DB, PAYS_FERMES, ETABS_FERMES
main_script_start = src.find('// ═══')
if main_script_start == -1:
    main_script_start = src.find('const DB={')

# Find end of ETABS_FERMES (last of the 3 data blocks)
# It ends just before: const ZC=
zc_pos = src.find('\nconst ZC=')
if zc_pos == -1:
    zc_pos = src.find('\nconst ZC =')

db_block = src[main_script_start:zc_pos].strip()

# Write db.js
with open('db.js', 'w', encoding='utf-8') as f:
    f.write('// BASE DONNÉES AEFE — généré automatiquement\n')
    f.write(db_block)
    f.write('\n')
print(f"db.js written ({len(db_block)} chars)")

# Build index.html: replace the data block with <script src="db.js"></script>
# The replacement goes between <script src="topojson..."> and the data block
insert_marker = '<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>'
insert_pos = src.find(insert_marker) + len(insert_marker)

# Find the <script> tag that opens the main block containing the data
# It's right after the topojson script tag
main_open = src.find('\n<script>\n//', insert_pos)
if main_open == -1:
    main_open = src.find('\n<script>\nconst DB', insert_pos)

# The main script tag closes the data block at zc_pos and continues with code
# We want to keep everything from zc_pos to </script> at the end
code_block = src[zc_pos:]  # from const ZC= to </body></html>

new_html = (
    src[:insert_pos] +
    '\n<script src="db.js"></script>' +
    '\n<script>' +
    code_block
)

# Also remove the search-wrap div and its script (optional - separate task)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
print(f"index.html written ({len(new_html)} chars)")
print("Done! Check db.js and index.html")
