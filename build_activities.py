"""Build activities.html — the per-day activity explorer.

Inputs: activities_data.py (hand-written details), activities_reviews.py (paraphrased review themes),
data/activity_images.json (Wikimedia Commons, scraped via Chrome), data/activity_gmaps.json (Google Maps
rating / review count / topic tags, scraped via Chrome). Run: python3 build_activities.py
"""
import json
from pathlib import Path
from urllib.parse import quote_plus

import activities_data as AD
from activities_reviews import REVIEWS, OPERATOR, SKIP_RATING

HERE = Path(__file__).parent
IMG = json.loads((HERE / "data/activity_images.json").read_text())
GM = json.loads((HERE / "data/activity_gmaps.json").read_text())

acts = []
for a in AD.A:
    g = GM.get(a["id"], {})
    rated = a["id"] not in SKIP_RATING and g.get("r")
    praise, watch = REVIEWS.get(a["id"], ("", ""))
    acts.append(dict(
        a,
        images=[dict(src=i["src"], page=i["page"], by=i["by"] or "Unknown", lic=i["lic"] or "see source") for i in IMG.get(a["id"], [])],
        rating=g.get("r", "") if rated else "",
        count=g.get("c", "").replace(" reviews", "") if rated else "",
        topics=[t.split(":")[0] for t in g.get("tp", [])] if rated else [],
        operator=OPERATOR.get(a["id"], ""),
        praise=praise, watch=watch,
        maps=f"https://www.google.com/maps/search/?api=1&query={quote_plus(a['maps_q'])}",
        directions=f"https://www.google.com/maps/dir/?api=1&destination={a['lat']},{a['lng']}",
    ))

data = dict(days=[dict(id=d, date=dt, place=p, theme=t, gap=getattr(AD, "FOOD_GAPS", {}).get(d, "")) for d, dt, p, t in AD.DAYS], acts=acts)
tpl = (HERE / "activities_template.html").read_text()
(HERE / "activities.html").write_text(tpl.replace("/*__DATA__*/", "window.ACT = " + json.dumps(data, ensure_ascii=False) + ";"))
print(f"activities.html: {len(acts)} activities, {sum(len(x['images']) for x in acts)} images, {sum(1 for x in acts if x['rating'])} rated")
