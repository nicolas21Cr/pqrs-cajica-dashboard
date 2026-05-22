# Dashboard PQRS - Alcaldía de Cajicá

Aplicación en Streamlit para visualizar y gestionar PQRS por secretaría, con login, roles, dashboard institucional, filtros y edición de observaciones.

## 1. Estructura

```text
pqrs_cajica_streamlit/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── base_pqrs_cajica_prueba_streamlit.xlsx
└── .streamlit/
    └── config.toml
```

## 2. Ejecutar localmente

Abre terminal dentro de la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 3. Usuarios de prueba

| Usuario | Contraseña | Rol | Acceso |
|---|---|---|---|
| admin@cajica.gov.co | Admin123* | ADMIN | Todas las secretarías |
| gobierno@cajica.gov.co | Gobierno123* | SECRETARIA | Secretaría de Gobierno |
| hacienda@cajica.gov.co | Hacienda123* | SECRETARIA | Secretaría de Hacienda |
| planeacion@cajica.gov.co | Planeacion123* | SECRETARIA | Secretaría de Planeación |
| infraestructura@cajica.gov.co | Infra123* | SECRETARIA | Secretaría de Infraestructura |
| juridica@cajica.gov.co | Juridica123* | SECRETARIA | Secretaría Jurídica |

## 4. Seguridad

La aplicación no depende de parámetros en URL para proteger los datos. Cada usuario tiene una secretaría asignada y el filtro se aplica automáticamente después del login.

Para producción se recomienda cambiar las contraseñas de prueba y usar autenticación institucional, por ejemplo Google Workspace/OIDC, Firebase Auth o una base de usuarios formal.

## 5. Despliegue en Streamlit Cloud

1. Sube esta carpeta a un repositorio de GitHub.
2. Entra a Streamlit Cloud.
3. Crea una nueva app.
4. Selecciona el repositorio.
5. Archivo principal: `app.py`.
6. Deploy.

## 6. Despliegue en Google Cloud

Para un ambiente institucional, se recomienda desplegar en Cloud Run y conectar la persistencia a PostgreSQL/Cloud SQL.
