from __future__ import annotations

from collections.abc import Iterable

from app.services.clinical_consistency import build_validated_findings


def generate_lifestyle_recommendations(
    payload: dict[str, object],
    *,
    language: str = "en",
    risk_status: dict[str, object] | None = None,
) -> str | None:
    findings = build_validated_findings(payload=payload, abnormal_markers=[])
    normalized_markers = findings.normalized_markers
    abnormal_markers = [marker for marker in normalized_markers if marker.status in {"low", "high"} and marker.value is not None]

    if not normalized_markers:
        return None

    marker_map = {marker.name: marker for marker in normalized_markers}
    messages = _messages(language)

    vitamin_d = _first_marker(marker_map, "Vitamin D (25-OH)", "Витамин D (25-OH)")
    zinc = _first_marker(marker_map, "Zinc", "Цинк")
    hemoglobin = _first_marker(marker_map, "Hemoglobin", "Гемоглобин")
    rbc = _first_marker(marker_map, "RBC", "Эритроциты")
    hematocrit = _first_marker(marker_map, "Hematocrit", "Гематокрит")
    mcv = marker_map.get("MCV")

    has_macrocytic_pattern = "macrocytic_anemia" in findings.detected_patterns or (
        hemoglobin is not None
        and hemoglobin.status == "low"
        and mcv is not None
        and mcv.status == "high"
    )
    has_low_hemoglobin = hemoglobin is not None and hemoglobin.status == "low"
    has_low_vitamin_d = vitamin_d is not None and vitamin_d.status == "low"
    has_low_zinc = zinc is not None and zinc.status == "low"
    is_significant = _is_significant(risk_status, findings.severity)

    sections: list[str] = []

    if not abnormal_markers:
        sections.extend(
            [
                _section(
                    messages["heading_now"],
                    messages["normal_now"],
                ),
                _section(
                    messages["heading_activity"],
                    messages["normal_activity"],
                ),
                _section(
                    messages["heading_recovery"],
                    messages["normal_recovery"],
                ),
            ]
        )
        return "\n\n".join(section for section in sections if section)

    sections.append(
        _section(
            messages["heading_now"],
            _what_matters_now(
                messages=messages,
                vitamin_d=vitamin_d,
                zinc=zinc,
                hemoglobin=hemoglobin,
                rbc=rbc,
                hematocrit=hematocrit,
                mcv=mcv,
                has_macrocytic_pattern=has_macrocytic_pattern,
                is_significant=is_significant,
                abnormal_markers=abnormal_markers,
            ),
        )
    )

    nutrition_lines = _nutrition_lines(
        messages=messages,
        vitamin_d=vitamin_d,
        zinc=zinc,
        has_macrocytic_pattern=has_macrocytic_pattern,
    )
    if nutrition_lines:
        sections.append(_section(messages["heading_nutrition"], nutrition_lines))

    activity_lines = _activity_lines(
        messages=messages,
        has_macrocytic_pattern=has_macrocytic_pattern,
        has_low_hemoglobin=has_low_hemoglobin,
        is_significant=is_significant,
    )
    if activity_lines:
        sections.append(_section(messages["heading_activity"], activity_lines))

    recovery_lines = _recovery_lines(
        messages=messages,
        has_macrocytic_pattern=has_macrocytic_pattern,
        has_low_hemoglobin=has_low_hemoglobin,
        has_low_vitamin_d=has_low_vitamin_d,
        has_low_zinc=has_low_zinc,
    )
    if recovery_lines:
        sections.append(_section(messages["heading_recovery"], recovery_lines))

    sections.append(
        _section(
            messages["heading_clinician"],
            _clinician_lines(
                messages=messages,
                has_macrocytic_pattern=has_macrocytic_pattern,
                has_low_hemoglobin=has_low_hemoglobin,
                has_low_vitamin_d=has_low_vitamin_d,
                has_low_zinc=has_low_zinc,
                is_significant=is_significant,
            ),
        )
    )

    return "\n\n".join(section for section in sections if section)


def _what_matters_now(
    *,
    messages: dict[str, str],
    vitamin_d,
    zinc,
    hemoglobin,
    rbc,
    hematocrit,
    mcv,
    has_macrocytic_pattern: bool,
    is_significant: bool,
    abnormal_markers: list[object],
) -> str:
    if has_macrocytic_pattern:
        return messages["now_macrocytic"].format(
            hemoglobin=_marker_phrase(hemoglobin, messages["label_hemoglobin"]),
            rbc=_marker_phrase(rbc, messages["label_rbc"]),
            hematocrit=_marker_phrase(hematocrit, messages["label_hematocrit"]),
            mcv=_marker_phrase(mcv, messages["label_mcv"]),
        )
    if vitamin_d is not None and vitamin_d.status == "low" and zinc is not None and zinc.status == "low":
        return messages["now_vitamin_d_zinc"].format(
            vitamin_d=_marker_phrase(vitamin_d, messages["label_vitamin_d"]),
            zinc=_marker_phrase(zinc, messages["label_zinc"]),
        )
    if vitamin_d is not None and vitamin_d.status == "low":
        return messages["now_vitamin_d"].format(
            vitamin_d=_marker_phrase(vitamin_d, messages["label_vitamin_d"]),
        )
    if zinc is not None and zinc.status == "low":
        return messages["now_zinc"].format(
            zinc=_marker_phrase(zinc, messages["label_zinc"]),
        )

    marker_summary = ", ".join(marker.name for marker in abnormal_markers[:3])
    key = "now_generic_significant" if is_significant else "now_generic"
    return messages[key].format(marker_summary=marker_summary)


def _nutrition_lines(
    *,
    messages: dict[str, str],
    vitamin_d,
    zinc,
    has_macrocytic_pattern: bool,
) -> str | None:
    lines: list[str] = []
    if has_macrocytic_pattern:
        lines.append(messages["nutrition_macrocytic"])
    if vitamin_d is not None and vitamin_d.status == "low":
        lines.append(messages["nutrition_vitamin_d"])
    if zinc is not None and zinc.status == "low":
        lines.append(messages["nutrition_zinc"])
    return _join_lines(lines)


def _activity_lines(
    *,
    messages: dict[str, str],
    has_macrocytic_pattern: bool,
    has_low_hemoglobin: bool,
    is_significant: bool,
) -> str:
    if has_macrocytic_pattern or (has_low_hemoglobin and is_significant):
        return messages["activity_macrocytic"]
    if has_low_hemoglobin:
        return messages["activity_low_hemoglobin"]
    return messages["activity_mild"]


def _recovery_lines(
    *,
    messages: dict[str, str],
    has_macrocytic_pattern: bool,
    has_low_hemoglobin: bool,
    has_low_vitamin_d: bool,
    has_low_zinc: bool,
) -> str | None:
    lines: list[str] = []
    if has_macrocytic_pattern or has_low_hemoglobin:
        lines.append(messages["recovery_blood"])
    if has_low_vitamin_d or has_low_zinc:
        lines.append(messages["recovery_deficiency"])
    return _join_lines(lines)


def _clinician_lines(
    *,
    messages: dict[str, str],
    has_macrocytic_pattern: bool,
    has_low_hemoglobin: bool,
    has_low_vitamin_d: bool,
    has_low_zinc: bool,
    is_significant: bool,
) -> str:
    lines: list[str] = []
    if has_macrocytic_pattern:
        lines.append(messages["clinician_macrocytic"])
    elif has_low_hemoglobin:
        lines.append(messages["clinician_low_hemoglobin"])

    if has_low_vitamin_d and has_low_zinc:
        lines.append(messages["clinician_vitamin_d_zinc"])
    elif has_low_vitamin_d:
        lines.append(messages["clinician_vitamin_d"])
    elif has_low_zinc:
        lines.append(messages["clinician_zinc"])

    if not lines:
        lines.append(messages["clinician_generic"])

    lines.append(messages["clinician_significant"] if is_significant else messages["clinician_standard"])
    return _join_lines(lines) or messages["clinician_standard"]


def _section(title: str, body: str | None) -> str:
    cleaned = (body or "").strip()
    if not cleaned:
        return ""
    return f"{title}\n{cleaned}"


def _join_lines(lines: Iterable[str]) -> str | None:
    cleaned = [line.strip() for line in lines if line and line.strip()]
    if not cleaned:
        return None
    deduped: list[str] = []
    for line in cleaned:
        if line not in deduped:
            deduped.append(line)
    return " ".join(deduped)


def _marker_phrase(marker, label: str) -> str:
    if marker is None or marker.value is None:
        return label
    return f"{label} {_format_value(marker.value)}"


def _first_marker(marker_map: dict[str, object], *names: str):
    for name in names:
        marker = marker_map.get(name)
        if marker is not None:
            return marker
    return None


def _format_value(value: float | None) -> str:
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _is_significant(risk_status: dict[str, object] | None, severity: str) -> bool:
    color_key = str((risk_status or {}).get("color_key", "")).lower()
    return color_key == "red" or severity in {"SIGNIFICANT", "CRITICAL"}


def _messages(language: str) -> dict[str, str]:
    messages = {
        "en": {
            "heading_now": "What matters now",
            "heading_nutrition": "Nutrition",
            "heading_activity": "Physical activity",
            "heading_recovery": "Sleep and recovery",
            "heading_clinician": "What to discuss with a clinician",
            "label_vitamin_d": "vitamin D",
            "label_zinc": "zinc",
            "label_hemoglobin": "hemoglobin",
            "label_rbc": "RBC",
            "label_hematocrit": "hematocrit",
            "label_mcv": "MCV",
            "normal_now": "No confirmed out-of-range markers were identified in this report. The current pattern looks steady, so the main focus is on keeping consistent habits rather than making major changes.",
            "normal_activity": "Regular walking, light strength work, and usual day-to-day movement are reasonable if they already feel comfortable.",
            "normal_recovery": "Consistent sleep, hydration, and meals are enough here. Routine follow-up can stay guided by your usual clinician care and any future trend changes.",
            "now_macrocytic": "The confirmed pattern shows {hemoglobin}, {rbc}, and {hematocrit} below range together with {mcv} above range. That combination can fit a macrocytic anemia pattern, so lifestyle steps should stay supportive while clinician review takes priority.",
            "now_vitamin_d_zinc": "The confirmed deviations are mild and centered on {vitamin_d} and {zinc} below range. This is usually a good place for steady habit support rather than drastic changes.",
            "now_vitamin_d": "The confirmed deviation is {vitamin_d} below range. This is usually a calm, non-urgent pattern where daily habits may support correction alongside routine follow-up.",
            "now_zinc": "The confirmed deviation is {zinc} below range. A practical, food-first approach is usually more useful here than making aggressive changes.",
            "now_generic": "There are confirmed deviations in {marker_summary}. The most useful approach is to keep recommendations practical and supportive without overriding the main interpretation.",
            "now_generic_significant": "There are confirmed clinically important deviations in {marker_summary}. Lifestyle steps can still support recovery, but they should stay secondary to timely clinical review.",
            "nutrition_macrocytic": "Regular meals with protein and foods that naturally provide vitamin B12 and folate, such as fish, eggs, dairy, legumes, and leafy greens, may support recovery while the cause is being clarified.",
            "nutrition_vitamin_d": "Daylight exposure and foods such as oily fish, eggs, and fortified dairy or plant alternatives may support vitamin D status over time.",
            "nutrition_zinc": "Foods such as meat, shellfish, legumes, dairy, nuts, and seeds may help support zinc intake without moving straight to high-dose supplements.",
            "activity_macrocytic": "Until this pattern is reviewed, it is better to avoid intense exercise. Gentle walking and low-strain daily movement are more appropriate if they feel manageable.",
            "activity_low_hemoglobin": "For now, lighter movement is more appropriate than intense training, with activity guided by comfort until the blood count pattern is reviewed.",
            "activity_mild": "Light regular movement is reasonable here. Walking, mobility work, and moderate routine exercise are enough without trying to force a correction through training.",
            "recovery_blood": "Consistent sleep, hydration, and a less overloaded schedule may help support recovery while the blood-count pattern is being followed up.",
            "recovery_deficiency": "A steady routine matters more than short bursts of effort here. Regular meals, sleep, and time outdoors may support gradual correction.",
            "clinician_macrocytic": "Consider discussing repeat CBC testing and vitamin B12 and folate testing, rather than starting treatment on your own.",
            "clinician_low_hemoglobin": "Consider discussing repeat blood counts and whether cause-directed follow-up testing makes sense from the rest of your clinical picture.",
            "clinician_vitamin_d": "It may be useful to discuss repeat vitamin D testing and whether supplementation is appropriate for you.",
            "clinician_zinc": "It may be useful to discuss whether repeat zinc testing is needed before making major supplement changes.",
            "clinician_vitamin_d_zinc": "It may be useful to discuss repeat vitamin D and zinc testing after correction, and whether supplementation should be individualized rather than self-directed.",
            "clinician_generic": "Consider discussing whether repeat testing or a focused review of the abnormal markers would be useful in context.",
            "clinician_significant": "Because the report suggests a clinically important deviation, clinician guidance should lead the next step.",
            "clinician_standard": "These suggestions are supportive only and should stay alongside the main report, not replace clinician advice.",
        },
        "ru": {
            "heading_now": "Что важно сейчас",
            "heading_nutrition": "Питание",
            "heading_activity": "Активность",
            "heading_recovery": "Сон и восстановление",
            "heading_clinician": "Что обсудить с врачом",
            "label_vitamin_d": "витамин D",
            "label_zinc": "цинк",
            "label_hemoglobin": "гемоглобин",
            "label_rbc": "эритроциты",
            "label_hematocrit": "гематокрит",
            "label_mcv": "MCV",
            "normal_now": "Подтверждённых отклонений от референсного диапазона в этом отчёте не видно. Картина выглядит спокойной, поэтому сейчас важнее сохранять устойчивые привычки, а не резко что-то менять.",
            "normal_activity": "Подходят обычная ходьба, лёгкие силовые нагрузки и привычная повседневная активность, если они переносятся комфортно.",
            "normal_recovery": "Достаточно стабильного сна, гидратации и регулярного питания. Дальнейший контроль можно оставлять в рамках обычного наблюдения и оценки динамики со временем.",
            "now_macrocytic": "Подтверждённая картина показывает, что {hemoglobin}, {rbc} и {hematocrit} ниже диапазона, а {mcv} выше него. Такое сочетание может соответствовать макроцитарному анемическому паттерну, поэтому рекомендации по образу жизни здесь должны оставаться только поддерживающими, а приоритетом остаётся очная оценка.",
            "now_vitamin_d_zinc": "Подтверждённые отклонения выглядят умеренными и касаются {vitamin_d} и {zinc} ниже диапазона. В такой ситуации обычно важнее спокойная коррекция повседневных привычек, а не резкие меры.",
            "now_vitamin_d": "Подтверждённое отклонение касается {vitamin_d} ниже диапазона. Обычно это спокойная, неэкстренная ситуация, где повседневные привычки могут поддержать коррекцию вместе с плановым наблюдением.",
            "now_zinc": "Подтверждённое отклонение касается {zinc} ниже диапазона. Здесь обычно полезнее практичный пищевой подход, чем агрессивные изменения.",
            "now_generic": "Есть подтверждённые отклонения по показателям {marker_summary}. Наиболее разумно оставить рекомендации практичными и поддерживающими, не подменяя ими основную интерпретацию.",
            "now_generic_significant": "Есть подтверждённые клинически значимые отклонения по показателям {marker_summary}. Образ жизни может поддерживать восстановление, но должен оставаться вторичным по отношению к своевременной клинической оценке.",
            "nutrition_macrocytic": "Может быть полезно делать упор на регулярное питание с источниками белка и продуктами, которые естественно содержат витамин B12 и фолаты: рыбой, яйцами, молочными продуктами, бобовыми и листовой зеленью.",
            "nutrition_vitamin_d": "Поддержать уровень витамина D со временем могут дневной свет и продукты вроде жирной рыбы, яиц и обогащённых молочных или растительных альтернатив.",
            "nutrition_zinc": "Поддержать поступление цинка могут мясо, морепродукты, бобовые, молочные продукты, орехи и семена, без перехода сразу к высоким дозам добавок.",
            "activity_macrocytic": "До врачебной оценки лучше избегать интенсивных нагрузок. Более уместны спокойная ходьба и щадящая повседневная активность, если они переносятся нормально.",
            "activity_low_hemoglobin": "Пока картина крови не уточнена, разумнее оставить активность более лёгкой и не пытаться компенсировать состояние интенсивными тренировками.",
            "activity_mild": "Лёгкая регулярная активность здесь уместна. Ходьба, мягкая мобильность и умеренные привычные нагрузки обычно достаточны без попытки «исправить» анализ тренировками.",
            "recovery_blood": "Стабильный сон, достаточная гидратация и менее перегруженный режим могут поддержать восстановление, пока показатели крови дооцениваются.",
            "recovery_deficiency": "Здесь обычно важнее ровный режим, чем короткие периоды чрезмерных усилий. Регулярное питание, сон и время на улице могут поддержать постепенную коррекцию.",
            "clinician_macrocytic": "Можно обсудить повторный общий анализ крови, а также проверку витамина B12 и фолатов, не начиная самостоятельное лечение.",
            "clinician_low_hemoglobin": "Можно обсудить повторный контроль показателей крови и то, имеет ли смысл дообследование по предполагаемой причине с учётом общей клинической картины.",
            "clinician_vitamin_d": "Имеет смысл обсудить повторный контроль витамина D и необходимость добавок именно в вашем случае.",
            "clinician_zinc": "Имеет смысл обсудить, нужен ли повторный анализ цинка до существенных изменений в добавках.",
            "clinician_vitamin_d_zinc": "Можно обсудить повторный контроль витамина D и цинка после коррекции, а также то, стоит ли подбирать добавки индивидуально, а не самостоятельно.",
            "clinician_generic": "Можно обсудить, нужны ли повторные анализы или более прицельный разбор отклонённых показателей в вашем контексте.",
            "clinician_significant": "Если отклонение уже выглядит клинически значимым, следующий шаг лучше строить вокруг рекомендаций врача.",
            "clinician_standard": "Эти рекомендации носят только поддерживающий характер и должны оставаться дополнением к основному отчёту, а не заменой консультации врача.",
        },
        "es": {
            "heading_now": "Qué importa ahora",
            "heading_nutrition": "Nutrición",
            "heading_activity": "Actividad física",
            "heading_recovery": "Sueño y recuperación",
            "heading_clinician": "Qué comentar con un profesional",
            "label_vitamin_d": "vitamina D",
            "label_zinc": "zinc",
            "label_hemoglobin": "hemoglobina",
            "label_rbc": "eritrocitos",
            "label_hematocrit": "hematocrito",
            "label_mcv": "VCM",
            "normal_now": "No se ven desviaciones confirmadas fuera de rango en este informe. El patrón general luce estable, así que ahora lo importante es sostener buenos hábitos, no hacer cambios bruscos.",
            "normal_activity": "La caminata regular, algo de fuerza ligera y la actividad cotidiana habitual son razonables si ya se sienten bien toleradas.",
            "normal_recovery": "Aquí basta con sueño consistente, buena hidratación y comidas regulares. El seguimiento puede mantenerse dentro del control habitual y de la evolución con el tiempo.",
            "now_macrocytic": "El patrón confirmado muestra {hemoglobin}, {rbc} y {hematocrit} por debajo del rango junto con {mcv} por encima. Esa combinación puede encajar con un patrón de anemia macrocítica, por lo que las medidas de estilo de vida deben quedarse en un plano de apoyo mientras la valoración clínica toma prioridad.",
            "now_vitamin_d_zinc": "Las desviaciones confirmadas parecen leves y se concentran en {vitamin_d} y {zinc} por debajo del rango. En este contexto suele ser más útil una corrección tranquila de hábitos que medidas drásticas.",
            "now_vitamin_d": "La desviación confirmada corresponde a {vitamin_d} por debajo del rango. Suele ser un patrón tranquilo y no urgente, donde los hábitos diarios pueden apoyar la corrección junto con un seguimiento habitual.",
            "now_zinc": "La desviación confirmada corresponde a {zinc} por debajo del rango. Aquí suele ser más útil un enfoque práctico basado en la alimentación que cambios agresivos.",
            "now_generic": "Hay desviaciones confirmadas en {marker_summary}. Lo más útil es mantener estas recomendaciones como apoyo práctico, sin competir con la interpretación principal.",
            "now_generic_significant": "Hay desviaciones confirmadas clínicamente importantes en {marker_summary}. El estilo de vida puede apoyar la recuperación, pero debe quedar en segundo plano frente a una valoración clínica oportuna.",
            "nutrition_macrocytic": "Puede ayudar priorizar comidas regulares con proteína y alimentos que aporten de forma natural vitamina B12 y folato, como pescado, huevos, lácteos, legumbres y verduras de hoja verde.",
            "nutrition_vitamin_d": "La luz diurna y alimentos como pescado azul, huevos y lácteos o alternativas vegetales fortificadas pueden apoyar el nivel de vitamina D con el tiempo.",
            "nutrition_zinc": "Carnes, mariscos, legumbres, lácteos, frutos secos y semillas pueden ayudar a sostener la ingesta de zinc sin pasar de inmediato a suplementos en dosis altas.",
            "activity_macrocytic": "Hasta que haya valoración clínica, conviene evitar el ejercicio intenso. La caminata suave y la actividad diaria de baja carga son opciones más prudentes si se toleran bien.",
            "activity_low_hemoglobin": "Mientras se revisa el patrón de la sangre, es más razonable mantener la actividad en un nivel ligero y no intentar compensar con entrenamientos intensos.",
            "activity_mild": "La actividad ligera y regular es razonable aquí. Caminar, movilidad suave y ejercicio moderado habitual suelen ser suficientes sin intentar corregir el análisis con entrenamiento.",
            "recovery_blood": "Un sueño consistente, buena hidratación y una rutina menos sobrecargada pueden apoyar la recuperación mientras se revisan estos marcadores de sangre.",
            "recovery_deficiency": "Aquí suele ayudar más una rutina estable que esfuerzos puntuales. Comidas regulares, sueño y tiempo al aire libre pueden apoyar una corrección gradual.",
            "clinician_macrocytic": "Conviene comentar la repetición del hemograma y la medición de vitamina B12 y folato, sin iniciar tratamiento por cuenta propia.",
            "clinician_low_hemoglobin": "Conviene comentar un nuevo control de la analítica y si tiene sentido ampliar el estudio según el contexto clínico general.",
            "clinician_vitamin_d": "Puede ser útil comentar la repetición del análisis de vitamina D y si la suplementación sería adecuada en su caso.",
            "clinician_zinc": "Puede ser útil comentar si hace falta repetir el análisis de zinc antes de hacer cambios importantes en suplementos.",
            "clinician_vitamin_d_zinc": "Puede ser útil comentar un nuevo control de vitamina D y zinc tras la corrección, y si la suplementación debería individualizarse en lugar de dirigirse por cuenta propia.",
            "clinician_generic": "Conviene comentar si sería útil repetir estudios o revisar de forma más dirigida los marcadores alterados en su contexto.",
            "clinician_significant": "Si la desviación ya parece clínicamente importante, el siguiente paso debería quedar guiado por un profesional.",
            "clinician_standard": "Estas sugerencias son solo de apoyo y deben mantenerse como complemento del informe principal, no como sustituto del consejo profesional.",
        },
    }
    return messages.get(language, messages["en"])
