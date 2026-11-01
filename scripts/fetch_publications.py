#!/usr/bin/env python3
"""
Pull the lab's publications from PubMed and write _data/publications.json.

Run locally with:      python scripts/fetch_publications.py
Runs automatically:    monthly, via .github/workflows/publications.yml

PubMed only carries some preprints, so preprints also come from Europe PMC.

Curation happens in _data/publication_overrides.yml, not here. That file lets
you exclude PMIDs, include papers the author search misses (e.g. consortium
authorship), list extra spellings of lab members' names, and add per-paper
details. This script never overwrites it.

Lab members come from _data/authors.yml and are marked in each paper's
lab_authors list so the Publications page can bold them. PDB codes come from
RCSB: every entry whose primary citation is the paper or its preprint.
"""

import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

import yaml

# The full name, not "Manglik A[Author]", which also returns other A. Mangliks.
QUERY = '"Manglik, Aashish"[Full Author Name]'
EMAIL = "aashish.manglik@ucsf.edu"       # NCBI asks for a contact address
TOOL = "mangliklab-website"
API_KEY = os.environ.get("NCBI_API_KEY")  # optional, raises the rate limit

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_data" / "publications.json"
OVERRIDES = ROOT / "_data" / "publication_overrides.yml"
MEMBERS = ROOT / "_data" / "authors.yml"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PREPRINT_QUERY = 'AUTH:"Manglik A" AND SRC:PPR'


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": TOOL})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _params(**kw):
    kw.update(tool=TOOL, email=EMAIL)
    if API_KEY:
        kw["api_key"] = API_KEY
    return urllib.parse.urlencode(kw)


def search_pmids():
    url = f"{EUTILS}/esearch.fcgi?" + _params(
        db="pubmed", term=QUERY, retmax=1000, retmode="json"
    )
    data = json.loads(_get(url))
    return data["esearchresult"]["idlist"]


def fetch_records(pmids):
    """PubMed asks for batches of 200 or fewer."""
    records = []
    for i in range(0, len(pmids), 200):
        batch = pmids[i:i + 200]
        url = f"{EUTILS}/efetch.fcgi?" + _params(
            db="pubmed", id=",".join(batch), retmode="xml"
        )
        root = ElementTree.fromstring(_get(url))
        records.extend(root.findall(".//PubmedArticle"))
        time.sleep(0.4)
    return records


def fetch_preprints():
    """Aashish's preprints on Europe PMC, in the same shape as parse() returns."""
    records, cursor = [], "*"
    while True:
        url = EUROPE_PMC + "?" + urllib.parse.urlencode({
            "query": PREPRINT_QUERY, "format": "json", "resultType": "core",
            "pageSize": 100, "cursorMark": cursor,
        })
        data = json.loads(_get(url))
        records.extend(data["resultList"]["result"])
        if data.get("nextCursorMark", cursor) == cursor or not data["resultList"]["result"]:
            break
        cursor = data["nextCursorMark"]

    preprints = []
    for rec in records:
        people = rec.get("authorList", {}).get("author", [])
        # The search is by initial, so check it's Aashish and not another A. Manglik.
        if not any(a.get("lastName") == "Manglik"
                   and (a.get("firstName") or "").startswith("Aashish") for a in people):
            continue

        authors, full_names = [], []
        for a in people:
            if a.get("lastName"):
                authors.append(f"{a['lastName']} {a.get('initials', '')}".strip())
                full_names.append((authors[-1], a.get("firstName", ""), a["lastName"]))
            elif a.get("collectiveName"):
                authors.append(a["collectiveName"])

        date = rec.get("firstPublicationDate", "")
        preprints.append({
            "erratum": False,
            "pmid": rec["id"],
            "source_pmid": rec.get("pmid", ""),
            "title": re.sub(r"<[^>]+>", "", rec.get("title", "")).strip().rstrip("."),
            "authors": authors,
            "full_names": full_names,
            "journal": rec.get("bookOrReportDetails", {}).get("publisher", "Preprint"),
            "year": int(date[:4]) if date[:4].isdigit() else None,
            "volume": "",
            "pages": "",
            "doi": rec.get("doi", ""),
            "pmcid": rec.get("pmcid", ""),
            "preprint": True,
            "update_in": "",
            "url": "",  # not on PubMed; the page links to the preprint by DOI
        })
    return preprints


def text(node, path, default=""):
    # itertext, not .text: titles carry inline markup (<i>, <sub>) and .text
    # stops at the first child, truncating e.g. "µ-opioid receptor-G<sub>i</sub>".
    found = node.find(path)
    if found is None:
        return default
    joined = re.sub(r"\s+", " ", "".join(found.itertext())).strip()
    return joined or default


def parse(article):
    pmid = text(article, ".//PMID")

    authors, full_names = [], []
    for a in article.findall("./MedlineCitation/Article/AuthorList/Author"):
        last = text(a, "LastName")
        initials = text(a, "Initials")
        if last:
            authors.append(f"{last} {initials}".strip())
            full_names.append((authors[-1], text(a, "ForeName"), last))
        elif text(a, "CollectiveName"):
            authors.append(text(a, "CollectiveName"))

    year = (
        text(article, ".//ArticleDate/Year")
        or text(article, ".//PubDate/Year")
        or text(article, ".//PubMedPubDate/Year")
    )

    journal = text(article, ".//Journal/ISOAbbreviation") or text(
        article, ".//Journal/Title"
    )

    # The paper's own IDs only. ".//ArticleId" would also match the IDs of every
    # work in its reference list.
    own_ids = article.findall("./PubmedData/ArticleIdList/ArticleId")

    doi = ""
    for eid in own_ids:
        if eid.get("IdType") == "doi":
            doi = (eid.text or "").strip()

    pmcid = ""
    for eid in own_ids:
        if eid.get("IdType") == "pmc":
            pmcid = (eid.text or "").strip()

    # PublicationType is authoritative; the journal-name check is a backstop
    # for preprints PubMed hasn't typed yet.
    ptypes = {(t.text or "").lower() for t in article.findall(".//PublicationType")}
    is_preprint = "preprint" in ptypes or journal.lower() in {
        "biorxiv", "medrxiv", "res sq", "arxiv"
    }

    # NLM links preprints to their peer-reviewed version with RefType="UpdateIn".
    # It computes this against the bioRxiv, Crossref and Europe PMC APIs plus an
    # internal title/author/abstract matcher, so when it's present, trust it.
    update_in = ""
    for cc in article.findall(".//CommentsCorrections"):
        if cc.get("RefType") == "UpdateIn":
            pm = cc.find("PMID")
            if pm is not None and pm.text:
                update_in = pm.text.strip()

    return {
        "erratum": "published erratum" in ptypes,
        "pmid": pmid,
        "title": text(article, ".//ArticleTitle").rstrip("."),
        "authors": authors,
        "full_names": full_names,
        "journal": journal,
        "year": int(year) if year.isdigit() else None,
        "volume": text(article, ".//JournalIssue/Volume"),
        "pages": text(article, ".//Pagination/MedlinePgn"),
        "doi": doi,
        "pmcid": pmcid,
        "preprint": is_preprint,
        "update_in": update_in,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }


GREEK = {
    "\u03bc": "mu", "\u00b5": "mu", "\u03ba": "kappa", "\u03b2": "beta",
    "\u03b1": "alpha", "\u03b4": "delta", "\u03c3": "sigma", "\u03b3": "gamma",
    "\u03c9": "omega", "\u03b5": "epsilon",
}

FUZZY_THRESHOLD = 0.70


def normalize_title(title):
    """Collapse the differences that appear between a preprint and its paper.

    Journals routinely swap spelled-out Greek letters for symbols (mu -> \u03bc),
    add or drop hyphens (proton-sensing -> proton sensing), and change case.
    Normalizing these turns most pairs into exact matches.
    """
    t = title.lower()
    for glyph, name in GREEK.items():
        t = t.replace(glyph, name)
    t = re.sub(r"[\u2010-\u2015-]", " ", t)      # any dash -> space
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _endpoints(pub):
    """First and last author — the pair most stable across peer review."""
    a = pub["authors"]
    return (a[0].lower() if a else "", a[-1].lower() if a else "")


def _same_authors(pre, published):
    """The published paper with nearly all the preprint's authors and its last
    author, for titles too reworded to match. Small author lists are skipped."""
    authors = set(pre["authors"])
    if len(authors) < 4:
        return None, ""
    best, score = None, 0.0
    for cand in published:
        if cand["year"] and pre["year"] and cand["year"] < pre["year"]:
            continue
        if not cand["authors"] or cand["authors"][-1] != pre["authors"][-1]:
            continue
        overlap = len(authors & set(cand["authors"])) / len(authors)
        if overlap > score:
            best, score = cand, overlap
    return (best, f"authors {score:.2f}") if score >= 0.9 else (None, "")


def link_preprints(pubs, supersedes):
    """Attach each preprint to its published version and drop it from the list.

    Five tiers, most to least reliable:
      1. PubMed's own UpdateIn link.
      2. Manual `supersedes:` entries in publication_overrides.yml.
      3. Normalized exact title match.
      4. Fuzzy title match above threshold, corroborated by a shared first or
         last author. Titles that were substantially reworded land here.
      5. Nearly the same author list and the same last author.

    Anything still unmatched is reported so you can add it to `supersedes:`.
    """
    by_pmid = {p["pmid"]: p for p in pubs}
    published = [p for p in pubs if not p["preprint"]]
    by_norm = {normalize_title(p["title"]): p for p in published}

    supersedes = {str(k): str(v) for k, v in supersedes.items()}
    resolved, unmatched = {}, []

    for pre in (p for p in pubs if p["preprint"]):
        target = None
        how = ""

        if pre["update_in"] and pre["update_in"] in by_pmid:
            target, how = by_pmid[pre["update_in"]], "pubmed"
        elif pre["pmid"] in supersedes and supersedes[pre["pmid"]] in by_pmid:
            target, how = by_pmid[supersedes[pre["pmid"]]], "manual"
        else:
            key = normalize_title(pre["title"])
            if key in by_norm and by_norm[key]["pmid"] != pre["pmid"]:
                target, how = by_norm[key], "title"
            else:
                best, score = None, 0.0
                pre_ends = _endpoints(pre)
                for cand in published:
                    r = difflib.SequenceMatcher(
                        None, key, normalize_title(cand["title"])
                    ).ratio()
                    if r > score:
                        best, score = cand, r
                if best and score >= FUZZY_THRESHOLD:
                    shared = set(pre_ends) & set(_endpoints(best))
                    if shared - {""}:
                        target, how = best, f"fuzzy {score:.2f}"
                if not target:
                    target, how = _same_authors(pre, published)

        if target:
            target.setdefault("preprint_pmid", pre["pmid"])
            target.setdefault("preprint_doi", pre["doi"])
            target.setdefault("preprint_server", pre["journal"])
            resolved[pre["pmid"]] = how
        else:
            unmatched.append(pre)

    for pmid, how in sorted(resolved.items()):
        print(f"  linked preprint {pmid} -> published ({how})")
    for pre in unmatched:
        age = f"{pre['year']}" if pre["year"] else "?"
        print(f"  unlinked preprint {pre['pmid']} ({age}): {pre['title'][:60]}")

    return [p for p in pubs if p["pmid"] not in resolved]


def fetch_pdbs(pub):
    """PDB codes of entries whose primary citation is this paper or its preprint."""
    dois = [d for d in (pub.get("doi"), pub.get("preprint_doi")) if d]
    if not dois:
        return []
    nodes = [
        {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_primary_citation.pdbx_database_id_DOI",
                "operator": "exact_match",
                "value": value,
            },
        }
        for doi in dois
        for value in {doi, doi.lower(), doi.upper()}
    ]
    query = {
        "query": {"type": "group", "logical_operator": "or", "nodes": nodes},
        "return_type": "entry",
        "request_options": {"return_all_hits": True},
    }
    req = urllib.request.Request(
        RCSB_SEARCH,
        data=json.dumps(query).encode(),
        headers={"Content-Type": "application/json", "User-Agent": TOOL},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()  # empty (204) when nothing matches
    time.sleep(0.15)
    return sorted(hit["identifier"] for hit in json.loads(body)["result_set"]) if body else []


def _fold(name):
    """Lowercase, strip accents, and drop hyphens so spellings compare equal."""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[-\u2010-\u2015]", " ", name).casefold().strip()


def load_members():
    """(first name, last name) of everyone on the Members page, past and present."""
    with MEMBERS.open(encoding="utf-8") as fh:
        people = yaml.safe_load(fh) or {}
    members = set()
    for person in people.values():
        if person.get("member") and person.get("name"):
            first, _, last = _fold(person["name"]).partition(" ")
            members.add((first, last))
    return members


def lab_authors(pub, members, extra_names):
    """Authors whose full first and last name match a lab member.

    Matching on the first name, not just the initial, keeps common surnames
    (Wang H, Kim J) on large collaborations from being claimed as lab members.
    """
    matched = []
    for display, fore, last in pub["full_names"]:
        first = _fold(fore).split(" ")[0] if fore else ""
        if (first, _fold(last)) in members or display in extra_names:
            matched.append(display)
    return matched


def load_overrides():
    if not OVERRIDES.exists():
        return {"exclude": [], "include": [], "extra": {},
                "supersedes": {}, "lab_author_names": []}
    with OVERRIDES.open() as fh:
        data = yaml.safe_load(fh) or {}
    for key, empty in [("exclude", []), ("include", []), ("extra", {}), ("supersedes", {}), ("lab_author_names", [])]:
        if data.get(key) is None:
            data[key] = empty
    return data


def main():
    overrides = load_overrides()
    exclude = {str(p) for p in overrides["exclude"]}

    found = search_pmids()
    if not found:
        print("No PMIDs returned — refusing to overwrite existing data.", file=sys.stderr)
        return 1

    pmids = list(dict.fromkeys(found + [str(p) for p in overrides["include"]]))
    pmids = [p for p in pmids if p not in exclude]

    pubs = [parse(a) for a in fetch_records(pmids)]

    # Preprints PubMed doesn't have. Skip any it does, or that have been excluded.
    known_dois = {p["doi"].lower() for p in pubs if p["doi"]}
    for pre in fetch_preprints():
        if pre["doi"].lower() in known_dois:
            continue
        if pre["pmid"] in exclude or pre.pop("source_pmid") in exclude:
            continue
        pubs.append(pre)

    # Corrections ("Author Correction: ...") are their own PubMed records.
    pubs = [p for p in pubs if not p.pop("erratum")]

    pubs = link_preprints(pubs, overrides.get("supersedes", {}) or {})

    members = load_members()
    extra_names = set(overrides["lab_author_names"])

    for p in pubs:
        p["lab_authors"] = lab_authors(p, members, extra_names)
        del p["full_names"]
        pdbs = fetch_pdbs(p)
        if pdbs:
            p["pdbs"] = pdbs
        p.update(overrides["extra"].get(p["pmid"], {}))
        if p["pmid"].isdigit():
            p.update(overrides["extra"].get(int(p["pmid"]), {}))
        p.pop("source_pmid", None)

    # Within a year, Europe PMC preprints (no PMID) come first.
    pubs.sort(
        key=lambda p: (p["year"] or 0, not p["pmid"].isdigit(),
                       int(re.sub(r"\D", "", p["pmid"]))),
        reverse=True,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as fh:
        json.dump(pubs, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"Wrote {len(pubs)} publications to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
