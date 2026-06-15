# SPEC-101 — Memoria de investigacion sobre TestClient y HTTPX ASGITransport

Fecha: 2026-06-15  
Rol: Ingeniero de software  
Alcance: investigar por que FastAPI `TestClient` y HTTPX `ASGITransport` se cuelgan al intentar convertir los tests de SPEC-101 en pruebas API reales.

## Como leer los comandos

Los comandos de esta memoria estan escritos en formato multilnea para que sean faciles de copiar y revisar.

Patron usado:

```bash
cd backend
timeout 12s poetry run python -u <<'PY'
# Codigo Python ejecutado dentro del entorno Poetry del backend
PY
```

Notas:

- `cd backend`: ejecuta la prueba desde el paquete backend.
- `timeout 12s`: corta el proceso si se queda colgado.
- `poetry run python -u`: usa el virtualenv de Poetry y salida sin buffer, para ver `print()` antes de un cuelgue.
- `<<'PY' ... PY`: heredoc de Bash; permite escribir Python normal en varias lineas.
- `faulthandler.dump_traceback_later(...)`: imprime trazas si el proceso se queda bloqueado.

## Resumen ejecutivo

El cuelgue no parece originarse en la implementacion de autenticacion, SQLAlchemy, Alembic ni las rutas de SPEC-101. Se reproduce con una aplicacion FastAPI minima y con una aplicacion Starlette minima.

La causa probable es una interaccion entre el event loop por defecto de `asyncio` en este entorno y callbacks lanzados desde otros hilos mediante `loop.call_soon_threadsafe()`. AnyIO y Starlette `TestClient` dependen de ese mecanismo para ejecutar trabajo entre hilos. En este entorno, el selector del loop por defecto puede quedarse esperando indefinidamente si no hay otro temporizador que lo despierte.

Activar `uvloop` resuelve las reproducciones minimas:

- `asyncio.call_soon_threadsafe()` desde un hilo despierta correctamente.
- `anyio.to_thread.run_sync()` completa correctamente.
- FastAPI `TestClient` completa una request.
- HTTPX `ASGITransport` completa una request contra endpoints sincronicos.

## Versiones observadas

Comando:

```bash
cd backend
poetry run python <<'PY'
import fastapi
import httpx
import starlette
import anyio

print("fastapi", fastapi.__version__)
print("starlette", starlette.__version__)
print("httpx", httpx.__version__)
print("anyio", getattr(anyio, "__version__", "unknown"))
PY
```

Resultado:

```text
fastapi 0.124.4
starlette 0.50.0
httpx 0.28.1
anyio unknown
```

Comando:

```bash
cd backend
poetry run pip freeze | rg '^(anyio|fastapi|starlette|httpx|sniffio|uvloop|trio|pytest)=='
```

Resultado relevante:

```text
anyio==4.13.0
fastapi==0.124.4
httpx==0.28.1
pytest==9.0.3
starlette==0.50.0
uvloop==0.22.1
```

## Comprobaciones realizadas

### 1. `TestClient` se cuelga con FastAPI minimo

Objetivo: comprobar si el problema aparece con una app minima, sin importar `app.main`, sin DB y sin rutas de auth.

Comando:

```bash
cd backend
timeout 12s poetry run python -u <<'PY'
import faulthandler

from fastapi import FastAPI
from fastapi.testclient import TestClient

faulthandler.dump_traceback_later(5, repeat=False)

app = FastAPI()
app.get("/ping")(lambda: {"ok": True})

print("before", flush=True)
client = TestClient(app)
print("client", flush=True)

response = client.get("/ping")
print(response.status_code, response.json(), flush=True)
PY
```

Resultado:

```text
before
client
Timeout (0:00:05)!
...
starlette/testclient.py", line 344 in handle_request
...
```

Interpretacion: el problema aparece incluso con FastAPI minimo. No depende de SQLAlchemy, migraciones, cookies ni rutas de SPEC-101.

### 2. HTTPX `ASGITransport` funciona con endpoint async puro

Objetivo: comprobar si HTTPX `ASGITransport` esta roto de forma general.

Comando:

```bash
cd backend
timeout 12s poetry run python -u <<'PY'
import asyncio

import httpx
from fastapi import FastAPI

app = FastAPI()


async def ping() -> dict[str, bool]:
    return {"ok": True}


app.get("/ping")(ping)


async def main() -> None:
    print("before", flush=True)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("client", flush=True)
        response = await client.get("/ping")
        print(response.status_code, response.json(), flush=True)


asyncio.run(main())
PY
```

Resultado:

```text
before
client
200 {'ok': True}
```

Interpretacion: `ASGITransport` funciona si toda la ejecucion permanece dentro del event loop. El problema aparece cuando el flujo necesita comunicacion entre hilos.

### 3. HTTPX `ASGITransport` se cuelga con endpoint sincronico

Objetivo: comprobar el camino que usa FastAPI para endpoints `def`, que pasan por threadpool mediante AnyIO.

Comando:

```bash
cd backend
timeout 12s poetry run python -u <<'PY'
import asyncio
import faulthandler

import httpx
from fastapi import FastAPI

faulthandler.dump_traceback_later(5, repeat=False)

app = FastAPI()


def ping() -> dict[str, bool]:
    return {"ok": True}


app.get("/ping")(ping)


async def main() -> None:
    print("before", flush=True)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("client", flush=True)
        response = await client.get("/ping")
        print(response.status_code, response.json(), flush=True)


asyncio.run(main())
PY
```

Resultado:

```text
before
client
Timeout (0:00:05)!
...
anyio/_backends/_asyncio.py", line 991 in run
...
```

Interpretacion: los endpoints sincronicos de FastAPI pasan por AnyIO/threadpool. Ese camino se cuelga en este entorno.

### 4. `anyio.to_thread.run_sync()` se cuelga aislado

Objetivo: quitar FastAPI, Starlette y HTTPX de la ecuacion y probar AnyIO directamente.

Comando:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import anyio


async def main() -> None:
    print("before", flush=True)
    result = await anyio.to_thread.run_sync(lambda: {"ok": True})
    print(result, flush=True)


anyio.run(main)
print("done", flush=True)
PY
```

Resultado:

```text
before
```

El proceso agoto el timeout.

Interpretacion: el bloqueo esta por debajo de FastAPI/Starlette, en el camino AnyIO + asyncio + worker threads.

### 5. Los hilos nativos de Python funcionan

Objetivo: descartar que el entorno no pueda crear o ejecutar hilos.

Comando con `threading`:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import queue
import threading

print("before", flush=True)

q: queue.Queue[dict[str, bool]] = queue.Queue()
t = threading.Thread(target=lambda: q.put({"ok": True}))
t.start()

print(q.get(timeout=3), flush=True)
t.join(timeout=3)
print("done", flush=True)
PY
```

Resultado:

```text
before
{'ok': True}
done
```

Comando con `ThreadPoolExecutor`:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import concurrent.futures

print("before", flush=True)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
future = executor.submit(lambda: {"ok": True})

print(future.result(timeout=3), flush=True)
executor.shutdown()
print("done", flush=True)
PY
```

Resultado:

```text
before
{'ok': True}
done
```

Interpretacion: no es una incapacidad general del entorno para crear o ejecutar hilos.

### 6. `call_soon_threadsafe()` no despierta el selector si no hay otro temporizador

Objetivo: comprobar el mecanismo concreto que AnyIO usa para devolver el resultado del hilo al event loop.

Comando sin temporizador adicional:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import asyncio
import threading


async def main() -> None:
    print("before", flush=True)

    loop = asyncio.get_running_loop()
    future: asyncio.Future[dict[str, bool]] = loop.create_future()

    def worker() -> None:
        print("worker", flush=True)
        loop.call_soon_threadsafe(future.set_result, {"ok": True})

    threading.Thread(target=worker).start()
    print(await future, flush=True)


asyncio.run(main())
print("done", flush=True)
PY
```

Resultado:

```text
before
worker
```

El proceso agoto el timeout.

Comando con un temporizador explicito:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import asyncio
import threading


async def main() -> None:
    print("before", flush=True)

    loop = asyncio.get_running_loop()
    future: asyncio.Future[dict[str, bool]] = loop.create_future()

    def set_result() -> None:
        print("callback", flush=True)
        future.set_result({"ok": True})

    def worker() -> None:
        print("worker", flush=True)
        loop.call_soon_threadsafe(set_result)

    threading.Thread(target=worker).start()

    # Este sleep programa un temporizador que despierta el selector.
    await asyncio.sleep(0.1)

    print("after sleep", future.done(), flush=True)
    print(await future, flush=True)


asyncio.run(main())
print("done", flush=True)
PY
```

Resultado:

```text
before
worker
callback
after sleep True
{'ok': True}
done
```

Interpretacion: el callback thread-safe se procesa cuando otro evento despierta el loop. Sin ese temporizador, el selector queda bloqueado. Esto explica el cuelgue de AnyIO y Starlette `TestClient`.

### 7. `uvloop` corrige las reproducciones

Objetivo: comprobar si cambiar la politica de event loop resuelve el problema sin tocar la app.

Comando con `call_soon_threadsafe()` y `uvloop`:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import asyncio
import threading

import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def main() -> None:
    print("before", flush=True)

    loop = asyncio.get_running_loop()
    future: asyncio.Future[dict[str, bool]] = loop.create_future()

    def worker() -> None:
        print("worker", flush=True)
        loop.call_soon_threadsafe(future.set_result, {"ok": True})

    threading.Thread(target=worker).start()
    print(await future, flush=True)


asyncio.run(main())
print("done", flush=True)
PY
```

Resultado:

```text
before
worker
{'ok': True}
done
```

Comando con AnyIO y `uvloop`:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import anyio


async def main() -> None:
    print("before", flush=True)
    result = await anyio.to_thread.run_sync(lambda: {"ok": True})
    print(result, flush=True)


anyio.run(main, backend_options={"use_uvloop": True})
print("done", flush=True)
PY
```

Resultado:

```text
before
{'ok': True}
done
```

Comando con FastAPI `TestClient` y `uvloop`:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
from fastapi.testclient import TestClient

from app.main import app

print("before", flush=True)

client = TestClient(app, backend_options={"use_uvloop": True})
response = client.get("/health")

print(response.status_code, response.json(), flush=True)
PY
```

Resultado:

```text
before
200 {'status': 'ok'}
```

Comando con HTTPX `ASGITransport` y `uvloop`:

```bash
cd backend
timeout 8s poetry run python -u <<'PY'
import asyncio

import httpx
import uvloop

from app.main import app

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def main() -> None:
    print("before", flush=True)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        print(response.status_code, response.json(), flush=True)


asyncio.run(main())
PY
```

Resultado:

```text
before
200 {'status': 'ok'}
```

Interpretacion: `uvloop` es una solucion practica para tests in-process en este entorno. Ademas ya esta instalado porque `uvicorn[standard]` forma parte del backend.

## Causas probables

1. Problema del event loop selector por defecto de Python en este entorno WSL/Linux al recibir wakeups desde otros hilos.
2. Interaccion entre Python 3.12, `asyncio`, AnyIO 4.13.0 y el entorno local.
3. No hay evidencia de que SQLAlchemy, la DB, Alembic, la app de OpsDesk o la implementacion de SPEC-101 sean la causa primaria.

## Opciones de solucion

### Opcion A: usar `uvloop` en tests in-process

Para `TestClient`:

```python
client = TestClient(app, backend_options={"use_uvloop": True})
```

Para HTTPX `ASGITransport`:

```python
import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```

Ventajas:

- Mantiene tests API rapidos dentro de pytest.
- Cubre rutas, dependencias, serializacion, errores y cookies sin Docker.
- Usa una dependencia ya instalada.

Riesgos:

- Acopla los tests a `uvloop`, por lo que conviene documentarlo como requisito de harness.
- Si CI corre en un entorno sin `uvloop`, habria que instalarlo o usar otra opcion.

### Opcion B: automatizar pruebas HTTP contra backend Docker/local

Ventajas:

- Valida la superficie HTTP real, incluyendo Uvicorn, red local y contenedor.
- Evita el problema in-process del event loop.

Riesgos:

- Mas lento.
- Requiere Docker activo.
- Requiere control estricto del estado de DB para no contaminar first-user bootstrap.

### Opcion C: convertir endpoints y dependencias a async

No se recomienda como solucion primaria.

Aunque HTTPX `ASGITransport` funciono con endpoints async puros, SPEC-101 usa SQLAlchemy sincronico y dependencias sincronicas. Convertir endpoints a `async def` sin cambiar el acceso DB a async podria bloquear el event loop y no resolveria `TestClient`, que tambien necesita comunicacion entre hilos para su portal.

### Opcion D: fijar o cambiar versiones de AnyIO/Python

Puede investigarse si se quiere evitar `uvloop`, pero no se ha verificado en esta sesion porque implicaria cambiar dependencias del entorno. Si se aborda, deberia hacerse con una rama o commit especifico y actualizar `poetry.lock` de forma intencional.

## Recomendacion

Para cerrar SPEC-101, implementar tests API in-process usando FastAPI `TestClient` con:

```python
TestClient(app, backend_options={"use_uvloop": True})
```

Los tests deben cubrir todos los criterios declarados en SPEC-101 y sustituir la validacion manual con `curl` por evidencia automatizada. Si en CI `uvloop` da problemas, usar como fallback un harness HTTP contra Docker/local backend, tambien automatizado.
