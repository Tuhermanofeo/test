def manage_hping3_interactive():
    """
    Versión "con color y vida" de la función interactiva para comprobar/instalar hping3
    y preparar/ejecutar un comando.

    - Igual comportamiento funcional que antes (no hace sys.exit; devuelve un dict con resultados).
    - Salidas más vívidas: colores ANSI, emojis y mensajes amistosos.
    - Todavía exige la frase exacta "I HAVE AUTHORIZATION" para ejecutar.
    - Diseñada para pegar dentro de un script existente.
    """
    import subprocess, shutil, ipaddress, getpass, time, re, sys, os

    # -----------------------
    # Helpers de color/estilo
    # -----------------------
    def supports_color():
        # Detecta soporte de color (tty o terminal que soporte ANSI)
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False
        if os.name == "nt":
            # Intentar habilitar VT processing en Windows 10+ para que ANSI funcione
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                mode = ctypes.c_uint()
                if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) != 0:
                    kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                    return True
            except Exception:
                return False
        return True

    USE_COLOR = supports_color()

    def c(text, code):
        return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

    # color palette
    G = lambda s: c(s, "32")   # green
    Y = lambda s: c(s, "33")   # yellow
    R = lambda s: c(s, "31")   # red
    B = lambda s: c(s, "34")   # blue
    M = lambda s: c(s, "35")   # magenta / fancy
    C = lambda s: c(s, "36")   # cyan
    U = lambda s: c(s, "4;37") # underlined-ish white

    # -----------------------
    # Comportamiento principal
    # -----------------------
    MANAGERS_CMDS = {
        "pkg":     "pkg install -y hping3",
        "apt":     "sudo apt update && sudo apt install -y hping3",
        "apt-get": "sudo apt-get update && sudo apt-get install -y hping3",
        "yum":     "sudo yum install -y hping3",
        "dnf":     "sudo dnf install -y hping3",
        "pacman":  "sudo pacman -Syu --noconfirm hping3",
        "zypper":  "sudo zypper install -y hping3",
        "apk":     "sudo apk add hping",  # Alpine suele llamar al paquete 'hping'
        "emerge":  "sudo emerge --sync && sudo emerge -avh net-analyzer/hping",
        "snap":    "sudo snap install hping3 || true",
        "brew":    "brew install hping || brew install hping3 || true",
    }

    def run_cmd(cmd, timeout=300, shell=True):
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=timeout, shell=shell, universal_newlines=True)
            out = (r.stdout or r.stderr or "").strip()
            return r.returncode, out
        except subprocess.TimeoutExpired:
            return 124, "timeout"
        except Exception as e:
            return 1, str(e)

    def check_hping():
        if shutil.which("hping3") is None:
            return False, "hping3 no está en PATH"
        code, out = run_cmd("hping3 --version", timeout=10)
        if code == 0:
            first = out.splitlines()[0] if out else "versión desconocida"
            return True, first
        return False, out or f"salida con código {code}"

    def detect_managers():
        found = []
        for m in MANAGERS_CMDS:
            if shutil.which(m):
                found.append(m)
        return found

    def valid_host(s):
        s = s.strip()
        if s.lower() == "localhost":
            return True
        try:
            ipaddress.ip_address(s)
            return True
        except ValueError:
            return bool(re.fullmatch(r"[A-Za-z0-9.-]{1,253}", s))

    # Resultado (no hace sys.exit)
    result = {"installed": False, "final_cmd": None, "executed": False, "returncode": None, "error": None}

    try:
        # Saludo animado
        print(M("♪♫") + " " + C("¡Vamos a revisar hping3! ✨") + " " + M("♫♪"))

        ok, info = check_hping()
        if ok:
            print(G("✅ hping3 encontrado:"), B(info))
            result["installed"] = True
        else:
            print(Y("⚠️  hping3 no disponible:"), info)
            managers = detect_managers()
            if not managers:
                print(Y("🤔 No se detectaron gestores de paquetes conocidos en PATH."))
            else:
                print(C("🔎 Gestores detectados:"), ", ".join(managers))
                for m in managers:
                    cmd = MANAGERS_CMDS.get(m)
                    if not cmd:
                        continue
                    print("\n" + M("➤") + " " + B(f"Gestor detectado: {m}"))
                    print(Y(f"  Comando propuesto: {cmd}"))
                    ans = input(G("¿Intentar instalar con este gestor? [y/N]: ")).strip().lower()
                    if ans not in ("y", "yes"):
                        print(C("  → Omitido. Siguiente..."))
                        continue
                    print(C("  Ejecutando... (puede pedir contraseña sudo)"))
                    code, out = run_cmd(cmd, timeout=900, shell=True)
                    if out:
                        # Mostrar solo las primeras líneas para no saturar
                        preview = "\n".join(out.splitlines()[:8])
                        if len(out.splitlines()) > 8:
                            preview += "\n" + C("  ...(salida truncada)")
                        print(B(f"  Salida ({m}):\n") + preview)
                    print(C(f"  Código de salida: {code}"))
                    ok, info = check_hping()
                    if ok:
                        print(G("🎉 Instalación detectada correctamente:"), B(info))
                        result["installed"] = True
                        break
                    else:
                        print(R("  ❌ hping3 aún no disponible tras este intento."))

        # Última verificación
        ok, info = check_hping()
        if not ok:
            result["error"] = f"hping3 no disponible: {info}"
            print(R("⛔") + " " + R(result["error"]))
            print(M("Si lo deseas, instala hping3 manualmente y vuelve a ejecutar esta función."))
            return result

        # Pedir objetivo y parámetros
        print("\n" + C("🚀 Preparar ejecución de hping3 (solo si estás autorizado)"))
        while True:
            target = input(G("Objetivo (IP/host) [ej. 192.0.2.1, localhost, ejemplo.com]: ")).strip()
            if valid_host(target):
                break
            print(R("Formato inválido — intenta de nuevo."))

        params = input(G("Parámetros para hping3 (ej. -S -p 80 -c 5) [vacío = ninguno]: ")).strip()

        need_sudo = (getpass.getuser() != "root")
        prefix = "sudo " if need_sudo else ""
        final_cmd = f"{prefix}hping3 {params} {target}".strip()
        result["final_cmd"] = final_cmd

        # Mensaje de advertencia coloreado y animado
        print("\n" + Y("⚠️  AVISO IMPORTANTE:") + " " + R("No ejecutes esto contra objetivos sin autorización explícita."))
        print(C("Si realmente tienes permiso y deseas ejecutar el comando ahora, escribe exactamente:"))
        print(U('  I HAVE AUTHORIZATION'))

        confirm = input(G("Confirmación (frase exacta para ejecutar; cualquier otra cosa cancela): ")).strip()
        if confirm != "I HAVE AUTHORIZATION":
            print(Y("❎ Frase de autorización incorrecta — No se ejecutará el comando."))
            print(B("Comando preparado (puedes copiar/pegar más tarde):"))
            print(M(final_cmd))
            return result

        # Cuenta regresiva vistosa
        print("\n" + C("✨ Preparando ejecución... (Ctrl-C para cancelar)"))
        try:
            for i in range(3, 0, -1):
                print(B(f"  Ejecutando en {i}... ") + ("•" * (4 - i)), end="\r", flush=True)
                time.sleep(1)
            print(" " * 40, end="\r")  # limpiar línea
        except KeyboardInterrupt:
            print(R("\n✋ Ejecución cancelada por usuario."))
            return result

        # Ejecutar y mostrar
        print(G("▶ Ejecutando: ") + M(final_cmd))
        # Nota sobre seguridad: usamos shell=True para respetar parámetros tal cual; se asume confianza en la entrada.
        try:
            proc = subprocess.Popen(final_cmd, shell=True)
            proc.wait()
            result["executed"] = True
            result["returncode"] = proc.returncode
            if proc.returncode == 0:
                print(G(f"✅ Proceso finalizó con código {proc.returncode}."))
            else:
                print(R(f"❌ Proceso finalizó con código {proc.returncode}."))
            return result
        except KeyboardInterrupt:
            print(R("\n✋ Ejecución interrumpida por usuario (SIGINT)."))
            result["error"] = "interrumpido por usuario"
            return result
        except Exception as e:
            result["error"] = str(e)
            print(R("⚠️ Error al ejecutar el comando:"), str(e))
            return result

    except Exception as e:
        result["error"] = str(e)
        print(R("💥 Ha ocurrido un error inesperado:"), str(e))
        return result


print("1.- test")
opcion = input("ingrese opcion: ")

if opcion == 1:
  manage_hping3_interactive()
