# 📚 Guía Completa de Value Investing
## Todo lo que necesitas saber para entender Value Analyst

---

## Parte 1 — La Filosofía: ¿Qué es invertir en valor?

### La idea central en una frase

> **Comprar un billete de 100€ por 70€.**

Eso es, literalmente, todo el value investing. El resto es técnica para descubrir cuánto vale realmente ese billete.

### La analogía de la casa

Imagina que quieres comprar una casa en tu barrio. Sabes que casas similares se han vendido por 200.000€. Un vecino desesperado por mudarse la pone a la venta por 140.000€.

- **200.000€** = **Valor Intrínseco** (lo que realmente vale)
- **140.000€** = **Precio de Mercado** (lo que te piden)
- **60.000€ de diferencia** = **Margen de Seguridad** (tu colchón por si te equivocas)

En la bolsa pasa exactamente lo mismo. Las empresas tienen un valor real basado en el dinero que generan, y un precio al que cotizan. A veces el precio es más bajo que el valor real → oportunidad. A veces es más alto → trampa.

### ¿Por qué funciona?

Porque el mercado es emocional a corto plazo. La gente entra en pánico y vende barato, o se emociona y compra caro. Pero a largo plazo, el precio siempre tiende a acercarse al valor real. Tu trabajo como analista es calcular ese valor real y actuar cuando haya una divergencia significativa.

---

## Parte 2 — Las Métricas Fundamentales

Estas son las "constantes vitales" de una empresa. Como cuando el médico te mide la tensión, el colesterol y la glucosa para saber si estás sano.

---

### 📊 EPS (Earnings Per Share / Beneficio por Acción)

**¿Qué es?** Cuánto dinero gana la empresa por cada acción que existe.

**Analogía de la panadería:**
Tienes una panadería que gana 100.000€ al año. Si tienes 4 socios iguales, cada uno "gana" 25.000€. El EPS es esos 25.000€ — el beneficio que corresponde a cada parte del negocio.

**Fórmula:**
```
EPS = Beneficio Neto / Número de Acciones
```

**¿Qué miro en la app?**
- **EPS TTM (Trailing Twelve Months)**: el EPS de los últimos 12 meses
- **EPS Histórico**: la media de los últimos años
- **Tendencia (↑ ↓ →)**: ¿está subiendo, bajando o estable?

**¿Buena señal?** EPS creciente año tras año. Significa que la empresa gana más dinero cada año.

**⚠️ Trampa:** Una empresa puede aumentar el EPS sin crecer realmente, simplemente recomprando acciones (menos socios = más tarta para cada uno). Por eso no nos fiamos solo del EPS.

---

### 💰 FCF Real (Free Cash Flow / Flujo de Caja Libre Real)

**¿Qué es?** El dinero **real** que queda en la caja después de pagar absolutamente todo: empleados, proveedores, impuestos, inversiones en maquinaria, Y la compensación en acciones a directivos.

**Analogía del sueldo:**
Tu sueldo bruto es 3.000€/mes. Pero pagas 600€ de impuestos, 800€ de hipoteca, 400€ de comida, 200€ de coche. Lo que te queda al final del mes para ahorrar o invertir es tu "flujo de caja libre": 1.000€. ESO es lo que realmente importa, no el sueldo bruto.

**¿Por qué "Real"?**
Nuestra app calcula un FCF más estricto que el normal:

```
FCF Real = FCF de Yahoo (OCF - CAPEX) - SBC
```

- **OCF** = Cash from Operations (dinero que entra por el negocio)
- **CAPEX** = Capital Expenditure (inversión en fábricas, maquinaria, tecnología)
- **SBC** = Stock Based Compensation (acciones que se regalan a empleados)

**¿Por qué restamos la SBC?**
Imagina que tu panadería contrata a un pastelero estrella y, en vez de pagarle 50.000€ en efectivo, le das un 5% de la empresa. En papel, tu flujo de caja no baja. Pero tu parte del negocio ya no es el 25%, sino el 23.75%. **Te han diluido**. La SBC es un coste real aunque no salga de la caja — y las empresas tecnológicas abusan de esto.

| Empresa | SBC Anual | % de FCF que se come |
|---------|-----------|---------------------|
| Meta | ~$17B | ~40% |
| Google | ~$22B | ~30% |
| Microsoft | ~$11B | ~15% |

**¿Buena señal?** FCF creciente y positivo. Si el FCF es negativo, la empresa está quemando dinero.

---

### 🏗️ ROIC (Return on Invested Capital / Retorno sobre Capital Invertido)

**¿Qué es?** Cuánto beneficio genera la empresa por cada euro que tiene invertido en el negocio. Es la métrica más importante para saber si una empresa tiene ventaja competitiva.

**Analogía de las máquinas expendedoras:**

- **Máquina A**: Inviertes 10.000€ y genera 3.000€/año de beneficio → ROIC = 30%
- **Máquina B**: Inviertes 10.000€ y genera 800€/año de beneficio → ROIC = 8%

¿Cuál prefieres? Obvio: la A. Ahora imagina que puedes reinvertir esos beneficios en más máquinas del mismo tipo. En 5 años, la Máquina A habrá multiplicado tu inversión varias veces. La B, apenas.

**Fórmula:**
```
ROIC = NOPAT / Capital Invertido × 100

Donde:
  NOPAT = EBIT × (1 - Tasa Impositiva)  →  "beneficio operativo después de impuestos"
  Capital Invertido = Patrimonio + Deuda - Efectivo  →  "todo el dinero metido en el negocio"
```

**Interpretación en la app:**

| ROIC | Significado | Ejemplo |
|------|-------------|---------|
| >20% | **Ventaja competitiva excepcional** (Wide Moat) | Apple, Google, Visa |
| 12-20% | **Ventaja competitiva moderada** (Narrow Moat) | Starbucks, Nike |
| 8-12% | **Sin ventaja clara** | Empresas genéricas |
| <8% | **Negocio mediocre** o capital-intensivo | Aerolíneas, acero |

> [!TIP]
> Warren Buffett busca empresas con ROIC > 15% sostenido durante 10+ años. Eso indica un "foso económico" (moat) que protege a la empresa de la competencia.

---

### 📈 PER (Price to Earnings Ratio / Ratio Precio-Beneficio)

**¿Qué es?** Cuántos años de beneficios actuales estás pagando por la empresa.

**Analogía directa:**
Si la panadería gana 25.000€/año y te la venden por 250.000€, estás pagando 10 años de beneficios → PER = 10.

**Fórmula:**
```
PER = Precio por Acción / EPS
```

**Interpretación:**

| PER | Significado |
|-----|-------------|
| <10 | Muy barato (¿o la empresa está en problemas?) |
| 10-20 | Valoración razonable |
| 20-35 | Caro, pero puede justificarse si crece rápido |
| >35 | Muy caro — el mercado espera un crecimiento enorme |

> [!WARNING]
> **Para empresas cíclicas (MU, acerero, petroleras), un PER bajo puede ser PELIGROSO.** Significa que los beneficios están en su pico, y cuando el ciclo baje, el PER subirá mucho. Peter Lynch decía: "Compra cíclicas cuando el PER está alto (beneficios en mínimo) y vende cuando está bajo (beneficios en máximo)."

---

### 🏭 EV/FCF (Enterprise Value / Free Cash Flow)

**¿Qué es?** Similar al PER, pero más preciso. En vez de mirar solo el precio de las acciones, mira el valor total de la empresa (incluyendo deuda) relativo al dinero que genera.

**Analogía de la casa (mejorada):**
No es lo mismo comprar una casa de 200.000€ sin hipoteca que una de 200.000€ con 150.000€ de hipoteca pendiente. El EV/FCF captura esa diferencia.

```
Enterprise Value = Market Cap + Deuda Total - Efectivo
EV/FCF = Enterprise Value / FCF
```

**Nuestra app muestra dos versiones:**
- **EV/FCF (post-SBC)**: Nuestro cálculo estricto, ajustado por dilución
- **EV/FCF (pre-SBC)**: Compatible con screeners como Yahoo Finance, Finviz, etc.

| EV/FCF | Interpretación |
|--------|---------------|
| <15 | Barato |
| 15-25 | Razonable |
| 25-40 | Caro |
| >40 | Muy caro |

---

### 📉 Tendencias (↑ ↓ → ?)

La app analiza la dirección de cada métrica:

| Símbolo | Significado | Cálculo |
|---------|-------------|---------|
| ↑ | Mejorando >5% vs media anterior | Positivo |
| → | Estable (±5%) | Neutral |
| ↓ | Deteriorándose >5% | Negativo |
| ? | Datos insuficientes | — |

---

## Parte 3 — Métodos de Valoración

Aquí está el corazón de la app: ¿cuánto vale realmente una empresa?

---

### 🏛️ Método Graham (Benjamin Graham, 1962)

**¿Para quién?** Empresas maduras, estables, con beneficios predecibles.

**La idea:** Benjamin Graham, el padre del value investing (y mentor de Warren Buffett), creó una fórmula sencilla basada en las ganancias actuales y el crecimiento esperado.

**Analogía:**
Imagina que valoras un piso de alquiler. Si genera 12.000€/año de renta y esperas que suba un 3% anual, ¿cuánto pagarías? Graham dice: multiplica la renta actual por un factor que depende del crecimiento esperado, y ajusta por los tipos de interés.

**Fórmula:**
```
Valor Intrínseco = EPS × (8.5 + 2g) × 4.4 / Y

Donde:
  EPS = Beneficio por acción actual
  g   = Tasa de crecimiento esperada (en %)
  8.5 = PER que Graham asigna a una empresa sin crecimiento
  2   = Cada punto de crecimiento vale 2x en PER
  4.4 = Rendimiento de bonos AAA en 1962 (referencia)
  Y   = Rendimiento actual de bonos AAA (4.5% hoy)
```

**Ejemplo con la panadería:**
- EPS = 5€
- Crecimiento esperado = 8%
- Valor = 5 × (8.5 + 16) × 4.4 / 4.5 = 5 × 24.5 × 0.978 = **119.8€**

**Limitaciones:**
- No funciona si el EPS es negativo (devuelve 0)
- No considera la deuda ni el efectivo
- Pensada para una época con tipos de interés muy diferentes

---

### 💵 DCF (Discounted Cash Flow / Flujo de Caja Descontado)

**¿Para quién?** Cualquier empresa con FCF positivo. Es el método más utilizado en Wall Street.

**La idea fundamental:**
> Un euro hoy vale más que un euro mañana.

Si te ofrezco 100€ hoy o 100€ dentro de un año, ¿cuál prefieres? Hoy, obviamente — puedes invertirlo y tener 110€ el año que viene. Eso significa que 100€ del año que viene "valen" solo ~91€ hoy (descontando al 10%).

**Analogía completa — La máquina de hacer dinero:**

Imagina que te venden una máquina que genera 10.000€ al año durante 10 años. ¿Cuánto pagarías por ella?

**NO pagarías 100.000€** (10.000 × 10), porque ese dinero futuro vale menos que dinero hoy. Hay que "descontarlo":

```
Año 1: 10.000 / 1.10  =  9.091€
Año 2: 10.000 / 1.21  =  8.264€
Año 3: 10.000 / 1.33  =  7.513€
...
Año 10: 10.000 / 2.59 =  3.855€
```

Sumando todo: **≈ 61.446€**. Eso es lo máximo que deberías pagar.

**Pero la máquina no se destruye en el año 10.** Sigue generando dinero para siempre (a un ritmo menor). Eso es el **Valor Terminal**:

```
Valor Terminal = FCF del año 11 / (WACC - crecimiento perpetuo)
```

**Los ingredientes del DCF:**

| Componente | Qué es | En la app |
|------------|--------|-----------|
| **FCF actual** | Dinero que genera hoy | FCF Real (post-SBC) |
| **Tasa de crecimiento** | A qué ritmo crecerá el FCF | Estimación analista o CAGR histórico |
| **WACC** | Tasa de descuento (tu "coste de oportunidad") | Variable por sector + tamaño |
| **Años proyectados** | Horizonte temporal | 10 años |
| **Crecimiento terminal** | Crecimiento perpetuo post-proyección | 2.5% (inflación + PIB) |

---

### 🚀 DCF Multi-Fase (para Compounders)

**¿Para quién?** Empresas de alta calidad que crecen rápido pero se desacelerarán gradualmente (NVDA, META, GOOG, MSFT).

**¿Por qué no usar el DCF normal?**
Porque asumir que META crecerá al 20% **para siempre** es absurdo. Pero asumir que crecerá al 2.5% desde mañana también lo es. La realidad está en medio.

**Analogía — La carrera del corredor:**
Un corredor de 25 años corre los 100m en 10 segundos. A los 35, lo hace en 11. A los 45, en 13. No para de golpe, se va desacelerando. Así crecen las empresas maduras de alta calidad.

**Las 3 fases:**

```
Fase 1 (años 1-5):   Crecimiento alto (ej: 20%)
Fase 2 (años 6-10):  Fade lineal de 20% → 2.5%
Fase 3 (año 11+):    Crecimiento perpetuo del 2.5%
```

**Ejemplo visual para META (growth = 20%, WACC = 9%):**
```
Año 1:  FCF × 1.20  → descontado
Año 2:  FCF × 1.44  → descontado
...
Año 5:  FCF × 2.49  → descontado
Año 6:  FCF × 2.49 × 1.165  → crecimiento baja a 16.5%
Año 7:  × 1.13  → baja a 13%
...
Año 10: × 1.025 → ya en crecimiento terminal
→ Valor Terminal con Gordon Growth Model
```

---

### 🔥 DCF sobre Revenue (para Hipercrecimiento)

**¿Para quién?** Empresas que aún no ganan dinero pero crecen explosivamente (startups pre-beneficio).

**¿Por qué?** Si la empresa no tiene beneficios, no puedes usar Graham ni DCF normal. Pero sí puedes proyectar sus ingresos y asumir que eventualmente alcanzará un margen de beneficio objetivo.

**Analogía — El restaurante nuevo:**
Abres un restaurante. El primer año facturas 200.000€ pero pierdes 50.000€ (local, decoración, publicidad). El segundo año facturas 400.000€ y empatas. El tercero facturas 600.000€ y ganas 90.000€. 

Un inversor no mira tus pérdidas actuales — mira el crecimiento de tu facturación y asume que eventualmente serás rentable.

**El modelo:**
```
1. Proyecta los ingresos (desacelerando el crecimiento año a año)
2. Ramp de margen: de 0% → margen objetivo del sector (ej: 25% para software)
3. FCF futuro = Ingresos × Margen
4. Descuenta todo al presente
```

---

### 🏦 Valoración por Book Value (para Financieros)

**¿Para quién?** Bancos, aseguradoras, gestoras de activos.

**¿Por qué un método diferente?** Los bancos son raros. Su "producto" es dinero — prestan dinero que no es suyo (depósitos). El FCF de un banco no significa lo mismo que el de una empresa normal. Por eso usamos el **Valor en Libros** (lo que la empresa posee menos lo que debe).

**Analogía:**
Imagina que un amigo tiene una cartera de inversiones con acciones, bonos y propiedades por valor de 500.000€. Te ofrece vendértela por 400.000€. Estás comprando 1€ de activos por 0.80€ → P/B = 0.8 → buena oferta.

**Fórmula del P/B Justificado:**
```
P/B Justificado = (ROE - g) / (CoE - g)

Donde:
  ROE = Return on Equity (rentabilidad sobre patrimonio)
  g   = Crecimiento sostenible (ROE × ratio de retención)
  CoE = Coste del equity (lo que exiges como inversor, ~WACC)
```

Si el ROE es alto (el banco es rentable), merece cotizar por encima de su valor en libros. Si es bajo, debería cotizar por debajo.

---

### 🏠 DDM — Dividend Discount Model (para REITs y Utilities)

**¿Para quién?** Empresas que reparten casi todo su beneficio en dividendos: REITs inmobiliarios, eléctricas, gasistas.

**¿Por qué?** Estas empresas no retienen beneficios para crecer — los reparten. Tu retorno como inversor viene principalmente del dividendo, no de la revalorización.

**Analogía — El piso de alquiler:**
Compras un piso que genera 12.000€/año de alquiler. Esperas que el alquiler suba un 2% anual. Si exiges un 8% de rentabilidad, ¿cuánto pagarías?

```
Valor = Alquiler del próximo año / (Rentabilidad exigida - Crecimiento del alquiler)
Valor = (12.000 × 1.02) / (0.08 - 0.02) = 12.240 / 0.06 = 204.000€
```

**Fórmula (Gordon Growth Model):**
```
V = D₁ / (r - g)

Donde:
  D₁ = Dividendo del próximo año
  r  = Tasa de descuento (WACC)
  g  = Crecimiento esperado del dividendo
```

> [!CAUTION]
> Si `g ≥ r` (el dividendo crece más rápido que tu tasa de descuento), la fórmula explota → el valor sería infinito. Eso no tiene sentido, así que la app devuelve 0 en ese caso.

---

### ⚡ EPV — Earnings Power Value (Fallback para empresas capital-intensivas)

**¿Para quién?** Empresas con mucho CAPEX donde el FCF no refleja la capacidad real de generar beneficios (ej: Micron, empresas que construyen fábricas enormes).

**El problema que resuelve:**
Micron genera $8.5B en beneficios netos, pero su FCF es solo $696M porque invierte $16B en fábricas. El DCF con $696M dice que MU vale $52/acción cuando cotiza a $923. Claramente, el DCF está roto para este tipo de empresa.

**Analogía — La pizzería que abre otro local:**
Tu pizzería gana 100.000€/año. Este año gastas 200.000€ en abrir un segundo local. Tu "flujo de caja libre" este año es -100.000€. ¿Significa que la pizzería no vale nada? ¡No! Significa que estás invirtiendo en crecer. El EPV mira la capacidad de generar beneficios, ignorando las inversiones puntuales de crecimiento.

**Fórmula simplificada:**
```
EPV = Beneficio Neto Normalizado / WACC + Efectivo - Deuda

Donde "normalizado" = media de los años con beneficios positivos
```

---

## Parte 4 — El Sistema de Arquetipos

No todas las empresas son iguales, y no se pueden valorar igual. Nuestra app clasifica automáticamente cada empresa en uno de 6 "arquetipos" y aplica el método de valoración más adecuado.

---

### 🚀 Compounder
**Ejemplos:** NVDA, META, GOOG, MSFT, AVGO, LULU

**¿Cómo se detecta?**
- EPS positivo Y
- ROIC promedio > 20% (automático) O
- ROIC > 15% + Crecimiento > 10%

**Método de valoración:** DCF Multi-Fase

**¿Por qué?** Son las "máquinas de hacer dinero" que reinvierten sus beneficios a tasas altísimas. Un euro reinvertido por Google genera más que un euro reinvertido por una eléctrica. El DCF Multi-Fase captura esta ventaja con un periodo de alto crecimiento seguido de una desaceleración natural.

**Analogía:** Un atleta de élite en su mejor momento. Rinde mucho ahora, pero eventualmente se desacelerará. No se retirará mañana, pero tampoco correrá así para siempre.

---

### 🏛️ Value Clásico
**Ejemplos:** MU, empresas maduras con ROIC moderado

**¿Cómo se detecta?**
- EPS positivo pero ROIC < 15%
- No es financiero, ni REIT, ni hipercrecimiento

**Método de valoración:** Graham + DCF estándar + EPV (si aplica)

**¿Por qué?** Son empresas "normales" sin ventaja competitiva excepcional. Graham funciona bien porque su fórmula fue diseñada para este tipo de empresa. El DCF estándar (sin fases) es apropiado porque no hay razón para asumir un crecimiento extraordinario.

**Analogía:** Un trabajador estable con un empleo decente. Gana bien, pero no esperas que su sueldo se duplique.

---

### 🏦 Financiero
**Ejemplos:** JPMorgan, Visa, PayPal, Berkshire Hathaway

**¿Cómo se detecta?**
- Sector = "Financial Services"

**Método de valoración:** P/Book Justificado + DCF secundario

**¿Por qué?** El FCF de un banco no es comparable con el de una empresa normal. Los bancos "fabrican dinero" — prestan los depósitos de sus clientes. El valor en libros y el ROE son las métricas que realmente importan.

---

### 🏠 REIT / Utility
**Ejemplos:** REITs inmobiliarios, Iberdrola, empresas eléctricas

**¿Cómo se detecta?**
- Sector = "Real Estate" o "Utilities"

**Método de valoración:** DDM (Dividendos) + DCF secundario

**¿Por qué?** Estas empresas están obligadas (REITs) o acostumbran (utilities) a repartir la mayoría de sus beneficios. El dividendo ES tu retorno.

---

### 🔥 Hipercrecimiento
**Ejemplos:** Empresas pre-beneficio con alto crecimiento de ingresos

**¿Cómo se detecta?**
- EPS ≤ 0 + Crecimiento de ingresos > 15%, O
- EPS > 0 pero crecimiento > 25% y revenue growth > 20% con ROIC ≤ 20%

**Método de valoración:** DCF sobre Revenue

**¿Por qué?** Sin beneficios, no hay EPS ni FCF que valorar. Solo se puede proyectar la facturación y asumir que algún día será rentable.

**Analogía:** Una startup que quema dinero pero crece al 100% anual. No gana dinero hoy, pero si captura suficiente mercado, los beneficios llegarán.

---

### ⚠️ Especulativo
**Ejemplos:** Empresas sin beneficios y sin crecimiento de ingresos fuerte

**¿Cómo se detecta?**
- EPS ≤ 0 + Crecimiento de ingresos ≤ 15%

**Método de valoración:** DCF tentativo (si FCF > 0) o ninguno

**¿Por qué?** No hay base fiable para valorar. La app te advierte que estás especulando.

---

## Parte 5 — WACC, Beta, y el Precio del Riesgo

Esta sección es clave. El WACC es el número más sensible de toda la app — cambiarlo un 1% puede mover el valor intrínseco un 20%.

---

### 🎲 Beta (Coeficiente Beta)

**¿Qué es?** Mide cuánto se mueve una acción cuando el mercado sube o baja. Es una medida de **riesgo** relativo al mercado.

**Analogía — Los barcos en una tormenta:**

Imagina que el mar (el mercado) tiene olas de 2 metros.

| Barco | Comportamiento | Beta |
|-------|---------------|------|
| **Petrolero grande** | Se mueve 1 metro (menos que las olas) | β = 0.5 |
| **Velero mediano** | Se mueve 2 metros (igual que las olas) | β = 1.0 |
| **Lancha rápida** | Se mueve 4 metros (el doble que las olas) | β = 2.0 |

**Interpretación práctica:**

| Beta | Significado | Ejemplo |
|------|-------------|---------|
| **β < 0.8** | Defensiva — menos volátil que el mercado | Utilities, Consumer Staples (Coca-Cola, Procter & Gamble) |
| **β ≈ 1.0** | Se mueve igual que el mercado | Empresas grandes y diversificadas (S&P 500) |
| **β = 1.0–1.5** | Más volátil que el mercado | Tech maduro (Apple, Google) |
| **β > 1.5** | Muy volátil — sube más cuando todo sube, cae más cuando todo cae | Startups, cíclicas, criptomonedas |
| **β < 0** | Se mueve al revés del mercado | Oro, algunos hedge funds (muy raro) |

**¿Cómo se calcula?**
Yahoo Finance calcula Beta automáticamente comparando los retornos mensuales de la acción vs el S&P 500 durante los últimos 5 años.

```
Beta = Covarianza(acción, mercado) / Varianza(mercado)
```

No necesitas calcular esto — la app lo obtiene directamente de Yahoo.

**¿Para qué lo usa la app?**
Beta aparece en la ficha de cada empresa como indicador de riesgo. En el WACC académico completo, Beta determina cuánta "prima de riesgo" exigirle a esa acción. En nuestra app, el WACC se calcula por sector y tamaño (que es una simplificación práctica), pero Beta te da contexto adicional para tu decisión.

**Ejemplo real:**
- **NVDA β = 1.64** → Si el mercado cae un 10%, espera que NVDA caiga ~16%. Si sube un 10%, NVDA sube ~16%.
- **JNJ β = 0.52** → Si el mercado cae un 10%, JNJ solo cae ~5%. Más tranquilo para dormir.

> [!TIP]
> Beta NO mide si una empresa es buena o mala. Solo mide cuánto se mueve. Una empresa con β = 2.0 puede ser excelente — simplemente necesitas estómago para la volatilidad.

---

### 📐 WACC (Weighted Average Cost of Capital / Coste Medio Ponderado del Capital)

**¿Qué es?** La tasa de descuento que usamos en el DCF. Representa el **retorno mínimo** que debes exigir para que invertir en esta empresa tenga sentido frente a alternativas más seguras.

**Analogía — El umbral de rentabilidad del inversor inmobiliario:**

Si tienes 100.000€ y puedes:
- Meterlos en un depósito bancario al 4% → 4.000€/año seguro
- Comprar bonos del gobierno al 5% → 5.000€/año casi seguro
- Invertir en un piso de alquiler → ¿cuánto exiges?

Como el piso tiene riesgo (el inquilino puede no pagar, puede haber averías, el precio puede bajar), exiges al menos un **8-10%**. Si el piso solo rinde 5%, mejor los bonos. Ese 8-10% es tu WACC para inversión inmobiliaria.

En acciones es igual. Cada empresa tiene un "precio de riesgo" diferente.

#### La fórmula académica completa (CAPM)

```
WACC = E/(E+D) × CoE + D/(E+D) × CoD × (1-t)

Donde:
  E = Valor de mercado del equity (Market Cap)
  D = Valor de la deuda
  CoE = Coste del equity = Rf + β × (Rm - Rf)
    Rf  = Tasa libre de riesgo (bono USA 10 años ≈ 4.2%)
    β   = Beta de la acción
    Rm  = Retorno esperado del mercado (≈ 10% histórico del S&P 500)
    (Rm - Rf) = Prima de riesgo del mercado (≈ 5.8%)
  CoD = Coste de la deuda (interés medio que paga)
  t   = Tasa impositiva
```

**Ejemplo para NVDA:**
```
CoE = 4.2% + 1.64 × 5.8% = 4.2% + 9.5% = 13.7%
```

#### ¿Cómo lo calcula NUESTRA app? (Simplificación práctica)

En vez de usar la fórmula CAPM completa (que requiere muchos datos y asunciones frágiles), usamos un método basado en **sector + tamaño**, que en la práctica es igual de efectivo:

**Paso 1 — WACC base por sector:**

| Sector | WACC Base | ¿Por qué? |
|--------|-----------|-----------|
| Utilities / Real Estate | 7% | Flujos estables y predecibles |
| Consumer Defensive | 8% | Coca-Cola se vende en crisis y bonanza |
| Healthcare / Financial / Industrial | 9% | Riesgo medio |
| Technology / Energy / Consumer Cyclical | 10% | Más volátiles, beneficios menos predecibles |

**Paso 2 — Ajuste por tamaño (Market Cap):**

| Market Cap | Ajuste | Razón |
|------------|--------|-------|
| > $200B (Mega Cap) | -1% | Microsoft no va a quebrar mañana |
| $10B–$200B (Large Cap) | ±0% | Sin ajuste |
| $2B–$10B (Mid Cap) | +1% | Más vulnerables a competencia |
| < $2B (Small Cap) | +2% | Alto riesgo de supervivencia |

**Paso 3 — Mínimo: 6%** (nunca bajamos del 6%, incluso para la utility más estable).

**Ejemplo:** NVDA (Technology, Market Cap > $200B)
```
WACC = 10% (tech) - 1% (mega cap) = 9%
```

> [!IMPORTANT]
> **¿Por qué una diferencia del 1% importa tanto?** Porque el Valor Terminal (que suele ser el 60-70% del DCF) usa la fórmula `FCF / (WACC - g)`. Si WACC = 10% y g = 2.5%, el denominador es 7.5%. Si WACC baja a 9%, el denominador es 6.5% → ¡el Valor Terminal sube un 15%! Por eso la tabla de sensibilidad es tan importante.

---

### 📦 EBITDA (Earnings Before Interest, Taxes, Depreciation & Amortization)

**¿Qué es?** El beneficio operativo ANTES de descontar intereses de la deuda, impuestos, y la depreciación de activos. Es una proxy del flujo de caja operativo "puro".

**Analogía — La panadería con un horno financiado:**

Tu panadería vende 300.000€ en pan. Gastas 150.000€ en ingredientes y personal. Tu EBITDA es 150.000€. Pero luego:
- Pagas 20.000€ de intereses por el préstamo del horno → EBIT = 130.000€
- Apuntas 15.000€ de depreciación del horno (pierde valor cada año) → Ya estaba en EBIT
- Pagas 30.000€ de impuestos → Beneficio Neto = 100.000€

```
EBITDA = Ingresos - Costes Operativos (sin intereses, impuestos, ni depreciación)
       = 150.000€

EBIT   = EBITDA - Depreciación & Amortización
       = 150.000 - 15.000 = 135.000€

Beneficio Neto = EBIT - Intereses - Impuestos
               = 135.000 - 20.000 - 30.000 = 85.000€
```

**¿Para qué lo usa la app?**
- **Detección Non-GAAP**: Compara EBITDA reportado vs calculado
- **Ratio Net Debt/EBITDA**: ¿Cuántos años de EBITDA necesita la empresa para pagar toda su deuda?

---

### 🔧 CAPEX (Capital Expenditure / Inversiones de Capital)

**¿Qué es?** El dinero que la empresa gasta en comprar o mejorar activos físicos: fábricas, maquinaria, edificios, equipos informáticos.

**Analogía:**
Tu taxista te dice que gana 50.000€/año. Pero cada 5 años necesita comprar un coche nuevo por 30.000€. Su CAPEX anual "normalizado" es 6.000€/año. Su verdadera capacidad de generar dinero es 44.000€/año.

```
FCF = Operating Cash Flow - CAPEX
```

**¿Por qué importa?**
Empresas como Micron ($16B en CAPEX) o Intel gastan cantidades enormes en fábricas. Su FCF es muy bajo, pero no porque el negocio sea malo — sino porque están invirtiendo en capacidad futura. Por eso creamos el modelo EPV como alternativa.

| Tipo empresa | CAPEX/Ingresos | Ejemplo |
|-------------|---------------|---------|
| Software (bajo CAPEX) | 3-8% | Microsoft, Google |
| Consumer | 5-10% | Coca-Cola, Nike |
| Semiconductores | 25-40% | Micron, Intel, TSMC |
| Oil & Gas | 15-30% | ExxonMobil, Chevron |

---

### 🔬 NOPAT (Net Operating Profit After Tax)

**¿Qué es?** El beneficio que genera el negocio puro, después de impuestos, pero ANTES de considerar cómo está financiado (deuda vs equity).

```
NOPAT = EBIT × (1 - Tasa Impositiva)
```

**Analogía:** Imagina dos panaderías idénticas. Una está financiada con deuda (paga intereses), la otra con capital propio (no paga intereses). El NOPAT es igual para ambas porque ignora la financiación. Es la "potencia del motor" independiente de cómo se compró el coche.

**¿Para qué lo usa la app?** Es el numerador del ROIC. Al ignorar la financiación, puedes comparar la eficiencia operativa de empresas con estructuras de deuda muy diferentes.

---

## Parte 5B — Análisis de Márgenes

Los márgenes te dicen qué porcentaje de cada euro de ventas se convierte en beneficio. Es como medir la eficiencia de una fábrica.

---

### 📊 Margen Bruto (Gross Margin)

```
Margen Bruto = (Ingresos - Coste de Ventas) / Ingresos × 100
```

**Analogía:** Vendes limonada a 3€ el vaso. Los limones, azúcar y vasos cuestan 1€. Tu margen bruto es 66%. Este margen NO incluye el alquiler del puesto, tu sueldo, ni publicidad — solo el coste directo del producto.

| Margen Bruto | Tipo de negocio |
|-------------|-----------------|
| >70% | Software, Lujo (Hermès, Adobe) |
| 50-70% | Tech hardware, Farma (Apple, Pfizer) |
| 30-50% | Retail, Industria (Nike, Starbucks) |
| 10-30% | Commodities, Supermercados (Walmart) |
| <10% | Distribución, Low-cost |

> [!TIP]
> Un margen bruto alto = **poder de fijación de precios**. La empresa puede subir precios sin perder clientes. Eso es una señal de moat.

---

### 📊 Margen Operativo (Operating Margin)

```
Margen Operativo = EBIT / Ingresos × 100
```

Es el margen bruto MENOS todos los gastos operativos (salarios, alquiler, I+D, marketing). Mide la eficiencia total del negocio.

**Analogía:** De los 2€ de margen bruto por limonada, pagas 0.50€ de alquiler del puesto y 0.50€ de publicidad. Tu margen operativo es 1€/3€ = 33%.

---

### 📊 Margen Neto (Net Margin)

```
Margen Neto = Beneficio Neto / Ingresos × 100
```

Después de ABSOLUTAMENTE todo: impuestos, intereses, gastos extraordinarios. Es el "bottom line" — lo que queda de verdad.

**¿Por qué miro los tres?**
Juntos cuentan una historia:
- **Margen bruto estable + operativo cayendo** = La empresa gasta demasiado (hinchando plantilla, malas inversiones)
- **Margen bruto cayendo** = Pierde poder de precios (competencia erosionando el moat)
- **Margen neto cayendo con operativo estable** = Problemas de deuda (pagando más intereses)

---

## Parte 5C — Análisis de Deuda

¿Puede la empresa pagar sus deudas? Estas métricas te lo dicen.

---

### 🏦 Net Debt / EBITDA (Deuda Neta sobre EBITDA)

```
Deuda Neta = Deuda Total - Efectivo en Caja
Net Debt / EBITDA = Deuda Neta / EBITDA
```

**Analogía directa:** Si ganas 50.000€/año y debes 100.000€ (descontando tus ahorros), tu ratio es 2.0x. Necesitas 2 años de ingresos brutos para pagar la deuda. ¿Es manejable? Sí. ¿Y si debieras 400.000€ (8x)? Muy peligroso.

| Ratio | Interpretación |
|-------|---------------|
| < 1x | Deuda muy baja — podría pagar en menos de 1 año |
| 1–3x | Deuda razonable — zona de confort |
| 3–5x | Deuda elevada — vigilar |
| > 5x | Deuda peligrosa — riesgo de insolvencia |
| Negativo | La empresa tiene MÁS efectivo que deuda (Apple, Google) |

---

### 🛡️ Interest Coverage (Cobertura de Intereses)

```
Interest Coverage = EBIT / Gastos por Intereses
```

**Analogía:** Si cobras 4.000€/mes y tu cuota de hipoteca es 800€/mes, tu cobertura es 5x. Si es 3.500€/mes, tu cobertura es solo 1.14x — cualquier imprevisto te lleva a impago.

| Cobertura | Interpretación |
|-----------|---------------|
| > 10x | Excelente — la deuda no es problema |
| 5–10x | Cómoda |
| 3–5x | Ajusta — vulnerable a caídas de beneficios |
| < 3x | Peligro — una recesión podría causar default |
| 999 | Sin deuda (no paga intereses) |

---

## Parte 5D — Métricas de Dividendos

---

### 💸 Dividend Yield (Rentabilidad por Dividendo)

```
Dividend Yield = Dividendo Anual por Acción / Precio de la Acción × 100
```

**Analogía:** Compras un piso de 200.000€ y cobras 8.000€/año de alquiler → Yield = 4%.

| Yield | Interpretación |
|-------|---------------|
| 0% | No paga dividendo (reinvierte todo: Amazon, Google históricamente) |
| 1-2% | Dividendo simbólico (Apple, Microsoft) |
| 2-4% | Dividendo atractivo (Coca-Cola, P&G) |
| 4-6% | Alto dividendo (REITs, Utilities) |
| > 8% | **¡Trampa!** Probablemente el dividendo es insostenible o los datos son erróneos |

> [!WARNING]
> Nuestra app marca como "no fiable" cualquier dividend yield > 20%. Yahoo Finance a menudo reporta yields absurdos para ADRs (ej: "META 33%") por errores de conversión de moneda. Si ves un yield sospechoso, la app lo excluye de sus cálculos automáticamente.

---

### 📤 Payout Ratio (Ratio de Distribución)

```
Payout Ratio = Dividendos Totales / Beneficio Neto × 100
```

**Analogía:** Si ganas 100.000€ y regalas 30.000€ a tu familia, tu payout ratio es 30%. Te queda 70% para reinvertir o ahorrar.

| Payout | Interpretación |
|--------|---------------|
| 0-30% | Conservador — mucho margen para subir el dividendo |
| 30-60% | Equilibrado — estándar para blue chips |
| 60-80% | Alto — poco margen para crecer |
| > 80% | Peligroso — ¿puede mantener el dividendo si bajan los beneficios? |
| > 100% | 🚨 Insostenible — está pagando más de lo que gana |

---

## Parte 5E — Market Cap (Capitalización de Mercado) y su impacto

```
Market Cap = Precio por Acción × Número de Acciones
```

Es el "precio total" de la empresa en bolsa. La app lo usa para ajustar el WACC.

| Categoría | Market Cap | Ejemplo | Ajuste WACC |
|-----------|-----------|---------|-------------|
| **Mega Cap** | > $200B | Apple, NVDA, MSFT | -1% (muy seguras) |
| **Large Cap** | $10B–$200B | Starbucks, Nike | ±0% |
| **Mid Cap** | $2B–$10B | Medianas cotizadas | +1% |
| **Small Cap** | < $2B | Empresas pequeñas | +2% (más riesgo) |

**Analogía:** Prestar 1.000€ a un amigo millonario (mega cap) es menos arriesgado que prestárselos a un emprendedor sin historial (small cap). Exiges más interés al segundo.

---

## Parte 5F — ADRs y el Multiplicador de Moneda

### ¿Qué es un ADR?

Un **ADR** (American Depositary Receipt) permite que acciones de empresas extranjeras se negocien en bolsas americanas en dólares.

**Analogía:** Es como un "envoltorio" americano para una acción extranjera. Compras TSM (Taiwan Semiconductor) en el NYSE en dólares, pero la empresa reporta en dólares taiwaneses (TWD).

### El problema de las dos monedas

- **Precio de trading:** En dólares (ej: TSM $195)
- **Estados financieros:** En moneda local (ej: TWD — los FCFs, EPS, deuda están en TWD)
- **Ratio ADR:** 1 ADR puede representar varias acciones ordinarias (ej: 1 TSM ADR = 5 acciones taiwanesas)

### El multiplicador

La app calcula un **multiplicador** que convierte entre ambos mundos:

```
Multiplicador = EPS en moneda financiera / EPS en moneda de trading
```

Para TSM: `Multiplicador ≈ 6` (combina el tipo de cambio USD/TWD + el ratio ADR de 5:1)

Todos los valores del DCF se calculan en moneda financiera y se dividen por el multiplicador para dar el resultado en la moneda de trading (dólares).

**¿Cómo te afecta?** Si el TWD se devalúa frente al dólar, el valor intrínseco en USD bajará, incluso si la empresa va bien. Es un riesgo de divisa.

---

## Parte 5G — Sector Benchmarking (Comparación Sectorial)

La app compara las métricas de cada empresa contra las medianas de su sector:

| Sector | PER Medio | ROIC Medio | Margen Bruto |
|--------|-----------|-----------|-------------|
| Technology | 25x | 15% | 50% |
| Healthcare | 20x | 12% | 55% |
| Consumer Defensive | 18x | 10% | 40% |
| Financial Services | 12x | 8% | — |
| Energy | 10x | 8% | 35% |

**¿Por qué importa?**
No puedes comparar el PER de una tech (25x) con el de una petrolera (10x). Son mundos diferentes. Un PER de 15x puede ser barato para tech pero caro para energía.

La app genera una **evaluación sectorial** automática:
- "El ROIC de NVDA (45%) **supera** la media sectorial de Technology (15%)"
- "El PER de NVDA (35x) cotiza **con prima** frente a la media de Technology (25x)"

---

## Parte 6 — Margen de Seguridad (MoS)

### El concepto más importante del value investing

> **Nunca compres sin colchón.**

Incluso si calculas que una empresa vale 100€, NO la compres a 100€. ¿Y si te equivocaste? ¿Y si hay una crisis? Compra a 70-80€ para tener un "colchón" por si las cosas van peor de lo esperado.

### Los dos márgenes de la app

#### MoS Absoluto (ms_absoluto)
```
MoS = (Valor Intrínseco - Precio) / Valor Intrínseco × 100
```
- **Positivo (+30%):** El precio está un 30% por debajo del valor real → oportunidad
- **Negativo (-20%):** El precio está un 20% por encima → sobrevalorada

#### MoS Relativo (ms_relativo)
Compara el múltiplo actual (PER o EV/FCF) con su media de los últimos 5 años.

```
MoS Relativo = (Múltiplo Medio 5 Años - Múltiplo Actual) / Múltiplo Medio 5 Años × 100
```

**Analogía:**
- **MoS Absoluto** = "¿Esta casa vale más o menos de lo que me piden?"
- **MoS Relativo** = "¿El precio actual de casas en este barrio es más alto o más bajo que su media histórica?"

Ambos importan. Puedes comprar una buena casa a un precio justo, pero si históricamente las casas en ese barrio suelen estar más baratas, quizás debas esperar.

---

## Parte 7 — Tasa de Crecimiento (Growth Rate)

### ¿De dónde sale el crecimiento que usamos?

La app sigue este orden de prioridad:

```
1. Estimación de analistas de Yahoo (si existe y es ≤ 100%)
2. CAGR histórico del EPS (si hay datos suficientes)
3. Default conservador: 5%
```

### Protecciones aplicadas

| Protección | Qué hace | Ejemplo |
|-----------|---------|---------|
| **Filtro >100%** | Si Yahoo dice 756% (MU), lo descarta | MU: 756% → usa EPS CAGR |
| **Haircut** | Si EPS crece >1.5× que Revenue, recorta | Evita confundir buybacks con crecimiento real |
| **Growth Cap** | Límite máximo por arquetipo | Compounder max 20%, Value max 15% |
| **Normalización cíclica** | Si FCF muy volátil, usa growth 3% | Para cíclicas con FCF normalizado |

### ¿Por qué hay un Growth Cap?

**Analogía del árbol:**
Un árbol joven crece un metro al año. ¿Crecerá un metro al año PARA SIEMPRE? No — a los 20 años, crecerá 10cm/año. A los 50, apenas crece.

Las empresas son iguales. Nadie crece al 30% para siempre. El growth cap evita que el DCF se "emocione" con tasas de crecimiento imposibles a largo plazo.

---

## Parte 8 — Métricas de Crecimiento (Growth Investing)

Para empresas de crecimiento, la app calcula métricas adicionales:

### PEG Ratio (Peter Lynch)

```
PEG = PER / Tasa de Crecimiento del EPS (en %)
```

**Analogía:** Si pagas PER 30 por una empresa que crece 30% anual, PEG = 1 → precio justo. Si crece 15%, PEG = 2 → caro.

| PEG | Interpretación |
|-----|---------------|
| <1.0 | Infravalorada para su crecimiento |
| 1.0-2.0 | Precio justo |
| >2.0 | Sobrevalorada |

### Rule of 40 (para SaaS/Tech)

```
Rule of 40 = Crecimiento de Ingresos (%) + Margen FCF (%)
```

**La idea:** Una empresa tech sana debe sumar al menos 40 entre su crecimiento y su rentabilidad. Si crece 30% con 10% de margen = 40 ✅. Si crece 10% con 5% de margen = 15 ❌.

---

## Parte 9 — Detección Non-GAAP

### ¿Qué es Non-GAAP?

**GAAP** = Generally Accepted Accounting Principles (las normas contables oficiales). Algunas empresas reportan resultados "ajustados" (Non-GAAP) donde eliminan gastos que no les gustan: reestructuraciones, amortizaciones, compensación en acciones...

**Analogía:**
Imagina que un restaurante dice "gano 100.000€/año" pero ha excluido el alquiler del local (50.000€) porque "es un gasto no recurrente" (aunque lo paga cada mes). Sus números pintarán mejor, pero son engañosos.

### Cómo lo detecta la app

```
Divergencia = |EBITDA Reportado - (EBIT + D&A)| / (EBIT + D&A)
```

| Divergencia | Señal |
|------------|-------|
| <15% | ✅ OK |
| 15-30% | ⚠️ Precaución |
| >30% | 🚫 No Elegible |

---

## Parte 10 — Calidad del Negocio

La app combina varias señales para dar una nota de calidad:

| Factor | Puntos | Lo que mide |
|--------|--------|------------|
| ROIC > 20% | +3 | Ventaja competitiva excepcional |
| ROIC > 15% | +2 | Ventaja competitiva moderada |
| ROIC > 10% | +1 | Rentabilidad aceptable |
| FCF tendencia ↑ | +2 | Generación de caja mejorando |
| EPS tendencia ↑ | +2 | Beneficios crecientes |
| MoS > 30% | +2 | Gran descuento sobre valor real |
| MoS > 20% | +1 | Descuento razonable |

| Puntuación | Calidad |
|------------|---------|
| ≥7 | ⭐ Alta Calidad |
| 4-6 | ✅ Calidad Aceptable |
| 2-3 | ⚠️ Calidad Media |
| 0-1 | ❌ Calidad Baja |

---

## Parte 11 — El Semáforo (Sistema de Alertas)

El semáforo combina todo lo anterior para darte una señal clara:

### Para Value + Book Value + Dividendos:
| Señal | Condición |
|-------|----------|
| 🟢 **STRONG BUY** | MoS Absoluto > 15% Y MoS Relativo > 10% |
| 🟢 **COMPRA DE CALIDAD** | MoS > 0% Y Relativo > 0% Y ROIC > 18% + Buybacks o Insider |
| 🟡 **MANTENER** | Cualquier otra situación |
| 🔴 **SOBREVALORADA** | MoS Absoluto < 0% Y MoS Relativo < 0% |
| 🚫 **NO ELEGIBLE** | Non-GAAP > 30% |

### Para Growth:
| Señal | Condición |
|-------|----------|
| 🟢 **GROWTH BUY** | PEG < 1.5 Y Rule of 40 ≥ 40 |
| 🟡 **GROWTH HOLD** | Intermedio |
| 🔴 **GROWTH OVERPRICED** | PEG > 2.5 O Rule of 40 < 20 |

### Para Especulativo:
| Señal | Condición |
|-------|----------|
| ⚠️ **ALTO RIESGO** | Siempre (por definición) |

---

## Parte 12 — El Reverse DCF (DCF Inverso)

### La pregunta más inteligente que puedes hacer

En vez de preguntar "¿cuánto vale esta empresa?", el Reverse DCF pregunta:

> **"¿Qué tasa de crecimiento necesita esta empresa para justificar su precio actual?"**

**Analogía:**
Te ofrecen un piso por 300.000€ que genera 15.000€/año de alquiler. El Reverse DCF calcula: "Para que me salga rentable a la tasa que exijo (10%), este alquiler tendría que crecer un 7% anual durante 10 años. ¿Es eso realista?"

Si el crecimiento implícito es 5% y la empresa ha crecido un 20% históricamente → el mercado está siendo pesimista → posible oportunidad.

Si el crecimiento implícito es 35% y la empresa crece al 10% → el mercado es demasiado optimista → posible trampa.

---

## Parte 13 — La Tabla de Sensibilidad

### ¿Y si me equivoco?

Nadie sabe el futuro con certeza. La tabla de sensibilidad muestra cómo varía el valor intrínseco bajo 9 escenarios diferentes:

```
              Crecimiento
              Bajo    Base    Alto
WACC Alto  [  $X   |  $X   |  $X  ]  ← escenario pesimista
WACC Base  [  $X   |  $X   |  $X  ]  ← caso base
WACC Bajo  [  $X   |  $X   |  $X  ]  ← escenario optimista
```

**¿Cómo usarla?**
- Si el precio actual está por debajo de TODOS los 9 escenarios → muy infravalorada
- Si está por encima de todos → muy sobrevalorada
- Si está en medio → depende de tu convicción

---

## Parte 14 — La Auditoría Cualitativa

Más allá de los números, la app analiza aspectos cualitativos:

### 🏰 Foso Económico (Economic Moat)
Basado en el ROIC: ¿tiene la empresa una ventaja competitiva duradera?

| ROIC | Foso |
|------|------|
| >18% | Wide Moat (Amplio) |
| 12-18% | Narrow Moat (Estrecho) |
| <12% | No Moat |

### 👔 Auditoría de Gestión
- **Skin in the Game**: ¿Los directivos poseen acciones? (alineación de intereses)
- **Recompra de acciones**: ¿Están reduciendo acciones en circulación? (bueno para ti)
- **Nivel de deuda**: Ratio Deuda/Patrimonio, ¿es sostenible?

### 📊 TAM/SAM/SOM (Tamaño del Mercado)
- **TAM**: Total Addressable Market (mercado total)
- **Market Share**: ¿Qué porcentaje del mercado tiene?
- Si tiene <2% del TAM con alto ROIC → "Joya de crecimiento en potencia"

---

## Resumen Final: El Checklist del Analista

Antes de invertir, verifica:

```
1. ☐ ¿Es un negocio de calidad? (ROIC > 15%, FCF ↑)
2. ☐ ¿Entiendo el negocio y su sector?
3. ☐ ¿Tiene ventaja competitiva? (Foso económico)
4. ☐ ¿Los números son de fiar? (Non-GAAP ✅ OK)
5. ☐ ¿Hay margen de seguridad? (MoS > 20%)
6. ☐ ¿El múltiplo actual es razonable vs su historia? (MoS Relativo > 0)
7. ☐ ¿El crecimiento implícito es realista? (Reverse DCF)
8. ☐ ¿El peor escenario de la tabla de sensibilidad me deja tranquilo?
9. ☐ ¿La directiva está alineada conmigo? (Insider ownership, buybacks)
10. ☐ ¿Estoy comprando por convicción o por emoción?
```

> [!IMPORTANT]
> **Ninguna herramienta sustituye tu criterio.** Los números son una guía, no una verdad absoluta. La app te da el mapa — tú decides el camino.
