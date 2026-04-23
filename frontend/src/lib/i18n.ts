export const SUPPORTED_LOCALES = ["en", "ru", "es"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_STORAGE_KEY = "labsense-locale";

export const localeLabels: Record<Locale, string> = {
  en: "EN",
  ru: "RU",
  es: "ES"
};

export const messages = {
  en: {
    brand: "Labsense",
    nav: {
      landing: "Home",
      upload: "Upload",
      results: "Results",
      history: "History",
      account: "Account"
    },
    common: {
      appTag: "AI lab interpretation",
      language: "Language",
      theme: "Theme",
      light: "Light",
      dark: "Dark",
      loading: "Loading...",
      source: "Report source",
      locale: "Language",
      processing: "Processing",
      markersExtracted: "Markers extracted",
      captured: "Captured",
      preparing: "Preparing...",
      reference: "Reference",
      included: "Included",
      pdf: "PDF",
      sourceDemo: "Preview",
      sourceVision: "AI extraction",
      sourcePdfplumber: "PDF text fallback"
    },
    landing: {
      headline: "Interpretation of blood tests",
      subhead: "Upload a lab report, review the key deviations, and get a calm, structured interpretation.",
      title: "About the project",
      heroRotation: {
        leading: "Interpretation of ",
        words: ["blood", "urine", "stool"],
        trailing: " tests"
      },
      description: "Labsense turns blood test results into a clear summary, focused marker review, and practical follow-up guidance.",
      ctaPrimary: "Upload a report",
      ctaSecondary: "View sample results",
      loading: "Preparing preview...",
      premiumEyebrow: "Support Labsense",
      premiumDescription:
        "Labsense is still early. Support helps improve the AI, the report experience, and the reliability of future updates.",
      demoRiskNotes: ["LDL is above target.", "CRP is above range."]
    },
    uploadPage: {
      title: "Upload report",
      subtitle: "Add your PDF report to extract markers and prepare your interpretation."
    },
    uploadForm: {
      badge: "Report upload",
      title: "Upload your blood test report",
      description: "We extract the values, organise the markers, and prepare a clear clinical summary.",
      chooseFile: "Select PDF report",
      tapToSelect: "Select a report",
      tapToChange: "Replace the file",
      language: "Report language",
      gender: "Sex",
      age: "Age",
      male: "Male",
      female: "Female",
      submit: "Analyse report",
      parsing: "Reading report...",
      interpreting: "Preparing interpretation...",
      policy: "Processed securely for this session",
      pdfNotStored: "The original PDF is not kept after processing",
      errors: {
        missingFile: "Choose a PDF report to continue.",
        invalidType: "Only PDF files are supported.",
        emptyFile: "The selected PDF is empty.",
        tooLarge: "The PDF exceeds the 10 MB limit.",
        invalidAge: "Enter a whole-number age between 1 and 120.",
        uploadFailed: "We couldn’t process that report. Please try again.",
        interpretationUnavailable: "The report was read successfully, but the interpretation is not available right now."
      }
    },
    results: {
      title: "Results",
      subtitle: "Your report, marker review, interpretation, and follow-up guidance.",
      loadingSubtitle: "Opening your latest report.",
      loadingBody: "Preparing your results...",
      emptySubtitle: "No report in this session yet.",
      emptyBody: "Upload a PDF report to see your summary, flagged markers, and interpretation.",
      emptyCta: "Upload a report"
    },
    history: {
      title: "History",
      subtitle: "Recent reports and their current review status.",
      loading: "Loading history...",
      previewNotice: "This is a preview. Your reports will appear here after you sign in.",
      exampleLabel: "Example",
      footnote: "History preview only. Saved reports appear here once your account is connected.",
      ready: "ready",
      processing: "in review"
    },
    account: {
      title: "Account",
      subtitle: "Sign in to save reports later. Support helps improve interpretation quality and product accuracy.",
      loading: "Loading account...",
      profile: "Account",
      signInPrompt: "Sign in to save reports and manage your history"
    },
    payments: {
      title: "Support Labsense",
      description:
        "If Labsense is useful, you can support the product with Stripe or PayPal. Support helps improve the AI, the report quality, and the product itself.",
      stripe: "Support via Stripe",
      paypal: "Support via PayPal",
      telegramStarsPlaceholder: "Telegram Stars support will appear here when available"
    },
    premium: {
      uploadEyebrow: "Support Labsense",
      uploadTitle: "Support early development",
      uploadDescription:
        "Labsense is an early-stage product. Support helps improve the AI interpretation, the report experience, and the reliability of future updates.",
      uploadFeatures: [
        "Help improve the quality and clarity of AI interpretation",
        "Support calmer, more reliable product refinement over time",
        "Keep development honest, focused, and independent"
      ],
      resultsEyebrow: "Support Labsense",
      resultsTitle: "Support the next stage of Labsense",
      resultsDescription:
        "The current report stays available as it is. Support helps fund better AI quality, more polished interpretation, and steadier product development.",
      resultsFeatures: [
        "Improve interpretation quality and consistency",
        "Support clearer report structure and calmer follow-up guidance",
        "Help shape an early product with real user feedback"
      ],
      accountEyebrow: "Support Labsense",
      accountTitle: "Choose a support method",
      accountDescription:
        "Support helps improve report clarity, interpretation accuracy, and the overall quality of Labsense.",
      accountFeatures: [
        "Help improve interpretation accuracy and consistency",
        "Support clearer reports and calmer product refinement",
        "Contribute directly without fake tiers or locked features"
      ],
      telegramNote: "Telegram Stars support will appear here once available."
    },
    summaryCard: {
      eyebrow: "Your report",
      emptyEyebrow: "Sample report",
      emptyTitle: "Your report appears here",
      emptyBody: "After you upload a PDF, Labsense shows a concise summary, key markers, and the report source.",
      emptyFootnote: "Saved only in this browser session."
    },
    riskStatus: {
      green: {
        label: "Normal",
        explanation: "All detected markers are within range."
      },
      yellow: {
        label: "Needs observation",
        explanation: "A mild deviation is present and should be observed."
      },
      red: {
        label: "Significant deviation",
        explanation: "Clinically relevant deviations are present and should be reviewed."
      }
    },
    markersCard: {
      title: "Markers",
      empty: "No markers are available for this report yet.",
      showing: "{visible} of {total} markers shown, with out-of-range results first.",
      referenceUnavailable: "Reference range unavailable",
      statusHigh: "high",
      statusLow: "low",
      statusNormal: "in range",
      statusUnknown: "review",
      unknownHint: "Some markers still need manual reference review."
    },
    interpretationCard: {
      title: "Interpretation",
      unavailable: "Interpretation is not available right now.",
      sections: {
        overallStatus: "Overall status",
        keyObservations: "Key observations",
        importance: "Importance",
        whatThisMeans: "What this means",
        optionalImprovements: "Optional improvements",
        nextSteps: "Next steps",
        finalConclusion: "Final conclusion"
      }
    },
    recommendationsCard: {
      title: "Next steps",
      empty: "Recommendations will appear here when ready."
    },
    disclaimer: {
      title: "Medical notice",
      short: "This interpretation is informational only. It is not a diagnosis and does not replace a clinician.",
      full:
        "Labsense helps summarize report patterns in clear language, but it does not provide a medical diagnosis. Any treatment, testing, or care decision should be made with a qualified clinician who can review your symptoms, history, and full results.",
      expand: "Read the full note",
      collapse: "Hide the note"
    },
    api: {
      parsePdfFallback: "Failed to parse PDF report.",
      interpretFallback: "Failed to interpret lab data.",
      missingFile: "A PDF file is required.",
      invalidFileType: "Only PDF uploads are supported.",
      emptyFile: "Uploaded PDF is empty.",
      invalidJson: "Request body must be valid JSON.",
      invalidPayload: "Interpretation request payload is invalid.",
      invalidParserResponse: "Parser service returned an invalid response.",
      invalidInterpretationResponse: "Interpretation service returned an invalid response.",
      uploadTimedOut: "Upload timed out while waiting for the parser service.",
      uploadUnavailable: "Upload service is currently unavailable.",
      interpretationTimedOut: "Interpretation timed out while waiting for the API service.",
      interpretationUnavailable: "Interpretation service is currently unavailable."
    },
    generated: {
      latestReport: "Latest report",
      reportFromDate: "Report from {date}",
      markersExtractedOverview: "{count} markers extracted from the report.",
      markersCapturedConfidence: "{count} markers captured",
      markersNeedReviewConfidence: "{count} marker needs attention",
      markersNeedReviewConfidencePlural: "{count} markers need attention",
      extractionIssueTitle: "Extraction issue",
      extractionIssueOverview: "Possible extraction issue detected. No interpretation was generated.",
      extractionIssueAction: "Please re-upload the report.",
      extractionIssueMarkersHidden: "Markers are hidden until the report is uploaded again.",
      recommendation: "Next step {index}",
      clinicalFollowUp: "Clinical follow-up",
      physicianReview: "Review these findings with your physician."
    }
  },
  ru: {
    brand: "Labsense",
    nav: {
      landing: "Главная",
      upload: "Загрузка",
      results: "Результаты",
      history: "История",
      account: "Аккаунт"
    },
    common: {
      appTag: "AI интерпретация анализов",
      language: "Язык",
      theme: "Тема",
      light: "Светлая",
      dark: "Тёмная",
      loading: "Загрузка...",
      source: "Источник отчёта",
      locale: "Язык",
      processing: "Обработка",
      markersExtracted: "Извлечено маркеров",
      captured: "Получено",
      preparing: "Подготовка...",
      reference: "Референс",
      included: "Показано",
      pdf: "PDF",
      sourceDemo: "Превью",
      sourceVision: "Извлечение с ИИ",
      sourcePdfplumber: "Текстовое извлечение из PDF"
    },
    landing: {
      headline: "Интерпретация анализов крови",
      subhead: "Загрузите лабораторный отчёт, проверьте ключевые отклонения и получите спокойное, структурированное объяснение.",
      title: "О проекте",
      heroRotation: {
        leading: "Интерпретация анализов ",
        words: ["крови", "мочи", "кала"],
        trailing: ""
      },
      description: "Labsense превращает показатели анализа крови в ясную сводку, обзор ключевых маркеров и спокойные рекомендации по дальнейшим шагам.",
      ctaPrimary: "Загрузить отчёт",
      ctaSecondary: "Открыть пример",
      loading: "Подготавливаем пример...",
      premiumEyebrow: "Поддержать Labsense",
      premiumDescription:
        "Labsense находится на ранней стадии. Поддержка помогает улучшать ИИ, опыт работы с отчётом и надёжность следующих обновлений.",
      demoRiskNotes: ["LDL выше цели.", "CRP выше референса."]
    },
    uploadPage: {
      title: "Загрузка отчёта",
      subtitle: "Добавьте PDF-файл, чтобы извлечь показатели и подготовить интерпретацию."
    },
    uploadForm: {
      badge: "Загрузка отчёта",
      title: "Загрузите анализ крови",
      description: "Мы извлечём показатели, упорядочим маркеры и подготовим понятную клиническую сводку.",
      chooseFile: "Выбрать PDF-отчёт",
      tapToSelect: "Выберите отчёт",
      tapToChange: "Заменить файл",
      language: "Язык отчёта",
      gender: "Пол",
      age: "Возраст",
      male: "Мужской",
      female: "Женский",
      submit: "Разобрать отчёт",
      parsing: "Читаем отчёт...",
      interpreting: "Готовим интерпретацию...",
      policy: "Безопасная обработка в рамках этой сессии",
      pdfNotStored: "Исходный PDF не хранится после обработки",
      errors: {
        missingFile: "Выберите PDF-отчёт, чтобы продолжить.",
        invalidType: "Поддерживаются только PDF-файлы.",
        emptyFile: "Выбранный PDF-файл пуст.",
        tooLarge: "Размер PDF превышает 10 МБ.",
        invalidAge: "Укажите возраст целым числом от 1 до 120.",
        uploadFailed: "Не удалось обработать отчёт. Попробуйте ещё раз.",
        interpretationUnavailable: "Отчёт успешно прочитан, но интерпретация сейчас недоступна."
      }
    },
    results: {
      title: "Результаты",
      subtitle: "Ваш отчёт, обзор маркеров, интерпретация и рекомендации по дальнейшим шагам.",
      loadingSubtitle: "Открываем ваш последний отчёт.",
      loadingBody: "Подготавливаем результаты...",
      emptySubtitle: "В этой сессии пока нет отчёта.",
      emptyBody: "Загрузите PDF-отчёт, чтобы увидеть сводку, отмеченные маркеры и интерпретацию.",
      emptyCta: "Перейти к загрузке"
    },
    history: {
      title: "История",
      subtitle: "Последние отчёты и текущий статус обработки.",
      loading: "Загружаем историю...",
      previewNotice: "Это демонстрация. Ваши отчёты появятся здесь после входа в аккаунт.",
      exampleLabel: "Пример",
      footnote: "Пока это только предпросмотр. Сохранённые отчёты появятся здесь после подключения аккаунта.",
      ready: "готово",
      processing: "в обработке"
    },
    account: {
      title: "Аккаунт",
      subtitle: "Вход понадобится, чтобы сохранять отчёты. Поддержка помогает повышать качество интерпретации и точность продукта.",
      loading: "Загружаем аккаунт...",
      profile: "Аккаунт",
      signInPrompt: "Войдите, чтобы сохранять отчёты и управлять историей"
    },
    payments: {
      title: "Поддержать Labsense",
      description:
        "Если Labsense полезен, вы можете поддержать продукт через Stripe или PayPal. Поддержка помогает улучшать ИИ, качество отчётов и сам продукт.",
      stripe: "Поддержать через Stripe",
      paypal: "Поддержать через PayPal",
      telegramStarsPlaceholder: "Поддержка через Telegram Stars появится здесь, когда станет доступна"
    },
    premium: {
      uploadEyebrow: "Поддержать Labsense",
      uploadTitle: "Поддержите раннюю разработку",
      uploadDescription:
        "Labsense находится на ранней стадии. Поддержка помогает улучшать ИИ-интерпретацию, опыт работы с отчётом и надёжность следующих версий.",
      uploadFeatures: [
        "Помогает повышать качество и ясность ИИ-интерпретации",
        "Поддерживает более спокойное и надёжное развитие продукта",
        "Сохраняет разработку честной, сфокусированной и независимой"
      ],
      resultsEyebrow: "Поддержать Labsense",
      resultsTitle: "Поддержите следующий этап Labsense",
      resultsDescription:
        "Текущий отчёт остаётся доступным как есть. Поддержка помогает улучшать качество ИИ, более аккуратную интерпретацию и устойчивое развитие продукта.",
      resultsFeatures: [
        "Помогает улучшать качество и стабильность интерпретации",
        "Поддерживает более ясную структуру отчёта и спокойные рекомендации",
        "Позволяет развивать ранний продукт с опорой на реальную обратную связь"
      ],
      accountEyebrow: "Поддержать Labsense",
      accountTitle: "Выберите способ поддержки",
      accountDescription:
        "Поддержка помогает улучшать ясность отчётов, точность интерпретации и общее качество Labsense.",
      accountFeatures: [
        "Помогает повышать точность и стабильность интерпретации",
        "Поддерживает более ясные отчёты и спокойное развитие продукта",
        "Даёт прямой вклад без фейковых тарифов и закрытых функций"
      ],
      telegramNote: "Поддержка через Telegram Stars появится здесь, когда станет доступна."
    },
    summaryCard: {
      eyebrow: "Ваш отчёт",
      emptyEyebrow: "Пример отчёта",
      emptyTitle: "Ваш отчёт появится здесь",
      emptyBody: "После загрузки PDF Labsense покажет краткую сводку, ключевые маркеры и источник отчёта.",
      emptyFootnote: "Сохраняется только в рамках этой сессии браузера."
    },
    riskStatus: {
      green: {
        label: "Норма",
        explanation: "Все обнаруженные маркеры находятся в пределах референса."
      },
      yellow: {
        label: "Нужно наблюдение",
        explanation: "Есть легкое отклонение, за которым стоит наблюдать."
      },
      red: {
        label: "Значимое отклонение",
        explanation: "Есть клинически значимые отклонения, которые стоит обсудить с врачом."
      }
    },
    markersCard: {
      title: "Маркеры",
      empty: "Для этого отчёта пока нет доступных маркеров.",
      showing: "Показано {visible} из {total} маркеров. Сначала выводятся отклонения.",
      referenceUnavailable: "Референсный диапазон недоступен",
      statusHigh: "выше нормы",
      statusLow: "ниже нормы",
      statusNormal: "в норме",
      statusUnknown: "проверить",
      unknownHint: "Для части маркеров нужен ручной просмотр референсов."
    },
    interpretationCard: {
      title: "Интерпретация",
      unavailable: "Интерпретация сейчас недоступна.",
      sections: {
        overallStatus: "Общий статус",
        keyObservations: "Ключевые наблюдения",
        importance: "Значение",
        whatThisMeans: "Что это значит",
        optionalImprovements: "Что можно улучшить",
        nextSteps: "Следующие шаги",
        finalConclusion: "Итог"
      }
    },
    recommendationsCard: {
      title: "Следующие шаги",
      empty: "Рекомендации появятся здесь, когда будут готовы."
    },
    disclaimer: {
      title: "Медицинская оговорка",
      short: "Этот разбор носит информационный характер. Он не является диагнозом и не заменяет консультацию врача.",
      full:
        "Labsense помогает понятно структурировать результаты анализа, но не ставит диагноз. Любые решения о лечении, дообследовании или наблюдении следует принимать вместе с врачом, который может учесть симптомы, анамнез и полную клиническую картину.",
      expand: "Полный текст",
      collapse: "Скрыть"
    },
    api: {
      parsePdfFallback: "Не удалось обработать PDF-отчёт.",
      interpretFallback: "Не удалось получить интерпретацию анализа.",
      missingFile: "Нужен PDF-файл.",
      invalidFileType: "Поддерживаются только PDF-файлы.",
      emptyFile: "Загруженный PDF-файл пуст.",
      invalidJson: "Тело запроса должно содержать корректный JSON.",
      invalidPayload: "Данные для интерпретации переданы в неверном формате.",
      invalidParserResponse: "Сервис разбора вернул некорректный ответ.",
      invalidInterpretationResponse: "Сервис интерпретации вернул некорректный ответ.",
      uploadTimedOut: "Время ожидания разбора PDF истекло.",
      uploadUnavailable: "Сервис загрузки сейчас недоступен.",
      interpretationTimedOut: "Время ожидания интерпретации истекло.",
      interpretationUnavailable: "Сервис интерпретации сейчас недоступен."
    },
    generated: {
      latestReport: "Последний анализ",
      reportFromDate: "Анализ от {date}",
      markersExtractedOverview: "Из отчёта извлечено {count} маркеров.",
      markersCapturedConfidence: "Получено {count} маркеров",
      markersNeedReviewConfidence: "{count} маркер требует внимания",
      markersNeedReviewConfidencePlural: "{count} маркера требуют внимания",
      extractionIssueTitle: "Ошибка извлечения",
      extractionIssueOverview: "Обнаружена возможная ошибка извлечения. Интерпретация не была создана.",
      extractionIssueAction: "Пожалуйста, загрузите отчёт повторно.",
      extractionIssueMarkersHidden: "Маркеры скрыты до повторной загрузки отчёта.",
      recommendation: "Следующий шаг {index}",
      clinicalFollowUp: "Дальнейшее наблюдение",
      physicianReview: "Обсудите эти результаты со своим врачом."
    }
  },
  es: {
    brand: "Labsense",
    nav: {
      landing: "Inicio",
      upload: "Subir",
      results: "Resultados",
      history: "Historial",
      account: "Cuenta"
    },
    common: {
      appTag: "Interpretación de análisis con IA",
      language: "Idioma",
      theme: "Tema",
      light: "Claro",
      dark: "Oscuro",
      loading: "Cargando...",
      source: "Origen del informe",
      locale: "Idioma",
      processing: "Procesamiento",
      markersExtracted: "Marcadores extraídos",
      captured: "Recibido",
      preparing: "Preparando...",
      reference: "Referencia",
      included: "Mostrados",
      pdf: "PDF",
      sourceDemo: "Vista previa",
      sourceVision: "Extracción con IA",
      sourcePdfplumber: "Lectura de texto del PDF"
    },
    landing: {
      headline: "Interpretación de análisis de sangre",
      subhead: "Sube tu informe, revisa los desvíos clave y recibe una interpretación serena y bien estructurada.",
      title: "Sobre el proyecto",
      heroRotation: {
        leading: "Interpretación de análisis de ",
        words: ["sangre", "orina", "heces"],
        trailing: ""
      },
      description: "Labsense convierte los resultados de un análisis de sangre en un resumen claro, una revisión enfocada de marcadores y orientación práctica.",
      ctaPrimary: "Subir informe",
      ctaSecondary: "Ver ejemplo",
      loading: "Preparando vista previa...",
      premiumEyebrow: "Apoyar Labsense",
      premiumDescription:
        "Labsense está en una etapa temprana. Tu apoyo ayuda a mejorar la IA, la experiencia del informe y la fiabilidad de las próximas versiones.",
      demoRiskNotes: ["LDL está por encima del objetivo.", "La CRP está por encima del rango."]
    },
    uploadPage: {
      title: "Subir informe",
      subtitle: "Añade tu PDF para extraer marcadores y preparar la interpretación."
    },
    uploadForm: {
      badge: "Carga de informe",
      title: "Sube tu informe de análisis de sangre",
      description: "Extraemos los valores, ordenamos los marcadores y preparamos un resumen clínico claro.",
      chooseFile: "Seleccionar informe en PDF",
      tapToSelect: "Selecciona un informe",
      tapToChange: "Reemplazar archivo",
      language: "Idioma del informe",
      gender: "Sexo",
      age: "Edad",
      male: "Masculino",
      female: "Femenino",
      submit: "Analizar informe",
      parsing: "Leyendo informe...",
      interpreting: "Preparando interpretación...",
      policy: "Procesamiento seguro durante esta sesión",
      pdfNotStored: "El PDF original no se conserva después del procesamiento",
      errors: {
        missingFile: "Selecciona un informe en PDF para continuar.",
        invalidType: "Solo se admiten archivos PDF.",
        emptyFile: "El PDF seleccionado está vacío.",
        tooLarge: "El PDF supera el límite de 10 MB.",
        invalidAge: "Indica una edad entera entre 1 y 120.",
        uploadFailed: "No pudimos procesar ese informe. Inténtalo de nuevo.",
        interpretationUnavailable: "El informe se leyó correctamente, pero la interpretación no está disponible ahora mismo."
      }
    },
    results: {
      title: "Resultados",
      subtitle: "Tu informe, revisión de marcadores, interpretación y orientación de seguimiento.",
      loadingSubtitle: "Abriendo tu informe más reciente.",
      loadingBody: "Preparando tus resultados...",
      emptySubtitle: "Todavía no hay un informe en esta sesión.",
      emptyBody: "Sube un informe en PDF para ver el resumen, los marcadores señalados y la interpretación.",
      emptyCta: "Subir informe"
    },
    history: {
      title: "Historial",
      subtitle: "Informes recientes y su estado actual de revisión.",
      loading: "Cargando historial...",
      previewNotice: "Esto es una vista previa. Sus informes aparecerán aquí después de iniciar sesión.",
      exampleLabel: "Ejemplo",
      footnote: "Vista previa del historial. Los informes guardados aparecerán aquí cuando la cuenta esté conectada.",
      ready: "listo",
      processing: "en revisión"
    },
    account: {
      title: "Cuenta",
      subtitle: "Inicie sesión para guardar informes más adelante. Su apoyo ayuda a mejorar la calidad de la interpretación y la precisión del producto.",
      loading: "Cargando cuenta...",
      profile: "Cuenta",
      signInPrompt: "Inicie sesión para guardar informes y gestionar su historial"
    },
    payments: {
      title: "Apoyar Labsense",
      description:
        "Si Labsense te resulta útil, puedes apoyar el producto con Stripe o PayPal. El apoyo ayuda a mejorar la IA, la calidad del informe y el producto en general.",
      stripe: "Apoyar con Stripe",
      paypal: "Apoyar con PayPal",
      telegramStarsPlaceholder: "La opción de apoyo con Telegram Stars aparecerá aquí cuando esté disponible"
    },
    premium: {
      uploadEyebrow: "Apoyar Labsense",
      uploadTitle: "Apoya el desarrollo inicial",
      uploadDescription:
        "Labsense está en una etapa temprana. Tu apoyo ayuda a mejorar la interpretación con IA, la experiencia del informe y la fiabilidad de las próximas versiones.",
      uploadFeatures: [
        "Ayuda a mejorar la calidad y la claridad de la interpretación con IA",
        "Apoya una evolución del producto más serena y fiable",
        "Mantiene el desarrollo honesto, enfocado e independiente"
      ],
      resultsEyebrow: "Apoyar Labsense",
      resultsTitle: "Apoya la siguiente etapa de Labsense",
      resultsDescription:
        "El informe actual sigue disponible tal como está. El apoyo ayuda a financiar una mejor calidad de IA, una interpretación más pulida y un desarrollo más estable del producto.",
      resultsFeatures: [
        "Mejorar la calidad y la consistencia de la interpretación",
        "Apoyar una estructura del informe más clara y una guía de seguimiento más serena",
        "Ayudar a dar forma a un producto temprano con feedback real"
      ],
      accountEyebrow: "Apoyar Labsense",
      accountTitle: "Elige cómo apoyar",
      accountDescription:
        "Tu apoyo ayuda a mejorar la claridad de los informes, la precisión de la interpretación y la calidad general de Labsense.",
      accountFeatures: [
        "Ayuda a mejorar la precisión y la consistencia de la interpretación",
        "Apoya informes más claros y una evolución más serena del producto",
        "Contribuye de forma directa, sin niveles falsos ni funciones bloqueadas"
      ],
      telegramNote: "La opción de apoyo con Telegram Stars aparecerá aquí cuando esté disponible."
    },
    summaryCard: {
      eyebrow: "Tu informe",
      emptyEyebrow: "Informe de ejemplo",
      emptyTitle: "Tu informe aparece aqui",
      emptyBody: "Despues de subir un PDF, Labsense mostrara un resumen breve, los marcadores clave y el origen del informe.",
      emptyFootnote: "Se guarda solo en esta sesion del navegador."
    },
    riskStatus: {
      green: {
        label: "Normal",
        explanation: "Todos los marcadores detectados están dentro de rango."
      },
      yellow: {
        label: "Necesita observación",
        explanation: "Hay una desviación leve que conviene observar."
      },
      red: {
        label: "Desviación significativa",
        explanation: "Hay desviaciones clínicamente relevantes que conviene revisar."
      }
    },
    markersCard: {
      title: "Marcadores",
      empty: "Todavía no hay marcadores disponibles para este informe.",
      showing: "Se muestran {visible} de {total} marcadores, con los valores fuera de rango primero.",
      referenceUnavailable: "Rango de referencia no disponible",
      statusHigh: "alto",
      statusLow: "bajo",
      statusNormal: "en rango",
      statusUnknown: "revisar",
      unknownHint: "Algunos marcadores aún requieren una revisión manual de referencia."
    },
    interpretationCard: {
      title: "Interpretación",
      unavailable: "La interpretación no está disponible en este momento.",
      sections: {
        overallStatus: "Estado general",
        keyObservations: "Observaciones clave",
        importance: "Importancia",
        whatThisMeans: "Qué significa",
        optionalImprovements: "Qué se puede mejorar",
        nextSteps: "Siguientes pasos",
        finalConclusion: "Conclusión final"
      }
    },
    recommendationsCard: {
      title: "Siguientes pasos",
      empty: "Las recomendaciones aparecerán aquí cuando estén listas."
    },
    disclaimer: {
      title: "Aviso médico",
      short: "Esta interpretación es solo informativa. No es un diagnóstico ni sustituye la valoración de un médico.",
      full:
        "Labsense ayuda a resumir los patrones del informe en un lenguaje claro, pero no emite un diagnóstico médico. Cualquier decisión sobre tratamiento, estudios adicionales o seguimiento debe tomarse con un profesional de salud que pueda revisar los síntomas, los antecedentes y los resultados completos.",
      expand: "Leer el texto completo",
      collapse: "Ocultar"
    },
    api: {
      parsePdfFallback: "No se pudo procesar el informe en PDF.",
      interpretFallback: "No se pudo interpretar el análisis.",
      missingFile: "Se necesita un archivo PDF.",
      invalidFileType: "Solo se admiten archivos PDF.",
      emptyFile: "El PDF cargado está vacío.",
      invalidJson: "El cuerpo de la solicitud debe ser JSON válido.",
      invalidPayload: "La solicitud de interpretación no tiene un formato válido.",
      invalidParserResponse: "El servicio de extracción devolvió una respuesta no válida.",
      invalidInterpretationResponse: "El servicio de interpretación devolvió una respuesta no válida.",
      uploadTimedOut: "La carga superó el tiempo de espera del servicio de extracción.",
      uploadUnavailable: "El servicio de carga no está disponible en este momento.",
      interpretationTimedOut: "La interpretación superó el tiempo de espera del servicio.",
      interpretationUnavailable: "El servicio de interpretación no está disponible en este momento."
    },
    generated: {
      latestReport: "Último análisis",
      reportFromDate: "Análisis del {date}",
      markersExtractedOverview: "Se extrajeron {count} marcadores del informe.",
      markersCapturedConfidence: "{count} marcadores recibidos",
      markersNeedReviewConfidence: "{count} marcador requiere atención",
      markersNeedReviewConfidencePlural: "{count} marcadores requieren atención",
      extractionIssueTitle: "Problema de extracción",
      extractionIssueOverview: "Se detectó un posible problema de extracción. No se generó ninguna interpretación.",
      extractionIssueAction: "Vuelve a subir el informe.",
      extractionIssueMarkersHidden: "Los marcadores están ocultos hasta que se vuelva a subir el informe.",
      recommendation: "Siguiente paso {index}",
      clinicalFollowUp: "Seguimiento clínico",
      physicianReview: "Revisa estos resultados con tu médico."
    }
  }
} as const;

export type Messages = (typeof messages)[Locale];

export function isLocale(value: string): value is Locale {
  return SUPPORTED_LOCALES.includes(value as Locale);
}

export function getMessages(locale: Locale = DEFAULT_LOCALE): Messages {
  return messages[locale];
}

export function formatMessage(template: string, values: Record<string, string | number>): string {
  return Object.entries(values).reduce(
    (output, [key, value]) => output.replaceAll(`{${key}}`, String(value)),
    template
  );
}
