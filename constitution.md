# Constitución de Py Personal Finance

## 1. Propósito

Py Personal Finance es una aplicación de finanzas personales para registrar ingresos y gastos, clasificar los gastos como necesarios, no necesarios o inversiones, y consultar sus totales.

El MVP está dirigido a un único usuario, funciona en local y no incluye autenticación. La visión del producto incluye la gestión mes a mes, pero la vista mensual queda fuera del MVP.

## 2. Principios

### 2.1 Seguridad y privacidad por defecto

- La aplicación no debe exponerse a Internet sin autenticación y una revisión de seguridad explícita.
- Los secretos se gestionan únicamente mediante variables de entorno. Nunca se versionan en el repositorio.
- No se registran secretos, credenciales ni datos financieros identificables en logs.
- Toda entrada del cliente se valida nuevamente en el servidor.
- La base de datos no se expone públicamente; solo se publica en localhost cuando sea necesario para desarrollo.

### 2.2 Dinero exacto

- Los importes se representan con `Decimal` en Python y `NUMERIC` en PostgreSQL.
- No se usa `float` para almacenar, calcular ni transportar dinero.
- El MVP maneja una sola moneda y no incluye conversión ni símbolos configurables.

### 2.3 Integridad de los datos

- Las invariantes críticas se refuerzan en la base de datos mediante restricciones, no solo en la aplicación.
- Alembic es la única fuente de verdad para el esquema. No se permite `Base.metadata.create_all()`.
- Cada migración debe tener un `upgrade` y un `downgrade` funcional.
- Las operaciones destructivas o irreversibles requieren autorización explícita.

### 2.4 Separación de responsabilidades

- El backend expone una API REST con FastAPI y accede a PostgreSQL mediante SQLAlchemy.
- El frontend consume exclusivamente la API; nunca accede directamente a la base de datos.
- La API es el contrato entre frontend y backend y debe mantenerse documentada mediante OpenAPI.
- No se introducen capas, abstracciones ni servicios adicionales sin una necesidad demostrable.

### 2.5 Convenciones de nombres

- El contrato externo se expresa en español: rutas de API, campos JSON, tablas y columnas de base de datos.
- El código interno se escribe en inglés: módulos, clases, funciones, variables, componentes, pruebas y comentarios.
- Los DTO de frontera conservan los nombres del contrato en español para evitar traducciones innecesarias.
- Los modelos de persistencia usan atributos en inglés mapeados explícitamente a tablas y columnas en español.
- Las fechas se transportan en formato ISO 8601.

### 2.6 Simplicidad

- Se aplica YAGNI: no se implementa funcionalidad no solicitada ni se anticipan abstracciones.
- Se prefiere la biblioteca estándar y las capacidades de la plataforma antes que dependencias nuevas.
- Toda dependencia nueva debe justificarse por necesidad, mantenimiento y coste.
- El MVP no usa autenticación, multiusuario, router, librería de estado global ni tareas en segundo plano.

### 2.7 Pruebas y trazabilidad

- Cada comportamiento relevante debe tener pruebas automatizadas o evidencia de verificación explícita.
- No se declara una prueba como superada si no se ejecutó.
- Se mantiene la trazabilidad requisito → decisión técnica → tarea → implementación → prueba.
- Las especificaciones y los planes se aprueban antes de implementar.

### 2.8 Reproducibilidad

- La aplicación completa se ejecuta con Docker Compose desde un entorno limpio.
- Las dependencias se fijan mediante archivos de bloqueo (`uv.lock`, `package-lock.json`).
- Toda configuración necesaria se documenta en `.env.example`.
- Los servicios incluyen healthchecks cuando aportan valor operativo.

### 2.9 Accesibilidad y experiencia de usuario

- La interfaz se escribe en español.
- Los formularios usan etiquetas asociadas, mensajes de error claros y navegación por teclado.
- Los estados de carga, error y vacío deben ser visibles y comprensibles.
- El contraste y el foco visible son requisitos mínimos, no mejoras opcionales.

### 2.10 Observabilidad

- Los servicios registran eventos en stdout sin exponer secretos ni datos sensibles.
- El backend expone un endpoint de salud que verifica la disponibilidad de la base de datos.
- El MVP no incorpora métricas, trazas ni alertas externas.

## 3. Reglas de trabajo

- Se sigue el flujo SDD: especificación → clarificación → plan → tareas → implementación → validación.
- No se implementa una funcionalidad cuyo `spec.md` o `plan.md` esté pendiente de aprobación.
- Los cambios de alcance se reflejan primero en la especificación correspondiente.
- No se modifica ni se reutiliza el contenido de `legacy/`; se conserva únicamente como referencia histórica.
- No se realizan commits, despliegues ni operaciones externas con efectos importantes sin una solicitud explícita y se realizará una segunda confirmación de seguridad antes de cualquier acción de este tipo.
- No se ocultan fallos ni se modifican pruebas para simular un resultado exitoso.

## 4. Calidad mínima

- Backend: `ruff check`, `ruff format --check` y `pytest` deben pasar.
- Frontend: `lint`, `typecheck`, `test` y `build` deben pasar.
- Docker Compose debe levantar la aplicación desde cero.
- No debe haber secretos en el repositorio.
- La documentación operativa (`AGENTS.md` y README) debe reflejar comandos reales.

## 5. Gobernanza

- Esta constitución solo cambia cuando cambian principios generales del proyecto.
- Cualquier cambio requiere justificación, aprobación explícita y revisión de las especificaciones afectadas.
- `AGENTS.md` contiene las instrucciones operativas; este documento contiene los principios estables.
- En caso de conflicto, prevalecen la seguridad, la integridad de los datos y la trazabilidad.
