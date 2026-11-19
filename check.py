import json, os, urllib.parse, urllib.request

API = "https://pwjzjlrqggaaiklxavsu.supabase.co/functions/v1/marketplace"
# slug -> service fee %, hardcoded in the site's JS ("85934:10.5", default 15).
# Excludes the payment-method fee (shown only at checkout).
SLUGS = {"universo-paralello-2027": 10.5, "universo-paralello-comissarios": 15}
STATE = "last_total.txt"  # "slug total" per line, committed back by the workflow so we notify once per change
MAX_TOTAL = float(os.environ["MAX_TOTAL"])  # R$, ticket + service fee


def lowest_total(ev):
    cents = ev["priceFrom"]
    return (cents + round(cents * SLUGS[ev["slug"]] / 100)) / 100


def main():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0"})
    events = [e for e in json.load(urllib.request.urlopen(req, timeout=30))["events"] if e["slug"] in SLUGS]
    last = dict(l.split() for l in open(STATE) if l.strip()) if os.path.exists(STATE) else {}
    now = {e["slug"]: f"{lowest_total(e):.2f}" for e in events}
    open(STATE, "w").write("".join(f"{s} {t}\n" for s, t in {**last, **now}.items()))
    for e in events:
        total, slug = now[e["slug"]], e["slug"]
        print(f"{slug}: lowest total R${total} ({e['offersCount']} offers)")
        if float(total) < MAX_TOTAL and total != last.get(slug):
            msg = f"{e['title']}: R${total} total incl. fee ({e['offersCount']} offers)\nhttps://revenda.ingresse.com/{slug}"
            url = f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage"
            body = urllib.parse.urlencode({"chat_id": os.environ["TG_CHAT_ID"], "text": msg}).encode()
            urllib.request.urlopen(url, body, timeout=30)


if __name__ == "__main__":
    assert lowest_total({"slug": "universo-paralello-2027", "priceFrom": 222000}) == 2453.1
    assert lowest_total({"slug": "universo-paralello-comissarios", "priceFrom": 319000}) == 3668.5
    main()
