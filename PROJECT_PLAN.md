# 1. Introducción

## 1.1 Propósito

El objetivo principal de este proyecto es reproducir de forma exacta los estudios publicados en la serie **Safe Withdrawal Rates** de EarlyRetirementNow, comenzando por el **Part 19 – Equity Glidepaths**.

Una vez reproducidos y validados dichos estudios, el proyecto deberá servir como plataforma para investigar nuevas estrategias de desacumulación y responder preguntas de investigación relacionadas con la jubilación mediante simulaciones históricas.

El proyecto no pretende limitarse a reproducir un único estudio, sino proporcionar un motor de simulación reutilizable capaz de ejecutar cualquier experimento basado en series históricas de activos financieros.

Todas las decisiones arquitectónicas deberán priorizar, en este orden:

1. Correctitud matemática.
2. Reproducibilidad.
3. Trazabilidad.
4. Extensibilidad.
5. Rendimiento.

---

## 1.2 Objetivos

El proyecto deberá ser capaz de:

- Reproducir exactamente los estudios de EarlyRetirementNow.
- Calcular Safe Withdrawal Rates para distintas estrategias.
- Comparar múltiples Allocation Policies.
- Ejecutar miles de cohortes históricas.
- Ejecutar múltiples experimentos automáticamente.
- Persistir todos los resultados.
- Permitir extender el motor sin modificar el dominio.

---

## 1.3 Alcance

La primera versión implementará únicamente:

- Datos mensuales.
- ACWI Total Return EUR.
- Bonos gubernamentales europeos.
- Fondo monetario EUR.
- Retirada constante ajustada por inflación.
- Glidepaths pasivos.
- Glidepaths activos.
- Rebalanceo mensual.
- Optimización mediante Binary Search.

Todo elemento adicional deberá justificarse mediante un caso de uso real.

---

## 1.4 Filosofía

El proyecto se divide en dos dominios completamente independientes.

### Engine

Responsable de ejecutar simulaciones.

Nunca conoce estudios concretos.

Nunca conoce EarlyRetirementNow.

Nunca conoce experimentos específicos.

Únicamente ejecuta simulaciones.

### Research

Responsable de definir estudios científicos.

Describe qué simulaciones deben ejecutarse.

Nunca implementa lógica de simulación.

Todo estudio deberá describirse mediante configuración y utilizar exclusivamente las capacidades proporcionadas por el Engine.

---

## 1.5 Principios

El dominio deberá ser completamente independiente de:

- SQLite.
- YAML.
- CSV.
- CLI.
- Logging.
- Gráficos.
- Interfaces de usuario.

Toda dependencia externa pertenecerá a Infrastructure.

# 2. Arquitectura General

## 2.1 Visión general

El proyecto se divide en los siguientes módulos:

- Engine
- Research
- Infrastructure
- Analysis
- CLI

Cada módulo tendrá una única responsabilidad.

---

## 2.2 Engine

Responsable de ejecutar simulaciones.

Contiene exclusivamente lógica de dominio.

Nunca realiza operaciones de entrada o salida.

Nunca conoce formatos de persistencia.

Nunca genera gráficos.

---

## 2.3 Research

Define experimentos científicos.

Contiene:

- Experimentos.
- Configuraciones.
- Estudios.
- Comparativas.

No contiene lógica de simulación.

---

## 2.4 Infrastructure

Responsable de todas las dependencias externas.

Incluye:

- SQLite.
- Lectura de CSV.
- Exportación.
- Logging.
- Configuración.
- Persistencia.

---

## 2.5 Analysis

Genera resultados derivados.

Ejemplos:

- Tablas.
- Comparativas.
- Gráficos.
- Informes.

Nunca ejecuta simulaciones.

---

## 2.6 CLI

Punto de entrada del programa.

Únicamente:

- Lee configuración.
- Construye experimentos.
- Ejecuta el Runner.
- Muestra el progreso.

Toda la lógica pertenece al Engine.

---

## 2.7 Dependencias

La dirección de dependencias será siempre:

CLI

↓

Research

↓

Engine

↓

Infrastructure

Analysis dependerá exclusivamente de los resultados generados por el Engine.

Nunca al contrario.

# 3. Modelo del Dominio

## 3.1 Filosofía

El dominio representa exclusivamente conceptos financieros y de simulación.

Nunca contendrá detalles de infraestructura.

Nunca conocerá bases de datos.

Nunca conocerá formatos de fichero.

Nunca conocerá interfaces gráficas.

---

## 3.2 Separación entre Engine y Research

El dominio se divide conceptualmente en dos niveles.

### Engine

Responsable de ejecutar simulaciones.

Únicamente conoce conceptos genéricos.

Ejemplos

- Portfolio
- Allocation
- Withdrawal
- Optimizer
- Dataset
- Simulation

Nunca conoce estudios concretos.

---

### Research

Responsable de definir estudios científicos.

Un estudio describe:

- Dataset.
- Horizonte.
- Allocation Policies.
- Withdrawal Policies.
- Optimizer.
- Targets.
- Configuración.

Todo estudio deberá implementarse mediante configuración.

Nunca mediante código específico.

---

## 3.3 Objetos principales

El dominio estará compuesto, como mínimo, por los siguientes conceptos.

ExperimentDefinition

ExperimentRun

Simulation

SimulationContext

SimulationState

SimulationResult

DecisionContext

MarketSnapshot

Portfolio

AssetHolding

Allocation

AllocationTarget

MonthlyResult

Summary

Statistics

Diagnostics

Trace

---

## 3.4 Separación entre configuración y estado

Todo objeto pertenecerá exactamente a una de estas categorías.

### Configuración

Información inmutable.

Ejemplos

- Dataset
- AllocationPolicy
- WithdrawalPolicy
- Horizonte
- Target

### Estado

Información mutable.

Ejemplos

- Portfolio
- Patrimonio
- Allocation actual
- Retirada acumulada

Nunca deberán mezclarse ambas responsabilidades.

---

## 3.5 Objetos inmutables

Como norma general, todos los objetos del dominio serán inmutables.

Únicamente podrán modificarse:

- SimulationState.
- Portfolio.
- AssetHolding.

El resto deberán reconstruirse cuando cambien.

---

## 3.6 Responsabilidad única

Cada objeto del dominio tendrá exactamente una responsabilidad.

Nunca se permitirá que un objeto:

- tome decisiones,
- modifique estado,
- persista información,
- genere gráficos,

al mismo tiempo.

---

## 3.7 Flujo general

El Engine seguirá el siguiente flujo conceptual.

ExperimentDefinition

↓

ExperimentRun

↓

Simulation

↓

SimulationResult

Research únicamente construye ExperimentDefinition.

El Engine ejecuta el resto.

---

## 3.8 Principio de independencia

El dominio deberá poder ejecutarse completamente:

- sin SQLite,
- sin YAML,
- sin CSV,
- sin Logging,
- sin CLI,

utilizando únicamente objetos en memoria.

# 4. Experimentos

## 4.1 Objetivo

Un ExperimentDefinition representa un estudio científico completamente definido.

Describe qué simulaciones deben ejecutarse.

Nunca ejecuta simulaciones.

Nunca conoce detalles de implementación.

---

## 4.2 Contenido

Como mínimo contendrá:

- Nombre.
- Descripción.
- Dataset.
- Horizonte.
- Allocation Policies.
- Withdrawal Policies.
- Optimizer.
- Targets.
- Configuración.

---

## 4.3 ExperimentRun

Cada ejecución de un ExperimentDefinition generará un ExperimentRun independiente.

ExperimentRun representa una ejecución concreta del experimento.

Permitirá repetir exactamente el mismo estudio múltiples veces.

---

## 4.4 Simulation

Cada combinación de:

- cohorte,
- Allocation Policy,
- Withdrawal Policy,
- Target,

generará una Simulation independiente.

Todas las Simulations serán completamente independientes entre sí.

---

## 4.5 Resultado

Cada Simulation producirá exactamente un SimulationResult.

Un ExperimentRun estará compuesto por una colección de SimulationResult.

---

## 4.6 Ciclo de vida

ExperimentDefinition

↓

ExperimentRun

↓

Simulation

↓

SimulationResult

---

## 4.7 Responsabilidades

ExperimentDefinition

Describe.

ExperimentRun

Coordina.

Simulation

Ejecuta.

SimulationResult

Almacena resultados.

Cada concepto tendrá una única responsabilidad.

---

## 4.8 Configuración

Toda la información necesaria para ejecutar un experimento deberá encontrarse en ExperimentDefinition.

No estará permitido modificar dicha configuración durante la ejecución.

---

## 4.9 Reproducibilidad

Dos ExperimentRun creados a partir del mismo ExperimentDefinition deberán producir exactamente los mismos resultados siempre que:

- el Dataset sea el mismo,
- la configuración sea la misma,
- las Policies sean las mismas,
- la versión del Engine sea la misma.

---

## 4.10 Independencia

ExperimentDefinition nunca conocerá:

- SQLite,
- CSV,
- YAML,
- Logging,
- CLI.

Únicamente contendrá información del dominio.

# 5. Datasets

## 5.1 Objetivo

Un Dataset representa una serie histórica utilizada por el Engine para ejecutar simulaciones.

El Dataset únicamente contiene datos.

Nunca contiene lógica.

Nunca conoce estrategias.

Nunca conoce simulaciones.

---

## 5.2 Alcance de la primera versión

La primera versión trabajará exclusivamente con:

- Frecuencia mensual.
- Una única serie temporal por AssetClass.
- ACWI Total Return EUR.
- Bonos gubernamentales europeos.
- Fondo monetario EUR.
- IPC.

La arquitectura permitirá ampliar posteriormente el número de AssetClass sin modificar el Engine.

---

## 5.3 Responsabilidades

Un Dataset deberá proporcionar:

- Fechas.
- Retornos mensuales.
- Inflación mensual.
- Índice acumulado.
- Información necesaria para construir los MarketSnapshot.

Nunca realizará cálculos durante la simulación.

---

## 5.4 Preprocesado

Antes de ejecutar cualquier experimento, el Dataset será preprocesado.

El preprocesado calculará toda la información derivada que pueda reutilizarse entre simulaciones.

Como mínimo:

- Índice acumulado.
- Running ATH.
- isATH.
- isUnderwater.
- Inflación acumulada.

El objetivo es evitar cálculos repetidos para cada cohorte.

---

## 5.5 Validación

Todo Dataset deberá validarse antes de utilizarse.

Como mínimo deberá comprobarse:

- Fechas ordenadas.
- Sin duplicados.
- Sin meses ausentes.
- Sin valores nulos.
- Todas las AssetClass presentes.
- IPC presente.

Un Dataset inválido impedirá la ejecución del experimento.

---

## 5.6 Independencia

El Engine nunca leerá directamente un CSV.

El Dataset ya deberá encontrarse cargado y validado antes de comenzar la simulación.

---

## 5.7 Inmutabilidad

Una vez construido, un Dataset será completamente inmutable.

Ninguna simulación podrá modificarlo.

Todas las simulaciones compartirán la misma instancia del Dataset.

---

## 5.8 Relación con MarketSnapshot

Durante el preprocesado se construirá un MarketSnapshot por cada mes del Dataset.

La simulación únicamente consumirá dichos MarketSnapshot.

Nunca accederá directamente al Dataset.

# 6. MarketSnapshot

## 6.1 Objetivo

MarketSnapshot representa el estado del mercado para un único mes.

Es un objeto completamente inmutable.

Se construye durante el preprocesado del Dataset y es reutilizado por todas las simulaciones.

---

## 6.2 Filosofía

MarketSnapshot representa únicamente información del mercado.

Nunca contiene información del Portfolio.

Nunca contiene información de una simulación concreta.

Nunca contiene lógica.

---

## 6.3 Contenido

Como mínimo contendrá:

- Fecha.
- Retorno mensual de cada AssetClass.
- Inflación mensual.
- Inflación acumulada.
- Valor acumulado del índice.
- Running ATH.
- isATH.
- isUnderwater.

---

## 6.4 Información excluida

MarketSnapshot nunca contendrá:

- Patrimonio.
- Allocation.
- Drawdown del Portfolio.
- Compras.
- Ventas.
- Retiradas.
- Rentabilidad de una cartera.

Toda esa información pertenece a SimulationState o MonthlyResult.

---

## 6.5 Construcción

Todos los MarketSnapshot deberán construirse durante el preprocesado.

Nunca durante la simulación.

El objetivo es minimizar el coste computacional de ejecutar miles de cohortes.

---

## 6.6 Consumo

Cada iteración mensual recibirá exactamente un MarketSnapshot.

Las Policies nunca accederán directamente al Dataset.

Toda la información del mercado deberá proporcionarse mediante este objeto.

---

## 6.7 Reutilización

Todos los ExperimentRun compartirán los mismos MarketSnapshot derivados de un Dataset.

Nunca se duplicarán innecesariamente en memoria.

---

## 6.8 Principio de responsabilidad única

MarketSnapshot únicamente representa el estado del mercado para un instante concreto.

No toma decisiones.

No modifica estado.

No conoce ninguna simulación.

# 7. AssetClass

## 7.1 Objetivo

AssetClass representa una categoría de activo financiero sobre la que puede invertirse durante una simulación.

No representa un ETF, un fondo concreto ni un ISIN.

Representa una clase de activo abstraída.

---

## 7.2 AssetClass iniciales

La primera versión implementará exclusivamente:

- ACWI Total Return EUR
- Euro Government Bonds
- Euro Money Market

La arquitectura permitirá añadir nuevas AssetClass sin modificar el Engine.

---

## 7.3 Responsabilidades

Una AssetClass únicamente identifica una serie temporal dentro de un Dataset.

Nunca almacena dinero.

Nunca conoce un Portfolio.

Nunca conoce Allocation.

Nunca contiene lógica.

---

## 7.4 Identidad

Cada AssetClass tendrá como mínimo:

- Id
- Nombre
- Descripción

Su identidad será estable durante toda la vida del proyecto.

---

## 7.5 Relación con Dataset

Cada AssetClass tendrá exactamente una serie temporal dentro de un Dataset.

La simulación siempre trabajará utilizando dicha serie.

---

## 7.6 Restricciones

Una AssetClass nunca contendrá:

- Rentabilidades calculadas.
- Cantidades monetarias.
- Pesos.
- Allocation.
- Holdings.

Toda esa información pertenece al Portfolio.

---

## 7.7 Extensibilidad

Será posible añadir nuevas AssetClass sin modificar:

- Simulation
- Portfolio
- AllocationPolicy
- WithdrawalPolicy

El único requisito será que el Dataset proporcione una serie temporal válida.

# 8. Portfolio

## 8.1 Objetivo

Portfolio representa el estado económico completo de una cartera en un instante determinado.

Únicamente almacena estado.

No implementa reglas de negocio.

No toma decisiones.

---

## 8.2 Contenido

Como mínimo contendrá:

- Lista de AssetHolding.
- Patrimonio total.
- Allocation actual.

---

## 8.3 AssetHolding

Cada AssetHolding representa el capital invertido en una única AssetClass.

Contendrá como mínimo:

- AssetClass.
- Valor actual en euros.

No almacenará porcentajes.

Los porcentajes se calcularán a partir del patrimonio total.

---

## 8.4 Filosofía

El Portfolio almacena euros.

No almacena participaciones.

No almacena número de títulos.

No almacena precios.

Toda la simulación se realiza sobre capital monetario.

---

## 8.5 Restricciones

Portfolio nunca implementará:

- comprar()
- vender()
- retirar()
- rebalancear()
- aplicar_retorno()
- calcular_valor()
- calcular_allocation()

Toda modificación será responsabilidad exclusiva de PortfolioService.

---

## 8.6 Invariantes

Siempre deberá cumplirse:

Patrimonio Total = Σ Valor de todos los AssetHolding.

Ningún AssetHolding podrá tener un valor negativo.

La suma de Allocation deberá ser exactamente 100%, salvo errores de redondeo definidos por el Engine.

---

## 8.7 Mutabilidad

Portfolio es uno de los pocos objetos mutables del dominio.

Toda modificación deberá realizarse exclusivamente mediante PortfolioService.

Nunca directamente.

---

## 8.8 Independencia

Portfolio nunca conocerá:

- AllocationPolicy.
- WithdrawalPolicy.
- Optimizer.
- Simulation.
- Dataset.

Únicamente representa el estado económico de la cartera.

# 9. PortfolioService

## 9.1 Objetivo

PortfolioService será el único componente autorizado para modificar un Portfolio.

Toda modificación del patrimonio deberá realizarse exclusivamente mediante este servicio.

---

## 9.2 Filosofía

PortfolioService ejecuta operaciones.

Nunca toma decisiones.

Nunca decide cuánto retirar.

Nunca decide cuándo rebalancear.

Nunca decide cuál debe ser la Allocation objetivo.

Todas esas decisiones pertenecen a las Policies.

---

## 9.3 Responsabilidades

Como mínimo implementará las siguientes operaciones:

- aplicar_retorno()
- retirar()
- comprar()
- vender()
- rebalancear()
- calcular_valor()
- calcular_allocation()

---

## 9.4 aplicar_retorno()

Aplica los retornos mensuales definidos por el MarketSnapshot.

Cada AssetHolding se actualizará utilizando exclusivamente el retorno correspondiente a su AssetClass.

No modifica la Allocation objetivo.

---

## 9.5 retirar()

Retira una cantidad determinada del Portfolio.

La retirada deberá intentar satisfacer el rebalanceo de forma implícita.

Si la retirada no es suficiente para alcanzar la AllocationTarget, será necesario ejecutar posteriormente un rebalanceo explícito.

---

## 9.6 rebalancear()

Recibe:

- Portfolio.
- AllocationTarget.

Su responsabilidad consiste en ejecutar las compras y ventas necesarias para alcanzar dicha asignación.

Nunca decide cuál debe ser la AllocationTarget.

---

## 9.7 Restricciones

PortfolioService nunca accederá directamente a:

- Dataset.
- Simulation.
- Optimizer.
- ExperimentDefinition.

Únicamente operará sobre el Portfolio recibido.

---

## 9.8 Invariantes

Tras cualquier operación deberán cumplirse las siguientes condiciones:

- Ningún AssetHolding será negativo.
- No se creará dinero.
- No se destruirá dinero.
- El patrimonio será igual a la suma de todos los AssetHolding.
- La Allocation reflejará exactamente el estado del Portfolio.

---

## 9.9 Principio de responsabilidad única

PortfolioService ejecuta operaciones.

Las Policies toman decisiones.

La simulación coordina el proceso.

Cada responsabilidad pertenece a un único componente.

# 10. AllocationDrift

## 10.1 Objetivo

AllocationDrift representa la desviación existente entre la Allocation actual del Portfolio y la AllocationTarget definida por la AllocationPolicy.

Es un objeto de dominio.

No contiene lógica de rebalanceo.

Únicamente describe la diferencia entre ambos estados.

---

## 10.2 Motivación

La desviación entre la asignación actual y la asignación objetivo es un concepto fundamental del dominio.

Permite:

- Conocer cuánto se ha desviado la cartera.
- Implementar rebalanceos por umbral.
- Medir la calidad del rebalanceo.
- Generar estadísticas de desviación.
- Facilitar la auditoría de la simulación.

Por este motivo se modela explícitamente.

---

## 10.3 Contenido

AllocationDrift contendrá, como mínimo:

- Allocation actual.
- Allocation objetivo.
- Diferencia por cada AssetClass.
- Desviación absoluta por AssetClass.
- Desviación máxima.
- Desviación total.

---

## 10.4 Construcción

AllocationDrift será construido por el Engine a partir de:

- Allocation.
- AllocationTarget.

Nunca será construido por una AllocationPolicy.

---

## 10.5 Responsabilidades

AllocationDrift nunca decidirá si debe rebalancearse.

Únicamente describe el estado actual.

La decisión corresponderá al RebalanceEngine.

---

## 10.6 Extensibilidad

En el futuro podrán añadirse métricas adicionales sin modificar el resto del dominio.

Ejemplos:

- Error cuadrático.
- Error medio absoluto.
- Distancia euclídea.
- Distancia Manhattan.

---

## 10.7 Inmutabilidad

AllocationDrift será completamente inmutable.

# 11. Policy

## 11.1 Objetivo

Policy representa un algoritmo capaz de tomar una decisión durante la simulación.

Nunca modifica el estado.

Nunca ejecuta operaciones.

Únicamente analiza el contexto recibido y devuelve una decisión.

Todas las políticas del Engine heredarán de esta abstracción.

---

## 11.2 Filosofía

Una Policy responde exactamente a una pregunta del dominio.

Ejemplos:

- ¿Cuál debe ser la asignación objetivo?
- ¿Cuánto dinero debe retirarse?
- ¿Qué impuestos deben aplicarse? (futuro)
- ¿Qué comisiones deben cobrarse? (futuro)

Nunca ejecuta dicha decisión.

---

## 11.3 Ciclo de vida

Toda Policy implementará:

before_simulation(context)

before_month(decision_context)

decide(decision_context)

↓

PolicyDecision

after_month(decision_context)

after_simulation(context)

---

## 11.4 Restricciones

Las Policy:

- Nunca modificarán el Portfolio.
- Nunca accederán al Dataset completo.
- Nunca accederán a SQLite.
- Nunca realizarán operaciones financieras.

Toda la información necesaria estará disponible mediante DecisionContext.

---

## 11.5 Determinismo

Dado el mismo DecisionContext deberán producir exactamente la misma PolicyDecision.

# 12. PolicyDecision

## 12.1 Objetivo

PolicyDecision representa el resultado producido por una Policy.

Es una abstracción del dominio.

Nunca contiene lógica.

Únicamente describe una decisión.

---

## 12.2 Filosofía

Cada tipo de Policy devolverá una especialización de PolicyDecision.

El resto del Engine trabajará siempre con esta abstracción.

---

## 12.3 Implementaciones iniciales

La primera versión implementará:

- AllocationDecision.
- WithdrawalDecision.

---

## 12.4 Implementaciones futuras

La arquitectura permitirá añadir:

- TaxDecision.
- FeeDecision.
- CurrencyDecision.
- RiskDecision.

Sin modificar SimulationRunner.

---

## 12.5 Inmutabilidad

Toda PolicyDecision será completamente inmutable.

# 13. AllocationPolicy

## 13.1 Objetivo

AllocationPolicy es una especialización de Policy.

Su única responsabilidad consiste en decidir cuál debe ser la AllocationTarget del Portfolio.

Nunca ejecuta operaciones.

---

## 13.2 Resultado

Toda AllocationPolicy devolverá un AllocationDecision.

AllocationDecision heredará de PolicyDecision.

Como mínimo contendrá:

- AllocationTarget.
- Motivo.
- Metadata opcional para auditoría.

---

## 13.3 Implementaciones iniciales

- Static Allocation.
- Passive Glidepath.
- Active Glidepath.

---

## 13.4 Active Glidepath

El Active Glidepath seguirá exactamente la definición utilizada en EarlyRetirementNow.

La pendiente únicamente avanzará cuando:

isUnderwater == true

Cuando:

isATH == true

la Allocation permanecerá congelada.

---

## 13.5 Restricciones

AllocationPolicy nunca:

- modificará el Portfolio,
- ejecutará rebalanceos,
- accederá al Dataset completo,
- realizará cálculos fuera del DecisionContext.

# 14. WithdrawalPolicy

## 14.1 Objetivo

WithdrawalPolicy es una especialización de Policy.

Determina cuánto dinero deberá retirarse durante el periodo actual.

Nunca ejecuta la retirada.

---

## 14.2 Resultado

Toda WithdrawalPolicy devolverá un WithdrawalDecision.

WithdrawalDecision heredará de PolicyDecision.

Como mínimo contendrá:

- Importe nominal.
- Importe real.
- Motivo.
- Metadata opcional.

---

## 14.3 Implementación inicial

La primera implementación será:

Constant Inflation Adjusted Withdrawal.

Su comportamiento reproducirá exactamente el estudio de EarlyRetirementNow.

---

## 14.4 Implementaciones futuras

- Guyton-Klinger.
- VPW.
- Floor & Ceiling.
- CAPE.
- Dynamic Spending.

---

## 14.5 Restricciones

WithdrawalPolicy nunca modificará el Portfolio.

Nunca ejecutará retiradas.

Toda la información necesaria estará disponible mediante DecisionContext.

# 15. SimulationContext

## 15.1 Objetivo

SimulationContext contiene toda la configuración inmutable necesaria para ejecutar una Simulation.

Se construye exactamente una vez antes del inicio de la simulación.

Nunca cambia durante toda su ejecución.

---

## 15.2 Contenido

Como mínimo contendrá:

- ExperimentDefinition.
- Cohorte.
- Fecha de inicio.
- Horizonte.
- Patrimonio inicial.
- Dataset.
- AllocationPolicy.
- WithdrawalPolicy.
- Optimizer.
- Objetivo final.

---

## 15.3 Filosofía

SimulationContext representa exclusivamente configuración.

Nunca contendrá estado.

Nunca contendrá resultados.

Nunca contendrá estadísticas.

---

## 15.4 Restricciones

Nunca contendrá:

- Portfolio.
- Allocation.
- AllocationTarget.
- AllocationDrift.
- Patrimonio actual.
- Timeline.
- MonthlyResult.
- SimulationStatistics.

# 16. SimulationState

## 16.1 Objetivo

SimulationState representa el estado mutable de una Simulation.

Representa exclusivamente el instante actual de la simulación.

---

## 16.2 Contenido

Como mínimo contendrá:

- Fecha actual.
- Número de periodo.
- Portfolio.
- Allocation actual.
- AllocationTarget.
- AllocationDrift.
- WithdrawalDecision actual.
- MarketSnapshot actual.
- Patrimonio actual.
- Máximo patrimonio alcanzado.

---

## 16.3 Filosofía

SimulationState representa únicamente el presente.

No almacena resultados históricos.

No almacena estadísticas.

---

## 16.4 Mutabilidad

SimulationState podrá modificarse durante la simulación.

Será el único objeto del dominio cuyo contenido evolucione continuamente.

---

## 16.5 Restricciones

Nunca contendrá:

- SimulationStatistics.
- SimulationTimeline.
- MonthlyResult.
- Summary.
- Diagnostics.

# 17. SimulationStatistics

## 17.1 Objetivo

SimulationStatistics almacena todas las métricas agregadas calculadas durante una Simulation.

No participa en la lógica financiera.

No modifica el comportamiento del Engine.

---

## 17.2 Contenido

Como mínimo contendrá:

- Meses simulados.
- Número de retiradas.
- Número de rebalanceos.
- Número de compras.
- Número de ventas.
- Capital retirado.
- Capital negociado.
- Máximo patrimonio.
- Patrimonio mínimo.
- Máximo drawdown.
- CAGR.
- Tiempo de ejecución.

---

## 17.3 Actualización

Será actualizado automáticamente durante la simulación.

Las Policies nunca modificarán este objeto.

---

## 17.4 Restricciones

Nunca contendrá:

- MonthlyResult.
- Portfolio.
- Allocation.
- Eventos.
- Configuración.

# 18. SimulationTimeline

## 18.1 Objetivo

SimulationTimeline almacena la evolución completa de una Simulation.

Contendrá un MonthlyResult por cada periodo simulado.

---

## 18.2 Contenido

Contendrá una colección cronológica de MonthlyResult.

---

## 18.3 Persistencia

Su almacenamiento será configurable.

Cuando esté deshabilitado únicamente se conservarán Summary y SimulationStatistics.

---

## 18.4 Restricciones

Nunca contendrá lógica.

Nunca modificará la simulación.

Será únicamente un contenedor de datos.

---

## 18.5 Orden

Los MonthlyResult deberán almacenarse cronológicamente.

No podrán existir meses duplicados ni huecos temporales.

# 19. SimulationEvent

## 19.1 Objetivo

SimulationEvent representa un hecho ocurrido durante una Simulation.

Todos los eventos serán completamente inmutables.

---

## 19.2 Contenido

Todo evento contendrá como mínimo:

- Fecha.
- Tipo.
- Payload.

---

## 19.3 Tipos iniciales

La primera versión implementará:

- SimulationStarted.
- AllocationCalculated.
- WithdrawalCalculated.
- WithdrawalExecuted.
- RebalanceExecuted.
- MarketReturnApplied.
- GlidepathAdvanced.
- GlidepathFrozen.
- SimulationFinished.

---

## 19.4 Restricciones

Los eventos representan hechos.

Nunca representan decisiones futuras.

Nunca contienen lógica.

Nunca modifican el estado.

# 20. MonthlyResult

## 20.1 Objetivo

MonthlyResult representa el estado completo de una Simulation al finalizar un periodo.

Es completamente inmutable.

---

## 20.2 Contenido

### Tiempo

- Fecha.
- Número de periodo.

### Mercado

- MarketSnapshot.

### Portfolio

- Patrimonio.
- Allocation.
- AllocationTarget.
- AllocationDrift.

### Operaciones

- WithdrawalDecision.
- RebalanceResult.

### Estadísticas

- Drawdown.
- Rentabilidad acumulada.
- Inflación acumulada.

### Eventos

- Colección de SimulationEvent ocurridos durante el periodo.

---

## 20.3 Objetivo

MonthlyResult deberá contener toda la información necesaria para reconstruir el estado de una Simulation en cualquier instante temporal.

---

## 20.4 Restricciones

Nunca contendrá referencias mutables.

Nunca contendrá lógica.

# 21. SimulationResult

## 21.1 Objetivo

SimulationResult representa el resultado completo producido por una única Simulation.

Es completamente inmutable.

Se construye exactamente una vez al finalizar la simulación.

---

## 21.2 Composición

SimulationResult estará compuesto por:

- SimulationContext.
- SimulationStatistics.
- SimulationTimeline.
- Summary.
- Diagnostics.

---

## 21.3 Summary

Summary contendrá la información mínima necesaria para identificar el resultado de la simulación.

Como mínimo:

- Nombre de la estrategia.
- Cohorte.
- Fecha de inicio.
- Fecha final.
- SWR utilizado.
- Patrimonio final.
- Objetivo alcanzado.
- Estado final de la simulación.

---

## 21.4 Diagnostics

Diagnostics contendrá información útil para depuración.

Ejemplos:

- Tiempo de construcción.
- Tiempo de simulación.
- Número de iteraciones.
- Versión del Engine.
- Versión del Dataset.

Nunca modificará el resultado matemático.

---

## 21.5 Inmutabilidad

Una vez construido, SimulationResult nunca podrá modificarse.

# 22. Application Layer

## 22.1 Objetivo

La Application Layer coordina la ejecución de las simulaciones.

No implementa reglas financieras.

No implementa reglas matemáticas.

Únicamente orquesta el dominio.

---

## 22.2 Componentes

La primera versión estará formada por:

- SimulationExecutor.
- SimulationRunner.
- SimulationPipeline.

---

## 22.3 Dependencias

La Application Layer podrá depender del Dominio.

El Dominio nunca dependerá de la Application Layer.

---

## 22.4 Responsabilidades

Será responsable de:

- Crear simulaciones.
- Ejecutarlas.
- Gestionar el paralelismo.
- Gestionar cancelaciones.
- Construir resultados.
- Persistir resultados.

Nunca decidirá AllocationTarget.

Nunca decidirá WithdrawalDecision.

# 23. SimulationExecutor

## 23.1 Objetivo

SimulationExecutor coordina la ejecución de múltiples Simulation.

Su principal responsabilidad es maximizar el paralelismo disponible.

---

## 23.2 Entrada

Recibirá un ExperimentRun.

---

## 23.3 Salida

Generará un SimulationResult por cada Simulation ejecutada.

---

## 23.4 Responsabilidades

Como mínimo:

- Crear SimulationRunner.
- Distribuir simulaciones.
- Gestionar procesos.
- Gestionar errores.
- Gestionar cancelaciones.
- Recoger resultados.

---

## 23.5 Paralelismo

Las simulaciones serán completamente independientes.

Podrán ejecutarse:

- Secuencialmente.
- Multiprocessing.
- Distribuidas.

El resultado nunca dependerá del orden de ejecución.

---

## 23.6 Restricciones

Nunca contendrá lógica financiera.

Nunca modificará el estado interno de una Simulation.

# 24. SimulationRunner

## 24.1 Objetivo

SimulationRunner ejecuta exactamente una Simulation.

Coordina todas las fases necesarias para completar la simulación.

---

## 24.2 Responsabilidades

Será responsable de:

- Construir el DecisionContext.
- Ejecutar las Policies.
- Coordinar PortfolioServices.
- Actualizar SimulationState.
- Actualizar SimulationStatistics.
- Construir MonthlyResult.
- Construir SimulationResult.

---

## 24.3 Restricciones

Nunca leerá directamente archivos CSV.

Nunca escribirá SQLite.

Nunca ejecutará varias simulaciones.

Nunca realizará optimizaciones.

---

## 24.4 Dependencias

Podrá utilizar:

- SimulationPipeline.
- PortfolioServices.
- Policies.
- Optimizer.
- EventFactory.

Nunca accederá directamente a la capa de persistencia.

# 25. SimulationPipeline

## 25.1 Objetivo

SimulationPipeline define las fases de ejecución de una Simulation.

Cada fase tendrá una única responsabilidad.

---

## 25.2 Orden de ejecución

Cada periodo mensual seguirá exactamente el siguiente flujo:

1. Construcción del MarketSnapshot.
2. Construcción del DecisionContext.
3. Ejecución de AllocationPolicy.
4. Ejecución de WithdrawalPolicy.
5. Ejecución de la retirada.
6. Rebalanceo del Portfolio si fuese necesario.
7. Aplicación de los retornos del mercado.
8. Actualización de SimulationState.
9. Actualización de SimulationStatistics.
10. Generación de SimulationEvent.
11. Construcción de MonthlyResult.
12. Inserción en SimulationTimeline.

---

## 25.3 Inmutabilidad

El orden de las fases será fijo.

Todas las simulaciones seguirán exactamente la misma secuencia.

---

## 25.4 Extensibilidad

Será posible añadir nuevas fases sin modificar las existentes.

Las nuevas fases deberán definir explícitamente su posición dentro del Pipeline.

# 26. ExperimentDefinition

## 26.1 Objetivo

ExperimentDefinition describe un experimento completo.

No ejecuta simulaciones.

No contiene resultados.

Únicamente define qué simulaciones deben ejecutarse.

---

## 26.2 Filosofía

ExperimentDefinition representa una especificación.

Nunca representa una ejecución.

---

## 26.3 Contenido

Como mínimo contendrá:

- Nombre.
- Descripción.
- Dataset.
- Horizonte.
- Cohortes.
- AllocationPolicies.
- WithdrawalPolicies.
- Targets finales.
- Optimizer.

---

## 26.4 Inmutabilidad

ExperimentDefinition será completamente inmutable.

---

## 26.5 Restricciones

Nunca contendrá:

- SimulationResult.
- MonthlyResult.
- Portfolio.
- Estadísticas.
- Timeline.

# 27. ExperimentRun

## 27.1 Objetivo

ExperimentRun representa una ejecución concreta de un ExperimentDefinition.

---

## 27.2 Contenido

Como mínimo contendrá:

- ExperimentDefinition.
- Fecha de ejecución.
- Identificador único.
- Estado.
- Configuración de ejecución.

---

## 27.3 Estados

Un ExperimentRun podrá encontrarse en uno de los siguientes estados:

- Pending.
- Running.
- Completed.
- Cancelled.
- Failed.

---

## 27.4 Responsabilidades

Será responsable de agrupar todas las Simulation pertenecientes al mismo experimento.

---

## 27.5 Restricciones

Nunca contendrá lógica financiera.

Nunca modificará los resultados.

# 28. Optimizer

## 28.1 Objetivo

Optimizer calcula el Safe Withdrawal Rate asociado a una Simulation.

Nunca ejecuta simulaciones directamente.

Únicamente coordina múltiples ejecuciones.

---

## 28.2 Filosofía

Optimizer es completamente independiente del dominio financiero.

Su única responsabilidad consiste en encontrar un valor óptimo.

---

## 28.3 Entrada

Recibirá:

- SimulationFactory.
- SimulationContext.
- Objetivo final.
- Intervalo de búsqueda.

---

## 28.4 Salida

Devolverá:

- Safe Withdrawal Rate.
- Número de iteraciones.
- Historial de convergencia.

---

## 28.5 Implementación inicial

La primera implementación utilizará búsqueda binaria.

---

## 28.6 Implementaciones futuras

La arquitectura permitirá añadir:

- Newton-Raphson.
- Brent.
- Golden Search.
- Algoritmos híbridos.

Sin modificar el resto del Engine.

# 29. Persistence Layer

## 29.1 Objetivo

La Persistence Layer será responsable del almacenamiento permanente de los resultados.

Nunca contendrá lógica financiera.

Nunca modificará el dominio.

---

## 29.2 Responsabilidades

Como mínimo:

- Guardar ExperimentRun.
- Guardar SimulationResult.
- Guardar SimulationStatistics.
- Guardar MonthlyResult.
- Recuperar resultados.

---

## 29.3 Implementación inicial

La primera implementación utilizará SQLite.

---

## 29.4 Extensibilidad

Será posible implementar posteriormente:

- PostgreSQL.
- DuckDB.
- Parquet.
- CSV.
- Apache Arrow.

Sin modificar el dominio.

---

## 29.5 Restricciones

El dominio nunca dependerá de la Persistence Layer.

# 30. Repository

## 30.1 Objetivo

Un Repository abstrae el acceso a la persistencia.

El dominio nunca conocerá la implementación concreta.

---

## 30.2 Repositories iniciales

La primera versión implementará:

- ExperimentRepository.
- SimulationRepository.
- StatisticsRepository.
- TimelineRepository.

---

## 30.3 Responsabilidades

Los Repository serán responsables de:

- Guardar.
- Recuperar.
- Buscar.
- Actualizar metadatos.

Nunca realizarán cálculos financieros.

---

## 30.4 Restricciones

Nunca contendrán lógica de simulación.

Nunca contendrán lógica de optimización.

Nunca modificarán el contenido del dominio.

---

## 30.5 Sustituibilidad

Será posible cambiar completamente el motor de persistencia sin modificar ninguna clase del dominio.

# 31. Dataset

## 31.1 Objetivo

Dataset representa el conjunto completo de datos históricos utilizados por las simulaciones.

Es completamente inmutable.

Todas las Simulation referenciarán el mismo Dataset.

---

## 31.2 Filosofía

Dataset representa una colección de series temporales ya cargadas en memoria.

Nunca accederá directamente a archivos.

Nunca realizará cálculos financieros.

---

## 31.3 Contenido

Como mínimo contendrá:

- Lista de AssetSeries.
- Fecha mínima.
- Fecha máxima.
- Frecuencia temporal.
- Versión del Dataset.

---

## 31.4 Restricciones

Nunca contendrá:

- Portfolio.
- Simulation.
- Policies.
- Resultados.

---

## 31.5 Compartición

El mismo Dataset podrá ser utilizado simultáneamente por miles de Simulation sin duplicar memoria.

# 32. AssetSeries

## 32.1 Objetivo

AssetSeries representa la serie histórica completa de una única AssetClass.

---

## 32.2 Filosofía

Una AssetSeries representa exclusivamente datos históricos.

Nunca contiene lógica de simulación.

---

## 32.3 Contenido

Como mínimo contendrá:

- AssetClass.
- Serie temporal.
- Fecha inicial.
- Fecha final.

---

## 32.4 Datos

Cada registro contendrá:

- Fecha.
- Valor Total Return.
- Inflación (si aplica a la serie).
- Metadatos opcionales.

---

## 32.5 Restricciones

Los datos deberán estar ordenados cronológicamente.

No podrán existir fechas duplicadas.

No podrán existir fechas ausentes dentro del rango de la serie.

# 33. MarketSnapshot

## 33.1 Objetivo

MarketSnapshot representa el estado del mercado durante un único periodo de simulación.

Es completamente inmutable.

---

## 33.2 Filosofía

MarketSnapshot contiene únicamente la información correspondiente al periodo actual.

Nunca conoce el pasado completo.

Nunca conoce el futuro.

---

## 33.3 Contenido

Como mínimo contendrá:

- Fecha.
- Retorno mensual de cada AssetClass.
- Valor Total Return de cada AssetClass.
- Inflación del periodo.

---

## 33.4 Información derivada

Durante su construcción se calcularán también:

- isATH.
- isUnderwater.
- Máximo histórico alcanzado hasta la fecha.

Estos valores se calculan utilizando exclusivamente la serie histórica hasta el periodo actual.

---

## 33.5 Restricciones

MarketSnapshot nunca accederá directamente al Dataset.

Será construido por un componente especializado a partir del Dataset.

# 34. DatasetProvider

## 34.1 Objetivo

DatasetProvider es responsable de construir un Dataset a partir de una fuente de datos.

---

## 34.2 Implementación inicial

La primera implementación utilizará un único fichero CSV.

---

## 34.3 Implementaciones futuras

Será posible implementar posteriormente:

- SQLite.
- PostgreSQL.
- Parquet.
- APIs.
- DuckDB.

Sin modificar el dominio.

---

## 34.4 Validación

Durante la carga deberán validarse:

- Orden cronológico.
- Duplicados.
- Valores nulos.
- Frecuencia temporal.
- Integridad de las AssetSeries.

---

## 34.5 Resultado

Si la validación finaliza correctamente devolverá un Dataset completamente construido.

# 35. CSV Specification

## 35.1 Objetivo

Definir el formato oficial del fichero CSV utilizado por la primera versión del simulador.

---

## 35.2 Estructura

Cada fila representará un único periodo temporal.

---

## 35.3 Columnas mínimas

- Date
- ACWI_TR_EUR
- EURO_GOV_SHORT_TR_EUR
- EURO_GOV_LONG_TR_EUR
- EURO_MONEY_MARKET_TR_EUR
- CPI

---

## 35.4 Restricciones

La columna Date:

- Será única.
- Estará ordenada.
- Tendrá frecuencia mensual.

Las columnas numéricas:

- No admitirán valores nulos.
- Utilizarán punto decimal.

---

## 35.5 Versionado

Todo Dataset deberá indicar explícitamente su versión para garantizar la reproducibilidad de las simulaciones.

# 36. Validation

## 36.1 Objetivo

Validation garantiza que todos los datos utilizados por el simulador cumplen las reglas definidas por el dominio.

La validación se realizará antes de ejecutar cualquier Simulation.

---

## 36.2 Alcance

Como mínimo se validarán:

- Dataset.
- ExperimentDefinition.
- AllocationPolicy.
- WithdrawalPolicy.
- Targets finales.
- Horizonte.
- Cohortes.

---

## 36.3 Tipos de validación

Existirán dos tipos:

- Validación estructural.
- Validación de dominio.

---

## 36.4 Validación estructural

Comprobará:

- Tipos.
- Campos obligatorios.
- Formato.
- Duplicados.
- Integridad.

---

## 36.5 Validación de dominio

Comprobará:

- Allocation = 100%.
- Pesos no negativos.
- Horizonte válido.
- Cohortes válidas.
- Dataset suficiente para la simulación.

---

## 36.6 Resultado

Toda validación devolverá un ValidationResult.

Nunca lanzará excepciones por errores esperables del usuario.

# 37. ValidationResult

## 37.1 Objetivo

ValidationResult representa el resultado producido por una validación.

---

## 37.2 Contenido

Como mínimo contendrá:

- Estado.
- Lista de errores.
- Lista de advertencias.

---

## 37.3 Estados

Podrán existir:

- Success.
- Warning.
- Error.

---

## 37.4 Filosofía

Un ValidationResult podrá contener múltiples errores simultáneamente.

El usuario deberá poder corregir todos ellos antes de volver a ejecutar el proceso.

---

## 37.5 Inmutabilidad

ValidationResult será completamente inmutable.

# 38. Logging

## 38.1 Objetivo

El sistema registrará información relevante para facilitar la depuración y el diagnóstico.

---

## 38.2 Niveles

Como mínimo existirán:

- TRACE.
- DEBUG.
- INFO.
- WARNING.
- ERROR.

---

## 38.3 Restricciones

El Logging nunca modificará el comportamiento del dominio.

Nunca alterará los resultados de una simulación.

---

## 38.4 Rendimiento

El Logging deberá poder deshabilitarse completamente para maximizar el rendimiento durante simulaciones masivas.

---

## 38.5 Destinos

La primera implementación permitirá registrar información en:

- Consola.
- Archivo.

# 39. Configuration

## 39.1 Objetivo

Configuration centraliza toda la configuración técnica del simulador.

No contiene reglas financieras.

---

## 39.2 Configuración inicial

Como mínimo permitirá configurar:

- Número máximo de procesos.
- Persistencia del Timeline.
- Nivel de Logging.
- Tamaño de lote.
- Directorio de salida.

---

## 39.3 Restricciones

Configuration nunca modificará el dominio.

Nunca modificará una Simulation.

---

## 39.4 Inmutabilidad

Una vez iniciado un ExperimentRun, la Configuration permanecerá inmutable.

# 40. Extensibility

## 40.1 Objetivo

Toda la arquitectura deberá diseñarse siguiendo el principio Open/Closed.

El sistema deberá ser fácilmente extensible sin modificar el código existente.

---

## 40.2 Nuevas AssetClass

Será posible añadir nuevas AssetClass sin modificar:

- Simulation.
- Policies.
- Portfolio.
- Optimizer.

---

## 40.3 Nuevas Policies

Será posible añadir nuevas Policy sin modificar:

- SimulationRunner.
- SimulationExecutor.
- SimulationPipeline.

---

## 40.4 Nuevos motores de persistencia

Será posible sustituir SQLite por cualquier otro sistema de persistencia implementando los Repository correspondientes.

---

## 40.5 Nuevos formatos de Dataset

Será posible añadir nuevos DatasetProvider sin modificar el dominio.

---

## 40.6 Compatibilidad

Toda ampliación deberá mantener la compatibilidad con los experimentos existentes siempre que la semántica del dominio no cambie.

---

## 40.7 Reproducibilidad

Dos ejecuciones con:

- el mismo Dataset,
- la misma Configuration,
- el mismo ExperimentDefinition,
- la misma versión del código,

deberán producir exactamente los mismos resultados.

# 41. SQLite Schema

## 41.1 Objetivo

Definir el esquema lógico de la base de datos SQLite utilizada para persistir los resultados de las simulaciones.

---

## 41.2 Filosofía

La base de datos almacenará únicamente resultados.

Nunca será utilizada como fuente de datos durante una Simulation.

---

## 41.3 Tablas iniciales

La primera versión implementará como mínimo:

- experiment_run
- simulation
- simulation_summary
- simulation_statistics
- monthly_result

---

## 41.4 Claves

Todas las tablas dispondrán de una clave primaria estable.

Las relaciones utilizarán claves foráneas.

---

## 41.5 Restricciones

Nunca se almacenarán objetos serializados completos cuando puedan normalizarse mediante tablas relacionadas.

# 42. Indexing Strategy

## 42.1 Objetivo

Definir la estrategia de índices utilizada por SQLite.

---

## 42.2 Índices mínimos

Como mínimo existirán índices sobre:

- experiment_id
- simulation_id
- cohort
- strategy_name
- start_date

---

## 42.3 Objetivo

Los índices deberán optimizar principalmente consultas analíticas.

La velocidad de escritura será un objetivo secundario.

---

## 42.4 Restricciones

No deberán existir índices redundantes.

Cada índice deberá estar justificado por un caso de uso.

# 43. Benchmark Suite

## 43.1 Objetivo

Medir el rendimiento del simulador entre versiones.

---

## 43.2 Métricas

Como mínimo se medirán:

- Simulaciones por segundo.
- Meses simulados por segundo.
- Tiempo medio por Simulation.
- Uso máximo de memoria.
- Uso medio de CPU.

---

## 43.3 Escenarios

La primera versión incluirá:

- Ejecución secuencial.
- Multiprocessing.
- Diferentes tamaños de Dataset.

---

## 43.4 Reproducibilidad

Todos los benchmarks deberán ejecutarse utilizando exactamente los mismos datos.

# 44. Testing Strategy

## 44.1 Objetivo

Garantizar la corrección matemática y funcional del simulador.

---

## 44.2 Tipos de pruebas

Como mínimo existirán:

- Unit Tests.
- Integration Tests.
- Property Tests.
- Regression Tests.

---

## 44.3 Regression Tests

Toda corrección de un error deberá incorporar un test que impida su reaparición.

---

## 44.4 Casos de referencia

Existirán simulaciones conocidas cuyos resultados deberán mantenerse entre versiones.

---

## 44.5 Determinismo

Todos los tests deberán ser completamente deterministas.

# 45. Acceptance Criteria

## 45.1 Objetivo

Definir cuándo una versión del simulador puede considerarse válida.

---

## 45.2 Correctitud

El simulador deberá reproducir exactamente el comportamiento especificado para:

- Static Allocation.
- Passive Glidepath.
- Active Glidepath.

---

## 45.3 Validación

Los resultados obtenidos deberán ser comparables con el estudio de EarlyRetirementNow utilizando datos equivalentes.

Las diferencias únicamente podrán atribuirse a:

- Dataset distinto.
- Activos distintos.
- Redondeos definidos explícitamente.

---

## 45.4 Rendimiento

El simulador deberá ser capaz de ejecutar miles de simulaciones utilizando todos los núcleos disponibles.

---

## 45.5 Reproducibilidad

Dos ejecuciones idénticas deberán producir exactamente los mismos resultados.

---

## 45.6 Trazabilidad

Toda decisión tomada durante una Simulation deberá poder reconstruirse utilizando:

- SimulationTimeline.
- MonthlyResult.
- SimulationEvent.


# 46. Numerical Precision

## 46.1 Objetivo

Definir las reglas de precisión numérica utilizadas por el simulador.

---

## 46.2 Filosofía

Todas las simulaciones deberán producir exactamente el mismo resultado independientemente del hardware utilizado.

---

## 46.3 Tipo numérico

Los importes monetarios se representarán utilizando Decimal.

Nunca se utilizarán números en coma flotante para representar dinero.

---

## 46.4 Redondeo

La política de redondeo será única para todo el proyecto.

Toda operación monetaria utilizará la misma estrategia.

---

## 46.5 Comparaciones

Las comparaciones entre importes monetarios deberán realizarse utilizando Decimal.

Nunca se compararán valores monetarios utilizando float.

---

## 46.6 Configuración

La precisión y el modo de redondeo estarán centralizados en un único componente.

# 47. Performance Strategy

## 47.1 Objetivo

Definir las decisiones de diseño destinadas a maximizar el rendimiento del simulador.

---

## 47.2 Principios

Se priorizará:

- Reducir asignaciones de memoria.
- Evitar copias innecesarias.
- Compartir estructuras inmutables.
- Minimizar sincronización entre procesos.

---

## 47.3 Paralelización

Las simulaciones deberán poder ejecutarse de forma completamente independiente.

La comunicación entre procesos será mínima.

---

## 47.4 Memoria

El Dataset será compartido siempre que sea posible.

Nunca se duplicará innecesariamente.

---

## 47.5 Persistencia

La escritura en SQLite deberá realizarse por lotes cuando resulte beneficioso para el rendimiento.

# 48. Versioning

## 48.1 Objetivo

Garantizar la reproducibilidad completa de cualquier resultado almacenado.

---

## 48.2 Versiones registradas

Toda SimulationResult almacenará:

- Versión del simulador.
- Versión del Dataset.
- Versión del esquema SQLite.
- Versión de la especificación.

---

## 48.3 Compatibilidad

Toda modificación incompatible incrementará la versión mayor del simulador.

---

## 48.4 Auditoría

Será posible conocer exactamente con qué versión del sistema se generó cualquier resultado.

# 49. Error Handling

## 49.1 Objetivo

Definir el comportamiento del sistema ante errores.

---

## 49.2 Errores recuperables

Ejemplos:

- Dataset inválido.
- Configuración incorrecta.
- Cohorte inexistente.

Estos errores deberán notificarse mediante ValidationResult.

---

## 49.3 Errores no recuperables

Ejemplos:

- Corrupción de memoria.
- Error interno del simulador.
- Inconsistencia del dominio.

Estos errores finalizarán la ejecución correspondiente.

---

## 49.4 Registro

Todo error deberá registrarse mediante el sistema de Logging.

---

## 49.5 Aislamiento

Un fallo en una Simulation nunca deberá provocar el fallo del resto del ExperimentRun.

# 50. Roadmap

## 50.1 Objetivo

Definir el orden recomendado de implementación del simulador.

---

## 50.2 Fase 1

Infraestructura:

- Dominio.
- Dataset.
- CSV Loader.
- Validación.

---

## 50.3 Fase 2

Motor:

- Portfolio.
- Policies.
- SimulationRunner.
- Optimizer.

---

## 50.4 Fase 3

Persistencia:

- SQLite.
- Repository.
- Timeline.
- Statistics.

---

## 50.5 Fase 4

Optimización:

- Multiprocessing.
- Benchmarks.
- Profiling.

---

## 50.6 Fase 5

Extensiones:

- Nuevas Policies.
- Nuevas AssetClass.
- Nuevos DatasetProvider.
- Nuevos motores de persistencia.

---

## 50.7 Objetivo final

El simulador deberá permitir reproducir, extender y comparar estudios de Safe Withdrawal Rate de forma determinista, reproducible, auditable y eficiente.

# 51. Domain Invariants

## 51.1 Objetivo

Definir todas las reglas que nunca podrán incumplirse durante una Simulation.

Estas reglas deberán verificarse mediante assertions internas o validaciones del dominio.

---

## 51.2 Portfolio

En todo momento deberá cumplirse:

- El patrimonio será mayor o igual que cero.
- Ningún AssetHolding podrá ser negativo.
- La suma de todos los AssetHolding será igual al patrimonio total.

---

## 51.3 Allocation

Toda Allocation deberá cumplir:

- La suma de pesos será exactamente 100%.
- Ningún peso será negativo.
- Ningún AssetClass aparecerá dos veces.

---

## 51.4 AllocationTarget

Toda AllocationTarget deberá cumplir las mismas restricciones que Allocation.

---

## 51.5 Timeline

Todo SimulationTimeline deberá cumplir:

- Los meses estarán ordenados.
- No existirán duplicados.
- No existirán huecos.

---

## 51.6 Simulation

Toda Simulation finalizará exactamente en uno de estos estados:

- Completed.
- Failed.
- Cancelled.

# 52. Determinism

## 52.1 Objetivo

Garantizar que cualquier experimento sea completamente reproducible.

---

## 52.2 Principio

Dados:

- El mismo código.
- El mismo Dataset.
- La misma configuración.
- El mismo ExperimentDefinition.

El resultado deberá ser idéntico.

---

## 52.3 Orden de ejecución

El orden en que se ejecuten las Simulation nunca modificará los resultados.

---

## 52.4 Paralelización

El uso de múltiples procesos nunca alterará los cálculos.

---

## 52.5 Persistencia

La base de datos nunca modificará el resultado de una Simulation.

Únicamente almacenará información.

# 53. Public API

## 53.1 Objetivo

Definir la API pública del simulador.

---

## 53.2 Principio

Los usuarios del proyecto únicamente interactuarán con la Application Layer.

Nunca directamente con el dominio.

---

## 53.3 Entrada principal

La ejecución estándar será:

ExperimentDefinition

↓

ExperimentExecutor

↓

ExperimentResult

---

## 53.4 API estable

Las interfaces públicas deberán mantenerse estables entre versiones menores.

---

## 53.5 API interna

Las clases internas podrán modificarse sin afectar a la API pública.

# 54. Coding Standards

## 54.1 Objetivo

Definir los criterios mínimos de implementación.

---

## 54.2 Principios

Todo el código deberá seguir:

- SOLID.
- Clean Architecture.
- Domain Driven Design.
- Composition over inheritance.

---

## 54.3 Complejidad

Se evitarán métodos largos.

Se evitarán clases con múltiples responsabilidades.

---

## 54.4 Dependencias

Las dependencias deberán apuntar siempre hacia el dominio.

Nunca al contrario.

---

## 54.5 Tests

Toda nueva funcionalidad deberá incorporar sus correspondientes pruebas.

# 55. Future Extensions

## 55.1 Objetivo

Documentar posibles ampliaciones futuras del proyecto.

---

## 55.2 AllocationPolicy

Posibles implementaciones:

- Threshold Rebalancing.
- CAPE.
- Momentum.
- Valuation.
- Glidepath con pausas.
- Glidepath no lineal.

---

## 55.3 WithdrawalPolicy

Posibles implementaciones:

- Guyton-Klinger.
- VPW.
- Floor & Ceiling.
- Guardrails.
- Dynamic Spending.

---

## 55.4 AssetClass

Posibles nuevas clases:

- Oro.
- REITs.
- Commodities.
- TIPS.
- Corporate Bonds.
- Small Cap.
- Value.

---

## 55.5 Objetivo

Todas estas ampliaciones deberán implementarse sin modificar el dominio existente.

