import json, os, urllib.parse as up, urllib.request

PLACES = {"성북구": (37.5894, 127.0167), "강남구": (37.5172, 127.0473)}
OFFSET = 0  # 케바케 보정: 추위 많이 타면 +2~3, 더위 많이 타면 -2~3 (체감온도에 더해 구간 판정)

# (체감온도 하한, 옷차림)
TABLE = [(28, "민소매·반팔·반바지"), (23, "반팔·얇은 셔츠"), (20, "얇은 가디건·긴팔"),
         (17, "맨투맨·가디건·청바지"), (12, "자켓·야상·니트"), (9, "트렌치코트·가죽자켓·니트"),
         (5, "코트·히트텍·니트"), (-99, "패딩·두꺼운 코트·목도리")]

def outfit(t):
    return next(o for lo, o in TABLE if t + OFFSET >= lo)

def fetch(lat, lon):
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&timezone=Asia%%2FSeoul&forecast_days=1"
           "&daily=temperature_2m_min,temperature_2m_max,apparent_temperature_min,apparent_temperature_max,precipitation_probability_max")
    return json.load(urllib.request.urlopen(url % (lat, lon)))["daily"]

def line(name, d):
    mn, mx = d["temperature_2m_min"][0], d["temperature_2m_max"][0]
    amn, amx = d["apparent_temperature_min"][0], d["apparent_temperature_max"][0]
    rain = d["precipitation_probability_max"][0] or 0
    s = f"**{name}** {mn:.0f}~{mx:.0f}℃ (체감 {amn:.0f}~{amx:.0f}℃)\n👕 {outfit((amn + amx) / 2)}"
    if mx - mn >= 10: s += f"\n🧥 일교차 {mx - mn:.0f}℃ — 아침엔 {outfit(amn)}, 낮엔 {outfit(amx)}"
    if rain >= 50: s += f"\n☂️ 강수확률 {rain}% — 우산"
    return s

def links(d):
    t = round((d["apparent_temperature_min"][0] + d["apparent_temperature_max"][0]) / 2)
    q = up.quote(f"{t}도 코디")
    return (f"🔎 {t}도 코디 참고: <https://www.pinterest.com/search/pins/?q={q}> · "
            f"<https://www.youtube.com/results?search_query={q}> · <https://www.instagram.com/explore/tags/{up.quote(f'{t}도코디')}/>")

if __name__ == "__main__":
    assert outfit(30) == "민소매·반팔·반바지" and outfit(-3).startswith("패딩")
    data = {n: fetch(*c) for n, c in PLACES.items()}
    msg = "\n\n".join(line(n, d) for n, d in data.items()) + "\n\n" + links(next(iter(data.values())))
    hook = os.environ.get("DISCORD_WEBHOOK")
    if not hook: print(msg)
    else:
        req = urllib.request.Request(hook, json.dumps({"content": "☀️ 오늘의 날씨·옷차림\n\n" + msg}).encode(),
                                     {"Content-Type": "application/json", "User-Agent": "outfit-bot"})
        urllib.request.urlopen(req)
