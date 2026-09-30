# Croatia + Herzegovina trip · Oct 9–19

Shareable itinerary site (GitHub Pages).

- `index.html` — trip deck: route, day-by-day plan, interactive map, travel times, stays with walk times, logistics.
- `activities.html` — per-day activity explorer with photos (Wikimedia Commons), Google ratings and paraphrased review themes.
- `croatia_trip.kml` — all pins, importable into Google My Maps.

Regenerate after editing data:

```sh
python3 trip_data.py        # map pins, stays, travel legs -> index.html + KML
python3 build_activities.py # activities_data.py + data/*.json -> activities.html
```

Prices and ratings were collected Sept 30 2026 and are approximate.
