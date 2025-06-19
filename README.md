 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//Programa Socioecon\303\263micos/README.md"	 b//Programa Socioecon\303\263micos/README.md"	
index 094fc1faf92c4d80206ac8b899600f719447b635..2e0ee16040048f7a1a960cc848aab9d5b06c208d 100644
--- a//Programa Socioecon\303\263micos/README.md"	
+++ b//Programa Socioecon\303\263micos/README.md"	
@@ -1,2 +1,19 @@
 # PCA-SS
-PCA servicio social
+Herramienta de análisis de datos con PCA usada en servicio social.
+
+## Uso básico
+
+```bash
+python main.py --excel ruta/a/archivo.xlsx \
+               --excel-output-dir ruta/salida/excel \
+               --plot-output-dir ruta/salida/plots
+```
+
+También es posible indicar varias rutas de Excel después de `--excel`:
+
+```bash
+python main.py --excel archivo1.xlsx archivo2.xlsx
+```
+
+Si no se proporcionan argumentos se utilizarán las rutas por defecto que venían
+preconfiguradas en el script.
 
EOF
)
