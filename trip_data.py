"""Single source of truth for the Croatia trip: POIs, stays, travel legs.

Run `python3 trip_data.py` to regenerate:
  - croatia_trip.kml          (import into Google My Maps; one layer per folder)
  - the TRIPDATA block inside index.html
"""
import json, re, html
from pathlib import Path
from urllib.parse import quote_plus

HERE = Path(__file__).parent

# ---------------------------------------------------------------- POIs
# kind: stay | hub | culture | nature | adventure | relax | food | alt
# (name, lat, lng, kind, note)
LAYERS = [
    ("Oct 10 · Zagreb", "#c25b8a", [
        ("Zagreb Airport (ZAG)", 45.7429, 16.0688, "hub", "LH 1404 lands 14:00. Pick up the rental car here (one-way to Split). ~25 min to the centre."),
        ("Ban Jelačić Square", 45.8131, 15.9772, "culture", "The main square and meeting point; trams everywhere. [added]"),
        ("Dolac Market", 45.8143, 15.9775, "food", "Red-umbrella farmers' market. Sat closes ~15:00 — you'll likely miss it; Sun 7–13 works before the drive. [added]"),
        ("Zagreb Cathedral", 45.8144, 15.9798, "culture", "Neo-Gothic twin spires over Kaptol. [added]"),
        ("Tkalčićeva Street", 45.8155, 15.9760, "food", "Café and bar street — best for the evening. [added]"),
        ("Stone Gate", 45.8152, 15.9751, "culture", "Candle-lit shrine in the last surviving old-town gate. [added]"),
        ("St. Mark's Church", 45.8164, 15.9735, "culture", "The tiled roof with the coats of arms. [added]"),
        ("Museum of Broken Relationships", 45.8150, 15.9727, "culture", "Rain-proof and genuinely moving; open 9–21 in October. [added]"),
        ("Lotrščak Tower & funicular", 45.8143, 15.9728, "culture", "Shortest funicular in the world; Strossmayer promenade views. [added]"),
        ("La Štruk", 45.8140, 15.9748, "food", "Štrukli (baked cheese pastry) specialists. [added]"),
    ]),
    ("Oct 11 · Rastoke, Barać → Plitvice", "#9bb87f", [
        ("Rastoke (Slunj)", 45.1224, 15.5808, "culture", "Water-mill village on the way down, ~1 h 20 from Zagreb. Fine in the rain."),
        ("Barać Caves", 45.0119, 15.5669, "alt", "Underground = rain-proof. Tours leave as groups form (10–45 min wait); 9 °C inside — bring a layer."),
        ("Restaurant Lička Kuća", 44.9020, 15.6080, "food", "Lamb & Lika potatoes by Entrance 1. [added]"),
    ]),
    ("Oct 12 · Plitvice → Krka → Split", "#87a96b", [
        ("Plitvice – Entrance 1", 44.9019, 15.6097, "nature", "Program C starts here; arrive for the 8:00 slot. Done ~13:30."),
        ("Plitvice – Entrance 2", 44.8813, 15.6222, "nature", "Start of Program H."),
        ("Veliki Slap (Great Waterfall)", 44.9031, 15.6100, "nature", "78 m — tallest in Croatia."),
        ("Kozjak Lake boat (P1–P2)", 44.8800, 15.6180, "nature", "Electric boat crossing, included in ticket."),
        ("Galovac & Upper Lakes", 44.8700, 15.6010, "nature", "Best cascades; autumn colour peak mid-Oct."),
        ("Viewpoint over Lower Lakes (Kozjačka)", 44.9005, 15.6090, "nature", "Classic postcard shot near Entrance 1."),
        ("Krka NP – Skradinski Buk", 43.8050, 15.9630, "nature", "Plitvice → Krka ~2 h. Skradinski Buk open 8–18 until Oct 15 (last entry earlier); boardwalk loop ~1.5 h. Then ~1 h to Split."),
        ("Šibenik – St. James Cathedral", 43.7367, 15.8889, "alt", "UNESCO cathedral; only if you skip Krka."),
        ("Trogir Old Town", 43.5170, 16.2510, "alt", "UNESCO island town; now an alternate (no slot in the Zagreb-start plan)."),
        ("Kamerlengo Fortress", 43.5160, 16.2480, "alt", "Trogir's fortress walk-up."),
    ]),
    ("Oct 13 · Omiš, Cetina & Klis", "#e0503a", [
        ("Omiš Old Town", 43.4447, 16.6886, "culture", "Split → Omiš 41 min / 25 km."),
        ("Cetina rafting put-in (Penšići area)", 43.4400, 16.7700, "adventure", "Half-day rafting, 3–4 h; operators pick up in Omiš."),
        ("Radmanove Mlinice", 43.4450, 16.7270, "food", "Riverside mill restaurant — rafting take-out. Trout!"),
        ("Zipline Omiš", 43.4480, 16.7000, "adventure", "8 lines over the canyon, ~3 h incl. transfer."),
        ("Fortica (Starigrad) Fortress", 43.4460, 16.6960, "adventure", "Steep ~1 h hike, huge canyon/sea view."),
        ("Mirabela Fortress", 43.4450, 16.6900, "culture", "Easy 10-min climb from town."),
        ("Gubavica Waterfall", 43.4338, 16.8898, "nature", "Canyon waterfall viewpoint above Zadvarje. [added]"),
        ("Biokovo Skywalk", 43.3200, 17.0580, "alt", "Glass platform, ~1 h 15 from Omiš via Makarska. Check park road hours/wind."),
        ("Makarska", 43.2969, 17.0178, "alt", "Base town for Biokovo. [added]"),
        ("Klis Fortress", 43.5596, 16.5234, "culture", "Omiš → Klis ~40 min on the way back; go for sunset (~18:20), then 20 min into Split."),
        ("Restoran Perlica (Klis)", 43.5620, 16.5260, "food", "Spit-roast lamb (Klis is famous for it). [added]"),
    ]),
    ("Oct 12–14 · Split (evenings + Oct 14 morning)", "#d46a4c", [
        ("Diocletian's Palace – Peristyle", 43.5081, 16.4402, "culture", "Heart of the palace. Go at night too — lit up, live klapa singing some evenings."),
        ("Cathedral of St. Domnius & Bell Tower", 43.5078, 16.4405, "culture", "Climb the bell tower for the best Old Town rooftop view."),
        ("Palace Cellars (Substructures)", 43.5076, 16.4400, "culture", "Rain-proof; Game of Thrones filming location."),
        ("Golden Gate & Grgur Ninski statue", 43.5093, 16.4398, "culture", "Rub the statue's toe for luck."),
        ("Riva Promenade", 43.5075, 16.4385, "relax", "Evening stroll + coffee."),
        ("Green Market (Pazar)", 43.5087, 16.4415, "food", "Morning produce, figs, cheese, dried lavender. [added]"),
        ("Vidilica Café (Marjan viewpoint)", 43.5095, 16.4299, "nature", "15-min stair climb from Varoš; sunset view over Split. [added]"),
        ("Marjan – Telegrin summit", 43.5087, 16.4133, "nature", "Top of Marjan; full loop 2–3 h."),
        ("Kasjuni Beach", 43.5040, 16.4025, "relax", "Quieter Marjan beach if warm. [added]"),
        ("Salona Archaeological Park", 43.5390, 16.4830, "alt", "Roman provincial capital ruins, 15 min from Split."),
        ("Bačvice Beach", 43.5020, 16.4470, "relax", "City beach; play picigin. [added]"),
    ]),
    ("Oct 14 · Hvar Town", "#6ba6b8", [
        ("Split Ferry Port", 43.5033, 16.4413, "hub", "Oct 14 sailings to Hvar Town: 13:00 Krilo, 14:00 Jadrolinija, 15:10 TP Line, 16:00 Krilo (~55–85 min). Line 641 ends Oct 11."),
        ("Hvar Town catamaran pier", 43.1715, 16.4405, "hub", "Arrival."),
        ("St. Stephen's Square & Cathedral", 43.1722, 16.4420, "culture", "Largest square in Dalmatia."),
        ("Fortica (Španjola) Hvar", 43.1745, 16.4410, "nature", "20-min climb; sunset over Pakleni Islands."),
        ("Franciscan Monastery", 43.1695, 16.4455, "culture", "Seaside cloister, Last Supper painting."),
        ("Arsenal & Renaissance Theatre", 43.1717, 16.4412, "culture", "One of Europe's oldest public theatres (1612). [added]"),
        ("Pakleni Islands – Palmižana", 43.1630, 16.3960, "relax", "Taxi boat 15–20 min if sea is calm."),
        ("Pokonji Dol beach", 43.1640, 16.4610, "relax", "20-min coastal walk east of town."),
        ("Hula Hula Beach Bar", 43.1686, 16.4330, "food", "Sunset drinks, west promenade. [added]"),
    ]),
    ("Oct 15 · Hvar Island loop", "#5b8fa0", [
        ("Velo Grablje", 43.1700, 16.5080, "nature", "Abandoned lavender village; Konoba Zbondini. 15 min from town."),
        ("Malo Grablje", 43.1580, 16.5170, "nature", "Ghost village; Konoba Stori Komin. [route option]"),
        ("Milna (Hvar)", 43.1575, 16.4910, "relax", "Small cove village."),
        ("Brusje", 43.1860, 16.4770, "nature", "Hilltop village, herb & olive country."),
        ("Dubovica Beach", 43.1537, 16.5260, "relax", "Park at road, 15-min walk down. 15 min from Hvar Town."),
        ("Stari Grad & Tvrdalj", 43.1842, 16.5945, "culture", "Oldest town in Croatia (384 BC). 25 min from Hvar Town."),
        ("Stari Grad Plain (UNESCO)", 43.1780, 16.6300, "nature", "Greek field grid 2,400 years old; cycle or drive through."),
        ("Vrboska", 43.1810, 16.6750, "culture", "'Little Venice' of Hvar; 15 min past Stari Grad."),
        ("Jelsa", 43.1618, 16.6932, "food", "Nice harbour for lunch. [added]"),
        ("Sveta Nedjelja", 43.1449, 16.6102, "adventure", "Via Pitve tunnel; cliff climbing, vineyards (Zlatan Otok winery)."),
        ("Zlatan Otok Winery", 43.1440, 16.6120, "food", "Tasting at Sveta Nedjelja. [added]"),
    ]),
    ("Oct 16–17 · Dubrovnik", "#a88ec9", [
        ("Dubrovnik Gruž Port", 42.6580, 18.0850, "hub", "Catamaran from Hvar ~3 h 30–4 h; taxi/bus to Pile 15 min."),
        ("Pile Gate", 42.6415, 18.1070, "culture", "Main entrance."),
        ("Stradun", 42.6410, 18.1098, "culture", "Main street."),
        ("Old Port", 42.6405, 18.1135, "culture", "Boats to Lokrum leave here."),
        ("Cable Car lower station", 42.6430, 18.1140, "hub", "4 min up."),
        ("Mount Srđ / Fort Imperial", 42.6480, 18.1150, "nature", "Hike 45–60 min or cable car; go for sunset."),
        ("City Walls entrance (Pile)", 42.6419, 18.1073, "culture", "Start 8 am opening; 2 km loop, 1.5–2 h."),
        ("Minčeta Tower", 42.6428, 18.1085, "culture", "Highest point on the walls."),
        ("Fort Lovrijenac", 42.6410, 18.1040, "culture", "Included with walls ticket."),
        ("Lokrum Island", 42.6270, 18.1210, "nature", "15-min ferry; botanical garden, Dead Sea lake, peacocks."),
        ("Sea kayak launch (Pulitika / Pile)", 42.6417, 18.1060, "adventure", "Kayak to Lokrum & Betina cave, ~3 h."),
        ("Rector's Palace", 42.6403, 18.1109, "culture", "Rain option."),
        ("Maritime Museum (St. John Fortress)", 42.6397, 18.1137, "culture", "Rain option."),
        ("Buža Bar", 42.6388, 18.1102, "relax", "Cliff-side bar outside the walls. [added]"),
        ("Banje Beach", 42.6415, 18.1165, "relax", "Old Town view beach. [added]"),
        ("Trsteno Arboretum", 42.7120, 17.9750, "alt", "25 min north; windy-sea alternate."),
    ]),
    ("Oct 18 · Herzegovina", "#c9804a", [
        ("Kravica Waterfalls", 43.1566, 17.6078, "nature", "Dubrovnik → Kravica ~2 h 15 incl. border."),
        ("Počitelj", 43.1339, 17.7314, "culture", "Ottoman fortress village, 20 min from Kravica."),
        ("Blagaj Tekke", 43.2567, 17.9024, "alt", "Dervish house at Buna spring; 20 min from Mostar."),
        ("Stari Most (Old Bridge)", 43.3373, 17.8150, "culture", "Watch divers; Kujundžiluk bazaar."),
        ("Koski Mehmed Pasha Mosque minaret", 43.3393, 17.8144, "culture", "Best bridge viewpoint."),
        ("Crooked Bridge (Kriva Ćuprija)", 43.3383, 17.8138, "culture", "Tiny predecessor to Stari Most. [added]"),
        ("Kotor, Montenegro", 42.4247, 18.7712, "alt", "Alternative day trip instead of Bosnia."),
    ]),
    ("Oct 19 · Departure", "#8a8378", [
        ("Cavtat Riva", 42.5808, 18.2180, "relax", "If late flight. 10 min to airport."),
        ("Račić Mausoleum", 42.5836, 18.2140, "culture", "Meštrović-designed, on Cavtat peninsula."),
        ("Dubrovnik Airport (DBV)", 42.5614, 18.2682, "hub", "Old Town → airport 32 min / 22 km."),
    ]),
    ("Stays (neighbourhoods)", "#ffffff", [
        ("STAY Oct 10–11 · Zagreb centre", 45.8120, 15.9770, "stay", "Near Ban Jelačić Square; pick a hotel with parking — you have the car."),
        ("STAY Oct 11–12 · Plitvice (Mukinje / Rastovača)", 44.8850, 15.6280, "stay", "Walk or 5-min drive to Entrance 2 — early start."),
        ("STAY Oct 12–14 · Split (Varoš / Old Town)", 43.5100, 16.4340, "stay", "You have the car until the evening of Oct 13 — book parking."),
        ("STAY Oct 14–16 · Hvar Town", 43.1710, 16.4430, "stay", "The splurge nights."),
        ("STAY Oct 16–19 · Dubrovnik (Ploče / Pile)", 42.6420, 18.1150, "stay", "Just outside the walls = easier luggage + views."),
    ]),
]

# ---------------------------------------------------------------- stays
def bk(slug, ci, co):
    return f"https://www.booking.com/hotel/hr/{slug}?checkin={ci}&checkout={co}&group_adults=2&no_rooms=1&group_children=0"

def ab(rid, ci, co):
    return f"https://www.airbnb.com/rooms/{rid}?check_in={ci}&check_out={co}&adults=2"

def bk_search(q, ci, co, nflt="review_score%3D90"):
    return (f"https://www.booking.com/searchresults.html?ss={quote_plus(q)}&checkin={ci}&checkout={co}"
            f"&group_adults=2&no_rooms=1&group_children=0&nflt={nflt}&order=popularity")

def ab_search(slug, ci, co):
    return f"https://www.airbnb.com/s/{slug}/homes?checkin={ci}&checkout={co}&adults=2&guest_favorite=true"

def gh_search(q, ci, co):
    return f"https://www.google.com/travel/search?q={quote_plus(q)}&checkin={ci}&checkout={co}&adults=2"

# prices are the total for the stay as shown on 2026-09-30 (USD, 2 adults); "—" = not captured, check link.
# km = straight-line distance from the listing's map pin to the leg's anchor (checked 2026-09-30 via Booking/Airbnb
# listing coordinates; Airbnb pins are approximate to ~200 m until booked). Walk time ≈ km × 1.3 at 5 km/h.
# booking tuple: (name, score, price, slug, tier, km[, note])   airbnb tuple: (name, score, price, id, km[, note])
STAYS = [
    dict(id="zagreb", title="Zagreb", dates="Oct 10 → 11", nights=1, ci="2026-10-10", co="2026-10-11",
         area="Donji Grad / Upper Town edge", anchor="Ban Jelačić Square",
         verdict="Matters moderately — you'll want to walk the Upper Town in the evening, and you'll have the car. All picks are ≤ 15 min on foot from Ban Jelačić Square.",
         tip="You land at 14:00 and pick up the car at the airport, so favour a hotel with on-site parking (Stellar, Capital, Esplanade). "
             "Booked last-minute (Oct 9), so only a handful of 9+ places were still free — check the searches for anything new.",
         searches=[("Booking · 9+ within 1.5 km", bk_search("Zagreb, Croatia", "2026-10-10", "2026-10-11", "review_score%3D90%3Bdistance%3D1500")),
                   ("Booking · 9+ with parking", bk_search("Zagreb, Croatia", "2026-10-10", "2026-10-11", "review_score%3D90%3Bdistance%3D1500%3Bhotelfacility%3D2")),
                   ("Airbnb · Guest favourites", ab_search("Zagreb--Croatia", "2026-10-10", "2026-10-11")),
                   ("Google Hotels", gh_search("hotels Zagreb Upper Town", "2026-10-10", "2026-10-11"))],
         booking=[("art'otel Zagreb", "9.3 · 2,534", "$328", "art-otel-zagreb.html", "Luxe", 0.28),
                  ("Esplanade Zagreb Hotel", "9.0 · 2,530", "$472", "esplanade-zagreb-hotel.html", "Luxe", 0.85, "Historic grand hotel; parking"),
                  ("Hotel PARK 45", "9.0 · 2,754", "$367", "park-45.html", "Luxe", 0.66),
                  ("Hotel Capital", "9.1 · 1,193", "$275", "amadria-park-capital.html", "Mid", 0.39, "Parking"),
                  ("Stay Swanky", "9.0 · 1,806", "$270", "swanky-bed-amp-breakfast.html", "Mid", 0.68),
                  ("Hotel Stellar Boutique Modules", "9.3 · 2,191", "$206", "jadran-zagreb.html", "Value", 0.56, "Parking")],
         airbnb=[]),
    dict(id="plitvice", title="Plitvice", dates="Oct 11 → 12", nights=1, ci="2026-10-11", co="2026-10-12",
         area="Rastovača (Entrance 1) or Mukinje / Jezerce (Entrance 2)", anchor="park entrance",
         verdict="Location matters a lot — it's the whole point of sleeping here. Pick by entrance: Entrance 1 → Program C (starts at the Great Waterfall); Entrance 2 → Program H.",
         tip="Arriving from Zagreb via Rastoke and Barać on Oct 11 (rainy), park day is Oct 12 (dry). Dropped two picks that were 8–10 km out (Drežnik Grad cabin, Guesthouse Zrinka). Everything below is walkable (≤ 25 min) to an entrance; "
             "you'll have the car anyway, and both entrances are a 5-min drive apart.",
         searches=[("Booking · 9+ near park", bk_search("Plitvice Lakes National Park, Croatia", "2026-10-11", "2026-10-12")),
                   ("Airbnb · Guest favourites", ab_search("Plitvička-Jezera--Croatia", "2026-10-11", "2026-10-12")),
                   ("Google Hotels", gh_search("hotels near Plitvice Lakes", "2026-10-11", "2026-10-12"))],
         booking=[("Hotel Jezero (park hotel)", "9.6", "—", "jezero.html", "Mid", 0.50, "Entrance 2"),
                  ("Fenomen Plitvice Resort", "9.4 · 678", "$230", "fenomen-plitvice.html", "Luxe", 0.65, "Entrance 1"),
                  ("Plitvice Falls Cottage – rooms & dinner", "9.6 · 1,831", "$114", "plitvice-falls-cottage.html", "Mid", 0.88, "Entrance 1"),
                  ("Apartman Lana", "9.9 · 112", "$112", "lana-plitvicka-jezera.html", "Value", 0.85, "Entrance 2"),
                  ("B&B Plitvica Creek", "9.7 · 782", "$121", "b-amp-b-plitvica-creek.html", "Value", 1.03, "Entrance 1"),
                  ("Guest House Plitvice Villa Verde", "9.8 · 887", "$100", "guest-house-plitvice-villa-verde.html", "Value", 1.89, "Entrance 2")],
         airbnb=[("800 m from the National Park", "4.98 · 84", "$125", "1131118921780855907", 0.94, "Entrance 2"),
                 ("In the heart of Plitvice, free parking", "4.96 · 111", "$113", "1111719293310602037", 1.04, "Entrance 2"),
                 ("Forest view with jacuzzi (Jezerce)", "4.91 · 80", "$97", "909427894493463613", 1.51, "Entrance 2"),
                 ("Walk to Plitvice Lakes Entrance 1", "4.94 · 88", "$125", "26776820", 0.92, "Entrance 1"),
                 ("500 m from park entrance (Rastovača B&B)", "4.86 · 857", "$79", "3380832", 1.01, "Entrance 1")]),
    dict(id="split2", title="Split #2", dates="Oct 12 → 14", nights=2, ci="2026-10-12", co="2026-10-14",
         area="Split Old Town", anchor="Peristyle",
         verdict="Old Town is right for evenings and the Oct 14 catamaran (ferry port is a 5-min walk) — the only catch is the car.",
         tip="You keep the car until the evening of Oct 13 (Omiš + Klis), so you need parking for one night (Oct 12→13). Either pick a place with parking (second search) "
             "or use a public garage on the Old Town edge and walk in. Alternative: drop the car on Oct 12 and take Omiš operators' Split hotel pickup — but then Klis needs a taxi.",
         searches=[("Booking · 9+ Old Town", bk_search("Split Old Town, Split, Croatia", "2026-10-12", "2026-10-14")),
                   ("Booking · with parking", bk_search("Split, Croatia", "2026-10-12", "2026-10-14", "review_score%3D90%3Bhotelfacility%3D2")),
                   ("Airbnb · Guest favourites", ab_search("Split--Croatia", "2026-10-12", "2026-10-14")),
                   ("Google Hotels", gh_search("hotels Split Croatia", "2026-10-12", "2026-10-14"))],
         booking=[("Heritage Hotel Cardo", "9.6 · 136", "$345", "heritage-cardo.html", "Luxe", 0.06),
                  ("Old Town Luxury House", "9.5 · 55", "$406", "old-town-luxury-house-split.html", "Luxe", 0.26),
                  ("Riva Palace", "9.2 · 348", "$187", "riva-palace-split.html", "Mid", 0.06),
                  ("Guest House Imperial", "9.6 · 181", "$169", "guest-house-imperial.html", "Mid", 0.10),
                  ("Luxury Apartments Lilly 2", "9.8 · 97", "$147", "luxury-apartments-lilly-2.html", "Value", 0.22),
                  ("Porto Nativo Split", "9.6 · 125", "$128", "porto-nativo-split.html", "Value", 0.37)],
         airbnb=[("1700s stone house in the Palace", "4.98 · 372", "$305", "27506542", 0.11),
                 ("Inside Diocletian's Palace, private entrance", "4.98 · 287", "$342", "5452710", 0.11),
                 ("Fruit Square, cathedral & tower views", "4.88 · 610", "$227", "18800883", 0.17),
                 ("Dobrić quarter, 40 m from Riva", "4.87 · 209", "$219", "43539463", 0.19),
                 ("Palace courtyard, private entrance", "4.91 · 220", "$302", "35411177", 0.08)]),
    dict(id="hvar", title="Hvar", dates="Oct 14 → 16", nights=2, ci="2026-10-14", co="2026-10-16",
         area="Hvar Town", anchor="catamaran pier",
         verdict="Matters — you arrive and leave by catamaran with bags. All picks are in Hvar Town; the Booking hotels are all on the harbour (≤ 4 min walk).",
         tip="Two Airbnbs sit 0.75–1 km west along the coast (quieter, sea views, ~15 min walk). Mid-October some Hvar hotels close around Oct 15–20 — confirm it's open both nights.",
         searches=[("Booking · 9+ Hvar", bk_search("Hvar, Hvar Island, Croatia", "2026-10-14", "2026-10-16")),
                   ("Booking · 4–5★", bk_search("Hvar, Hvar Island, Croatia", "2026-10-14", "2026-10-16", "class%3D4%3Bclass%3D5%3Breview_score%3D80")),
                   ("Airbnb · Guest favourites", ab_search("Hvar--Croatia", "2026-10-14", "2026-10-16")),
                   ("Google Hotels", gh_search("hotels Hvar Town", "2026-10-14", "2026-10-16"))],
         booking=[("Palace Elisabeth (Leading Hotels)", "9.5 · 109", "$579", "the-palace.html", "Luxe", 0.14),
                  ("Riva Marina Hvar Hotel", "9.5 · 303", "$368", "riva-suncani-hvar-hotels.html", "Luxe", 0.14),
                  ("Adriana Hvar Spa Hotel", "9.2 · 426", "$345", "adriana-hvar-marina-and-spa.html", "Luxe", 0.13),
                  ("Heritage Hotel Park Hvar", "9.5 · 440", "$251", "heritage-park-hvar.html", "Mid", 0.15),
                  ("History Hvar 1529", "9.7 · 434", "$170", "history-hvar.html", "Mid", 0.17),
                  ("Villa Nora Hvar", "9.8 · 415", "$170", "villa-nora-hvar.html", "Value", 0.27)],
         airbnb=[("Balcony with Pakleni Islands views", "4.96 · 397", "$318", "3569028", 0.11),
                 ("Sea & square views, stone house", "4.93 · 486", "$210", "4944145", 0.05),
                 ("Beachfront suite, sea-view balcony", "5.0 · 137", "$353", "26071963", 0.42),
                 ("Adriatic & Pakleni views, private terrace", "4.98 · 58", "$246", "1169804961497567856", 0.75, "West of town"),
                 ("Top floor panorama, beach access", "4.99 · 157", "$386", "1411990", 1.00, "West of town")]),
    dict(id="dubrovnik", title="Dubrovnik", dates="Oct 16 → 19", nights=3, ci="2026-10-16", co="2026-10-19",
         area="Old Town / Pile / Ploče", anchor="Pile Gate",
         verdict="Matters most of any leg — walls at 8 am, Lokrum boats, dinners, all on foot. Dropped two Lapad hotels (~4 km, bus/taxi every trip).",
         tip="Inside the walls = no cars, lots of stairs with bags (porters/taxis stop at Pile or Ploče gate). The 'Old Town view' Airbnbs are uphill above the walls — great views, steep steps.",
         searches=[("Booking · 9+ Old Town", bk_search("Dubrovnik Old Town, Dubrovnik, Croatia", "2026-10-16", "2026-10-19")),
                   ("Booking · 4–5★ Old Town", bk_search("Dubrovnik Old Town, Dubrovnik, Croatia", "2026-10-16", "2026-10-19", "class%3D4%3Bclass%3D5")),
                   ("Airbnb · Guest favourites", ab_search("Dubrovnik--Croatia", "2026-10-16", "2026-10-19")),
                   ("Google Hotels", gh_search("hotels Dubrovnik Old Town", "2026-10-16", "2026-10-19"))],
         booking=[("Hilton Imperial Dubrovnik", "—", "—", "hilton-imperial-dubrovnik.html", "Luxe", 0.23, "Right outside Pile Gate"),
                  ("The Pucić Palace", "—", "—", "the-pucic-palace.html", "Luxe", 0.25, "Inside the walls"),
                  ("Prijeko Palace", "9.2 · 333", "$410", "prijeko-palace.html", "Luxe", 0.15, "Inside the walls"),
                  ("Hotel Bellevue Dubrovnik", "9.4 · 471", "$343", "bellevue-dubrovnik.html", "Luxe", 1.35, "Cliffside, own beach; ~20 min walk or 5 min taxi"),
                  ("Angelus Apartments", "9.6 · 244", "$170", "angelus-apartments.html", "Mid", 0.07),
                  ("Placeta Apartments & Rooms", "9.2 · 395", "$112", "rooms-placeta.html", "Value", 0.13)],
         airbnb=[("Renovated Old Town flat near Stradun", "4.98 · 230", "$551", "46964824", 0.32),
                 ("Quiet area, 5-min walk to Old Town", "4.97 · 217", "$353", "44839084", 0.44),
                 ("Peaceful Pile, 5–10 min to Old Town", "4.94 · 368", "$393", "13768318", 0.52),
                 ("Sea & Old Town views balcony", "4.96 · 654", "$821", "679813", 0.69, "Uphill, steps"),
                 ("Panoramic Old Town views from balcony", "4.95 · 421", "$474", "2965048", 0.71, "Uphill, steps")]),
]


# ---------------------------------------------------------------- travel legs
def gdir(*stops):
    return "https://www.google.com/maps/dir/" + "/".join(quote_plus(s) for s in stops) + "/data=!4m2!4m1!3e0"

LEGS = [
    dict(date="Oct 10", mode="✈️ + 🚗", frm="Frankfurt", to="Zagreb centre", time="LH 1404 12:30→14:00 + 25 min", dist="17 km",
         note="Pick up the one-way rental (Zagreb airport → Split) on arrival. Croatia is in Schengen — no passport check at ZAG.", link=gdir("Zagreb Airport", "Ban Jelačić Square, Zagreb")),
    dict(date="Oct 11", mode="🚗", frm="Zagreb", to="Rastoke (Slunj)", time="~1 h 20 min", dist="~105 km",
         note="Optional Dolac market (Sun 7–13) or a štrukli class first. Rain day — that's fine for these stops.", link=gdir("Zagreb, Croatia", "Rastoke, Slunj")),
    dict(date="Oct 11", mode="🚗", frm="Rastoke", to="Barać Caves → Plitvice", time="~20 + 30 min", dist="~40 km",
         note="Cave tours leave as groups form. Sleep near the park.", link=gdir("Rastoke, Slunj", "Barać Caves", "Plitvice Lakes Entrance 1")),
    dict(date="Oct 12", mode="🚗", frm="Plitvice", to="Krka (Skradinski Buk)", time="~2 h", dist="~190 km",
         note="Leave Plitvice by ~13:30. Skradinski Buk is open until 18:00 through Oct 15.", link=gdir("Plitvice Lakes Entrance 1", "Skradinski buk")),
    dict(date="Oct 12", mode="🚗", frm="Krka", to="Split", time="~1 h", dist="~90 km",
         note="Arrive ~18:30; palace and Riva at night.", link=gdir("Skradinski buk", "Split, Croatia")),
    dict(date="Oct 13", mode="🚗", frm="Split", to="Omiš", time="41 min", dist="25 km",
         note="Drive yourselves (you still have the car). Rafting operators meet in Omiš; 3–4 h on the river.", link=gdir("Split, Croatia", "Omiš, Croatia")),
    dict(date="Oct 13", mode="🚗", frm="Omiš", to="Klis Fortress → Split", time="~40 + 20 min", dist="~45 km",
         note="Sunset at Klis (~18:20), then return the rental car in Split.", link=gdir("Omiš, Croatia", "Klis Fortress", "Split, Croatia")),
    dict(date="Oct 13 alt", mode="🚗", frm="Omiš", to="Biokovo Skywalk", time="~1 h 15 min", dist="~55 km",
         note="Park road is single-lane and slow; closes in high wind.", link=gdir("Omiš, Croatia", "Biokovo Skywalk")),
    dict(date="Oct 14", mode="⛴️", frm="Split port", to="Hvar Town", time="~55 min – 1 h 25", dist="catamaran",
         note="✅ Checked on Ferryhopper Oct 10: 9 sailings with seats (08:00–15:45; after the Split morning: 13:00 Krilo, 15:10 TP Line, 15:45 TP Line). ~$58 for 2.",
         link="https://www.croatiaferries.com/split-hvar-ferry.htm"),
    dict(date="Oct 15", mode="🛵/🚗", frm="Hvar Town", to="Dubovica → Stari Grad → Vrboska", time="15 + 25 + 15 min", dist="~40 km",
         note="Rent a scooter/car in Hvar Town for the day. Sveta Nedjelja via Pitve tunnel ~35 min from Stari Grad.",
         link=gdir("Hvar Town", "Dubovica Beach, Hvar", "Stari Grad, Hvar", "Vrboska", "Hvar Town")),
    dict(date="Oct 16", mode="⛴️", frm="Hvar Town", to="Dubrovnik (Gruž)", time="3 h 20 – 3 h 35", dist="catamaran",
         note="✅ Checked on Ferryhopper Oct 10: 09:10→12:30 Krilo ($115 for 2), 10:40→14:15 TP Line, 16:45→20:20 TP Line ($127 for 2). Book the 09:10.",
         link="https://www.tp-line.hr/en/novost/high-speed-ferry-line-842-dubrovnik-korcula-hvar-milna-split"),
    dict(date="Oct 16", mode="🚕", frm="Gruž port", to="Pile Gate", time="~15 min", dist="4 km", note="Taxi or bus 1A/1B/3.", link=gdir("Port of Dubrovnik Gruž", "Pile Gate, Dubrovnik")),
    dict(date="Oct 17", mode="🚶/⛴️", frm="Old Port", to="Lokrum", time="15 min boat", dist="—", note="Boats every 30 min; last return ~6 pm in October.", link="https://www.lokrum.hr/en/"),
    dict(date="Oct 18", mode="🚗", frm="Dubrovnik", to="Kravica → Počitelj → Mostar", time="3 h 33 min total", dist="180 km",
         note="Two border crossings (HR→BiH). Bring passports & car green card if self-driving.", link=gdir("Pile Gate, Dubrovnik", "Kravica Waterfall", "Počitelj", "Stari Most, Mostar")),
    dict(date="Oct 18", mode="🚗", frm="Mostar", to="Dubrovnik", time="2 h 39 min", dist="137 km",
         note="Blagaj adds ~20 min each way.", link=gdir("Stari Most, Mostar", "Pile Gate, Dubrovnik")),
    dict(date="Oct 19", mode="🚗", frm="Dubrovnik", to="Airport (DBV)", time="32 min", dist="22 km",
         note="Cavtat → airport only ~10 min.", link=gdir("Pile Gate, Dubrovnik", "Dubrovnik Airport")),
]

# ---------------------------------------------------------------- KML
ICON = {"stay": "1602", "hub": "1504", "culture": "1598", "nature": "1892", "adventure": "1596",
        "relax": "1521", "food": "1577", "alt": "1899"}

def kml():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Croatia + Herzegovina · Oct 9–19</name>']
    for li, (layer, color, pois) in enumerate(LAYERS):
        hexc = color.lstrip("#")
        kcol = "ff" + hexc[4:6] + hexc[2:4] + hexc[0:2]
        out.append(f'<Style id="s{li}"><IconStyle><color>{kcol}</color><scale>1.1</scale>'
                   f'<Icon><href>https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png</href></Icon></IconStyle></Style>')
        out.append(f"<Folder><name>{html.escape(layer)}</name>")
        for name, lat, lng, kind, note in pois:
            desc = f"[{kind}] {note}"
            out.append(f"<Placemark><name>{html.escape(name)}</name><description>{html.escape(desc)}</description>"
                       f"<styleUrl>#s{li}</styleUrl><Point><coordinates>{lng},{lat},0</coordinates></Point></Placemark>")
        out.append("</Folder>")
    out.append("</Document></kml>")
    return "\n".join(out)

# ---------------------------------------------------------------- HTML injection
def tripdata_js():
    def walk(km):
        m = max(1, round(km * 1.3 / 5 * 60))
        return f"{m} min walk" if m < 30 else f"{km:.1f} km"
    stays = []
    for s in STAYS:
        stays.append(dict(id=s["id"], title=s["title"], dates=s["dates"], nights=s["nights"], area=s["area"],
                          anchor=s["anchor"], verdict=s["verdict"], tip=s["tip"],
                          searches=[dict(label=l, url=u) for l, u in s["searches"]],
                          booking=[dict(name=h[0], score=h[1], price=h[2], tier=h[4], km=h[5], walk=walk(h[5]),
                                        note=h[6] if len(h) > 6 else "", url=bk(h[3], s["ci"], s["co"])) for h in s["booking"]],
                          airbnb=[dict(name=h[0], score=h[1], price=h[2], km=h[4], walk=walk(h[4]),
                                       note=h[5] if len(h) > 5 else "", url=ab(h[3], s["ci"], s["co"])) for h in s["airbnb"]]))
    layers = [dict(name=n, color=c, pois=[dict(name=a, lat=b, lng=d, kind=k, note=e) for a, b, d, k, e in p]) for n, c, p in LAYERS]
    data = dict(stays=stays, legs=LEGS, layers=layers)
    return "window.TRIP = " + json.dumps(data, ensure_ascii=False) + ";"

if __name__ == "__main__":
    (HERE / "croatia_trip.kml").write_text(kml(), encoding="utf-8")
    page = HERE / "index.html"
    src = page.read_text(encoding="utf-8")
    block = f"<script id=\"tripdata\">\n{tripdata_js()}\n</script>"
    src, n = re.subn(r'<script id="tripdata">.*?</script>', lambda _: block, src, flags=re.S)
    if n != 1:
        raise SystemExit("TRIPDATA marker not found in HTML")
    page.write_text(src, encoding="utf-8")
    print("wrote croatia_trip.kml and updated HTML;", sum(len(p) for _, _, p in LAYERS), "POIs,", len(STAYS), "stays,", len(LEGS), "legs")
