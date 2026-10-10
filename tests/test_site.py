import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://felipedelgadopsicologo.com.br"
PAGES = {
    ROOT / "index.html": f"{BASE}/",
    ROOT / "terapia-individual" / "index.html": f"{BASE}/terapia-individual/",
    ROOT / "terapia-de-casal" / "index.html": f"{BASE}/terapia-de-casal/",
    ROOT / "terapia-e-trabalho" / "index.html": f"{BASE}/terapia-e-trabalho/",
    ROOT / "terapia-junguiana" / "index.html": f"{BASE}/terapia-junguiana/",
    ROOT / "sobre" / "index.html": f"{BASE}/sobre/",
    ROOT / "acupuntura" / "index.html": f"{BASE}/acupuntura/",
}


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.ids = set()
        self.h1_count = 0
        self.main_count = 0
        self.title_parts = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.tags.append((tag, data))
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)

    def attrs_for(self, tag):
        return [attrs for found, attrs in self.tags if found == tag]


def parse(path):
    document = Document()
    document.feed(path.read_text(encoding="utf-8"))
    return document


def local_target(source, raw_url):
    parsed = urlparse(raw_url)
    if parsed.scheme or raw_url.startswith(("mailto:", "tel:", "javascript:")):
        return None, None
    fragment = unquote(parsed.fragment)
    relative = unquote(parsed.path)
    if not relative:
        return source, fragment
    if relative.startswith("/"):
        candidate = ROOT / relative.lstrip("/")
    else:
        candidate = source.parent / relative
    if relative.endswith("/") or candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate.resolve(), fragment


class SiteTests(unittest.TestCase):
    def test_required_public_and_operational_files(self):
        for relative in [
            "CNAME", ".nojekyll", "404.html", "robots.txt", "sitemap.xml",
            "llms.txt", "README.md", "AGENTS.md", "CHANGELOG.md",
            ".github/workflows/validate.yml", "assets/style.css", "assets/app.js",
        ]:
            self.assertTrue((ROOT / relative).exists(), relative)

    def test_metadata_semantics_and_canonical(self):
        titles = set()
        for path, canonical in PAGES.items():
            doc = parse(path)
            html_attrs = doc.attrs_for("html")
            self.assertTrue(html_attrs and html_attrs[0].get("lang") == "pt-BR", path)
            title = "".join(doc.title_parts).strip()
            self.assertTrue(title, path)
            self.assertNotIn(title, titles, path)
            titles.add(title)
            self.assertEqual(doc.h1_count, 1, path)
            self.assertEqual(doc.main_count, 1, path)
            metas = doc.attrs_for("meta")
            self.assertTrue(any(m.get("name") == "description" and m.get("content") for m in metas), path)
            self.assertFalse(any(m.get("name") == "robots" and "noindex" in m.get("content", "") for m in metas), path)
            links = doc.attrs_for("link")
            self.assertTrue(any(l.get("rel") == "canonical" and l.get("href") == canonical for l in links), path)
            self.assertTrue(any(m.get("property") == "og:url" and m.get("content") == canonical for m in metas), path)
            self.assertTrue(any(m.get("property") == "og:image:alt" and m.get("content") for m in metas), path)

    def test_local_references_and_fragments_exist(self):
        for path in [*PAGES, ROOT / "404.html"]:
            doc = parse(path)
            for tag, attr in (("a", "href"), ("img", "src"), ("script", "src"), ("link", "href")):
                for attrs in doc.attrs_for(tag):
                    raw = attrs.get(attr)
                    if not raw or raw.startswith(("http://", "https://", "//", "data:")):
                        continue
                    target, fragment = local_target(path, raw)
                    if target is None:
                        continue
                    self.assertTrue(target.exists(), f"{path}: {raw}")
                    if fragment and target.suffix.lower() == ".html":
                        self.assertIn(fragment, parse(target).ids, f"{path}: {raw}")

    def test_images_have_alt_and_dimensions(self):
        for path in PAGES:
            for attrs in parse(path).attrs_for("img"):
                self.assertIn("alt", attrs, f"{path}: {attrs.get('src')}")
                self.assertRegex(attrs.get("width", ""), r"^[1-9]\d*$", f"{path}: {attrs.get('src')}")
                self.assertRegex(attrs.get("height", ""), r"^[1-9]\d*$", f"{path}: {attrs.get('src')}")

    def test_json_ld_is_valid(self):
        pattern = re.compile(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.IGNORECASE | re.DOTALL,
        )
        for path in PAGES:
            payloads = pattern.findall(path.read_text(encoding="utf-8"))
            self.assertTrue(payloads, path)
            for payload in payloads:
                parsed = json.loads(payload)
                self.assertEqual(parsed.get("@context"), "https://schema.org", path)

    def test_sitemap_robots_and_llms_match_canonical(self):
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Sitemap: {BASE}/sitemap.xml", robots)
        tree = ElementTree.parse(ROOT / "sitemap.xml")
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = {node.text for node in tree.findall("s:url/s:loc", namespace)}
        self.assertEqual(locations, set(PAGES.values()))
        llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn(f"Site: {BASE}/", llms)
        self.assertNotIn("/Felipe-Delgado/", llms)
        self.assertNotIn("mobspot.github.io", llms)

    def test_no_placeholder_form_or_obvious_secret(self):
        corpus = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts and path.suffix.lower() in {".html", ".js", ".css", ".md", ".txt", ".xml", ".yml"}
        )
        self.assertNotIn("formspree.io/f/[SEU_ID]", corpus)
        self.assertNotIn("<form", corpus.lower())
        for pattern in [
            r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
            r"sk-[A-Za-z0-9]{20,}", r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        ]:
            self.assertIsNone(re.search(pattern, corpus), pattern)

    def test_404_is_not_indexable(self):
        text = (ROOT / "404.html").read_text(encoding="utf-8")
        self.assertIn('name="robots" content="noindex, nofollow"', text)
        self.assertIn("Página não encontrada", text)

    def test_external_blank_links_are_safe(self):
        for path in PAGES:
            for attrs in parse(path).attrs_for("a"):
                if attrs.get("target") == "_blank":
                    self.assertIn("noopener", attrs.get("rel", "").split(), f"{path}: {attrs.get('href')}")

    def test_mobile_menu_contract(self):
        script = (ROOT / "assets/app.js").read_text(encoding="utf-8")
        self.assertIn("aria-hidden", script)
        self.assertIn("inert", script)
        self.assertIn("e.key==='Tab'", script)
        for path in PAGES:
            text = path.read_text(encoding="utf-8")
            self.assertIn('aria-controls="panel"', text, path)
            self.assertIn('aria-hidden="true" inert', text, path)

    def test_cname_is_canonical(self):
        self.assertEqual((ROOT / "CNAME").read_text(encoding="utf-8").strip(), "felipedelgadopsicologo.com.br")


if __name__ == "__main__":
    unittest.main()
