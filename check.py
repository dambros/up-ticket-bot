import json, os, urllib.parse, urllib.request

API = "https://pwjzjlrqggaaiklxavsu.supabase.co/functions/v1/marketplace"
SLUG = "universo-paralello-2027"
STATE = "last_total.txt"  # committed back by the workflow so we notify once per change
MAX_TOTAL = float(os.environ["MAX_TOTAL"])  # R$, ticket + service fee
# Service fee for event 85934, hardcoded in the site's JS. Excludes the payment-method fee (shown only at checkout).
FEE_PCT = float(os.environ.get("FEE_PCT") or 10.5)


def lowest_total(data):
    ev = next(e for e in data["events"] if e["slug"] == SLUG)
    cents = ev["priceFrom"]
    return (cents + round(cents * FEE_PCT / 100)) / 100, ev["offersCount"]


def main():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0"})
    total, offers = lowest_total(json.load(urllib.request.urlopen(req, timeout=30)))
    now = f"{total:.2f}"
    print(f"lowest total R${now} ({offers} offers)")
    last = open(STATE).read().strip() if os.path.exists(STATE) else ""
    open(STATE, "w").write(now)
    if total < MAX_TOTAL and now != last:
        msg = f"UP 2027: R${now} total incl. fee ({offers} offers)\nhttps://revenda.ingresse.com/{SLUG}"
        url = f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage"
        body = urllib.parse.urlencode({"chat_id": os.environ["TG_CHAT_ID"], "text": msg}).encode()
        urllib.request.urlopen(url, body, timeout=30)


if __name__ == "__main__":
    assert lowest_total({"events": [{"slug": SLUG, "priceFrom": 222000, "offersCount": 1}]}) == (2453.1, 1)
    main()
