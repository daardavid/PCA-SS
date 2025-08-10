# Configuración de Build para PCAPP

## Pasos para crear distribución

### 1. Pre- Subir `PCAPP-Setup-1.0.0.exe`aración inicial
```bash
# Instalar dependencias de build
pip install pyinstaller

# Verificar que todas las dependencias están instaladas
pip install -r requirements.txt
```

### 2. Ejecutar build automatizado
```batch
# Windows
build.bat
```

### 3. Estructura de salida esperada
```
Output/
├── PCAPP-Setup-1.0.0.exe    # Instalador final
dist/
├── PCAPP/
    ├── PCAPP.exe             # Ejecutable principal
    ├── _internal/                          # Dependencias
    ├── config/                             # Configuraciones
    ├── README.md                           # Documentación
    └── LICENSE.txt                         # Licencia
```

## Optimizaciones aplicadas

### PyInstaller
- ✅ Modo `--onedir` para estructura limpia
- ✅ `--windowed` sin consola
- ✅ Exclusión de módulos de testing
- ✅ Compresión UPX para reducir tamaño
- ✅ Inclusión automática de datos (config/, i18n)

### Inno Setup
- ✅ Instalación por usuario (sin admin)
- ✅ Soporte para Windows 10+ 64-bit
- ✅ Asociación de archivos .pcaproject
- ✅ Creación de directorios de usuario
- ✅ Desinstalación limpia
- ✅ Múltiples idiomas (ES/EN)

### Distribución
- ✅ Instalador único .exe
- ✅ Tamaño optimizado (~50-80MB típico)
- ✅ Sin dependencias externas requeridas
- ✅ Datos de ejemplo incluidos

## Requisitos del sistema final

### Mínimos
- Windows 10 64-bit
- 4 GB RAM
- 200 MB espacio libre
- Pantalla 1024x768

### Recomendados  
- Windows 11 64-bit
- 8 GB RAM
- 500 MB espacio libre
- Pantalla 1920x1080

## Testing checklist

Antes de distribuir, probar en:
- [ ] VM Windows 10 limpia
- [ ] VM Windows 11 limpia
- [ ] Instalación sin permisos admin
- [ ] Todas las funciones principales
- [ ] Importar/exportar datos
- [ ] Guardado de proyectos
- [ ] Cambio de idiomas
- [ ] Desinstalación completa

## Distribución

### GitHub Releases
1. Crear tag: `v1.0.0`
2. Subir `PCA-Socioeconomicos-Setup-1.0.0.exe`
3. Incluir SHA256 checksum
4. Documentar cambios en release notes

### Checksum
```bash
# Generar checksum para verificación
certutil -hashfile "Output\PCAPP-Setup-1.0.0.exe" SHA256
```

## Troubleshooting común

### Error: "Failed to execute script"
- Verificar que todas las dependencias están en requirements.txt
- Revisar imports en hiddenimports del .spec

### Error: "ModuleNotFoundError" 
- Añadir módulo faltante a hiddenimports en .spec
- Recompilar con `--clean`

### Instalador muy grande (>100MB)
- Revisar exclusiones en .spec
- Verificar que no se incluyan archivos de test
- Considerar distribución de dependencias por separado

### Error en Matplotlib
- Asegurar que backend_tkagg está en hiddenimports
- Verificar que matplotlib.get_py2exe_datafiles() está incluido

## Futuras mejoras

### Código signing
- Obtener certificado Code Signing
- Firmar exe e instalador para evitar warnings

### Auto-updater
- Implementar verificación de actualizaciones
- Sistema de parches incrementales

### MSI corporativo
- Versión MSI para instalaciones IT
- Group Policy deployment
- Instalación silenciosa masiva
