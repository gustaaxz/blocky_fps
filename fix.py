import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Fix double const rnd
bad_str = """        function generateObstacles(seedStr) {
            obstacles = []; bushes = []; items = [];
            const rnd = mulberry32(hashCode(seedStr || "default"));
            const rnd = mulberry32(hashCode(seedStr || "default"));"""
good_str = """        function generateObstacles(seedStr) {
            obstacles = []; bushes = []; items = [];
            const rnd = mulberry32(hashCode(seedStr || "default"));"""

html = html.replace(bad_str, good_str)

# Also check for other duplicate lines around there
bad2 = """            const rnd = mulberry32(hashCode(seedStr || "default"));\n            const rnd = mulberry32(hashCode(seedStr || "default"));"""
good2 = """            const rnd = mulberry32(hashCode(seedStr || "default"));"""
html = html.replace(bad2, good2)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Fix applied")
