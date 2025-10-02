#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSINT Toolkit (modular, Linux-friendly)
- Autor: Generado por ChatGPT (adaptar y revisar antes de uso)
- Uso responsable: sólo recopilar datos públicamente disponibles y con permiso.
"""

import os
import sys
import time
import json
import csv
import yaml
import argparse
import logging
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Networking & parsing
import requests
from bs4 import BeautifulSoup
import tldextract
import whois
import dns.resolver
import ipaddress

# Optional services / enrichment
try:
    import shodan
except Exception:
    shodan = None

# File metadata & OCR
try:
    import exifread
except Exception:
    exifread = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None
try:
    from PIL import Image
    import pytesseract
except Exception:
    Image = None
    pytesseract = None

# Graphing & analysis
try:
    import networkx as nx
    import matplotlib.pyplot as plt
except Exception:
    nx = None

# Encryption for stored data
try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None

# --- Configuration defaults ---
DEFAULT_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
        "curl/7.68.0"
    ],
    "use_tor": False,
    "tor_socks": "socks5h://127.0.0.1:9050",
    "rate_limit_seconds": 1.0,
    "shodan_api_key": None,
    "ip_info_token": None,  # Optional: ipinfo.io token
    "output_dir": "osint_output",
    "encrypt_results": False,
    "encryption_key": None  # if encrypt_results True, set a base64 key (Fernet)
}

# --- Utils ---
def load_config(path: Optional[str]) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    if path and os.path.exists(path):
        with open(path, 'r') as f:
            user_cfg = yaml.safe_load(f) or {}
            cfg.update(user_cfg)
    return cfg

def setup_logging(output_dir: str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(output_dir) / f"osint_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

def random_user_agent(cfg: dict) -> str:
    return random.choice(cfg.get("user_agents", DEFAULT_CONFIG["user_agents"]))

def get_session(cfg: dict) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": random_user_agent(cfg)})
    if cfg.get("use_tor"):
        # requires tor running locally (sudo apt install tor && service tor start)
        s.proxies.update({"http": cfg["tor_socks"], "https": cfg["tor_socks"]})
    return s

def safe_sleep(cfg: dict):
    time.sleep(cfg.get("rate_limit_seconds", 1.0))

# --- Core collectors ---
def search_duckduckgo(query: str, cfg: dict, max_results=10) -> List[Dict[str, str]]:
    """
    Simple DuckDuckGo scraping (HTML). Avoid heavy scraping; uses polite rate-limits.
    """
    session = get_session(cfg)
    results = []
    params = {"q": query}
    headers = {"User-Agent": random_user_agent(cfg)}
    resp = session.get("https://html.duckduckgo.com/html/", params=params, headers=headers, timeout=20)
    safe_sleep(cfg)
    if resp.status_code != 200:
        logging.warning("DuckDuckGo request failed: %s", resp.status_code)
        return results
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select(".result__a")[:max_results]:
        title = a.get_text().strip()
        href = a.get('href')
        results.append({"title": title, "url": href})
    logging.info("DuckDuckGo: found %d results for '%s'", len(results), query)
    return results

def scrape_url(url: str, cfg: dict, max_chars=100000) -> Dict[str, Any]:
    """
    Fetch page, return text, meta tags, and basic links. Respects proxies and UA rotation.
    """
    session = get_session(cfg)
    try:
        r = session.get(url, timeout=20)
        safe_sleep(cfg)
    except Exception as e:
        logging.warning("scrape_url error for %s: %s", url, e)
        return {"url": url, "error": str(e)}

    out = {"url": url, "status_code": r.status_code}
    ct = r.headers.get("Content-Type", "")
    if "text" in ct or "html" in ct:
        soup = BeautifulSoup(r.text, "html.parser")
        out["title"] = soup.title.string.strip() if soup.title else ""
        out["meta"] = {m.get('name') or m.get('property'): m.get('content') for m in soup.find_all('meta') if (m.get('name') or m.get('property'))}
        out["text"] = soup.get_text()[:max_chars]
        out["links"] = list({a.get('href') for a in soup.find_all('a') if a.get('href')})
    else:
        out["content_type"] = ct
    return out

def whois_lookup(domain: str) -> Dict[str, Any]:
    try:
        w = whois.whois(domain)
        return dict(w)
    except Exception as e:
        logging.warning("whois error for %s: %s", domain, e)
        return {"domain": domain, "error": str(e)}

def dns_lookup(name: str, record_type='A') -> Dict[str, Any]:
    res = {}
    try:
        answers = dns.resolver.resolve(name, record_type, lifetime=10)
        res["answers"] = [r.to_text() for r in answers]
    except Exception as e:
        res["error"] = str(e)
    return res

def geolocate_ip(ip: str, cfg: dict) -> Dict[str, Any]:
    # ipinfo.io example (requires token for high rate use). Free tier works limited.
    if not cfg.get("ip_info_token"):
        url = f"https://ipinfo.io/{ip}/json"
        headers = {"User-Agent": random_user_agent(cfg)}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            return r.json()
        except Exception as e:
            return {"error": str(e)}
    else:
        token = cfg["ip_info_token"]
        try:
            r = requests.get(f"https://ipinfo.io/{ip}/json?token={token}", timeout=10)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

def file_metadata_extract(path: str) -> Dict[str, Any]:
    """
    Extracts metadata from images and PDFs (best-effort).
    """
    res = {"path": path}
    if path.lower().endswith(".pdf") and PdfReader:
        try:
            rdr = PdfReader(path)
            res["pdf_metadata"] = rdr.metadata
        except Exception as e:
            res["error_pdf"] = str(e)
    else:
        if exifread:
            try:
                with open(path, "rb") as f:
                    tags = exifread.process_file(f, details=False)
                    res["exif"] = {k: str(v) for k, v in tags.items()}
            except Exception as e:
                res["error_exif"] = str(e)
        else:
            res["exif"] = "exifread not installed"
    return res

def ocr_image(path: str) -> str:
    if not (Image and pytesseract):
        raise RuntimeError("Pillow or pytesseract not installed")
    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    return text

def shodan_search(query: str, cfg: dict, limit=10) -> Dict[str, Any]:
    api_key = cfg.get("shodan_api_key")
    if not api_key:
        return {"error": "no_shodan_api_key"}
    if not shodan:
        return {"error": "shodan library not installed"}
    try:
        client = shodan.Shodan(api_key)
        res = client.search(query, limit=limit)
        return res
    except Exception as e:
        return {"error": str(e)}

# --- Analysis & correlation ---
def normalize_entity(e: str) -> str:
    return e.strip().lower()

def correlate_entities(results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Very simple correlation: finds repeated emails/phones/hosts across results texts/metadata.
    """
    index = {}
    for r in results:
        text = ""
        if isinstance(r, dict):
            text = (r.get("text") or "") + " " + " ".join([str(v) for v in (r.get("meta") or {}).values()])
        else:
            text = str(r)
        for token in set(text.split()):
            if "@" in token or token.isdigit() and len(token) >= 7:
                k = normalize_entity(token)
                index.setdefault(k, []).append(r.get("url") if isinstance(r, dict) else str(r))
    return index

# --- Export & storage (JSON/CSV) ---
def export_json(data: Any, output_dir: str, name: str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info("Exported JSON -> %s", path)
    return str(path)

def export_csv(rows: List[Dict[str, Any]], output_dir: str, name: str):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if not rows:
        return None
    path = Path(output_dir) / f"{name}.csv"
    keys = sorted({k for r in rows for k in r.keys()})
    with open(path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    logging.info("Exported CSV -> %s", path)
    return str(path)

def encrypt_file(path: str, key: bytes):
    if not Fernet:
        logging.error("cryptography not installed; cannot encrypt")
        return False
    f = Fernet(key)
    with open(path, "rb") as fd:
        data = fd.read()
    token = f.encrypt(data)
    enc_path = path + ".enc"
    with open(enc_path, "wb") as fo:
        fo.write(token)
    logging.info("Encrypted file saved to %s", enc_path)
    return enc_path

# --- Visualization ---
def build_graph(relations: Dict[str, List[str]], output_dir: str, name="graph"):
    if not nx:
        logging.warning("networkx not installed - skipping graph")
        return None
    G = nx.Graph()
    for k, vs in relations.items():
        G.add_node(k)
        for v in vs:
            G.add_node(v)
            G.add_edge(k, v)
    img_path = Path(output_dir) / f"{name}.png"
    plt.figure(figsize=(10, 8))
    nx.draw(G, with_labels=True, node_size=300, font_size=8)
    plt.tight_layout()
    plt.savefig(img_path, dpi=150)
    plt.close()
    logging.info("Graph saved to %s", img_path)
    return str(img_path)

# --- Plugin loader (simple) ---
def load_plugins(plugins_dir="plugins"):
    plugins = []
    pdir = Path(plugins_dir)
    if not pdir.exists():
        return plugins
    sys.path.insert(0, str(pdir.resolve()))
    for py in pdir.glob("*.py"):
        name = py.stem
        try:
            module = __import__(name)
            if hasattr(module, "register"):
                plugins.append(module)
                logging.info("Plugin loaded: %s", name)
        except Exception as e:
            logging.warning("Error loading plugin %s: %s", name, e)
    return plugins

# --- CLI orchestration ---
def main():
    parser = argparse.ArgumentParser(description="OSINT Toolkit - Modular")
    parser.add_argument("--config", "-c", help="Path to YAML config", default="config.yaml")
    parser.add_argument("--query", "-q", help="Query term or domain or IP")
    parser.add_argument("--domain", help="Domain to analyze")
    parser.add_argument("--ip", help="IP to analyze")
    parser.add_argument("--url", help="URL to scrape")
    parser.add_argument("--whois", action="store_true", help="Run whois")
    parser.add_argument("--dns", action="store_true", help="Run DNS lookups (A, MX, TXT)")
    parser.add_argument("--shodan", action="store_true", help="Run Shodan search (requires key in config)")
    parser.add_argument("--scrape", action="store_true", help="Scrape provided URL")
    parser.add_argument("--ocr", help="OCR an image file path")
    parser.add_argument("--metadata", help="Extract metadata from file")
    parser.add_argument("--use-tor", action="store_true", help="Route requests through Tor")
    parser.add_argument("--output-dir", "-o", help="Output directory")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.use_tor:
        cfg["use_tor"] = True
    if args.output_dir:
        cfg["output_dir"] = args.output_dir

    setup_logging(cfg["output_dir"])
    logging.info("Starting OSINT Toolkit")

    results = {"meta": {"started": datetime.utcnow().isoformat()}, "data": []}

    # Load plugins (if any)
    plugins = load_plugins("plugins")
    for p in plugins:
        try:
            p.register(cfg, results)
        except Exception as e:
            logging.warning("Plugin register error: %s", e)

    # Query search
    if args.query:
        dd = search_duckduckgo(args.query, cfg, max_results=8)
        results["data"].append({"type": "search.duckduckgo", "query": args.query, "results": dd})
        export_json(dd, cfg["output_dir"], f"search_{hashlib.md5(args.query.encode()).hexdigest()[:8]}")

    # Domain analysis
    if args.domain:
        domain = args.domain
        who = whois_lookup(domain) if args.whois or args.whois is None else {}
        dns_a = dns_lookup(domain, "A") if args.dns else {}
        dns_mx = dns_lookup(domain, "MX") if args.dns else {}
        results["data"].append({"type": "domain", "domain": domain, "whois": who, "dns_a": dns_a, "dns_mx": dns_mx})
        export_json(results["data"][-1], cfg["output_dir"], f"domain_{domain}")

    # IP analysis
    if args.ip:
        ip = args.ip
        geo = geolocate_ip(ip, cfg)
        results["data"].append({"type": "ip", "ip": ip, "geo": geo})
        export_json(geo, cfg["output_dir"], f"ip_{ip.replace('.', '_')}")

    # Shodan
    if args.shodan and args.query:
        sd = shodan_search(args.query, cfg)
        results["data"].append({"type": "shodan", "query": args.query, "results": sd})
        export_json(sd, cfg["output_dir"], f"shodan_{hashlib.md5(args.query.encode()).hexdigest()[:8]}")

    # Scrape URL
    if args.scrape and args.url:
        scraped = scrape_url(args.url, cfg)
        results["data"].append({"type": "scrape", "url": args.url, "result": scraped})
        export_json(scraped, cfg["output_dir"], f"scrape_{hashlib.md5(args.url.encode()).hexdigest()[:8]}")

    # Metadata
    if args.metadata:
        met = file_metadata_extract(args.metadata)
        results["data"].append({"type": "file_metadata", "path": args.metadata, "metadata": met})
        export_json(met, cfg["output_dir"], f"metadata_{Path(args.metadata).stem}")

    # OCR
    if args.ocr:
        try:
            txt = ocr_image(args.ocr)
            results["data"].append({"type": "ocr", "path": args.ocr, "text": txt})
            export_json({"path": args.ocr, "text": txt}, cfg["output_dir"], f"ocr_{Path(args.ocr).stem}")
        except Exception as e:
            logging.error("OCR failed: %s", e)

    # Correlation (basic)
    correlated = correlate_entities([d.get("result") or d.get("results") or d for d in results["data"]])
    results["correlation"] = correlated
    export_json(correlated, cfg["output_dir"], "correlation")

    # Visualize relations
    if correlated:
        build_graph(correlated, cfg["output_dir"], name="correlation_graph")

    # Encrypt outputs (optional)
    if cfg.get("encrypt_results") and cfg.get("encryption_key"):
        key = cfg["encryption_key"].encode()
        # encrypt all json files in output dir
        for j in Path(cfg["output_dir"]).glob("*.json"):
            try:
                encrypt_file(str(j), key)
            except Exception as e:
                logging.error("Encryption error for %s: %s", j, e)

    results["meta"]["finished"] = datetime.utcnow().isoformat()
    export_json(results, cfg["output_dir"], "run_summary")
    logging.info("OSINT run completed. Outputs in %s", cfg["output_dir"])

if __name__ == "__main__":
    main()
