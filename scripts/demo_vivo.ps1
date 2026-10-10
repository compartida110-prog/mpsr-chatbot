<#
  Demostración EN VIVO del proyecto MPSR: estructura, entrenamiento del SVM de referencia y de Rasa/DIET, demo interactiva y pruebas.
  Se lanza con doble clic en scripts\demo_vivo.bat  (o:  powershell -ExecutionPolicy Bypass -NoExit -File scripts\demo_vivo.ps1)

  Opciones:  -Auto            sin pausas ni preguntas (para probar la demo de principio a fin)
             -Rapida          DEMO RÁPIDA: entrena DIET con 20 épocas en lugar de 100 (NO es la configuración oficial)
             -Pruebas ejecutar|guardado|preguntar   paso 7: correr las 9 pruebas (~25 min) o mostrar el último resultado completo

  Reglas: NO modifica el modelo congelado, las particiones, el corpus real, el lote 2 ni los datos privados; NO evalúa el test; no hace commit ni push.
  Todo lo que genera va a models\demo_vivo\ y logs\demo_vivo_AAAAMMDD_HHMM.txt (ambos ignorados por Git).
#>
param(
    [switch]$Auto,
    [switch]$Rapida,
    [ValidateSet("preguntar", "ejecutar", "guardado")][string]$Pruebas = "preguntar"
)
$ErrorActionPreference = "Continue"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
try { chcp 65001 | Out-Null; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$env:PYTHONIOENCODING = "utf-8"; $env:TF_CPP_MIN_LOG_LEVEL = "3"; $env:PYTHONWARNINGS = "ignore"; $env:PYTHONUNBUFFERED = "1"
$host.UI.RawUI.WindowTitle = "MPSR demo en vivo"

New-Item -ItemType Directory -Force -Path (Join-Path $raiz "logs") | Out-Null
$log = Join-Path $raiz ("logs\demo_vivo_{0}.txt" -f (Get-Date -Format "yyyyMMdd_HHmm"))
Start-Transcript -Path $log -Force | Out-Null

$estado = [ordered]@{}
$tiempos = @{}
function Banner($n, $titulo, $que) {
    Write-Host ""
    Write-Host ("=" * 100) -ForegroundColor Cyan
    Write-Host ("  PASO {0} — {1}" -f $n, $titulo) -ForegroundColor Yellow
    Write-Host ("  {0}" -f $que) -ForegroundColor Gray
    Write-Host ("=" * 100) -ForegroundColor Cyan
}
function Pausa {
    if ($Auto) { return }
    Write-Host ""
    Read-Host "  >> Presiona Enter para continuar" | Out-Null
}
function Ok($t) { Write-Host "  [OK] $t" -ForegroundColor Green }
function Falla($t) { Write-Host "  [FALLÓ] $t" -ForegroundColor Red }
function Py {
    # ejecuta Python y devuelve el código de salida; el resultado se ve en pantalla
    & $script:py @args | Out-Host        # Out-Host: la salida va a pantalla y al registro, y la función devuelve SOLO el código de salida
    return [int]$LASTEXITCODE
}
function Cierra($n, $codigo, $mensaje) {
    if ($codigo -eq 0) { $script:estado[$n] = "OK"; Ok $mensaje } else { $script:estado[$n] = "FALLÓ (código $codigo)"; Falla "$mensaje (código $codigo). Revisa el error de arriba; los pasos que no dependen de éste continúan." }
}

Write-Host ""
Write-Host "  DEMOSTRACIÓN EN VIVO — Chatbot MPSR (Rasa NLU / DIET y SVM de referencia)" -ForegroundColor Cyan
Write-Host "  Registro de esta sesión: $log" -ForegroundColor DarkGray
if ($Auto) { Write-Host "  Modo automático (-Auto): sin pausas." -ForegroundColor DarkGray }

# ----------------------------------------------------------------------------------- PASO 0
Banner 0 "Comprobaciones" "Carpeta, rama y git status; localizar el entorno de Python con Rasa 3.6 (venv o conda) y mostrar versiones. Se usa 'python -m', nunca pip.exe ni rasa.exe."
Write-Host "  Carpeta: $(Get-Location)"
Write-Host "  Rama:    $(git branch --show-current)"
Write-Host "  git status --short (antes de la demo):" -ForegroundColor Gray
$gs = git status --short
if ($gs) { $gs | ForEach-Object { Write-Host "    $_" } } else { Write-Host "    (limpio)" }
$candidatos = @((Join-Path $raiz "venv\Scripts\python.exe"))
if (Get-Command conda -ErrorAction SilentlyContinue) {
    try { (conda env list 2>$null) | Where-Object { $_ -and $_ -notmatch '^#' } | ForEach-Object { $p = ($_ -split '\s+')[-1]; if (Test-Path (Join-Path $p "python.exe")) { $candidatos += (Join-Path $p "python.exe") } } } catch {}
}
$py = $null
foreach ($c in $candidatos) {
    if (Test-Path $c) {
        & $c -c "import rasa, sklearn" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $py = $c; break }
    }
}
if (-not $py) {
    Falla "No encontré un Python con Rasa (busqué venv\Scripts\python.exe y los entornos de conda). Sin entorno no se puede continuar."
    Stop-Transcript | Out-Null
    if (-not $Auto) { Read-Host "  Enter para cerrar" | Out-Null }
    exit 1
}
$env:PATH = "$(Split-Path $py);$env:PATH"      # equivale a activar el venv sin ejecutar Activate.ps1 (que la política de ejecución puede bloquear)
Write-Host "  Entorno: $py" -ForegroundColor Green
& $py -c "import sys, rasa, sklearn, numpy, pandas; print('  Python', sys.version.split()[0], '| Rasa', rasa.__version__, '| scikit-learn', sklearn.__version__, '| numpy', numpy.__version__, '| pandas', pandas.__version__)"
$c0 = Py scripts\demo_vivo.py snapshot guardar
Cierra "0" $c0 "Comprobaciones hechas (huellas de los archivos protegidos guardadas para compararlas al final)"
Pausa

# ----------------------------------------------------------------------------------- PASO 1
Banner 1 "Estructura del proyecto" "Árbol resumido (configs/, data/, corpus/, scripts/, logs/), pipeline de Rasa del modelo congelado y configuración del SVM."
$c = Py scripts\demo_vivo.py estructura
Cierra "1" $c "Estructura mostrada"
Pausa

# ----------------------------------------------------------------------------------- PASO 2
Banner 2 "Datos de entrenamiento (solo conteos)" "Frases por partición, intenciones, categorías y origen sintético/real. NO se imprime ninguna frase real ni código de participante."
$c = Py scripts\demo_vivo.py datos
Cierra "2" $c "Conteos mostrados"
Pausa

# ----------------------------------------------------------------------------------- PASO 3
Banner 3 "Congelamiento del modelo (solo lectura)" "Verifica las 5 huellas sha256 de LOTE2-FINAL v1 (modelo, configuración, dominio, entrenamiento, umbral). Debe decir «intacto»."
$c = Py scripts\congelar_modelo.py --verificar
Cierra "3" $c "Verificación del modelo congelado (debe decir «Modelo congelado intacto»)"
Pausa

# ----------------------------------------------------------------------------------- PASO 4
Banner 4 "SVM de referencia (TF-IDF + SVM lineal)" "Entrena con el entrenamiento sintético, elige C en VALIDACIÓN y evalúa SOLO en validación. El test no se usa. Guarda en models\demo_vivo\."
$sw = [Diagnostics.Stopwatch]::StartNew()
$c = Py scripts\demo_vivo.py svm
$tiempos["svm"] = $sw.Elapsed.TotalSeconds
Cierra "4" $c "SVM entrenado y evaluado en validación"
$okSvm = ($c -eq 0)
Pausa

# ----------------------------------------------------------------------------------- PASO 5
Banner 5 "Rasa / DIET: entrenamiento en vivo" "Misma configuración del modelo congelado: DIET 100 épocas, batch 64, embedding 20, lr 0.001, semilla 42, FallbackClassifier 0.50. Se guarda en models\demo_vivo\ y se evalúa SOLO en validación."
# Rasa agrega "assistant_id" al archivo de configuracion que se le pasa a "rasa train"; por eso se entrena con una COPIA byte a byte (nunca con el archivo congelado).
$cfg = "models\demo_vivo\config_oficial_copia.yml"
New-Item -ItemType Directory -Force -Path "models\demo_vivo" | Out-Null
Copy-Item "configs\rasa_config_lote2.yml" $cfg -Force
$modo = "OFICIAL (100 épocas)"
$quiereRapida = $Rapida.IsPresent
if (-not $Auto -and -not $Rapida) {
    $r = Read-Host "  Enter = entrenamiento OFICIAL (100 épocas, unos 5-10 min).  R = DEMO RÁPIDA (20 épocas, NO oficial)"
    if ($r -match '^[rR]') { $quiereRapida = $true }
}
if ($quiereRapida) {
    Py scripts\demo_vivo.py config-rapida | Out-Null
    $cfg = "models\demo_vivo\config_rapida.yml"
    $modo = "DEMO RÁPIDA (20 épocas) — NO es la configuración oficial"
    Write-Host "  *** DEMO RÁPIDA: 20 épocas. Los números NO son los de la configuración oficial. ***" -ForegroundColor Magenta
}
Write-Host "  Modo: $modo" -ForegroundColor Yellow
Write-Host "  Comando: python -m rasa train nlu --nlu data\nlu_train.yml --config $cfg --domain domain_v3.yml --out models\demo_vivo --fixed-model-name DEMO-VIVO" -ForegroundColor DarkGray
if (Test-Path "models\demo_vivo\rasa_cache") { Remove-Item "models\demo_vivo\rasa_cache" -Recurse -Force }      # cache propia y VACIA: si Rasa reutiliza su cache, el "entrenamiento" dura segundos y no se ven las epocas
$env:RASA_CACHE_DIRECTORY = (Join-Path $raiz "models\demo_vivo\rasa_cache")
if (Test-Path "models\demo_vivo\DEMO-VIVO.tar.gz") { Remove-Item "models\demo_vivo\DEMO-VIVO.tar.gz" -Force }   # solo el modelo de la demo; nunca models\rasa\
$sw = [Diagnostics.Stopwatch]::StartNew()
& $py -m rasa train nlu --nlu data\nlu_train.yml --config $cfg --domain domain_v3.yml --out models\demo_vivo --fixed-model-name DEMO-VIVO
$cTrain = $LASTEXITCODE
$tiempos["diet"] = $sw.Elapsed.TotalSeconds
$okDiet = ($cTrain -eq 0) -and (Test-Path "models\demo_vivo\DEMO-VIVO.tar.gz")
Write-Host ("  Entrenamiento de DIET: {0:N0} s ({1:N1} min)" -f $tiempos["diet"], ($tiempos["diet"] / 60)) -ForegroundColor Yellow
if ($okDiet) {
    Cierra "5" 0 "DIET entrenado ($modo)"
    $c = Py scripts\demo_vivo.py diet-eval
    Cierra "5b" $c "DIET evaluado en validación"
} else {
    Cierra "5" 1 "El entrenamiento de DIET no terminó (no se evalúa ni se usa en el paso 6)"
    if ($tiempos["diet"] -gt 600) { Write-Host "  Tardó mucho: puedes relanzar con la versión DEMO RÁPIDA:  scripts\demo_vivo.bat  y elegir R (o -Rapida)." -ForegroundColor Magenta }
}
Pausa

# ----------------------------------------------------------------------------------- PASO 6
Banner 6 "Demostración interactiva" "8 frases SINTÉTICAS (5 claras, 2 ambiguas, 1 fuera de alcance) con DIET y SVM: intención, confianza y si responde o se abstiene («no entendí»). Después, escribe tu propia frase."
if ($okSvm -or $okDiet) {
    if ($Auto) { $c = Py scripts\demo_vivo.py interactivo --auto } else { $c = Py scripts\demo_vivo.py interactivo }
    Cierra "6" $c "Demostración interactiva"
} else {
    Cierra "6" 1 "No hay ningún modelo de la demo (SVM y DIET fallaron)"
}
Pausa

# ----------------------------------------------------------------------------------- PASO 7
Banner 7 "Pruebas automáticas" "El proyecto NO usa pytest (no está instalado y las pruebas son scripts independientes tests\smoke_*.py con datos falsos). Se suman sus comprobaciones. Ninguna toca el test ni los datos reales."
$modoPruebas = $Pruebas
if ($modoPruebas -eq "preguntar") {
    if ($Auto) { $modoPruebas = "guardado" }
    else {
        $r = Read-Host "  Enter = mostrar el último resultado completo guardado.  E = EJECUTAR las 9 pruebas ahora (~25 min)"
        $modoPruebas = if ($r -match '^[eE]') { "ejecutar" } else { "guardado" }
    }
}
$sw = [Diagnostics.Stopwatch]::StartNew()
$c = Py scripts\demo_vivo.py pruebas $modoPruebas
$tiempos["pruebas"] = $sw.Elapsed.TotalSeconds
Cierra "7" $c "Pruebas ($modoPruebas): copia el TOTAL de arriba para la diapositiva 7"
Pausa

# ----------------------------------------------------------------------------------- PASO 8
Banner 8 "Cierre" "Vuelve a verificar el modelo congelado, compara las huellas de los archivos protegidos con las del inicio y revisa git status."
$c = Py scripts\congelar_modelo.py --verificar
Cierra "8a" $c "Modelo congelado verificado de nuevo"
$c = Py scripts\demo_vivo.py snapshot comparar
Cierra "8b" $c "Archivos protegidos sin cambios respecto al inicio"
Write-Host "  git status --short (después de la demo):" -ForegroundColor Gray
$gs2 = git status --short
if ($gs2) { $gs2 | ForEach-Object { Write-Host "    $_" } } else { Write-Host "    (limpio)" }
Write-Host "  ¿Ignorado por Git lo que genera la demo?" -ForegroundColor Gray
git check-ignore -v models/demo_vivo/DEMO-VIVO.tar.gz "logs/demo_vivo_ejemplo.txt" 2>&1 | ForEach-Object { Write-Host "    $_" }

# ----------------------------------------------------------------------------------- resumen
Write-Host ""
Write-Host ("=" * 100) -ForegroundColor Cyan
Write-Host "  RESUMEN" -ForegroundColor Yellow
foreach ($k in $estado.Keys) {
    $col = if ($estado[$k] -eq "OK") { "Green" } else { "Red" }
    Write-Host ("    Paso {0,-3} {1}" -f $k, $estado[$k]) -ForegroundColor $col
}
try {
    $m1 = Get-Content "models\demo_vivo\svm_metricas.json" -Raw | ConvertFrom-Json
    Write-Host ("    SVM : F1 macro validación {0:N4} · exactitud {1:N4} · {2:N1} s" -f $m1.f1_macro_validacion, $m1.accuracy_validacion, $m1.segundos)
} catch {}
try {
    $m2 = Get-Content "models\demo_vivo\diet_metricas.json" -Raw | ConvertFrom-Json
    Write-Host ("    DIET: F1 macro validación {0:N4} · cobertura (t=0.50) {1:P1} · entrenamiento {2:N0} s ({3})" -f $m2.f1_macro_validacion, $m2.cobertura, $tiempos["diet"], $modo)
} catch {}
Write-Host "    Registro completo: $log"
Write-Host ("=" * 100) -ForegroundColor Cyan
Stop-Transcript | Out-Null
if (-not $Auto) { Read-Host "  Enter para cerrar" | Out-Null }
