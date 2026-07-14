# AI Chatbot con Memoria Persistente

Sistema completo de chatbot con inteligencia artificial, memoria persistente y despliegue automático.

## Características

- Frontend moderno con Next.js
- Backend con Python y FastAPI
- Base de datos Turso para memoria persistente
- Sistema RAG para búsqueda semántica
- Despliegue automático en Vercel

## Requisitos Previos

1. **Python 3.8+**
2. **Node.js 16+**
3. **Cuentas en:**
   - GitHub (con token de acceso personal)
   - Vercel (con token de acceso)
   - Turso (con token de autenticación)

## Tokens Necesarios

### GitHub Token
1. Ve a GitHub Settings > Developer settings > Personal access tokens
2. Genera un token con permisos `repo`

### Vercel Token
1. Ve a Vercel Dashboard > Settings > Tokens
2. Crea un nuevo token

### Turso Token
1. Instala Turso CLI: `curl -sSfL https://get.tur.so/install.sh | bash`
2. Inicia sesión: `turso auth login`
3. Crea una base de datos: `turso db create chatbot`
4. Obtén el URL: `turso db show chatbot --url`
5. Obtén el token: `turso db tokens create chatbot`

## Instalación Automática

### Paso 1: Clonar el repositorio

```bash
git clone <tu-repositorio>
cd ai-chatbot
```

### Paso 2: Editar archivo de configuración

Copia y edita el archivo de configuración:

```bash
cp config/.env.example config/.env
```

Edita `config/.env` con tus tokens:

```
GITHUB_TOKEN=tu_token_de_github
VERCEL_TOKEN=tu_token_de_vercel
TURSO_DB_URL=tu_url_de_turso
TURSO_AUTH_TOKEN=tu_token_de_turso
```

### Paso 3: Ejecutar script de configuración

```bash
python scripts/setup.py
```

El script automáticamente:
- Creará el repositorio en GitHub
- Subirá todo el código
- Creará la base de datos en Turso
- Desplegará el frontend en Vercel
- Iniciará el servidor backend

## Instalación Manual

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Estructura del Proyecto

```
ai-chatbot/
├── backend/
│   ├── main.py          # API principal
│   ├── rag.py           # Sistema RAG
│   ├── database.py      # Conexión Turso
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   └── components/
│   │       ├── ChatMessage.tsx
│   │       └── ChatInput.tsx
│   ├── package.json
│   └── vercel.json
├── scripts/
│   ├── setup.py         # Script principal
│   ├── setup_github.py  # Configuración GitHub
│   ├── deploy_vercel.py # Despliegue Vercel
│   └── init_turso.py    # Configuración Turso
├── config/
│   └── .env.example
└── README.md
```

## API Endpoints

### POST /chat
Envía un mensaje y recibe una respuesta del chatbot.

**Request:**
```json
{
  "message": "Hola, ¿cómo estás?",
  "user_id": "default"
}
```

**Response:**
```json
{
  "response": "¡Hola! Estoy bien, gracias por preguntar.",
  "sources": []
}
```

### GET /health
Verifica el estado del servidor.

## Funcionamiento del Sistema RAG

1. **Almacenamiento**: Cada interacción se guarda con su embedding
2. **Búsqueda**: Se buscan conversaciones similares usando similitud coseno
3. **Contexto**: Se recuperan las k conversaciones más relevantes
4. **Generación**: Se genera una respuesta usando el contexto recuperado

## Solución de Problemas

### Error de conexión a Turso
- Verifica que `TURSO_DB_URL` y `TURSO_AUTH_TOKEN` sean correctos
- Asegúrate de que la base de datos exista

### Error de despliegue en Vercel
- Verifica que `VERCEL_TOKEN` tenga permisos
- Revisa los logs en el dashboard de Vercel

### Error de GitHub
- Verifica que `GITHUB_TOKEN` tenga permisos `repo`
- Asegúrate de de que el nombre del repositorio no exista

## Licencia

MIT License
