def manage_hping3_interactive():
    """
    Función interactiva para comprobar/instalar hping3 y preparar/ejecutar un comando.
    Diseñada para integrarse en otro script (no hace sys.exit por cuenta propia; devuelve un dict con resultados).

    Comportamiento:
      - Intenta `hping3 --version`.
      - Si no está disponible, detecta gestores de paquetes comunes y ofrece intentar instalarlos (pregunta antes de ejecutar cada intento).
      - Si hping3 queda disponible, pide IP/host objetivo y parámetros.
      - **Solo ejecuta** hping3 si el usuario escribe exactamente: "I HAVE AUTHORIZATION".
      - Devuelve un dict:
          {
            "installed": bool,      # si hping3 está finalmente disponible
            "final_cmd": str,       # comando preparado (aunque no se haya ejecutado)
            "executed": bool,       # si se ejecutó el comando
            "returncode": int|None, # código de retorno si se ejecutó, else None
            "error": str|None       # mensaje de error si hubo problema no manejado
          }
    Nota de seguridad: No uses esta función contra sistemas que no controles o para los que no tengas permiso.
    """
    import subprocess, shutil, ipaddress, getpass, time, re

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
            return r.returncode, (r.stdout or r.stderr).strip()
        except subprocess.TimeoutExpired:
            return 124, "timeout"
        except Exception as e:
            return 1, str(e)

    def check_hping():
        if shutil.which("hping3") is None:
            return False, "hping3 no está en PATH"
        code, out = run_cmd("hping3 --version", timeout=10)
        if code == 0:
            return True, out.splitlines()[0] if out else "versión desconocida"
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

    result = {"installed": False, "final_cmd": None, "executed": False, "returncode": None, "error": None}

    try:
        ok, info = check_hping()
        if ok:
            result["installed"] = True
        else:
            # intentar instalar usando gestores detectados (pregunta para cada uno)
            managers = detect_managers()
            if managers:
                for m in managers:
                    cmd = MANAGERS_CMDS.get(m)
                    if not cmd:
                        continue
                    print(f"\nSe detectó gestor: {m}")
                    print(f"Comando propuesto: {cmd}")
                    ans = input("¿Deseas intentar ejecutar este comando para instalar hping3? [y/N]: ").strip().lower()
                    if ans not in ("y", "yes"):
                        print("Omitido:", m)
                        continue
                    print("Ejecutando (puede pedir contraseña sudo)...")
                    code, out = run_cmd(cmd, timeout=900, shell=True)
                    print(f"Resultado ({m}): código {code}. Salida:\n{out}\n")
                    ok, info = check_hping()
                    if ok:
                        result["installed"] = True
                        break
            else:
                print("No se detectaron gestores de paquete conocidos en PATH.")
        # última verificación
        ok, info = check_hping()
        if not ok:
            result["error"] = f"hping3 no disponible: {info}"
            return result

        # pedir objetivo y parámetros (no sanitizamos parámetros en exceso: se muestran antes de ejecutar)
        result["installed"] = True
        while True:
            target = input("IP/host objetivo (ej. 192.0.2.1, localhost, ejemplo.com): ").strip()
            if valid_host(target):
                break
            print("Formato inválido. Intenta de nuevo.")
        params = input("Parámetros para hping3 (ej. -S -p 80 -c 5) [vacío = ninguno]: ").strip()

        need_sudo = (getpass.getuser() != "root")
        prefix = "sudo " if need_sudo else ""
        final_cmd = f"{prefix}hping3 {params} {target}".strip()
        result["final_cmd"] = final_cmd

        print("\nATENCIÓN: No ejecutes esto contra sistemas sin autorización explícita del propietario.")
        print("Si quieres que el script ejecute el comando ahora, escribe exactamente:")
        print('  I HAVE AUTHORIZATION')
        confirm = input("Confirmación (frase exacta para ejecutar, cualquier otra cosa cancela): ").strip()
        if confirm != "I HAVE AUTHORIZATION":
            print("Confirmación no válida. No se ejecutará el comando.")
            return result

        # breve espera con posibilidad de cancelación
        print("\nEjecutando en 2 segundos (Ctrl-C para cancelar)...")
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print("Ejecutado cancelado por usuario.")
            return result

        # ejecutar y devolver código
        print("Ejecutando:", final_cmd)
        proc = subprocess.Popen(final_cmd, shell=True)
        proc.wait()
        result["executed"] = True
        result["returncode"] = proc.returncode
        return result

    except Exception as e:
        result["error"] = str(e)
        return result

print("1.- test")
opcion = input("ingrese opcion: ")

if opcion == 1:
  manage_hping3_interactive()
