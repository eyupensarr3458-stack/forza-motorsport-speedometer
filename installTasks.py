import subprocess
import addonHandler

addonHandler.initTranslation()

def onInstall():
    """
    Runs automatically when the addon is installed.
    Attempts to fix Loopback Exemptions and Firewall rules globally.
    """
    commands = [
        # Loopback Exemptions
        "CheckNetIsolation.exe LoopbackExempt -a -n=Microsoft.ForzaMotorsport_8wekyb3d8bbwe", # FM2023
        "CheckNetIsolation.exe LoopbackExempt -a -n=Microsoft.624F8B84B80_8wekyb3d8bbwe",     # FH5
        "CheckNetIsolation.exe LoopbackExempt -a -n=Microsoft.SunriseBaseGame_8wekyb3d8bbwe",  # FH4
        
        # Firewall Rule (Generic for all Forza UDP 5300)
        'netsh advfirewall firewall add rule name="NVDA_Forza_UDP" dir=in action=allow protocol=UDP localport=5300 profile=any'
    ]

    for cmd in commands:
        try:
            # shell=True is required to run internal commands and find executables in path
            # We don't check=True because we don't want to fail the install if one fails (e.g. rule exists)
            subprocess.run(cmd, shell=True) 
        except Exception:
            pass
