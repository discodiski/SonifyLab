# Legacy - Archivos Originales de SonifyLab

Este directorio contiene los archivos originales monolíticos de SonifyLab Pro que han sido reemplazados por la nueva arquitectura modular.

## Archivos Contenidos

- `SonifyLab.py` - Versión original PyQt5 (799 líneas)
- `sonifylab_gtk.py` - Versión original GTK4 (702 líneas)

## Estado: DEPRECIADO ⚠️

Estos archivos **NO** deben usarse en producción. Se mantienen únicamente como:

1. **Referencia histórica** - Para entender la evolución del código
2. **Backup temporal** - Por si se necesita recuperar funcionalidad específica durante la transición
3. **Comparación** - Para validar que la nueva implementación mantiene paridad funcional

## Migración a Nueva Arquitectura

La funcionalidad de estos archivos ha sido dividida en la nueva estructura modular:

### Funcionalidades Distribuidas

| Funcionalidad Original | Nueva Ubicación |
|------------------------|----------------|
| Lógica de conversión | `sonifylab/core/converter.py` |
| Modelos de datos | `sonifylab/models/` |
| Interfaz PyQt5 | `sonifylab/ui/pyqt5_interface.py` |
| Interfaz GTK4 | `sonifylab/ui/gtk4_interface.py` |
| Validaciones | `sonifylab/utils/file_validator.py` |
| Logging | `sonifylab/utils/logger.py` |

## Timeline de Eliminación

- ✅ **Fase 1** (Completada): Nueva arquitectura implementada y funcional
- ⏳ **Fase 2** (En curso): Testing y validación de paridad funcional
- 🔜 **Fase 3** (Pendiente): Eliminación definitiva de legacy (v2.0.0)

## Notas para Desarrolladores

Si necesitas referenciar código de estos archivos:

1. **No copies código directamente** - Mejor reimplementa en la nueva arquitectura
2. **Verifica tests** - Asegúrate que la nueva implementación pasa todos los tests
3. **Documenta cambios** - Si encuentras diferencias funcionales, repórtalas

## Comandos Útiles

```bash
# Comparar funcionalidades (ejemplo)
diff <(grep "def " SonifyLab.py | sort) <(find ../sonifylab -name "*.py" -exec grep "def " {} \; | sort)

# Buscar una función específica en legacy
grep -n "nombre_funcion" SonifyLab.py

# Ver estadísticas de código
wc -l SonifyLab.py sonifylab_gtk.py
```

---

**Fecha de depreciación**: 2024
**Reemplazado por**: Arquitectura modular v2.0.0
**Mantenimiento**: Solo correcciones críticas de seguridad hasta eliminación definitiva
