/**
 * ═══════════════════════════════════════════════════════════════════
 * VALUE ANALYST — Presentación Educativa e Inversora
 * ═══════════════════════════════════════════════════════════════════
 *
 * INSTRUCCIONES:
 * 1. Abre Google Slides y crea una presentación VACÍA.
 * 2. Ve a Extensiones > Apps Script.
 * 3. Borra todo el contenido del editor y pega este código.
 * 4. Haz clic en ▶ Ejecutar (función: crearPresentacion).
 * 5. Acepta los permisos la primera vez.
 * 6. Vuelve a la presentación y ya tendrás todas las diapositivas.
 *
 * Después aplica el tema/plantilla de diseño que prefieras.
 * ═══════════════════════════════════════════════════════════════════
 */

function crearPresentacion() {
  const pres = SlidesApp.getActivePresentation();

  // Eliminar diapositiva vacía inicial
  const slides = pres.getSlides();
  if (slides.length === 1 && slides[0].getPageElements().length === 0) {
    slides[0].remove();
  }

  // ─── Colores corporativos ────────────────────────────────────
  const GOLD    = '#FBBF24';
  const DARK    = '#0F172A';
  const WHITE   = '#FFFFFF';
  const GREEN   = '#22C55E';
  const YELLOW  = '#EAB308';
  const RED     = '#EF4444';
  const ACCENT  = '#3B82F6';
  const GRAY    = '#94A3B8';
  const BG_DARK = '#1E293B';

  // ─── Helper: crear diapositiva ───────────────────────────────
  function addSlide(titleText, bodyText, opts = {}) {
    const slide = pres.appendSlide(SlidesApp.PredefinedLayout.BLANK);
    
    // Fondo
    slide.getBackground().setSolidFill(opts.bg || BG_DARK);

    // Título
    const title = slide.insertTextBox(titleText, 40, 30, 640, 60);
    const titleStyle = title.getText().getTextStyle();
    titleStyle.setFontSize(28).setBold(true).setForegroundColor(opts.titleColor || GOLD);
    titleStyle.setFontFamily('Montserrat');

    // Cuerpo
    if (bodyText) {
      const body = slide.insertTextBox(bodyText, 40, 100, 640, 300);
      const bodyStyle = body.getText().getTextStyle();
      bodyStyle.setFontSize(14).setForegroundColor(opts.bodyColor || WHITE);
      bodyStyle.setFontFamily('Open Sans');
      body.getText().getParagraphStyle().setSpaceAbove(6);
    }

    // Notas del orador
    if (opts.notes) {
      slide.getNotesPage().getSpeakerNotesShape().getText().setText(opts.notes);
    }

    return slide;
  }

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 1: PORTADA
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🍊 Value Analyst',
    'Tu motor de análisis fundamental para invertir con cabeza\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    'Una guía completa de inversión en valor\n' +
    'para personas que nunca han invertido en bolsa\n\n' +
    '🎯 Teoría · 📱 App · 📊 Ejemplos Reales · 🚀 Futuro',
    {
      notes: 'Bienvenida. Esta presentación está diseñada para que cualquier persona, sin conocimientos financieros previos, entienda cómo analizar empresas como un inversor profesional.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 2: TEORÍA — QUÉ ES INVERTIR
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '💡 ¿Qué es realmente invertir en bolsa?',
    '🏠 Imagina que quieres comprar un piso para alquilarlo:\n\n' +
    '• Miras el barrio, el estado del piso, cuánto puedes cobrar de alquiler\n' +
    '• Comparas con otros pisos similares\n' +
    '• Si te piden 200.000€ por un piso que vale 300.000€... ¡GANGA!\n' +
    '• Si te piden 500.000€ por ese mismo piso... es carísimo\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    'Invertir en bolsa es EXACTAMENTE lo mismo.\n' +
    'Una acción es un trozo de un negocio real.\n' +
    'Nuestro objetivo: comprar buenos negocios a buen precio.',
    {
      notes: 'Usar la analogía del piso a lo largo de toda la presentación. Todo el mundo entiende el mercado inmobiliario. Comprar acciones = comprar un trocito de un negocio real, no es un casino.'
    }
  );

  addSlide(
    '⚔️ Dos filosofías de inversión',
    '🏛️ VALUE INVESTING (Inversión en Valor)\n' +
    '«Comprar billetes de 100€ cuando cuestan 60€»\n' +
    '• Buscamos empresas BARATAS respecto a lo que valen\n' +
    '• Warren Buffett, Benjamin Graham, Charlie Munger\n' +
    '• Enfoque: beneficios actuales, flujo de caja, dividendos\n' +
    '• Horizonte: largo plazo (3-10 años)\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '🚀 GROWTH INVESTING (Inversión en Crecimiento)\n' +
    '«Apostar por el barrio que va a revalorizarse»\n' +
    '• Buscamos empresas que CRECEN rápidamente\n' +
    '• Pueden no tener beneficios hoy, pero dominan el futuro\n' +
    '• Enfoque: ventas disparadas, mercado gigante, innovación\n' +
    '• Riesgo: mayor, pero la recompensa puede ser brutal',
    {
      notes: 'Value = comprar a descuento (como las rebajas). Growth = apostar por el futuro (como comprar en un barrio en plena transformación antes de que suban los precios). Ambos son válidos, la app cubre los dos.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 3: CONCEPTOS CLAVE CON EJEMPLOS COTIDIANOS
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🔑 Concepto 1: Valor Intrínseco',
    '¿Cuánto VALE realmente algo?\n\n' +
    '🏠 Ejemplo del piso:\n' +
    'Un piso genera 800€/mes de alquiler = 9.600€/año\n' +
    'Si pisos similares se venden a 20 veces su alquiler anual:\n' +
    'Valor Intrínseco = 9.600€ × 20 = 192.000€\n\n' +
    '📈 En empresas:\n' +
    'Una empresa genera 5.000M€ al año de caja real\n' +
    'El motor calcula cuánto valen esos flujos futuros HOY\n' +
    'usando modelos matemáticos (Graham, DCF, EPV)\n\n' +
    '⚡ La app hace este cálculo automáticamente\n' +
    'para darte el "precio justo" de cada acción.',
    {
      notes: 'El valor intrínseco es el concepto MÁS importante. Es el precio "justo" que deberías pagar. Si el mercado te cobra menos, es una oportunidad. Si te cobra más, estás pagando de más. La app calcula esto con 3 modelos diferentes para cada empresa.'
    }
  );

  addSlide(
    '🛡️ Concepto 2: Margen de Seguridad',
    'El "colchón" que te protege de equivocarte\n\n' +
    '🏠 Ejemplo:\n' +
    'Si un piso vale 200.000€ y lo compras a 160.000€\n' +
    'tienes un descuento del 20% = Margen de Seguridad del 20%\n' +
    'Aunque te equivoques un poco, sigues ganando dinero\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    'En la app tenemos DOS márgenes de seguridad:\n\n' +
    '🟢 MoS Absoluto: ¿Está barata vs su valor real?\n' +
    '   Precio actual vs Valor Intrínseco (Graham/DCF)\n\n' +
    '🟡 MoS Relativo: ¿Está barata vs su historia?\n' +
    '   Múltiplo actual vs su media de los últimos 5 años\n\n' +
    '💎 STRONG BUY = Ambos márgenes son positivos',
    {
      notes: 'El margen de seguridad es como ir con cinturón Y airbag. Protege contra errores de cálculo y cisnes negros. Benjamin Graham lo inventó tras perder dinero en el crash de 1929. La app exige MoS Absoluto > 15% Y MoS Relativo > 10% para dar semáforo verde.'
    }
  );

  addSlide(
    '💸 Concepto 3: Flujo de Caja Libre (FCF)',
    'El dinero REAL que le queda al negocio\n\n' +
    '🍊 Ejemplo de un puesto de naranjas:\n' +
    'Vendes 1.000€ de naranjas al mes\n' +
    '- 400€ comprar naranjas al mayorista\n' +
    '- 200€ alquiler del puesto\n' +
    '-  50€ impuestos\n' +
    '-  50€ reparar la balanza\n' +
    '= 300€ de CAJA REAL que te llevas a casa\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '⚠️ TRAMPA CONTABLE: Algunas empresas tech pagan\n' +
    'a sus empleados con acciones (SBC) en vez de dinero.\n' +
    'Eso NO aparece como gasto pero DILUYE al accionista.\n\n' +
    '🛡️ La app resta el SBC del FCF para darte\n' +
    'el flujo de caja REAL REAL, sin trampas.',
    {
      notes: 'El FCF es la métrica de oro. Es el dinero que realmente queda después de pagar TODO. Muchas empresas de Silicon Valley inflan su FCF pagando en acciones (Stock-Based Compensation). Nuestra app lo detecta y lo resta.'
    }
  );

  addSlide(
    '💪 Concepto 4: ROIC (Rentabilidad del Capital)',
    'La eficiencia del negocio para generar dinero\n\n' +
    '🏠 Ejemplo:\n' +
    'Inviertes 100.000€ en un piso y ganas 15.000€/año\n' +
    'ROIC = 15% → Muy buen negocio\n\n' +
    'Inviertes 100.000€ en otro y ganas 3.000€/año\n' +
    'ROIC = 3% → Negocio mediocre\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    'Clasificación en la app:\n\n' +
    '⭐ ROIC > 20% → Ventaja competitiva brutal (Wide Moat)\n' +
    '     Ejemplos: Apple, Visa, NVIDIA\n\n' +
    '✅ ROIC 12-20% → Buen negocio rentable\n' +
    '     Ejemplos: Pepsi, Johnson & Johnson\n\n' +
    '❌ ROIC < 10% → Negocio mediocre o destructor de valor',
    {
      notes: 'ROIC = cuánto dinero gana la empresa por cada euro que se invierte en ella. Es el indicador más potente para saber si un negocio tiene "Moat" (ventaja competitiva duradera como una marca, patentes o costes bajos). Warren Buffett busca ROIC > 15% sostenido.'
    }
  );

  addSlide(
    '🚦 Concepto 5: El Semáforo de Inversión',
    'La app analiza TODO automáticamente y te da una señal:\n\n' +
    '🟢 STRONG BUY — Compra fuerte\n' +
    '   Barata por fundamentales Y barata históricamente\n' +
    '   MoS Absoluto > 15% + MoS Relativo > 10%\n\n' +
    '🟢 COMPRA DE CALIDAD (Estilo Buffett) — Negocio top a precio razonable\n' +
    '   MoS > 0% + ROIC > 18% + Recompra de acciones / Skin in the Game\n\n' +
    '🟡 MANTENER / SEGUIMIENTO — Señal mixta\n' +
    '   Barata por un lado pero cara por otro (o sin descuento suficiente)\n\n' +
    '🔴 SOBREVALORADA — Evitar compra\n' +
    '   Cara por fundamentales Y cara históricamente (ambos MoS < 0%)\n\n' +
    '🚫 NO ELEGIBLE — Las cuentas no cuadran\n' +
    '   Desviación excesiva entre contabilidad GAAP y reportada (Non-GAAP)',
    {
      notes: 'El semáforo es la conclusión final del análisis. Combina Margen de Seguridad Absoluto y Relativo. Para empresas excelentes pero a precio justo, activa la señal 🟢 COMPRA DE CALIDAD si recompran acciones o hay directores invertidos. Para Growth usa PEG < 1.5 y Rule of 40 >= 40.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 4: ARQUETIPOS — TIPOS DE EMPRESAS
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🧩 Arquetipos: No todas las empresas se valoran igual',
    'La app clasifica cada empresa automáticamente:\n\n' +
    '🏛️ VALUE CLÁSICO (Coca-Cola, Walmart)\n' +
    '   Empresas maduras, estables, "aburridas pero rentables"\n' +
    '   Se valoran con Graham + DCF tradicional a 10 años\n\n' +
    '🚀 COMPOUNDER (Apple, NVIDIA, Visa)\n' +
    '   Máquinas de generar dinero con ventajas brutales\n' +
    '   Se valoran con DCF Multi-Fase (alto crecimiento → decae)\n\n' +
    '🔥 HIPERCRECIMIENTO (Palantir, CrowdStrike)\n' +
    '   Sin beneficios hoy, pero ventas disparadas\n' +
    '   Se valoran con DCF basado en ventas futuras\n\n' +
    '🏦 FINANCIERO (JPMorgan, Goldman Sachs)\n' +
    '   Bancos: su deuda son depósitos de clientes\n' +
    '   Se valoran con Precio/Valor en Libros\n\n' +
    '🏠 REIT/UTILITY (NextEra Energy, Realty Income)\n' +
    '   Reparten casi todo en dividendos\n' +
    '   Se valoran con Descuento de Dividendos (DDM)',
    {
      notes: 'Este es un concepto CLAVE de la app. No puedes valorar a Netflix con las mismas reglas que a un banco. El motor detecta automáticamente el arquetipo de cada empresa y aplica el modelo matemático correcto. Esto evita errores graves.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 5: LA APP — DEMOSTRACIÓN
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '📱 La App: ¿Cómo funciona?',
    'Value Analyst es una aplicación web que automatiza\n' +
    'todo el proceso de análisis de un inversor profesional:\n\n' +
    '1️⃣  Escribes el ticker de una empresa (ej: AAPL, MSFT)\n\n' +
    '2️⃣  El motor descarga datos reales de Yahoo Finance:\n' +
    '     • 5 años de estados financieros\n' +
    '     • Flujos de caja, deuda, márgenes, acciones\n' +
    '     • Estimaciones de analistas profesionales\n\n' +
    '3️⃣  Ejecuta el motor analítico:\n' +
    '     • Clasifica el arquetipo automáticamente\n' +
    '     • Calcula FCF Real (restando SBC y trampas)\n' +
    '     • Aplica el modelo de valoración correcto\n' +
    '     • Calcula ambos Márgenes de Seguridad\n\n' +
    '4️⃣  Te devuelve el Semáforo de Inversión 🚦\n' +
    '     con un informe completo y tesis de inversión',
    {
      notes: 'Demo en vivo si es posible. El proceso tarda 3-5 segundos. Los datos vienen de Yahoo Finance vía la librería yfinance de Python. El backend está en Flask y el motor de valoración tiene más de 1.700 líneas de código Python puro.'
    }
  );

  addSlide(
    '🔍 El Explorador de Valor',
    'Escaneo masivo del mercado para encontrar oportunidades:\n\n' +
    '🌍 Mercados disponibles:\n' +
    '   S&P 500 · NASDAQ · Dow Jones · STOXX 600\n' +
    '   FTSE 100 · DAX 40 · CAC 40 · IBEX 35 · Japón\n' +
    '   🌐 Todos los Mercados (Global)\n\n' +
    '🎛️ Filtros con deslizadores interactivos:\n' +
    '   • PER máximo (valoración relativa)\n' +
    '   • ROIC mínimo (calidad del negocio)\n' +
    '   • FCF Yield mínimo (generación de caja)\n' +
    '   • Margen de Seguridad mínimo (descuento exigido)\n\n' +
    '🧩 Filtros adicionales:\n' +
    '   • Por Arquetipo (Compounder, Value, Growth...)\n' +
    '   • Por Sector (Tecnología, Salud, Defensa...)\n\n' +
    '📊 Resultados ordenables por MoS, ROIC, FCF Yield, PER',
    {
      notes: 'El explorador escanea hasta 300 empresas en paralelo (5 hilos simultáneos) y las filtra en tiempo real. Es la herramienta más potente de la app para DESCUBRIR oportunidades que no conocías.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 6: EJEMPLO VERDE — STRONG BUY
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🟢 Ejemplo Real: Lululemon (LULU) — STRONG BUY',
    'Marca premium de ropa deportiva (yoga, running)\n\n' +
    '📊 Datos del motor:\n' +
    '   Precio actual:           $131\n' +
    '   Valor Intrínseco (DCF):  $230\n' +
    '   Margen de Seguridad:     +43%\n' +
    '   Arquetipo:               🚀 Compounder\n' +
    '   ROIC:                    > 25%\n' +
    '   FCF TTM:                 $860M\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '🏠 Analogía del piso:\n' +
    '"Un piso que vale 230.000€ en una zona premium\n' +
    ' y te lo venden por 131.000€ porque el dueño\n' +
    ' necesita vender rápido. Es una GANGA."\n\n' +
    '✅ Semáforo: VERDE porque ambos MoS son positivos\n' +
    '   y la calidad del negocio es excepcional.',
    {
      titleColor: GREEN,
      notes: 'LULU tiene un ROIC brutal (>25%), márgenes de beneficio altísimos, marca con poder de fijación de precios, y FCF creciente. El mercado la ha castigado temporalmente (caída de la moda athleisure) pero los fundamentales son sólidos. MoS del 43% = descuento enorme.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 7: EJEMPLO AMARILLO — MANTENER
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🟡 Ejemplo Real: Google / Alphabet (GOOG) — MANTENER',
    'El gigante tecnológico de búsquedas, YouTube, Cloud\n\n' +
    '📊 Datos del motor:\n' +
    '   Precio actual:           $376\n' +
    '   Valor Intrínseco (DCF):  $406\n' +
    '   Margen de Seguridad:     +7.3%\n' +
    '   Arquetipo:               🚀 Compounder\n' +
    '   ROIC:                    > 20%\n' +
    '   FCF TTM:                 $48.300M\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '🏠 Analogía del piso:\n' +
    '"Un piso en la MEJOR zona de Madrid que vale\n' +
    ' 406.000€ y te piden 376.000€. Descuento del 7%.\n' +
    ' No es una ganga espectacular pero tampoco es caro.\n' +
    ' Si te encanta el barrio, puede valer la pena."\n\n' +
    '🟡 Semáforo: AMARILLO. El MoS (+7%) no llega al 15%\n' +
    '   mínimo exigido para STRONG BUY.',
    {
      titleColor: YELLOW,
      notes: 'Google es un negocio EXCEPCIONAL (monopolio de búsquedas, YouTube, Cloud creciendo). Pero el precio no tiene suficiente descuento para un Strong Buy. El 7% de margen no te protege ante un susto. Estrategia: seguir vigilando y esperar una caída del mercado para comprar con más margen.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 8: EJEMPLO ROJO — SOBREVALORADA
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🔴 Ejemplo Real: Ferrari (RACE) — SOBREVALORADA',
    'La marca de coches de lujo más icónica del mundo\n\n' +
    '📊 Datos del motor:\n' +
    '   Precio actual:           $340\n' +
    '   Valor Intrínseco (DCF):  $113\n' +
    '   Margen de Seguridad:     -201%\n' +
    '   Arquetipo:               🚀 Compounder\n' +
    '   ROIC:                    > 30%\n' +
    '   FCF TTM:                 $1.410M\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '🏠 Analogía del piso:\n' +
    '"Un piso que vale 113.000€ por sus alquileres\n' +
    ' pero te piden 340.000€ porque es un ático de\n' +
    ' diseño famoso. Pagas 3 VECES lo que vale.\n' +
    ' Es un lujo, no una inversión."\n\n' +
    '🔴 Semáforo: ROJO. Negocio espectacular pero\n' +
    '   el precio de mercado ya descuenta 10+ años\n' +
    '   de crecimiento perfecto. Cero margen de error.',
    {
      titleColor: RED,
      notes: 'Ferrari es un negocio BRUTAL: ROIC >30%, márgenes de lujo, marca indestructible. PERO el mercado ya lo sabe y paga un precio desorbitado (PER >50x). Aquí la app nos protege: el negocio es perfecto pero el PRECIO es un robo. Value investing = calidad Y precio.'
    }
  );

  addSlide(
    '📚 Lección de los 3 ejemplos',
    'La calidad del negocio NO es suficiente.\n' +
    'El PRECIO que pagas determina tu rentabilidad.\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '┌─────────────┬──────────┬──────────┬──────────┐\n' +
    '│             │  LULU 🟢 │  GOOG 🟡 │  RACE 🔴 │\n' +
    '├─────────────┼──────────┼──────────┼──────────┤\n' +
    '│ ROIC        │   >25%   │   >20%   │   >30%   │\n' +
    '│ Calidad     │  ⭐ Alta │  ⭐ Alta │  ⭐ Alta │\n' +
    '│ MoS         │  +43%    │   +7%    │  -201%   │\n' +
    '│ Semáforo    │   🟢     │    🟡    │    🔴    │\n' +
    '└─────────────┴──────────┴──────────┴──────────┘\n\n' +
    '💡 Las tres son empresas EXCEPCIONALES.\n' +
    'La diferencia: solo LULU cotiza con descuento.\n\n' +
    '🏠 "Comprar el mejor piso del mundo a precio de ganga\n' +
    '    es mejor que comprar el mejor piso del mundo\n' +
    '    pagando el triple de lo que vale."',
    {
      notes: 'Esta diapositiva es el CORAZÓN de la presentación. Demuestra que la calidad sin precio es insuficiente. Ferrari es mejor empresa que Lululemon objetivamente (mayor ROIC) pero es PEOR inversión porque está carísima. Warren Buffett: "El precio es lo que pagas, el valor es lo que recibes."'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 9: GROWTH INVESTING EN LA APP
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🚀 Growth Investing en la App',
    'Para empresas de hipercrecimiento sin beneficios actuales:\n\n' +
    '📊 PEG Ratio (Peter Lynch):\n' +
    '   PER ÷ Tasa de Crecimiento. PEG < 1.0 = Barato | PEG > 2.0 = Caro.\n' +
    '   💡 ¡NUEVO!: Se muestra como indicador complementario universal para TODAS las empresas.\n\n' +
    '🔥 Rule of 40 (SaaS & Tech):\n' +
    '   Crecimiento Ventas (%) + Margen FCF (%). Score ≥ 40 = Élite.\n\n' +
    '💰 EV/Revenue (Múltiplo de ventas):\n' +
    '   Compara el valor total vs ventas anuales (con proyección Forward a 3 años).\n\n' +
    '🚦 Semáforo Growth (Hipercrecimiento):\n' +
    '   🟢 PEG < 1.5 + Rule of 40 ≥ 40 = GROWTH BUY\n' +
    '   🔴 PEG > 2.5 o Rule of 40 < 20 = GROWTH OVERPRICED\n' +
    '   🟡 GROWTH HOLD = Rango intermedio de valoración',
    {
      notes: 'Para empresas como Palantir o CrowdStrike, el valor intrínseco clásico no funciona. La app activa automáticamente las métricas Growth para el arquetipo Hipercrecimiento, y ahora calcula el PEG de Lynch como indicador complementario en todas las empresas.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 10: CHECKLIST DEL ANALISTA
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '✅ Checklist del Analista — Antes de Invertir',
    '□ 1. ¿Entiendes el negocio? ¿Puedes explicar\n' +
    '      a un niño de 10 años cómo gana dinero?\n\n' +
    '□ 2. ¿ROIC > 15%? (Ventaja competitiva duradera)\n\n' +
    '□ 3. ¿FCF Real positivo y creciente? (Genera caja)\n\n' +
    '□ 4. ¿Deuda controlada? (Net Debt/EBITDA < 3x)\n\n' +
    '□ 5. ¿EPS creciente en los últimos 5 años?\n\n' +
    '□ 6. ¿MoS Absoluto > 15%? (Descuento real)\n\n' +
    '□ 7. ¿MoS Relativo > 10%? (Barata vs su historia)\n\n' +
    '□ 8. ¿El equipo directivo tiene acciones propias?\n' +
    '      (Skin in the Game > 0.1%)\n\n' +
    '□ 9. ¿EBITDA GAAP vs Ajustado OK? (Sin trampas)\n\n' +
    '□ 10. ¿Semáforo 🟢? ¡Entonces adelante!',
    {
      titleColor: GREEN,
      notes: 'Imprimir esta checklist y usarla para CADA inversión. Si no puedes marcar al menos 7 de 10 casillas, probablemente no es buen momento para comprar. La app cubre automáticamente los puntos 2-9, pero el punto 1 (entender el negocio) es tu responsabilidad.'
    }
  );

  addSlide(
    '📋 Checklist Avanzada — Dentro de la App',
    'Lo que la app analiza automáticamente:\n\n' +
    '🔢 PESTAÑA RESUMEN:\n' +
    '   □ Scorecard (ROIC, FCF, MoS, Deuda, Calidad)\n' +
    '   □ Semáforo de inversión\n' +
    '   □ Tesis de inversión con cifras concretas\n\n' +
    '📈 PESTAÑA MÉTRICAS:\n' +
    '   □ Tabla histórica 5 años (EPS, FCF, ROIC, PER)\n' +
    '   □ Márgenes (Bruto > 40% = Moat probable)\n' +
    '   □ Deuda (Cobertura de intereses > 3x)\n' +
    '   □ SBC y Beta del valor\n\n' +
    '💎 PESTAÑA VALORACIÓN:\n' +
    '   □ Modelos usados (Graham, DCF, EPV, DDM...)\n' +
    '   □ Tabla de Sensibilidad 3×3 (WACC vs Growth)\n' +
    '   □ Reverse DCF (crecimiento implícito en precio)\n\n' +
    '🔍 PESTAÑA CUALITATIVO:\n' +
    '   □ Foso económico y ventajas competitivas\n' +
    '   □ TAM/SAM/SOM (pista de crecimiento futuro)\n' +
    '   □ Riesgos de gobernanza',
    {
      notes: 'La app organiza toda la información en 4 pestañas para no saturar al usuario. Cada una responde a una pregunta: Resumen (¿compro o no?), Métricas (¿el negocio es bueno?), Valoración (¿el precio es justo?), Cualitativo (¿hay riesgos ocultos?).'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 11: MOTOR INTERNO — CORRELACIÓN TEORÍA-APP
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '⚙️ Cómo el motor conecta la teoría con la práctica',
    'Cada concepto teórico tiene su implementación real:\n\n' +
    '📖 TEORÍA                    →  ⚙️ APP\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n' +
    'Valor Intrínseco             →  3 modelos (Graham + DCF + EPV)\n' +
    'Margen de Seguridad          →  MoS Absoluto + MoS Relativo\n' +
    'Flujo de Caja Libre          →  FCF Real (GAAP, sin SBC)\n' +
    'Ventaja Competitiva          →  ROIC histórico (Moat)\n' +
    'Riesgo contable              →  Auditoría EBITDA (cap 30%)\n' +
    'Tipo de empresa              →  5 Arquetipos automáticos\n' +
    'Riesgo del sector            →  WACC Variable (6%-12%)\n' +
    'Tamaño de la empresa         →  Prima Small/Mid/Mega Cap\n' +
    'Multidivisa (Londres, €, $)  →  Corrección GBp/GBX auto.\n' +
    'Crecimiento futuro           →  Cap inteligente por arquetipo\n' +
    'Sostenibilidad del dividendo →  Payout Ratio + DDM\n' +
    'Sentimiento del mercado      →  PEG + Rule of 40 (Growth)',
    {
      notes: 'Esta tabla es para los más curiosos. Muestra que cada concepto académico de inversión tiene una implementación concreta en el código del motor. No hay "magia": son matemáticas financieras automatizadas.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 12: WACC VARIABLE
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🎯 WACC Variable: La tasa de descuento inteligente',
    '¿Cuánto "riesgo" tiene cada tipo de empresa?\n\n' +
    '🏠 Analogía: el interés de la hipoteca\n' +
    'Un banco te cobra MENOS interés por un piso en\n' +
    'el centro de Madrid que por uno en un pueblo remoto.\n' +
    '¿Por qué? Porque el riesgo es diferente.\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    'WACC por sector (tasa base):\n' +
    '   ⚡ Utilities / Real Estate:     7.0%  (muy estable)\n' +
    '   🛒 Consumo Defensivo:           8.0%  (estable)\n' +
    '   🏥 Salud / Finanzas / Industria: 9.0%\n' +
    '   💻 Tecnología / Energía:        10.0% (más volátil)\n\n' +
    'Ajustes por tamaño:\n' +
    '   🏛️ Mega Cap (>200B):  -1.0%  (menos riesgo)\n' +
    '   📏 Mid Cap (10-50B):  +1.0%  (más riesgo)\n' +
    '   🐣 Small Cap (<10B):  +2.0%  (mucho más riesgo)',
    {
      notes: 'El WACC (Weighted Average Cost of Capital) es la tasa que usamos para traer flujos futuros al presente. A mayor WACC, menor valor intrínseco. La app lo ajusta dinámicamente por sector y tamaño. Suelo mínimo: 6%.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 13: MONETIZACIÓN Y MEJORAS FUTURAS
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🚀 Hoja de Ruta: Mejoras con Inversión',
    'Cómo la app puede crecer con recursos económicos:\n\n' +
    '━━━ 💰 NIVEL 1: Datos Premium (~$50-100/mes) ━━━\n\n' +
    '📊 Yahoo Finance Premium API ($49/mes):\n' +
    '   • Datos en tiempo real (ahora hay 15 min de delay)\n' +
    '   • Estimaciones de analistas más detalladas\n' +
    '   • Ratios históricos a 10 años (ahora 5)\n' +
    '   • Sin límite de peticiones (ahora ≈2000/hora)\n\n' +
    '📈 Financial Modeling Prep API ($29/mes):\n' +
    '   • Datos financieros de +70.000 empresas globales\n' +
    '   • Transcripciones de earnings calls\n' +
    '   • Datos de insider trading en tiempo real\n' +
    '   • Ratios ESG y scoring de gobernanza mejorado\n\n' +
    '📰 Alpha Vantage Premium ($49/mes):\n' +
    '   • Datos fundamentales de mercados emergentes\n' +
    '   • Indicadores técnicos (RSI, MACD, Bollinger)\n' +
    '   • Sentiment analysis de noticias con IA',
    {
      titleColor: ACCENT,
      notes: 'Nivel 1 es la mejora de mayor impacto/coste. Con ~$100/mes se pasa de datos gratuitos limitados a datos profesionales. El principal cuello de botella actual es el rate limiting de yfinance gratuito.'
    }
  );

  addSlide(
    '🖥️ Nivel 2: Infraestructura (~$50-200/mes)',
    '━━━ 🖥️ SERVIDORES Y RENDIMIENTO ━━━\n\n' +
    '☁️ Servidor Dedicado (DigitalOcean/AWS):\n' +
    '   Actualmente: Render Free Tier (512MB RAM, sleep)\n' +
    '   Mejora: 2GB+ RAM, siempre activo ($12-50/mes)\n' +
    '   → Escaneos 5x más rápidos (más hilos paralelos)\n' +
    '   → Sin tiempos de arranque en frío (cold start)\n\n' +
    '🗄️ Base de Datos Dedicada (PostgreSQL):\n' +
    '   Actualmente: SQLite local\n' +
    '   Mejora: PostgreSQL en la nube ($15-30/mes)\n' +
    '   → Múltiples usuarios simultáneos sin conflictos\n' +
    '   → Historial de análisis persistente y buscable\n\n' +
    '🔄 Cache Redis ($10-20/mes):\n' +
    '   → Resultados cacheados inteligentemente\n' +
    '   → Respuestas instantáneas para tickers populares\n' +
    '   → Reduce peticiones a APIs externas en un 80%\n\n' +
    '📧 Dominio + SSL + Email ($10-15/mes):\n' +
    '   → URL profesional (valueanalyst.app)\n' +
    '   → Alertas por email cuando una empresa baja al 🟢',
    {
      titleColor: ACCENT,
      notes: 'El mayor dolor actual es el cold start de Render Free Tier (30s de arranque) y la limitación de RAM. Con $50/mes se resuelve todo. Redis sería un game changer para el explorador porque cachea los análisis.'
    }
  );

  addSlide(
    '🤖 Nivel 3: Funcionalidades Premium (~$100+/mes)',
    '━━━ 🤖 INTELIGENCIA ARTIFICIAL ━━━\n\n' +
    '🧠 Gemini/GPT API para Tesis de Inversión ($20-60/mes):\n' +
    '   → Tesis narrativa generada por IA a partir de los datos\n' +
    '   → Análisis de earnings calls con NLP\n' +
    '   → Resumen ejecutivo en lenguaje natural\n\n' +
    '━━━ 📊 FUNCIONALIDADES AVANZADAS ━━━\n\n' +
    '📱 App Nativa (iOS/Android) con notificaciones push:\n' +
    '   → Alertas cuando una empresa pasa a semáforo 🟢\n' +
    '   → Widget de portfolio en la pantalla de inicio\n\n' +
    '📊 Backtesting Histórico:\n' +
    '   → "Si hubieras comprado todas las 🟢 hace 5 años...\n' +
    '      habrías ganado un X% anualizado"\n\n' +
    '🌐 Mercados Emergentes y Criptomonedas:\n' +
    '   → Bolsas de India (NSE), Brasil (B3), Corea (KOSPI)\n' +
    '   → Análisis fundamental de protocolos crypto (TVL, fees)\n\n' +
    '👥 Red Social de Inversores:\n' +
    '   → Compartir análisis y portfolios entre usuarios\n' +
    '   → Rankings y seguimiento de inversores top',
    {
      titleColor: ACCENT,
      notes: 'Nivel 3 es el salto a producto profesional. La IA para tesis narrativas sería el diferenciador principal vs competidores. El backtesting añade credibilidad científica. Los mercados emergentes abren un TAM enorme.'
    }
  );

  addSlide(
    '💸 Resumen de Inversión por Nivel',
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '┌────────────────┬───────────┬───────────────────────┐\n' +
    '│ NIVEL          │ COSTE/MES │ IMPACTO PRINCIPAL     │\n' +
    '├────────────────┼───────────┼───────────────────────┤\n' +
    '│ 1. Datos       │  $50-100  │ Datos profesionales   │\n' +
    '│    Premium     │           │ 10 años históricos    │\n' +
    '│                │           │ Sin rate limiting      │\n' +
    '├────────────────┼───────────┼───────────────────────┤\n' +
    '│ 2. Infra       │  $50-200  │ 5x más rápido         │\n' +
    '│    Servidores  │           │ Siempre activo         │\n' +
    '│                │           │ Multi-usuario real     │\n' +
    '├────────────────┼───────────┼───────────────────────┤\n' +
    '│ 3. IA y        │  $100+    │ Tesis con IA          │\n' +
    '│    Premium     │           │ App móvil nativa      │\n' +
    '│                │           │ Backtesting            │\n' +
    '└────────────────┴───────────┴───────────────────────┘\n\n' +
    '💡 Recomendación: empezar por Nivel 1 + servidor\n' +
    '   básico (~$75/mes) para máximo impacto mínimo coste.',
    {
      titleColor: ACCENT,
      notes: 'El ROI más alto es Nivel 1 (datos premium) porque mejora directamente la calidad de los análisis. El Nivel 2 mejora la experiencia. El Nivel 3 es el futuro a medio plazo.'
    }
  );

  // ═══════════════════════════════════════════════════════════════
  // BLOQUE 14: CIERRE
  // ═══════════════════════════════════════════════════════════════

  addSlide(
    '🎯 Resumen Final',
    '━━━ Lo que has aprendido hoy ━━━\n\n' +
    '1️⃣  Invertir = comprar trozos de negocios reales\n' +
    '    No es un casino. Es como comprar pisos.\n\n' +
    '2️⃣  Value = comprar barato. Growth = apostar por el futuro\n' +
    '    Ambas estrategias son válidas y la app las cubre.\n\n' +
    '3️⃣  El Margen de Seguridad es tu cinturón + airbag\n' +
    '    Nunca compres sin descuento sobre el valor real.\n\n' +
    '4️⃣  La calidad del negocio NO basta (caso Ferrari)\n' +
    '    El PRECIO que pagas determina tu rentabilidad.\n\n' +
    '5️⃣  El semáforo 🟢🟡🔴 simplifica la decisión\n' +
    '    Convergencia de dos señales independientes.\n\n' +
    '6️⃣  La app automatiza lo que un analista profesional\n' +
    '    tarda horas en hacer. Tú solo lees el resultado.',
    {
      notes: 'Cerrar con fuerza. El mensaje final: esta herramienta democratiza el análisis profesional. Antes necesitabas un Bloomberg Terminal de $24.000/año. Ahora tienes un motor de análisis gratuito y transparente.'
    }
  );

  addSlide(
    '📖 Una última cita...',
    '\n\n\n' +
    '"El precio es lo que pagas.\n' +
    ' El valor es lo que recibes."\n\n' +
    '                          — Warren Buffett\n\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n' +
    '🍊 Value Analyst\n' +
    'Tu motor de análisis fundamental\n\n' +
    '¿Preguntas?',
    {
      notes: 'Dejar esta diapositiva en pantalla durante las preguntas. Si hay tiempo, hacer una demo en vivo analizando una empresa sugerida por el público.'
    }
  );

  // ─── Aviso final ─────────────────────────────────────────────
  Logger.log('✅ Presentación generada con éxito: ' + pres.getSlides().length + ' diapositivas.');
}
