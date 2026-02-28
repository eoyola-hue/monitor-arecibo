#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reporte Meteorológico Diario — Arecibo, Puerto Rico
Ejecutado automáticamente por GitHub Actions cada mañana a las 6 AM AST
Fuente: NWS San Juan (weather.gov/sju)
"""

import urllib.request
import json
import os
from datetime import datetime, timedelta

# ── ReportLab ──
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Colores ──
NAVY   = colors.HexColor("#0a1628")
DEEP   = colors.HexColor("#0d1f3c")
OCEAN  = colors.HexColor("#0e3a6e")
CYAN   = colors.HexColor("#00b4d8")
TEAL   = colors.HexColor("#00e5d4")
DANGER = colors.HexColor("#e63946")
WARN   = colors.HexColor("#ff6b35")
GOLD   = colors.HexColor("#ffd166")
SAFE   = colors.HexColor("#06d6a0")
LIGHT  = colors.HexColor("#e8f4fd")
MUTED  = colors.HexColor("#7fa8cc")
WHITE  = colors.white

# ── Traducción NWS inglés → español ──
TRADUCCIONES = [
    ("Mostly Sunny", "Mayormente Soleado"),
    ("Partly Sunny", "Parcialmente Soleado"),
    ("Mostly Clear", "Mayormente Despejado"),
    ("Partly Cloudy", "Parcialmente Nublado"),
    ("Mostly Cloudy", "Mayormente Nublado"),
    ("Chance Showers", "Posibilidad de Aguaceros"),
    ("Chance Rain", "Posibilidad de Lluvia"),
    ("Chance Thunderstorms", "Posibilidad de Tormentas"),
    ("Showers", "Aguaceros"),
    ("Thunderstorms", "Tormentas Eléctricas"),
    ("Light Rain", "Lluvia Ligera"),
    ("Heavy Rain", "Lluvia Intensa"),
    ("Rain", "Lluvia"),
    ("Sunny", "Soleado"),
    ("Clear", "Despejado"),
    ("Cloudy", "Nublado"),
    ("Overcast", "Cubierto"),
    ("Fog", "Neblina"),
    ("Haze", "Bruma"),
    ("Windy", "Vientos Fuertes"),
    ("Breezy", "Ventoso"),
    ("Tropical Storm", "Tormenta Tropical"),
    ("Hurricane", "Huracán"),
    ("Likely", "Probable"),
]

def traducir(texto):
    if not texto:
        return ""
    for en, es in TRADUCCIONES:
        texto = texto.replace(en, es)
    return texto

# ── Utilidades ──
def fetch_json(url):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "AreciboWeatherMonitor/2.0 github-actions"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠ No se pudo obtener {url}: {e}")
        return None

def get_pr_time():
    return datetime.utcnow() + timedelta(hours=-4)  # AST = UTC-4

def sev_color(sev):
    return {"Extreme": DANGER, "Severe": WARN, "Moderate": GOLD, "Minor": SAFE}.get(sev, MUTED)

def sev_es(sev):
    return {"Extreme": "EXTREMO", "Severe": "SEVERO",
            "Moderate": "MODERADO", "Minor": "MENOR"}.get(sev, sev or "—")

def p_style(name, font="Helvetica", size=9, color=LIGHT, align=TA_LEFT, leading=13):
    return ParagraphStyle(name, fontName=font, fontSize=size,
                          textColor=color, alignment=align, leading=leading)

def P(text, style): return Paragraph(text, style)
def HR(color=OCEAN): return HRFlowable(width="100%", thickness=1,
                                        color=color, spaceAfter=5, spaceBefore=3)

def section_title(txt, color=CYAN):
    return P(f'<font size="11"><b>{txt.upper()}</b></font>',
             p_style("sec", "Helvetica-Bold", 11, color, leading=15))

def body(txt, color=LIGHT, size=9):
    return P(txt, p_style("body", size=size, color=color, leading=13))

def mono(txt, color=MUTED, size=8):
    return P(f'<font name="Courier" size="{size}">{txt}</font>',
             p_style("mono", "Courier", size, color, leading=12))

# ── Tabla base ──
BASE_TS = [
    ("BACKGROUND", (0,0), (-1,0), OCEAN),
    ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0), (-1,-1), 8),
    ("TEXTCOLOR",  (0,1), (-1,-1), LIGHT),
    ("BACKGROUND", (0,1), (-1,-1), NAVY),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [NAVY, DEEP]),
    ("GRID",       (0,0), (-1,-1), 0.4, OCEAN),
    ("TOPPADDING",    (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING",   (0,0), (-1,-1), 7),
    ("RIGHTPADDING",  (0,0), (-1,-1), 7),
]

# ════════════════════════════════════════
def main():
# ════════════════════════════════════════

    pr_now   = get_pr_time()
    date_str = pr_now.strftime("%A, %d de %B de %Y")
    time_str = pr_now.strftime("%I:%M %p AST")
    file_date = pr_now.strftime("%Y-%m-%d")

    print(f"📅 Generando reporte para: {date_str}")
    print(f"🕐 Hora PR: {time_str}")

    # ── Carpeta de salida ──
    os.makedirs("reports", exist_ok=True)
    OUTPUT = f"reports/Reporte_Meteorologico_Arecibo_{file_date}.pdf"
    LATEST = "reports/reporte_mas_reciente.pdf"

    # ── Obtener datos ──
    print("🌐 Descargando datos del NWS...")
    alerts_data   = fetch_json("https://api.weather.gov/alerts/active?area=PR&limit=25")
    point_data    = fetch_json("https://api.weather.gov/points/18.4736,-66.7220")
    forecast_data = None

    if point_data and "properties" in point_data:
        fc_url = point_data["properties"].get("forecast")
        if fc_url:
            forecast_data = fetch_json(fc_url)

    alerts  = (alerts_data or {}).get("features", [])
    periods = []
    if forecast_data and "properties" in forecast_data:
        periods = forecast_data["properties"].get("periods", [])

    flood_alerts  = [a for a in alerts if any(k in (a["properties"].get("event","") or "").lower()
                                               for k in ["flood","flash","inunda"])]
    marine_alerts = [a for a in alerts if any(k in (a["properties"].get("event","") or "").lower()
                                               for k in ["marine","small craft","surf","beach","rip"])]

    print(f"  ✓ Alertas totales: {len(alerts)}")
    print(f"  ✓ Alertas inundación: {len(flood_alerts)}")
    print(f"  ✓ Períodos pronóstico: {len(periods)}")

    # ── Documento ──
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
        topMargin=0.55*inch,  bottomMargin=0.65*inch,
        title=f"Reporte Meteorológico Arecibo — {date_str}",
        author="Monitor Meteorológico Arecibo / NWS San Juan"
    )
    story = []

    # ─────────────────────────────────────
    # ENCABEZADO
    # ─────────────────────────────────────
    hdr = Table([[
        P('<font color="#00b4d8" size="20"><b>MONITOR METEOROLÓGICO</b></font><br/>'
          '<font color="#7fa8cc" size="8">Arecibo, Puerto Rico  •  18.4736°N 66.7220°W  •  NWS San Juan</font>',
          p_style("h1", "Helvetica-Bold", 20, WHITE, TA_LEFT, 26)),
        P(f'<font color="#e8f4fd" size="10"><b>{date_str.upper()}</b></font><br/>'
          f'<font color="#7fa8cc" size="8">Generado: {time_str}</font><br/>'
          f'<font color="#7fa8cc" size="7">Reporte automático · GitHub Actions</font>',
          p_style("h2", "Helvetica", 10, LIGHT, TA_RIGHT, 14))
    ]], colWidths=[4.3*inch, 2.9*inch])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("LEFTPADDING",   (0,0), (0,0),   16),
        ("RIGHTPADDING",  (-1,-1), (-1,-1), 16),
        ("TOPPADDING",    (0,0), (-1,-1), 13),
        ("BOTTOMPADDING", (0,0), (-1,-1), 13),
        ("LINEBELOW",     (0,0), (-1,-1), 2, CYAN),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story += [hdr, Spacer(1, 12)]

    # ─────────────────────────────────────
    # RESUMEN EJECUTIVO (semáforo)
    # ─────────────────────────────────────
    story.append(section_title("📊  Resumen Ejecutivo", CYAN))
    story.append(HR(CYAN))

    # Calcular riesgo
    if flood_alerts and any(a["properties"].get("severity") == "Extreme" for a in flood_alerts):
        riesgo, r_color, r_icon = "EXTREMO", DANGER, "🔴"
    elif flood_alerts and any(a["properties"].get("severity") == "Severe" for a in flood_alerts):
        riesgo, r_color, r_icon = "ALTO", WARN, "🟠"
    elif flood_alerts:
        riesgo, r_color, r_icon = "MODERADO", GOLD, "🟡"
    elif alerts:
        riesgo, r_color, r_icon = "BAJO-MOD", CYAN, "🟡"
    else:
        riesgo, r_color, r_icon = "BAJO", SAFE, "🟢"

    today = next((p for p in periods if p.get("isDaytime")), None)
    lluvia_pct = (today or {}).get("probabilityOfPrecipitation", {})
    lluvia_val = lluvia_pct.get("value") if lluvia_pct else None
    lluvia_str = f"{lluvia_val}%" if lluvia_val is not None else "—"
    if lluvia_val and lluvia_val >= 80:   l_color, l_icon = DANGER, "🔴"
    elif lluvia_val and lluvia_val >= 60: l_color, l_icon = WARN,   "🟠"
    elif lluvia_val and lluvia_val >= 40: l_color, l_icon = GOLD,   "🟡"
    else:                                 l_color, l_icon = SAFE,   "🟢"

    resumen = [
        ["INDICADOR", "ESTADO", "VALOR"],
        [f"{r_icon}  Riesgo Inundación",    P(f"<b>{riesgo}</b>", p_style("rv","Helvetica-Bold",9,r_color)), f"{len(flood_alerts)} alerta(s)"],
        [f"{l_icon}  Prob. Lluvia Hoy",     P(f"<b>{lluvia_str}</b>", p_style("lv","Helvetica-Bold",9,l_color)), traducir(today.get("shortForecast","—") if today else "—")[:40]],
        ["🌊  Alertas Marinas",             P(f"<b>{'AVISO VIGENTE' if marine_alerts else 'SIN ALERTA'}</b>", p_style("mv","Helvetica-Bold",9,WARN if marine_alerts else SAFE)), f"{len(marine_alerts)} alerta(s)"],
        ["⚠️  Total Alertas PR",            P(f"<b>{len(alerts)}</b>", p_style("av","Helvetica-Bold",9,DANGER if alerts else SAFE)), "weather.gov/sju"],
    ]
    rt = Table(resumen, colWidths=[2.4*inch, 2.0*inch, 2.8*inch], repeatRows=1)
    rt.setStyle(TableStyle(BASE_TS + [
        ("TEXTCOLOR", (0,0), (-1,0), CYAN),
        ("FONTNAME",  (0,1), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,1), (0,-1), MUTED),
    ]))
    story += [rt, Spacer(1, 12)]

    # ─────────────────────────────────────
    # ALERTAS ACTIVAS
    # ─────────────────────────────────────
    story.append(section_title("⚠  Alertas Activas — Puerto Rico", DANGER if alerts else SAFE))
    story.append(HR(DANGER if alerts else SAFE))

    if not alerts:
        story.append(body("✅  Sin alertas activas en este momento para Puerto Rico.", SAFE))
    else:
        a_rows = [["EVENTO", "SEVERIDAD", "ÁREA", "EXPIRA"]]
        for a in alerts[:14]:
            p = a["properties"]
            sev  = sev_es(p.get("severity",""))
            area = (p.get("areaDesc","") or "").split(";")[0][:32]
            ev   = (p.get("event","") or "")[:38]
            exp  = "—"
            if p.get("expires"):
                try:
                    ed = datetime.strptime(p["expires"][:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=-4)
                    exp = ed.strftime("%d/%m %I:%M %p")
                except:
                    exp = p["expires"][:10]
            a_rows.append([ev, sev, area, exp])

        at = Table(a_rows, colWidths=[2.7*inch, 0.85*inch, 2.1*inch, 1.05*inch], repeatRows=1)
        ts = list(BASE_TS) + [("TEXTCOLOR",(0,0),(-1,0), DANGER)]
        # Color severidad
        for i, a in enumerate(alerts[:14]):
            col = sev_color(a["properties"].get("severity",""))
            ts.append(("TEXTCOLOR", (1,i+1), (1,i+1), col))
            ts.append(("FONTNAME",  (1,i+1), (1,i+1), "Helvetica-Bold"))
        at.setStyle(TableStyle(ts))
        story.append(at)

        # Detalle de alertas críticas
        criticas = [a for a in alerts if a["properties"].get("severity") in ["Extreme","Severe"]]
        if criticas:
            story += [Spacer(1,8), body("<b>DETALLE — ALERTAS CRÍTICAS:</b>", DANGER, 9)]
            for a in criticas[:4]:
                p2 = a["properties"]
                story.append(body(f"<b>► {p2.get('event','')}</b> — {sev_es(p2.get('severity',''))}", sev_color(p2.get("severity","")), 9))
                desc = p2.get("description","") or p2.get("headline","") or ""
                story.append(mono(desc[:400] + ("..." if len(desc)>400 else ""), MUTED, 7.5))
                story.append(Spacer(1,4))

    story.append(Spacer(1, 10))

    # ─────────────────────────────────────
    # INUNDACIONES Y RÍOS
    # ─────────────────────────────────────
    story.append(section_title("🌊  Inundaciones y Ríos — Área Arecibo", CYAN))
    story.append(HR(CYAN))

    flood_rows = [
        ["ESTACIÓN / INDICADOR",    "CÓDIGO",  "ESTADO",                   "ENLACE"],
        ["Río Arecibo",             "AREP4",   "Verificar AHPS",            "water.weather.gov"],
        ["Río Grande de Arecibo",   "GRAP4",   "Verificar AHPS",            "water.weather.gov"],
        ["Río Camuy",               "CMAP4",   "Verificar AHPS",            "water.weather.gov"],
        ["Río Manatí",              "MNTP4",   "Verificar AHPS",            "water.weather.gov"],
        ["USGS Flujo Tiempo Real",  "50029000","Verificar en vivo",         "waterdata.usgs.gov"],
        ["Alertas Flash Flood PR",  "—",       f"{len(flood_alerts)} activa(s)", "api.weather.gov"],
    ]
    flt = Table(flood_rows, colWidths=[2.3*inch, 0.85*inch, 1.65*inch, 1.9*inch], repeatRows=1)
    ts2 = list(BASE_TS) + [
        ("TEXTCOLOR", (0,0), (-1,0), TEAL),
        ("FONTNAME",  (0,1), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,1), (0,-1), MUTED),
        ("TEXTCOLOR", (3,1), (3,-1), CYAN),
    ]
    if flood_alerts:
        ts2.append(("TEXTCOLOR", (2,-1), (2,-1), DANGER))
        ts2.append(("FONTNAME",  (2,-1), (2,-1), "Helvetica-Bold"))
    flt.setStyle(TableStyle(ts2))
    story += [flt, Spacer(1, 10)]

    # ─────────────────────────────────────
    # PRONÓSTICO 7 DÍAS
    # ─────────────────────────────────────
    story.append(section_title("📅  Pronóstico 7 Días — Arecibo, PR", CYAN))
    story.append(HR(CYAN))

    if periods:
        day_p = [p for p in periods if p.get("isDaytime")][:7]
        fc_rows = [["DÍA", "TEMP", "LLUVIA", "CONDICIÓN"]]
        for p in day_p:
            try:
                d = datetime.fromisoformat(p["startTime"][:10])
                # Día en español
                dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
                day_name = f"{dias[d.weekday()]} {d.strftime('%d/%m')}"
            except:
                day_name = p.get("name","—")
            temp  = f"{p.get('temperature','—')}°{p.get('temperatureUnit','F')}"
            prob  = (p.get("probabilityOfPrecipitation") or {}).get("value")
            rain  = f"{prob}%" if prob is not None else "—"
            short = traducir(p.get("shortForecast","—") or "—")[:45]
            fc_rows.append([day_name, temp, rain, short])

        fct = Table(fc_rows, colWidths=[0.95*inch, 0.7*inch, 0.75*inch, 4.35*inch], repeatRows=1)
        fcts = list(BASE_TS) + [("TEXTCOLOR",(0,0),(-1,0), CYAN)]
        for i, p in enumerate(day_p):
            prob = (p.get("probabilityOfPrecipitation") or {}).get("value") or 0
            col  = DANGER if prob>=80 else WARN if prob>=60 else GOLD if prob>=40 else SAFE
            fcts += [("TEXTCOLOR",(2,i+1),(2,i+1),col), ("FONTNAME",(2,i+1),(2,i+1),"Helvetica-Bold")]
        fct.setStyle(TableStyle(fcts))
        story.append(fct)

        # Detalle hoy
        if today:
            story += [Spacer(1,6), body("<b>DETALLE HOY:</b>", MUTED, 8)]
            story.append(mono(traducir(today.get("detailedForecast","") or "")[:300], LIGHT, 8))
    else:
        story.append(body("⚠ No se pudo obtener pronóstico. Consulte: forecast.weather.gov", WARN))

    story.append(Spacer(1, 10))

    # ─────────────────────────────────────
    # CONDICIONES MARÍTIMAS
    # ─────────────────────────────────────
    story.append(section_title("⛵  Condiciones Marítimas — Costa Norte PR", WARN))
    story.append(HR(WARN))

    marine_rows = [
        ["PARÁMETRO",              "CONDICIÓN",                         "NIVEL"],
        ["Oleaje Costa Norte",     "9-10 pies",                         "PELIGROSO"],
        ["Vientos Alisios",        "E 10-20 kt, ráfagas hasta 30 kt",  "AVISO VIGENTE"],
        ["Período del oleaje",     "8-10 segundos",                     "MODERADO-ALTO"],
        ["Corrientes marinas",     "Peligrosas (rip currents)",         "PELIGROSO"],
        ["Natación en playas",     "NO RECOMENDADO",                    "PELIGROSO"],
        ["Embarcaciones pequeñas", "Small Craft Advisory vigente",      "RESTRINGIDA"],
    ]
    mt = Table(marine_rows, colWidths=[2.1*inch, 2.9*inch, 1.75*inch], repeatRows=1)
    mts = list(BASE_TS) + [
        ("TEXTCOLOR", (0,0), (-1,0), WARN),
        ("FONTNAME",  (0,1), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,1), (0,-1), MUTED),
        ("TEXTCOLOR", (2,1), (2,-1), DANGER),
        ("FONTNAME",  (2,1), (2,-1), "Helvetica-Bold"),
    ]
    mt.setStyle(TableStyle(mts))
    story += [mt, Spacer(1, 10)]

    # ─────────────────────────────────────
    # CONTACTOS DE EMERGENCIA
    # ─────────────────────────────────────
    story.append(section_title("📞  Contactos de Emergencia y Recursos", GOLD))
    story.append(HR(GOLD))

    contacts = [
        ["RECURSO",                         "CONTACTO / URL"],
        ["🆘 Emergencias Puerto Rico",       "9-1-1"],
        ["🌀 NWS San Juan",                  "(787) 253-4586  |  weather.gov/sju"],
        ["🚒 SCEM Puerto Rico",              "(787) 724-0124  |  spcpr.pr.gov"],
        ["🛣️ DTOP — Carreteras",             "(787) 723-3600  |  dtop.pr.gov"],
        ["🏥 Cruz Roja PR",                  "(787) 759-7979"],
        ["📊 Río Arecibo (AREP4) en vivo",   "water.weather.gov/ahps2/hydrograph.php?gage=AREP4"],
        ["📈 USGS Ríos Puerto Rico",         "waterdata.usgs.gov/pr/nwis/rt"],
        ["🌀 NHC — Ciclones Tropicales",     "nhc.noaa.gov"],
        ["📡 Radar NWS TJUA",                "radar.weather.gov/station/TJUA/standard"],
    ]
    ct = Table(contacts, colWidths=[2.4*inch, 4.35*inch], repeatRows=1)
    cts = list(BASE_TS) + [
        ("TEXTCOLOR", (0,0), (-1,0), GOLD),
        ("FONTNAME",  (0,1), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,1), (0,-1), MUTED),
        ("TEXTCOLOR", (1,1), (1,-1), CYAN),
    ]
    ct.setStyle(TableStyle(cts))
    story += [ct, Spacer(1, 14)]

    # ─────────────────────────────────────
    # PIE DE PÁGINA
    # ─────────────────────────────────────
    pie = Table([[
        P('<font color="#7fa8cc" size="7">'
          'Reporte generado automáticamente por GitHub Actions a las 6:00 AM AST. '
          'Siempre consulte weather.gov/sju para decisiones críticas de seguridad. '
          'Este reporte no reemplaza las alertas oficiales del Servicio Nacional de Meteorología.'
          '</font>',
          p_style("ft","Helvetica",7,MUTED,TA_CENTER,10))
    ]], colWidths=[7.1*inch])
    pie.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#060e1c")),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LINEABOVE",     (0,0),(-1,0), 1, OCEAN),
    ]))
    story.append(pie)

    # ── Construir PDF ──
    doc.build(story)
    print(f"✅ PDF generado: {OUTPUT}")

    # Copiar como "más reciente"
    import shutil
    shutil.copy2(OUTPUT, LATEST)
    print(f"✅ Copiado como: {LATEST}")

    # ── Crear index.json para el dashboard ──
    info = {
        "fecha": date_str,
        "hora": time_str,
        "archivo": f"Reporte_Meteorologico_Arecibo_{file_date}.pdf",
        "alertas_total": len(alerts),
        "alertas_inundacion": len(flood_alerts),
        "alertas_marinas": len(marine_alerts),
        "lluvia_hoy_pct": lluvia_val,
        "riesgo": riesgo,
        "generado_utc": datetime.utcnow().isoformat()
    }
    with open("reports/reporte_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON de info generado: reports/reporte_info.json")

if __name__ == "__main__":
    main()
