// ── Security threats ──────────────────────────────────────────────────────────
// Sources: MITRE ATT&CK, Sysinternals abuse reports, threat intel feeds
const DANGEROUS_PROCS = {
  // VPN / proxy bypass
  'xray.exe':         'VPN/proxy bypass (Xray)',
  'xray':             'VPN/proxy bypass (Xray)',
  'v2ray.exe':        'VPN/proxy bypass (V2Ray)',
  'v2ray':            'VPN/proxy bypass (V2Ray)',
  'sing-box.exe':     'VPN/proxy bypass (sing-box)',
  'sing-box':         'VPN/proxy bypass (sing-box)',
  'trojan.exe':       'Proxy bypass (Trojan)',
  'trojan':           'Proxy bypass (Trojan)',
  'trojan-go.exe':    'Proxy bypass (Trojan-Go)',
  'trojan-go':        'Proxy bypass (Trojan-Go)',
  'shadowsocks.exe':  'Proxy bypass (Shadowsocks)',
  'sslocal.exe':      'Proxy bypass (Shadowsocks)',
  'clash.exe':        'Proxy client (Clash)',
  'clash-meta.exe':   'Proxy client (Clash Meta)',
  'mihomo.exe':       'Proxy client (Mihomo)',
  'tor.exe':          'Anonymization (Tor)',
  'tor':              'Anonymization (Tor)',
  'openvpn.exe':      'VPN client (OpenVPN)',
  'openvpn':          'VPN client (OpenVPN)',
  'wireguard.exe':    'VPN client (WireGuard)',
  'wg.exe':           'VPN client (WireGuard)',
  'openconnect.exe':  'VPN client (OpenConnect)',
  'proxifier.exe':    'Traffic proxy (Proxifier)',
  'proxycap.exe':     'Traffic proxy (ProxyCap)',
  // Tunnels / reverse proxies
  'ngrok.exe':        'Reverse tunnel (ngrok)',
  'ngrok':            'Reverse tunnel (ngrok)',
  'frpc.exe':         'Reverse tunnel (FRP client)',
  'frpc':             'Reverse tunnel (FRP client)',
  'frps.exe':         'Reverse tunnel (FRP server)',
  'chisel.exe':       'Reverse tunnel (Chisel)',
  'chisel':           'Reverse tunnel (Chisel)',
  'ligolo-ng.exe':    'Reverse tunnel (Ligolo)',
  'plink.exe':        'SSH tunnel (PuTTY Link)',
  'stunnel.exe':      'SSL tunnel (stunnel)',
  // Remote access (abused)
  'anydesk.exe':      'Remote access (AnyDesk)',
  'anydesk':          'Remote access (AnyDesk)',
  'ultraviewer.exe':  'Remote access (UltraViewer)',
  'ammyyadmin.exe':   'Remote access (Ammyy Admin)',
  'radmin.exe':       'Remote access (Radmin)',
  'radminserver.exe': 'Remote access (Radmin Server)',
  'supremo.exe':      'Remote access (Supremo)',
  'atera.exe':        'RMM agent (Atera)',
  'screenconnect.exe':'Remote access (ScreenConnect)',
  // Credential / exploitation tools
  'mimikatz.exe':     'Credential dumping (Mimikatz)',
  'procdump.exe':     'Memory dump tool (ProcDump)',
  'procdump64.exe':   'Memory dump tool (ProcDump64)',
  'wce.exe':          'Credential tool (WCE)',
  'pwdump.exe':       'Credential dump (pwdump)',
  'gsecdump.exe':     'Credential dump (gsecdump)',
  'fgdump.exe':       'Credential dump (fgdump)',
  // Post-exploitation / C2
  'psexec.exe':       'Remote execution (PsExec)',
  'psexec64.exe':     'Remote execution (PsExec64)',
  'paexec.exe':       'Remote execution (PAExec)',
  'cobalt strike':    'C2 framework (Cobalt Strike)',
  'beacon.exe':       'C2 beacon (Cobalt Strike)',
  'meterpreter':      'C2 agent (Metasploit)',
  // Network recon
  'nmap.exe':         'Network scanner (Nmap)',
  'nmap':             'Network scanner (Nmap)',
  'masscan.exe':      'Port scanner (Masscan)',
  'zmap.exe':         'Network scanner (ZMap)',
  'netcat.exe':       'Network utility (Netcat)',
  'nc.exe':           'Network utility (Netcat)',
  'ncat.exe':         'Network utility (Ncat)',
  'socat.exe':        'Socket relay (socat)',
  'socat':            'Socket relay (socat)',
  // Password attacks
  'hydra.exe':        'Brute-force tool (Hydra)',
  'hydra':            'Brute-force tool (Hydra)',
  'medusa.exe':       'Brute-force tool (Medusa)',
  'hashcat.exe':      'Password cracker (Hashcat)',
  'hashcat':          'Password cracker (Hashcat)',
  'john.exe':         'Password cracker (John)',
  'john':             'Password cracker (John)',
  // Process / system tools (dual-use, frequently abused)
  'processhacker.exe':  'Process inspector (Process Hacker)',
  'processhacker2.exe': 'Process inspector (Process Hacker)',
  'pe-sieve.exe':       'PE sniffer (PE-sieve)',
  'hollows_hunter.exe': 'Process scan tool',
}

// ── Games & entertainment ─────────────────────────────────────────────────────
// Sources: PCGamingWiki, Steam DB, popular launcher process lists
const GAMES_PROCS = new Set([
  // Steam ecosystem
  'steam.exe', 'steamservice.exe', 'steamwebhelper.exe',
  'gameoverlayui.exe', 'steamupdater.exe', 'steamtriage.exe',
  // Epic Games
  'epicgameslauncher.exe', 'epicwebhelper.exe', 'epiconlineservices.exe',
  'easyanticheat.exe', 'easyanticheat_launcher.exe',
  // Roblox
  'robloxplayerbeta.exe', 'robloxplayerlauncher.exe', 'robloxcrashhandler.exe',
  'robloxstudio.exe', 'roblox.exe',
  // EA / Origin
  'origin.exe', 'originwebhelperservice.exe', 'originclientservice.exe',
  'eadesktop.exe', 'eabackgroundservice.exe', 'easteamproxy.exe',
  'eaanticheat.exe',
  // GOG Galaxy
  'gogalaxy.exe', 'goggalaxy.exe',
  // Ubisoft Connect
  'ubisoftconnect.exe', 'upc.exe', 'uplaywebcore.exe', 'ubisoftgamerunner.exe',
  // Battle.net / Blizzard
  'battle.net.exe', 'battlenet.exe', 'agent.exe', 'bna.exe',
  // Riot Games
  'riotclientservices.exe', 'riotclientux.exe', 'riotclientuxrender.exe',
  'leagueclientux.exe', 'leagueclient.exe',
  // Rockstar
  'rockstargameslauncher.exe', 'socialclub.exe',
  // Bethesda
  'bethesdanetlauncher.exe',
  // Xbox / Microsoft Store gaming
  'xboxapp.exe', 'gamingservices.exe',
  // Overwolf (gaming overlay)
  'overwolf.exe', 'overwolfbrowser.exe',
  // Popular games
  'fortnitelauncher.exe', 'fortniteclient-win64-shipping.exe',
  'cs2.exe', 'csgo.exe',
  'dota2.exe',
  'valorant.exe', 'valorant-win64-shipping.exe', 'vanguard.exe',
  'gta5.exe', 'gtav.exe', 'rdr2.exe',
  'wow.exe', 'wowclassic.exe',
  'hearthstone.exe', 'overwatch.exe', 'overwatch2.exe',
  'r5apex.exe',           // Apex Legends
  'cyberpunk2077.exe',
  'eldenring.exe', 'sekiro.exe', 'darksoulsiii.exe', 'darksoulsremastered.exe',
  'minecraft.exe', 'minecraftlauncher.exe',
  'witcher3.exe', 'witcher2.exe',
  'destiny2.exe',
  'pubg.exe', 'tslgame.exe',
  'pathofexile.exe', 'pathofexile_x64.exe',
  'diablo4.exe', 'diablo3.exe', 'd3.exe',
  'starcraft2.exe', 'sc2.exe',
  'warframe.exe', 'warframe.x64.exe',
  'escape from tarkov.exe',
  'hunt.exe',             // Hunt: Showdown
  'theforest.exe', 'sonsoftheforest.exe',
  'rust.exe',
  'palworld.exe',
  'helldivers2.exe',
  'hogwartslegacy.exe',
  'starfield.exe',
  'baldursgate3.exe', 'bg3.exe',
  // Anti-cheat engines (indicate gaming)
  'beservice.exe', 'beservice_x64.exe',   // BattlEye
  'pbsvc.exe', 'pbcl.exe',                 // PunkBuster
  'anticheatenginex64.exe',
  'faceitclient.exe', 'faceit.exe',
  // Media / streaming
  'spotify.exe',
  'vlc.exe',
  'itunes.exe', 'ituneshelper.exe',
  'amazonmusic.exe',
  'deezer.exe',
])

// ── Browsers ──────────────────────────────────────────────────────────────────
const BROWSERS_PROCS = new Set([
  'chrome.exe', 'msedge.exe', 'firefox.exe', 'opera.exe', 'brave.exe',
  'iexplore.exe', 'chromium.exe', 'vivaldi.exe',
  'safari',                       // macOS
  'yandex.exe', 'browser.exe',    // Yandex Browser
  'operagx.exe', 'launcher_opera_gx.exe',
  'arc.exe',                      // Arc browser
  'thorium.exe', 'waterfox.exe', 'librewolf.exe', 'palemoon.exe',
  'slimjet.exe', 'centbrowser.exe',
])

// ── Communications ────────────────────────────────────────────────────────────
const COMMS_PROCS = new Set([
  // Microsoft
  'teams.exe', 'ms-teams.exe',       // Teams classic + new
  'outlook.exe', 'olk.exe',          // Outlook classic + new
  'lync.exe',                         // Skype for Business
  // Slack
  'slack.exe',
  // Zoom
  'zoom.exe', 'zoomshare.exe', 'caphost.exe',
  // Messaging
  'telegram.exe', 'telegram desktop.exe',
  'whatsapp.exe',
  'skype.exe', 'skypehost.exe', 'skypebackgroundhost.exe',
  'signal.exe',
  'viber.exe',
  'discord.exe', 'discordptb.exe', 'discordcanary.exe',
  'element.exe',          // Matrix/Element
  'mattermost.exe',
  // Email clients
  'thunderbird.exe',
  'mailbird.exe',
  'eM client.exe',
  // Productivity comms
  'notion.exe',
  'obsidian.exe',
  'clickup.exe',
])

// ── Developer tools ───────────────────────────────────────────────────────────
const DEV_PROCS = new Set([
  // Editors / IDEs
  'code.exe', 'code - insiders.exe', 'code',       // VS Code
  'devenv.exe',                                      // Visual Studio
  'idea64.exe', 'idea.exe',                          // IntelliJ IDEA
  'pycharm64.exe', 'pycharm.exe',
  'webstorm64.exe', 'webstorm.exe',
  'rider64.exe', 'rider.exe',
  'datagrip64.exe', 'datagrip.exe',
  'clion64.exe', 'clion.exe',
  'goland64.exe', 'goland.exe',
  'phpstorm64.exe', 'phpstorm.exe',
  'studio64.exe',                   // Android Studio
  'sublime_text.exe', 'sublime text',
  'atom.exe',
  'notepad++.exe',
  'cursor.exe',                     // Cursor AI IDE
  'zed.exe', 'zed',
  // Runtimes / interpreters
  'node.exe', 'node',
  'python.exe', 'python3.exe', 'python3', 'python',
  'ruby.exe', 'ruby',
  'perl.exe', 'perl',
  'php.exe', 'php',
  'java.exe', 'javaw.exe', 'java',
  'dotnet.exe', 'dotnet',
  'go.exe', 'go',
  'rustc.exe', 'cargo.exe',
  'bun.exe', 'bun',
  'deno.exe', 'deno',
  // VCS
  'git.exe', 'git',
  'git-remote-https.exe',
  'sourcetree.exe', 'gitkraken.exe', 'fork.exe',
  // Terminal / shell
  'windowsterminal.exe', 'wt.exe',
  'pwsh.exe', 'pwsh',
  'powershell.exe',
  'cmd.exe',
  'wsl.exe', 'wslhost.exe', 'wslservice.exe',
  'iterm2', 'alacritty.exe', 'alacritty', 'kitty', 'wezterm.exe', 'wezterm',
  'hyper.exe',
  // Containers / infra
  'docker.exe', 'docker desktop.exe', 'dockerd', 'docker-desktop-backend.exe',
  'containerd', 'containerd-shim-runc-v2',
  'kubectl.exe', 'kubectl',
  'helm.exe', 'helm',
  'minikube.exe',
  'vagrant.exe',
  // API / DB tools
  'postman.exe',
  'insomnia.exe',
  'dbeaver.exe',
  'tableplus.exe',
  'datagrip64.exe',
  'sequel pro',                     // macOS
  'mongosh.exe',
  'redis-cli.exe',
  // Build tools
  'gradle', 'gradlew',
  'mvn', 'mvnw',
  'make', 'cmake', 'ninja',
  'msbuild.exe',
])

// ── System processes ──────────────────────────────────────────────────────────
const SYSTEM_NAMES = new Set([
  // Windows kernel / session
  'system', 'system idle process', 'idle', 'registry', 'memory compression', 'secure system',
  'smss.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
  'services.exe', 'lsass.exe', 'dwm.exe', 'fontdrvhost.exe',
  // Windows service infrastructure
  'svchost.exe', 'dllhost.exe', 'conhost.exe', 'runtimebroker.exe',
  'taskhostw.exe', 'taskhost.exe', 'dashost.exe', 'sihost.exe', 'ctfmon.exe',
  'audiodg.exe', 'wsappx.exe', 'wudfhost.exe', 'spoolsv.exe',
  'searchindexer.exe', 'searchhost.exe', 'searchapp.exe',
  'startmenuexperiencehost.exe', 'shellexperiencehost.exe',
  'textinputhost.exe', 'securityhealthservice.exe', 'smartscreen.exe',
  'applicationframehost.exe', 'lockapp.exe', 'lsm.exe',
  'msdtc.exe', 'wermgr.exe', 'wlanext.exe',
  // Windows system apps
  'explorer.exe', 'taskmgr.exe', 'mmc.exe', 'regedit.exe',
  'msmpeng.exe',              // Windows Defender
  'nissrv.exe',               // Windows Defender Network Inspection
  'securityhealthsystray.exe',
  // Linux base
  'systemd', 'systemd-journald', 'systemd-udevd', 'systemd-logind',
  'systemd-networkd', 'systemd-resolved', 'systemd-timesyncd',
  'dbus-daemon', 'dbus-broker', 'agetty', 'init', 'kthreadd',
  'bash', 'sh', 'zsh', 'fish',
  'cron', 'crond', 'rsyslogd', 'syslogd',
  'udevd', 'polkitd', 'cupsd',
])

const SYSTEM_PREFIXES = [
  'kworker/', 'ksoftirqd/', 'migration/', 'rcu_',
  'watchdog/', 'kblockd', 'kswapd', 'kauditd',
  'khugepaged', 'kcompactd', 'irq/', 'cpuhp/',
]

// ── Classification ────────────────────────────────────────────────────────────
export function classifyProcess(name) {
  const lower = name.toLowerCase()
  if (lower in DANGEROUS_PROCS)  return 'dangerous'
  if (GAMES_PROCS.has(lower))    return 'games'
  if (BROWSERS_PROCS.has(lower)) return 'browsers'
  if (COMMS_PROCS.has(lower))    return 'comms'
  if (DEV_PROCS.has(lower))      return 'dev'
  if (_isSystem(lower))          return 'system'
  return 'other'
}

export function getDangerReason(name) {
  return DANGEROUS_PROCS[name.toLowerCase()] ?? null
}

export function isSystemProcess(name) {
  return _isSystem(name.toLowerCase())
}

function _isSystem(lower) {
  if (SYSTEM_NAMES.has(lower)) return true
  return SYSTEM_PREFIXES.some(p => lower.startsWith(p))
}
