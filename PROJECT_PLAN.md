# FIRE Backtesting Framework (FBF)

Version: 1.0.0
Estado: Arquitectura Congelada (Frozen Specification)
Autor: OpenAI + Julio Gracia
Objetivo: Framework de investigación para estrategias de desacumulación (Safe Withdrawal Rates)

---

# 1. Objetivo

## 1.1 Propósito

Este proyecto NO pretende implementar únicamente el estudio de EarlyRetirementNow.

El objetivo es desarrollar un framework reutilizable capaz de investigar cualquier estrategia de desacumulación (withdrawal strategy) de forma completamente reproducible.

El framework debe servir tanto para:

- reproducir estudios existentes,
- extender dichos estudios,
- investigar nuevas estrategias.

Debe convertirse en una herramienta de investigación financiera.

---

## 1.2 Requisitos funcionales

El framework deberá ser capaz de estudiar:

- Carteras estáticas
- Glidepaths
- Glidepaths activos
- Nuevas reglas de retirada
- Nuevos activos
- Nuevos mercados
- Nuevos algoritmos de rebalanceo
- Monte Carlo (futuro)
- Bootstrap (futuro)

---

## 1.3 Requisitos no funcionales

El framework deberá ser:

- Determinista
- Reproducible
- Modular
- Escalable
- Extensible
- Testable
- Altamente documentado

---

## 1.4 Prioridades

Las prioridades del proyecto son:

1. Exactitud matemática.
2. Reproducibilidad.
3. Correctitud del dominio.
4. Arquitectura limpia.
5. Rendimiento.
6. Facilidad para añadir nuevas estrategias.

Nunca se sacrificará la exactitud para obtener mayor rendimiento.

---

# 2. Principios de Diseño

## 2.1 Clean Architecture

El framework seguirá Clean Architecture.

Se dividirá en cuatro capas.

```
Presentation

↓

Application

↓

Domain

↓

Infrastructure
```

La dependencia únicamente puede dirigirse hacia abajo.

Infrastructure nunca podrá ser utilizada directamente por Domain.

---

## 2.2 Separación de responsabilidades

Cada módulo tendrá una única responsabilidad.

Ejemplos:

- Portfolio únicamente conoce dinero.
- Strategy únicamente conoce pesos objetivo.
- Runner únicamente ejecuta experimentos.
- SQLite únicamente persiste resultados.

---

## 2.3 Inmutabilidad

Siempre que sea posible se utilizarán objetos inmutables.

Especialmente:

- Allocation
- AssetId
- Money
- SimulationParameters
- ExperimentConfiguration

---

## 2.4 Reproducibilidad

Toda simulación debe producir exactamente el mismo resultado cuando:

- CSV es idéntico.
- Configuración es idéntica.
- Estrategia es idéntica.
- Framework Version es idéntica.

---

## 2.5 Modularidad

Todo componente debe poder sustituirse.

Ejemplos

Nuevo algoritmo de rebalanceo.

Nueva estrategia.

Nuevo activo.

Nueva regla de retirada.

Sin modificar el motor.

---

## 2.6 Configuración

Ningún valor de negocio podrá aparecer hardcodeado.

Toda configuración deberá provenir de:

- YAML
- JSON
- Base de datos

---

# 3. Arquitectura General

```
fire_backtest/

    domain/

    application/

    infrastructure/

    presentation/

    docs/

    benchmarks/

    tests/
```

---

## Domain

Contiene únicamente lógica financiera.

No conoce:

- SQLite
- NumPy
- CLI
- Logging

---

## Application

Coordina el dominio.

Contiene:

- Runner
- Casos de uso
- Simulaciones

---

## Infrastructure

Contiene:

- SQLite
- SQLAlchemy
- CSV Loader
- Exportadores
- Logging

---

## Presentation

Contiene:

- CLI
- Futuras APIs
- Interfaz Web

---

# 4. Dominio

El dominio representa conceptos financieros.

Nunca librerías.

Nunca bases de datos.

Nunca archivos.

---

## Entidades

El dominio estará formado por entidades.

Inicialmente:

```
Asset

Portfolio

Allocation

Money

Withdrawal

Simulation

Experiment

Strategy

MarketData

SimulationResult
```

---

## Value Objects

También existirán objetos inmutables.

Ejemplos

```
AssetId

Percentage

Return

Inflation

Drawdown

Weight

AllocationTarget

WithdrawalAmount
```

---

## Servicios del Dominio

Los servicios contendrán lógica financiera.

Ejemplos

```
RebalanceService

WithdrawalService

BinarySearchService

PortfolioService
```

---

## Eventos

El dominio emitirá eventos.

Ejemplos

```
SimulationStarted

WithdrawalPerformed

AllocationChanged

PortfolioRebalanced

SimulationFinished

BinarySearchIteration
```

Los eventos no modificarán el dominio.

Únicamente informarán.

---

# 5. Flujo General

Todo experimento sigue exactamente este flujo.

```
Experiment

↓

Dataset

↓

Preprocessing

↓

Simulation Runner

↓

Simulation Engine

↓

Strategy

↓

Withdrawal Rule

↓

Portfolio

↓

Rebalance

↓

Monthly Result

↓

Simulation Result

↓

Statistics

↓

Persistence

↓

Analysis
```

---

## Experiment

Representa un estudio completo.

Ejemplo

```
Dataset

ACWI

Horizonte

60 años

Targets

0%

50%

100%

Strategies

40

Withdrawal Rules

3
```

Un Experiment puede ejecutar miles de simulaciones.

---

## Simulation

Representa una cohorte concreta.

Ejemplo

```
Inicio

1989-01

Horizonte

720 meses

Target

100%

Strategy

Glidepath 60→100

Withdrawal Rule

Constant Real
```

---

## Monthly Loop

Cada simulación sigue exactamente este orden.

```
Inicio del mes

↓

Actualizar pesos objetivo

↓

Calcular retirada

↓

Retirar utilizando el rebalanceo

↓

Si aún no coincide con AllocationTarget

Rebalancear

↓

Aplicar retornos del mes

↓

Guardar MonthlyResult

↓

Mes siguiente
```

Este orden es INMUTABLE.

No podrá modificarse sin crear un ADR.

---

## Resultado

Cada simulación devuelve un único objeto.

```
SimulationResult
```

Debe contener:

- Portfolio History
- Withdrawals
- Rebalances
- Drawdowns
- Allocation History
- Statistics
- Metadata
- Events
- Logs

Toda la información necesaria para reconstruir la simulación.

SQLite y Analysis trabajarán exclusivamente con SimulationResult.

Nunca accederán al motor.

# 6. Datos de Mercado (Market Data)

## 6.1 Filosofía

El framework trabaja exclusivamente con **retornos mensuales**.

Nunca utilizará precios como dato de entrada.

Los precios o índices acumulados se calcularán automáticamente durante el preprocesado.

Esto permite utilizar cualquier activo siempre que exista una serie de retornos.

---

## 6.2 Formato del CSV

El CSV deberá contener una fila por mes.

Campos obligatorios

date

inflation

Todos los demás campos serán interpretados como activos.

Ejemplo

date, inflation, ACWI, BOND_SHORT, BOND_LONG, MONEY

1989-01,0.0031,0.021,-0.004,0.011,0.002

1989-02,0.0018,-0.051,0.008,0.017,0.002

...

---

Cada columna representa

RETORNO TOTAL DEL MES

No precios.

No índices.

No dividendos separados.

No cotizaciones.

---

## 6.3 Dataset Registry

Los datasets no se cargarán directamente.

Cada dataset tendrá un identificador.

Ejemplo

ACWI_EUR_TOTAL_RETURN

SP500_SHILLER

MSCI_WORLD

EURO_GOV_SHORT

EURO_GOV_LONG

EUR_MONETARY

---

El objetivo es que las simulaciones almacenen

dataset_id

y no únicamente una ruta de fichero.

---

## 6.4 Validaciones

Antes de aceptar un dataset deberán comprobarse

- fechas ordenadas
- meses consecutivos
- sin duplicados
- sin valores nulos
- inflación existente
- activos existentes
- nombres únicos

Si alguna comprobación falla

InvalidDatasetException

---

# 7. Preprocesado

El preprocesado se ejecuta una única vez por dataset.

Nunca durante una simulación.

---

## 7.1 Objetivo

Reducir al mínimo el trabajo del motor.

Todo cálculo repetitivo deberá realizarse aquí.

---

## 7.2 Índices acumulados

Para cada activo

crear un índice base 100.

Ejemplo

ACWI

1989-01

100

1989-02

102.4

1989-03

98.1

...

---

## 7.3 IPC

Crear

CPI_INDEX

acumulado.

Permitirá calcular

retiradas reales.

---

## 7.4 ATH

Para cada activo

calcular

running_max

is_ath

is_underwater

drawdown

Todo quedará almacenado.

Nunca volverá a calcularse.

---

## 7.5 Drawdown

Guardar

drawdown absoluto

drawdown porcentual

duración del drawdown

profundidad máxima

Esto permitirá futuros estudios.

---

## 7.6 Caché

El resultado del preprocesado podrá serializarse.

Así no será necesario recalcularlo en futuras ejecuciones.

---

# 8. Activos

El framework no conoce activos concretos.

Únicamente conoce

Asset

---

## 8.1 Asset

Todo activo posee

AssetId

Nombre

Descripción

Moneda

Serie histórica

Metadatos

---

Nunca existen propiedades especiales.

No existe

portfolio.acwi

portfolio.money

Todo funciona mediante AssetId.

---

## 8.2 AssetId

Es un Value Object.

Ejemplos

ACWI

BOND_SHORT

BOND_LONG

MONEY

BTC

GOLD

REIT

SMALL_VALUE

---

## 8.3 Extensibilidad

Añadir un activo nuevo nunca debe requerir modificar el motor.

Únicamente

añadir columna al dataset

registrarlo

crear estrategia si fuese necesario

---

# 9. Portfolio

## 9.1 Filosofía

El portfolio almacena únicamente dinero.

Nunca participaciones.

Nunca ETFs.

Nunca fondos.

Nunca precios.

---

Cada activo tiene únicamente

valor_en_euros

---

## 9.2 Operaciones

Debe soportar

deposit()

withdraw()

buy()

sell()

apply_return()

rebalance()

allocation()

value()

---

## 9.3 Restricciones

Nunca puede existir

valor negativo

activo inexistente

dinero creado

dinero destruido

excepto mediante

retirada

o

rentabilidad.

---

## 9.4 Allocation

La asignación siempre se calcula

sobre el patrimonio total.

Nunca sobre el patrimonio invertido.

---

## 9.5 Historial

El portfolio no guarda historial.

El historial pertenece a

SimulationResult.

---

# 10. Estrategias

Las estrategias únicamente responden

¿Cuál debería ser la asignación objetivo?

Nunca realizan operaciones.

Nunca conocen dinero.

Nunca conocen el portfolio.

---

## 10.1 Interface

Toda estrategia implementa

initialize()

monthly_target()

finish()

---

## 10.2 Resultado

Devuelven

AllocationTarget

Ejemplo

ACWI

64%

BOND_SHORT

28%

MONEY

8%

---

## 10.3 Identidad

Toda estrategia posee

name

identifier

config_json

config_hash

---

config_hash

SHA256

del JSON ordenado.

---

## 10.4 Configuración

Las estrategias se crearán mediante

YAML

o

JSON.

Nunca mediante código hardcodeado.

Ejemplo

type: glidepath

start_equity: 60

end_equity: 100

slope: 0.333333

active: true

---

## 10.5 Estrategias previstas

Static Allocation

Passive Glidepath

Active Glidepath

Custom Strategy

---

## 10.6 Glidepath Pasivo

Incrementa

la asignación objetivo

todos los meses.

---

## 10.7 Glidepath Activo

Incrementa

únicamente cuando

is_underwater == true

Es decir

cuando el índice de referencia

NO está en ATH.

Si durante ese mes

el índice marca un nuevo ATH

el glidepath permanece congelado.

---

## 10.8 Validaciones

Toda estrategia debe comprobar

pesos positivos

suma igual al 100%

activos existentes

configuración válida

antes de comenzar la simulación.

En caso contrario

InvalidStrategyException.

# 11. Withdrawal Rules

## 11.1 Filosofía

Las reglas de retirada son completamente independientes del portfolio.

Su única responsabilidad es responder:

> ¿Cuánto dinero debe retirarse este mes?

Nunca ejecutan la retirada.

Nunca venden activos.

Nunca conocen el rebalanceo.

---

## 11.2 Interface

Toda regla implementará

initialize()

monthly_withdrawal()

finish()

---

## 11.3 Datos disponibles

Una WithdrawalRule podrá consultar:

- Patrimonio actual
- Patrimonio inicial
- Patrimonio máximo
- Inflación acumulada
- Mes de simulación
- Horizonte restante
- Historial de retiradas
- Historial de rentabilidades

Nunca podrá modificar estos datos.

---

## 11.4 Constant Real

Será la primera implementación.

Funcionamiento:

Retirada inicial

↓

Ajustar cada mes por IPC

↓

Nunca modificar por rentabilidad.

---

Ejemplo

Capital

360000€

SWR

4%

Retirada inicial

14400€/año

1200€/mes

Si el IPC del primer año es 2%

La retirada del segundo año será

14688€/año

---

## 11.5 Futuras reglas

VPW

Guyton-Klinger

Constant Percentage

Floor & Ceiling

Custom

No deberán requerir modificaciones en el motor.

---

# 12. Rebalanceo

## 12.1 Filosofía

El rebalanceo es un problema matemático.

Nunca una heurística.

Debe encontrar la solución óptima.

---

## 12.2 Objetivo

Minimizar

Σ compras + Σ ventas

Sujeto a

- Pesos objetivo
- Retirada solicitada
- Restricciones del portfolio

---

## 12.3 Orden mensual

El orden será SIEMPRE

1 Actualizar AllocationTarget

2 Calcular retirada

3 Ejecutar la retirada intentando satisfacer el rebalanceo

4 Si aún no coincide con AllocationTarget

Rebalancear

5 Aplicar retornos

---

## 12.4 Rebalanceo implícito

La retirada siempre intentará utilizarse para acercarse al AllocationTarget.

Ejemplo

Objetivo

60%

40%

Situación

63%

37%

Retirada

1000€

Primero se venderá RV.

Si tras esa venta se alcanza el objetivo

No habrá más operaciones.

---

## 12.5 Rebalanceo explícito

Si la retirada no ha sido suficiente

El algoritmo calculará

las compras y ventas mínimas

para alcanzar el AllocationTarget.

---

## 12.6 Restricciones

Nunca crear dinero.

Nunca destruir dinero.

Nunca dejar activos negativos.

Nunca superar el patrimonio.

---

# 13. Motor de Simulación

## 13.1 Filosofía

El Simulation Engine coordina.

No toma decisiones financieras.

Todas las decisiones pertenecen al dominio.

---

## 13.2 Responsabilidades

Para cada mes

Solicitar AllocationTarget

↓

Solicitar Withdrawal

↓

Actualizar Portfolio

↓

Aplicar retornos

↓

Generar MonthlyResult

---

## 13.3 El motor no conoce

SQLite

CSV

CLI

Logging

Gráficas

---

## 13.4 Contexto

Cada simulación recibe

Dataset

Strategy

WithdrawalRule

Horizonte

Portfolio inicial

Configuración

---

## 13.5 Resultado

Siempre devuelve

SimulationResult

Nunca escribe directamente en base de datos.

Nunca genera gráficos.

---

# 14. Binary Search

## 14.1 Objetivo

Encontrar la Safe Withdrawal Rate

que produce exactamente

el patrimonio objetivo al finalizar la simulación.

---

## 14.2 Entradas

Simulation

Target

Tolerancia

Máximo iteraciones

Valor inicial

---

## 14.3 Funcionamiento

El algoritmo ejecutará

Simulation

↓

Resultado

↓

Comparación

↓

Nuevo SWR

↓

Simulation

↓

...

Hasta converger.

---

## 14.4 Independencia

Binary Search nunca conoce

Portfolio

Strategy

Assets

Withdrawal

Únicamente recibe

SimulationResult.

---

## 14.5 Aproximación inicial

Cuando existan cohortes consecutivas

la búsqueda comenzará utilizando

la SWR obtenida para la cohorte anterior.

Esto reduce considerablemente el número de iteraciones.

---

## 14.6 Error

Si no converge

lanzará

BinarySearchDidNotConvergeException

Nunca devolverá resultados parciales.

---

# 15. Experimentos

## 15.1 Filosofía

Un experimento representa un conjunto completo de simulaciones.

No una única simulación.

---

## 15.2 Un experimento contiene

Dataset

Horizonte

Targets

Estrategias

Withdrawal Rules

Configuración

---

## 15.3 Un experimento genera

N simulaciones

↓

N resultados

↓

Estadísticas agregadas

---

## 15.4 Runner

El Runner únicamente ejecuta Experiments.

Nunca Strategies directamente.

Nunca Simulations directamente.

---

## 15.5 Paralelización

La unidad de paralelización será

la cohorte.

No el Binary Search.

No la estrategia.

Cada proceso ejecutará un conjunto de cohortes consecutivas.

## Modificación de la arquitectura

Se introduce un nuevo objeto de dominio:

SimulationContext

Su objetivo es contener toda la información INMUTABLE necesaria para ejecutar una simulación.

El SimulationContext se construye una única vez al comenzar la simulación.

A partir de ese momento ninguna parte del motor podrá modificarlo.

Contendrá como mínimo:

- ExperimentId
- SimulationId
- Dataset
- Strategy
- WithdrawalRule
- Horizonte
- Target
- Portfolio Inicial
- Configuración
- Referencias al preprocesado
- Parámetros del Binary Search
- Metadata

El Simulation Engine únicamente recibirá

SimulationContext

y el estado mutable de la simulación.

Nunca listas de parámetros independientes.

# 16. Simulation State

## 16.1 Filosofía

Toda la información mutable pertenece al SimulationState.

El estado mutable nunca debe mezclarse con la configuración.

---

## 16.2 Contenido

SimulationState contendrá

Mes actual

Portfolio actual

Historial de retiradas

Historial de rebalanceos

Historial de Allocation

Eventos

Estadísticas temporales

---

## 16.3 Inmutabilidad

SimulationContext

↓

Inmutable

SimulationState

↓

Mutable

---

## 16.4 Ventajas

Esta separación permite

- Reanudar simulaciones.
- Depuración.
- Checkpoints.
- Ejecución distribuida.
- Serialización.

---

# 17. SimulationResult

## 17.1 Filosofía

Toda simulación devuelve exactamente un objeto.

SimulationResult

Nunca múltiples estructuras.

---

## 17.2 Contenido

SimulationResult contendrá

SimulationMetadata

PortfolioHistory

WithdrawalHistory

AllocationHistory

RebalanceHistory

MonthlyStatistics

FinalStatistics

Eventos

Warnings

ExecutionStatistics

---

## 17.3 Estadísticas mínimas

Valor final

CAGR

Rentabilidad anualizada

Máximo Drawdown

Drawdown medio

Número de rebalanceos

Número de compras

Número de ventas

Retirada total

Retirada real

Retirada nominal

Tiempo de ejecución

Iteraciones Binary Search

---

## 17.4 Persistencia

SQLite nunca accederá al motor.

Persistirá exclusivamente

SimulationResult.

---

# 18. Persistencia

## 18.1 Filosofía

Toda persistencia pertenece a Infrastructure.

Nunca al dominio.

---

## 18.2 Tecnología

SQLAlchemy

Backend inicial

SQLite

El diseño permitirá migrar posteriormente a

PostgreSQL

DuckDB

MariaDB

sin modificar el dominio.

---

## 18.3 Tablas

Experiment

Run

Strategy

Dataset

Simulation

MonthlyResult

Statistics

Asset

Configuration

Event

---

## 18.4 Versionado

Nunca sobrescribir resultados.

Cada ejecución genera un nuevo Run.

---

## 18.5 Integridad

Toda clave foránea deberá existir.

No se permiten registros huérfanos.

---

# 19. Runner

## 19.1 Responsabilidad

El Runner coordina la ejecución de experimentos.

No conoce lógica financiera.

---

## 19.2 Flujo

Cargar configuración

↓

Construir Experiment

↓

Validar

↓

Preprocesar Dataset

↓

Crear Simulations

↓

Ejecutar

↓

Persistir

↓

Generar estadísticas

↓

Finalizar

---

## 19.3 Paralelización

La unidad de paralelización será

Simulation.

Cada proceso ejecutará múltiples cohortes consecutivas.

Nunca se paralelizará el Binary Search.

---

## 19.4 Recuperación

Si una simulación falla

el Runner continuará con el resto.

Los errores quedarán registrados.

---

# 20. Configuración

## 20.1 Filosofía

Toda configuración será externa.

Nunca hardcodeada.

---

## 20.2 Archivos

config.yaml

experiment.yaml

strategies/

datasets/

---

## 20.3 Configuración Global

La configuración global incluirá

Base de datos

Logging

Paralelización

Precisión

Horizonte por defecto

Binary Search

Directorios

Exportación

---

## 20.4 Configuración del Experimento

Cada experimento declarará

Dataset

Horizonte

Targets

Strategies

Withdrawal Rules

Semilla (si aplica)

Opciones de exportación

---

## 20.5 Configuración de Estrategias

Cada estrategia tendrá un fichero independiente.

Ejemplo

strategy_glidepath_active.yaml

strategy_static_60_40.yaml

strategy_static_80_20.yaml

---

## 20.6 Configuración Inmutable

Una vez comienza una simulación

la configuración queda congelada.

No puede modificarse durante la ejecución.

---

## 20.7 Validación

Toda configuración será validada antes de comenzar.

Errores posibles

InvalidConfiguration

MissingDataset

MissingStrategy

InvalidTarget

InvalidAllocation

InvalidWithdrawalRule

etc.

# 21. MarketSnapshot

## 21.1 Filosofía

El MarketSnapshot representa el estado del mercado para un único mes.

Es completamente inmutable.

Nunca conoce el pasado ni el futuro.

Únicamente contiene la información correspondiente al mes actual.

---

## 21.2 Contenido

Fecha

Retorno mensual de cada activo

Inflación mensual

Inflación acumulada

Índices acumulados

ATH

is_ath

is_underwater

Drawdown

Metadatos

---

## 21.3 Construcción

Se construye automáticamente a partir del preprocesado.

Nunca durante la simulación.

---

## 21.4 Objetivo

Evitar que las estrategias conozcan el Dataset completo.

Toda estrategia recibe únicamente el estado del mercado del mes actual.

---

# 22. DecisionContext

## 22.1 Filosofía

DecisionContext representa toda la información necesaria para tomar decisiones.

Las estrategias únicamente recibirán este objeto.

Nunca accederán directamente al Portfolio ni al Dataset.

---

## 22.2 Contenido

SimulationContext

SimulationState

MarketSnapshot

Portfolio actual

Allocation actual

Mes actual

Horizonte restante

Patrimonio inicial

Patrimonio actual

Máximo patrimonio alcanzado

Historial necesario

Metadatos

---

## 22.3 Restricciones

DecisionContext es completamente de solo lectura.

Las estrategias nunca podrán modificarlo.

---

## 22.4 Resultado

La estrategia devolverá exclusivamente

AllocationTarget

Nunca ejecutará operaciones.

Nunca modificará dinero.

Nunca modificará el Portfolio.

# 23. Sistema de Eventos

## 23.1 Filosofía

El dominio emitirá eventos.

Nunca ejecutará acciones secundarias.

Los eventos únicamente informan de que algo ha ocurrido.

---

## 23.2 Eventos previstos

ExperimentStarted

ExperimentFinished

SimulationStarted

SimulationFinished

MonthStarted

MonthFinished

WithdrawalCalculated

WithdrawalExecuted

PortfolioRebalanced

AllocationChanged

BinarySearchIteration

TargetReached

SimulationFailed

---

## 23.3 Uso

Los eventos permitirán

Logging

Persistencia

Métricas

Visualización

Depuración

Plugins

sin modificar el dominio.

---

# 24. Logging

Todo experimento deberá registrar

Fecha

Hora

Duración

Uso de RAM

Uso de CPU

Tiempo por simulación

Tiempo por Binary Search

Errores

Warnings

Configuración utilizada

---

El logging nunca podrá modificar el comportamiento del framework.

---

# 25. Validación

Todo objeto del dominio será válido desde el momento de su creación.

No existirán objetos parcialmente válidos.

Toda validación se realizará en el constructor.

---

Ejemplos

Allocation suma 100%

Pesos positivos

Horizonte positivo

Dataset existente

Strategy existente

---

# 26. Sistema de Errores

Nunca utilizar

exit()

return None

Errores silenciosos

---

Todos los errores serán excepciones tipadas.

Ejemplos

InvalidDatasetException

InvalidStrategyException

InvalidAllocationException

InvalidPortfolioException

InvalidConfigurationException

BinarySearchDidNotConvergeException

SimulationException

ExperimentException

---

# 27. Paralelización

La unidad mínima será

Simulation.

Cada proceso ejecutará múltiples cohortes consecutivas.

---

Nunca se compartirán objetos mutables entre procesos.

---

SimulationContext

puede compartirse.

SimulationState

nunca.

---

# 28. Rendimiento

No optimizar prematuramente.

Primero

correctitud.

Después

perfilado.

Finalmente

optimización.

---

Toda optimización deberá demostrar

reducción de tiempo

o

reducción de memoria

mediante benchmark.

---

# 29. Caché

La caché nunca podrá modificar resultados.

Únicamente reducir tiempo de ejecución.

---

Elementos cacheables

Dataset preprocesado

Glidepaths

Binary Search inicial

Índices

ATH

Drawdowns

---

# 30. Definición de Correctitud

Una simulación se considera correcta únicamente cuando

Produce exactamente los mismos resultados utilizando

el mismo Dataset

la misma Configuración

la misma Estrategia

la misma versión del framework

independientemente del número de procesos utilizados.


# 31. Policies

## 31.1 Objetivo

Toda decisión tomada durante una simulación deberá implementarse mediante una **Policy**.

Una Policy nunca modifica el estado del sistema.

Su única responsabilidad es recibir un contexto y devolver una decisión.

---

## 31.2 Interface

Todas las Policies implementarán el mismo ciclo de vida.

```python
initialize(context)

decide(decision_context)

finish()
```

---

## 31.3 Tipos de Policies

Primera versión

- StrategyPolicy
- WithdrawalPolicy

Versiones futuras

- RebalancePolicy
- TaxPolicy
- ContributionPolicy
- RiskPolicy
- AllocationPolicy
- OptimizationPolicy

---

## 31.4 Restricciones

Una Policy

- Nunca conoce SQLite.
- Nunca escribe archivos.
- Nunca modifica el Portfolio.
- Nunca modifica SimulationState.
- Nunca modifica SimulationContext.

Devuelve únicamente una decisión.

---

## 31.5 Composición

Las Policies deberán poder componerse.

Ejemplo

```
WithdrawalPolicy

↓

TaxPolicy

↓

RebalancePolicy
```

Cada una trabaja sobre la salida de la anterior.

---

# 32. Máquinas de Estado

Todo objeto con ciclo de vida implementará una máquina de estados explícita.

Nunca podrán existir estados imposibles.

---

## 32.1 Experiment

Estados

CREATED

↓

VALIDATED

↓

PREPROCESSED

↓

RUNNING

↓

FINISHED

↓

ARCHIVED

---

Transiciones inválidas lanzarán

InvalidExperimentStateException

---

## 32.2 Simulation

Estados

CREATED

↓

INITIALIZED

↓

RUNNING

↓

FINISHED

↓

PERSISTED

---

## 32.3 Binary Search

Estados

CREATED

↓

RUNNING

↓

CONVERGED

↓

FINISHED

o

FAILED

---

## 32.4 State Machine

Cada objeto conocerá únicamente

su estado actual

y

las transiciones válidas.

Nunca podrá saltar estados.

---

# 33. Reproducibilidad

Toda ejecución deberá poder reproducirse exactamente.

---

## 33.1 Metadata obligatoria

Framework Version

Git Commit

Git Branch

Git Dirty

Python Version

Sistema Operativo

Arquitectura CPU

Número de núcleos

RAM detectada

Fecha de inicio

Fecha de finalización

Duración

Hash SHA256 del Dataset

Hash SHA256 del fichero de configuración

Hash SHA256 de todas las estrategias

Hash SHA256 de las Withdrawal Policies

Semilla aleatoria (aunque no se utilice)

---

## 33.2 Reglas

Dos ejecuciones con

- mismo Dataset
- misma Configuración
- mismas Policies
- misma versión

deberán producir exactamente los mismos resultados.

---

## 33.3 Trazabilidad

Toda simulación deberá indicar

qué configuración produjo ese resultado.

Nunca podrán existir resultados anónimos.

---

# 34. Architecture Decision Records

Todo cambio arquitectónico deberá documentarse.

---

## 34.1 Ubicación

```
docs/

    adr/

        ADR-001.md

        ADR-002.md

        ...
```

---

## 34.2 Contenido

Cada ADR contendrá

Contexto

Problema

Alternativas

Decisión

Consecuencias

Estado

Fecha

---

## 34.3 Inmutabilidad

Los ADR aceptados nunca se modifican.

Si cambia una decisión

se crea un nuevo ADR.

---

## 34.4 ADR iniciales

ADR-001

Trabajar con retornos mensuales.

ADR-002

El Portfolio almacena euros.

ADR-003

El rebalanceo es un problema matemático.

ADR-004

SimulationContext y SimulationState están separados.

ADR-005

Las Strategies únicamente devuelven AllocationTarget.

ADR-006

Las Policies nunca modifican el estado.

ADR-007

El dominio no conoce Infrastructure.

---

# 35. Benchmarks

Existirá un proyecto de benchmarks independiente.

---

## 35.1 Objetivos

Medir

Tiempo

RAM

CPU

Escalabilidad

Iteraciones Binary Search

Tiempo por cohorte

---

## 35.2 Benchmarks mínimos

Carga del Dataset

Preprocesado

Simulación única

100 simulaciones

1000 simulaciones

10000 simulaciones

---

## 35.3 Reglas

Toda optimización deberá demostrar

una mejora medible.

No se aceptarán optimizaciones sin benchmark.

---

## 35.4 Comparación

Los benchmarks deberán permitir comparar

dos commits

dos ramas

dos versiones

y generar automáticamente un informe.

# 36. Testing

## 36.1 Filosofía

La exactitud del framework es prioritaria frente al rendimiento.

Todo componente público deberá estar cubierto por tests.

---

## 36.2 Tipos de tests

Unit Tests

Integration Tests

Regression Tests

Golden Tests

Performance Tests

Property Based Tests (Hypothesis)

Smoke Tests

---

## 36.3 Cobertura mínima

Objetivo mínimo

90%

La cobertura no sustituye a la calidad de los tests.

---

## 36.4 Golden Tests

Existirá un conjunto de simulaciones cuyo resultado será conocido.

Ejemplo

Dataset de 24 meses

3 activos

Static 60/40

Constant Real Withdrawal

Resultado esperado

- Valor final
- Retirada total
- Número de rebalanceos
- Allocation mensual
- Drawdown
- SWR

Nunca podrán modificarse estos resultados sin una justificación documentada.

---

## 36.5 Property Based Testing

Se utilizará Hypothesis para comprobar propiedades matemáticas.

Ejemplos

La suma de Allocation siempre es 100%.

El patrimonio nunca es negativo.

La suma de activos coincide con el patrimonio.

La retirada nunca crea dinero.

El rebalanceo conserva el patrimonio.

---

## 36.6 Regression Tests

Cada bug corregido deberá incluir un test que reproduzca el problema.

---

# 37. SimulationTrace

## 37.1 Filosofía

Opcionalmente una simulación podrá generar un registro completo de todas las decisiones tomadas.

Su objetivo es facilitar

- depuración
- auditoría
- comparación entre versiones
- validación científica

---

## 37.2 Activación

SimulationTrace únicamente se generará cuando

debug = true

---

## 37.3 Contenido

Cada mes almacenará

Fecha

MarketSnapshot

DecisionContext

Allocation objetivo

Allocation anterior

Retirada solicitada

Retirada ejecutada

Compras

Ventas

Rebalanceo

Eventos

Warnings

Motivos de cada decisión

---

## 37.4 Auditoría

Toda decisión deberá poder explicarse.

Ejemplos

"Glidepath no avanza porque el índice está en ATH."

"Se vende RF porque la retirada permite acercarse al AllocationTarget."

"No se rebalancea porque la retirada ya ha alcanzado el AllocationTarget."

Nunca registrar únicamente la acción.

Registrar también el motivo.

---

## 37.5 Persistencia

SimulationTrace podrá persistirse independientemente del resto de resultados.

Podrá deshabilitarse completamente para ahorrar memoria.

---

# 38. Plugins

## 38.1 Objetivo

El framework deberá poder ampliarse sin modificar el código existente.

---

## 38.2 Plugins previstos

Strategies

Withdrawal Rules

Policies

Assets

Analysis

Exportadores

Benchmarks

---

## 38.3 Registro

Todo plugin deberá registrarse automáticamente durante el arranque.

---

## 38.4 Restricciones

Un plugin nunca podrá modificar el dominio.

Únicamente podrá registrar nuevos componentes.

---

## 38.5 Compatibilidad

Todo plugin declarará

Nombre

Versión

Dependencias

Versión mínima del framework

Licencia

Autor

---

# 39. Documentación

## 39.1 Filosofía

La documentación forma parte del proyecto.

No es un añadido.

---

## 39.2 Documentación mínima

README.md

PROJECT_PLAN.md

Architecture.md

DeveloperGuide.md

Math.md

PluginGuide.md

Rebalance.md

Withdrawal.md

Glidepath.md

BinarySearch.md

DatasetFormat.md

ADR/

---

## 39.3 Docstrings

Todo elemento público deberá estar documentado.

Formato

Google Style Docstrings

---

## 39.4 Diagramas

El repositorio contendrá

Diagramas UML

Diagramas de secuencia

Diagramas de estados

Diagramas de componentes

Todos en formato editable.

---

# 40. Definición de Finalización

## 40.1 Objetivo

El proyecto se considerará terminado cuando sea capaz de reproducir completamente el estudio de EarlyRetirementNow utilizando:

- ACWI Total Return EUR
- RF gubernamental europea
- Monetario EUR

y permita modificar cualquiera de esos componentes sin alterar el motor.

---

## 40.2 Requisitos mínimos

Reproducir todos los experimentos definidos.

Ejecutar todas las cohortes históricas.

Persistir resultados.

Generar tablas comparativas.

Generar gráficos.

Permitir añadir nuevas estrategias.

Permitir añadir nuevas Withdrawal Policies.

Permitir añadir nuevos activos.

Permitir añadir nuevos experimentos.

---

## 40.3 Objetivo científico

El framework deberá servir como plataforma de investigación.

No estará limitado al estudio original.

Deberá permitir responder preguntas como

- ¿Cuál es el glidepath óptimo?

- ¿Qué SWR maximiza el patrimonio final?

- ¿Qué estrategia minimiza el riesgo de Sequence of Returns?

- ¿Cómo cambia la SWR utilizando ACWI frente al S&P500?

- ¿Qué ocurre utilizando bonos europeos?

- ¿Qué impacto tiene añadir monetarios?

- ¿Qué ocurre modificando la velocidad del glidepath?

Todo ello sin modificar el núcleo del framework.

---

## 40.4 Principio Rector

Siempre se priorizará

1. Correctitud matemática.

2. Reproducibilidad.

3. Trazabilidad.

4. Extensibilidad.

5. Rendimiento.

Nunca al contrario.

---

## 40.5 Congelación de la especificación

La versión 1.0 de esta especificación se considera congelada.

Toda modificación incompatible deberá documentarse mediante un ADR y supondrá un incremento de versión MAJOR siguiendo Semantic Versioning.
