
import threading
import socket
import struct
import time
import globalPluginHandler
import ui
import subprocess

class ForzaParser:
    def __init__(self, data):
        self.data = data
        self.size = len(data)
        self.version = "Bilinmeyen Format"
        
        # Correct offsets for FH4/FH5/FM (Standard Dash)
        self.offsets = {
            "speed": 244,
            "gear": 311,  # Corrected from 304 to 311
            "rpm": 16,
            "fuel": 272,
            "lap": 280,
            "pos": 292,
            "vx": 32,
            "vy": 36,
            "vz": 40
        }

        if self.size == 232:
            self.version = "Sled (V1)"
            self.offsets["vx"] = 32
            self.offsets["vy"] = 36
            self.offsets["vz"] = 40
        elif self.size == 331:
            self.version = "Dash (V3 - FM23)"
            self.offsets["gear"] = 307 # User confirmed 307 is active in V3
        else:
            self.version = "Dash (V2 - FH4/FH5)"
            # Default 311 is fine for V2

    def get_speed(self):
        # Body velocity: 32, 36, 40 (vx, vy, vz in m/s)
        if self.size >= 44:
            vx, vy, vz = struct.unpack_from('<fff', self.data, 32)
            return (vx**2 + vy**2 + vz**2)**0.5 * 3.6
        return 0.0

    def get_gear(self):
        if self.version == "Sled (V1)": return "N/A"
        
        off = self.offsets["gear"]
        if self.size >= off + 1:
            g = self.data[off]
            
            # FM23 (V3) Offset 307 is correct.
            # Value mapping seems standard: 0=Boş, 1=1st, 2=2nd, etc.
            # Reverse is likely 255 (0xFF/ -1 signed)
            
            if g == 0: return "Boş"
            if g == 255: return "Geri"
            return str(g)
        return "?"

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self.running, self.last_data, self.last_packet_time, self.error_msg = True, None, 0, None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.udp_listener, daemon=True)
        self.thread.start()
        # Silent repair
        threading.Thread(target=self.silent_repair, daemon=True).start()

    def silent_repair(self):
        try:
            # Try exempting common packages
            subprocess.run("CheckNetIsolation.exe LoopbackExempt -a -n=Microsoft.SunriseBaseGame_8wekyb3d8bbwe", shell=True) # FH4
            subprocess.run("CheckNetIsolation.exe LoopbackExempt -a -n=Microsoft.624F8B84B80_8wekyb3d8bbwe", shell=True) # FH5
            subprocess.run("CheckNetIsolation.exe LoopbackExempt -a -n=Microsoft.ForzaMotorsport_8wekyb3d8bbwe", shell=True) # FM8
            subprocess.run('netsh advfirewall firewall add rule name="NVDA_Forza_UDP" dir=in action=allow protocol=UDP localport=5300 profile=any', shell=True)
        except:
            pass

    def terminate(self):
        self.running = False
        super(GlobalPlugin, self).terminate()

    def udp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        try:
            sock.bind(("", 5300))
        except OSError:
             # Retry logic
            for _ in range(5):
                time.sleep(1)
                try:
                    sock.bind(("", 5300))
                    break
                except OSError:
                    pass
            else:
                self.error_msg = "Forza Portu (5300) meşgul."
                return
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024) # Usually 311-331 bytes
                with self.lock:
                    self.last_data = data
                    self.last_packet_time = time.time()
                self.error_msg = None
            except socket.timeout:
                continue
            except Exception:
                continue
        sock.close()

    def get_parser(self):
        with self.lock:
            # Only return parser if packet is fresh (< 2 seconds)
            return ForzaParser(self.last_data) if self.last_data and (time.time() - self.last_packet_time) < 2.0 else None

    def script_hizSoyle(self, gesture):
        p = self.get_parser()
        if not p:
            # Show specific error if exists
            msg = self.error_msg or "Forza verisi yok. (Oyun açık mı?)"
            ui.message(f"Hata: {msg}")
            return

        speed = int(p.get_speed())
        ui.message(f"{speed} km")

    def script_onar(self, gesture):
        ui.message("Bağlantı onarılıyor, lütfen bekleyin...")
        try:
            # Common PFNs for all Forza games
            pfns = [
                "Microsoft.ApolloBaseGame_8wekyb3d8bbwe",      # FM7
                "Microsoft.SunriseBaseGame_8wekyb3d8bbwe",     # FH4
                "Microsoft.624F8B84B80_8wekyb3d8bbwe",         # FH5
                "Microsoft.ForzaMotorsport_8wekyb3d8bbwe",     # FM2023
                "Microsoft.OpusPG_8wekyb3d8bbwe"               # FH3
            ]
            
            # 1. Loopback Exemption
            for pfn in pfns:
                subprocess.run(f"CheckNetIsolation.exe LoopbackExempt -a -n={pfn}", shell=True)
            
            # 2. Firewall Rule
            subprocess.run('netsh advfirewall firewall add rule name="NVDA_Forza_UDP" dir=in action=allow protocol=UDP localport=5300 profile=any', shell=True)
            
            ui.message("Onarım tamamlandı. Lütfen oyunu yeniden başlatın.")
        except Exception as e:
            ui.message(f"Onarım hatası: {e}")

    __gestures = {
        "kb:alt+a": "hizSoyle"
    }
