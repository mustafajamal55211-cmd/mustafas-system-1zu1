#!/usr/bin/env python3
import json, os, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageOps

cfg = json.load(open("theme/config.json", encoding="utf-8"))
SYS_NAME = cfg.get("sys_name", "MustafaOS")
SYS_SLUG = cfg.get("sys_slug", "mustafaos")
VEIL_MOCKUP = cfg.get("veil_mockup", True)

CHROOT = "config/includes.chroot"
os.makedirs(f"{CHROOT}/usr/share/mustafa", exist_ok=True)
os.makedirs(f"{CHROOT}/usr/local/bin", exist_ok=True)
os.makedirs(f"{CHROOT}/usr/share/applications", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/lightdm", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/default", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/sysctl.d", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/sudoers.d", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/xdg/xfce4/panel", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/skel/.config/gtk-3.0", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/skel/.config/autostart", exist_ok=True)
os.makedirs(f"{CHROOT}/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml", exist_ok=True)
os.makedirs("config/hooks/live", exist_ok=True)

def make_round_logo(src, out_path, size):
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    px = im.load()
    xs, ys = [], []
    step = max(1, min(w, h) // 100)
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b, a = px[x, y]
            if a > 20 and max(r, g, b) > 70:
                xs.append(x)
                ys.append(y)
    if xs and ys:
        x0, x1 = max(0, min(xs) - step), min(w, max(xs) + step)
        y0, y1 = max(0, min(ys) - step), min(h, max(ys) + step)
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        half = max(x1 - x0, y1 - y0) / 2.0
        if min(w, h) * 0.25 < half < min(w, h) * 0.49:
            im = im.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half)))
    im = ImageOps.fit(im, (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((1, 1, size - 2, size - 2), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    out.save(out_path, "PNG")

def make_default_logo(out_path, size):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 2, size - 3, size - 3), fill=(12, 26, 62, 255), outline=(56, 189, 248, 255), width=max(2, size // 24))
    d.ellipse((size // 6, size // 6, size - size // 6, size - size // 6), outline=(250, 204, 21, 255), width=max(2, size // 32))
    im.save(out_path, "PNG")

logo_src = "assets/logo_upload.png" if os.path.exists("assets/logo_upload.png") else None
for sz in (64, 256):
    out_p = f"{CHROOT}/usr/share/mustafa/logo-round-{sz}.png"
    if logo_src:
        make_round_logo(logo_src, out_p, sz)
    else:
        make_default_logo(out_p, sz)

logo_256 = Image.open(f"{CHROOT}/usr/share/mustafa/logo-round-256.png").convert("RGBA")

def make_wallpaper(out_path):
    W, H = 1920, 1080
    wp_src = "assets/wallpaper_upload.png" if os.path.exists("assets/wallpaper_upload.png") else None
    if wp_src:
        im = Image.open(wp_src).convert("RGBA")
        w, h = im.size
        if w / float(h) >= 1.5:
            canvas = ImageOps.fit(im, (W, H), method=Image.Resampling.LANCZOS)
        else:
            bg = ImageOps.fit(im, (W, H), method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28))
            shade = Image.new("RGBA", (W, H), (8, 15, 38, 130))
            canvas = Image.alpha_composite(bg, shade)
            new_w = int(w * (H / float(h)))
            center = im.resize((new_w, H), Image.Resampling.LANCZOS)
            cx = (W - new_w) // 2
            canvas.paste(center, (cx, 0), center)
            if VEIL_MOCKUP:
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                od.rectangle((0, H - 84, W, H), fill=(8, 16, 42, 225))
                s_ratio = new_w / 1080.0
                od.rounded_rectangle((cx + int(12 * s_ratio), 314, cx + int(468 * s_ratio), 928), radius=26, fill=(18, 28, 68, 232))
                od.rounded_rectangle((cx + int(734 * s_ratio), 14, cx + int(1070 * s_ratio), 532), radius=22, fill=(14, 24, 58, 225))
                canvas = Image.alpha_composite(canvas, ov)
    else:
        canvas = Image.new("RGBA", (W, H), (8, 18, 48, 255))
        d = ImageDraw.Draw(canvas)
        for y in range(H):
            t = y / float(H)
            c = (int(10 + 25 * t), int(18 + 20 * (1 - t)), int(52 + 45 * t), 255)
            d.line([(0, y), (W, y)], fill=c)
        lg = logo_256.resize((260, 260), Image.Resampling.LANCZOS)
        canvas.paste(lg, (W // 2 - 130, 140), lg)
    canvas.convert("RGB").save(out_path, "PNG")

make_wallpaper(f"{CHROOT}/usr/share/mustafa/wallpaper-1920x1080.png")

def make_boot_splash(w, h, out_path):
    im = Image.new("RGBA", (w, h), (10, 18, 46, 255))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / float(h)
        d.line([(0, y), (w, y)], fill=(int(10 + 24 * t), int(16 + 14 * t), int(48 + 44 * (1 - t)), 255))
    sz = int(h * 0.36)
    lg = logo_256.resize((sz, sz), Image.Resampling.LANCZOS)
    im.paste(lg, (w // 2 - sz // 2, int(h * 0.14)), lg)
    im.convert("RGB").save(out_path, "PNG")

os.makedirs("config/includes.binary/isolinux", exist_ok=True)
os.makedirs("config/includes.binary/boot/grub", exist_ok=True)
make_boot_splash(640, 480, "config/includes.binary/isolinux/splash.png")
make_boot_splash(800, 600, "config/includes.binary/boot/grub/splash.png")

if os.path.isdir("/usr/share/live/build/bootloaders"):
    if os.path.exists("config/bootloaders"):
        shutil.rmtree("config/bootloaders")
    shutil.copytree("/usr/share/live/build/bootloaders", "config/bootloaders")
    for sub, sz in [("isolinux", (640, 480)), ("syslinux_common", (640, 480)), ("grub-pc", (800, 600)), ("grub-efi", (800, 600))]:
        p = f"config/bootloaders/{sub}"
        if os.path.isdir(p):
            svg = os.path.join(p, "splash.svg")
            if os.path.exists(svg):
                os.remove(svg)
            make_boot_splash(sz[0], sz[1], os.path.join(p, "splash.png"))
    tt = "config/bootloaders/grub-pc/live-theme/theme.txt"
    if os.path.exists(tt):
        txt = open(tt, encoding="utf-8", errors="ignore").read().replace("Live Boot Menu with GRUB", SYS_NAME)
        open(tt, "w", encoding="utf-8").write(txt)
    mc = "config/bootloaders/syslinux_common/menu.cfg"
    if os.path.exists(mc):
        txt = open(mc, encoding="utf-8", errors="ignore").read().replace("menu title Boot menu", f"menu title {SYS_NAME}")
        open(mc, "w", encoding="utf-8").write(txt)

# Dateien ins Live-System kopieren
for fn in ["mustafa-widgets.py", "mustafa-menu.py", "mustafa-store.py", "mustafa-kamera.py", "mustafa-bluetooth.py", "mustafa-turbo"]:
    shutil.copy(f"theme/{fn}", f"{CHROOT}/usr/local/bin/{fn}")
    os.chmod(f"{CHROOT}/usr/local/bin/{fn}", 0o755)

with open(f"{CHROOT}/usr/local/bin/mustafa-menu-toggle", "w") as f:
    f.write("#!/bin/bash\nif pgrep -f /usr/local/bin/mustafa-menu.py >/dev/null; then pkill -f /usr/local/bin/mustafa-menu.py; else python3 /usr/local/bin/mustafa-menu.py & fi\n")
os.chmod(f"{CHROOT}/usr/local/bin/mustafa-menu-toggle", 0o755)

with open(f"{CHROOT}/usr/local/bin/mustafa-wallpaper-init", "w") as f:
    f.write("#!/bin/bash\nM=\"$HOME/.config/.mustafa-wp-done\"\n[ -f \"$M\" ] && exit 0\nsleep 3\nfor p in $(xfconf-query -c xfce4-desktop -l 2>/dev/null | grep last-image); do\n  xfconf-query -c xfce4-desktop -p \"$p\" -s /usr/share/mustafa/wallpaper-1920x1080.png || true\ndone\nmkdir -p \"$HOME/.config\"\ntouch \"$M\"\n")
os.chmod(f"{CHROOT}/usr/local/bin/mustafa-wallpaper-init", 0o755)

desktop_apps = {
    "mustafa-start.desktop": ("Startmenü", "/usr/share/mustafa/logo-round-64.png", "/usr/local/bin/mustafa-menu-toggle", True),
    "mustafa-search.desktop": ("Suche", "system-search", "python3 /usr/local/bin/mustafa-menu.py", True),
    "mustafa-explorer.desktop": ("Explorer", "system-file-manager", "thunar %F", False),
    "mustafa-browser.desktop": ("Browser", "firefox-esr", "firefox-esr %u", False),
    "mustafa-terminal.desktop": ("Terminal", "utilities-terminal", "xfce4-terminal", False),
    "mustafa-kamera.desktop": ("Kamera", "camera-photo", "python3 /usr/local/bin/mustafa-kamera.py", False),
    "mustafa-settings.desktop": ("Einstellungen", "preferences-system", "xfce4-settings-manager", False),
    "mustafa-store.desktop": ("App Store", "system-software-install", "python3 /usr/local/bin/mustafa-store.py", False),
    "mustafa-bluetooth.desktop": ("Bluetooth", "bluetooth", "python3 /usr/local/bin/mustafa-bluetooth.py", False),
    "mustafa-spotify.desktop": ("Spotify", "multimedia-audio-player", "firefox-esr https://open.spotify.com", False),
    "mustafa-discord.desktop": ("Discord", "internet-chat", "firefox-esr https://discord.com/app", False),
    "mustafa-instagram.desktop": ("Instagram", "emblem-photos", "firefox-esr https://www.instagram.com", False),
}
for fn, (nm, ic, ex, nod) in desktop_apps.items():
    with open(f"{CHROOT}/usr/share/applications/{fn}", "w") as f:
        f.write(f"[Desktop Entry]\nType=Application\nName={nm}\nIcon={ic}\nExec={ex}\n")
        if nod:
            f.write("NoDisplay=true\n")

with open(f"{CHROOT}/etc/skel/.config/gtk-3.0/gtk.css", "w") as f:
    f.write(""".xfce4-panel {
    background-color: rgba(10, 22, 54, 0.88);
    border: 1.5px solid rgba(56, 189, 248, 0.65);
    border-radius: 16px;
    color: #f8fafc;
}
.xfce4-panel button { border-radius: 10px; color: #f8fafc; }
.xfce4-panel button:hover { background-color: rgba(56, 189, 248, 0.28); }
""")

with open(f"{CHROOT}/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml", "w") as f:
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="2"/>
    <property name="icon-size" type="uint" value="48"/>
    <property name="file-icons" type="empty">
      <property name="show-home" type="bool" value="true"/>
      <property name="show-filesystem" type="bool" value="true"/>
      <property name="show-trash" type="bool" value="true"/>
      <property name="show-removable" type="bool" value="true"/>
    </property>
  </property>
  <property name="backdrop" type="empty">
    <property name="single-workspace-mode" type="bool" value="true"/>
  </property>
</channel>
""")

with open(f"{CHROOT}/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml", "w") as f:
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="use_compositing" type="bool" value="true"/>
    <property name="frame_opacity" type="int" value="100"/>
    <property name="show_dock_shadow" type="bool" value="false"/>
  </property>
</channel>
""")

with open(f"{CHROOT}/etc/xdg/xfce4/panel/default.xml", "w") as f:
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="configver" type="int" value="2"/>
  <property name="panels" type="array">
    <value type="int" value="1"/>
    <property name="dark-mode" type="bool" value="true"/>
    <property name="panel-1" type="empty">
      <property name="position" type="string" value="p=10;x=0;y=0"/>
      <property name="length" type="uint" value="94"/>
      <property name="length-adjust" type="bool" value="false"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="icon-size" type="uint" value="26"/>
      <property name="size" type="uint" value="50"/>
      <property name="background-style" type="uint" value="0"/>
      <property name="plugin-ids" type="array">
        <value type="int" value="1"/><value type="int" value="2"/><value type="int" value="3"/>
        <value type="int" value="4"/><value type="int" value="5"/><value type="int" value="6"/>
        <value type="int" value="7"/><value type="int" value="8"/><value type="int" value="9"/>
        <value type="int" value="10"/><value type="int" value="11"/><value type="int" value="12"/>
        <value type="int" value="13"/><value type="int" value="14"/><value type="int" value="15"/>
        <value type="int" value="16"/><value type="int" value="17"/><value type="int" value="18"/>
        <value type="int" value="19"/><value type="int" value="20"/><value type="int" value="21"/>
      </property>
    </property>
  </property>
  <property name="plugins" type="empty">
    <property name="plugin-1" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-start.desktop"/></property></property>
    <property name="plugin-2" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-search.desktop"/></property></property>
    <property name="plugin-3" type="string" value="separator"><property name="style" type="uint" value="1"/></property>
    <property name="plugin-4" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-explorer.desktop"/></property></property>
    <property name="plugin-5" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-browser.desktop"/></property></property>
    <property name="plugin-6" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-terminal.desktop"/></property></property>
    <property name="plugin-7" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-kamera.desktop"/></property></property>
    <property name="plugin-8" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-settings.desktop"/></property></property>
    <property name="plugin-9" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-store.desktop"/></property></property>
    <property name="plugin-10" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-bluetooth.desktop"/></property></property>
    <property name="plugin-11" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-spotify.desktop"/></property></property>
    <property name="plugin-12" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-discord.desktop"/></property></property>
    <property name="plugin-13" type="string" value="launcher"><property name="items" type="array"><value type="string" value="mustafa-instagram.desktop"/></property></property>
    <property name="plugin-14" type="string" value="separator"><property name="style" type="uint" value="1"/></property>
    <property name="plugin-15" type="string" value="tasklist">
      <property name="grouping" type="uint" value="1"/><property name="show-labels" type="bool" value="false"/><property name="flat-buttons" type="bool" value="true"/>
    </property>
    <property name="plugin-16" type="string" value="separator"><property name="expand" type="bool" value="true"/><property name="style" type="uint" value="0"/></property>
    <property name="plugin-17" type="string" value="systray"><property name="square-icons" type="bool" value="true"/><property name="icon-size" type="int" value="20"/></property>
    <property name="plugin-18" type="string" value="pulseaudio"><property name="enable-keyboard-shortcuts" type="bool" value="true"/></property>
    <property name="plugin-19" type="string" value="power-manager-plugin"/>
    <property name="plugin-20" type="string" value="clock">
      <property name="mode" type="uint" value="2"/><property name="digital-layout" type="uint" value="1"/>
      <property name="digital-time-format" type="string" value="%H:%M"/><property name="digital-date-format" type="string" value="%d.%m.%Y"/>
      <property name="show-frame" type="bool" value="false"/>
    </property>
    <property name="plugin-21" type="string" value="showdesktop"/>
  </property>
</channel>
""")

with open(f"{CHROOT}/etc/skel/.config/autostart/mustafa-widgets.desktop", "w") as f:
    f.write("[Desktop Entry]\nType=Application\nName=System Widgets\nExec=bash -c 'sleep 2 && python3 /usr/local/bin/mustafa-widgets.py'\nX-GNOME-Autostart-enabled=true\n")

with open(f"{CHROOT}/etc/skel/.config/autostart/mustafa-wallpaper-init.desktop", "w") as f:
    f.write("[Desktop Entry]\nType=Application\nName=Wallpaper Setup\nExec=/usr/local/bin/mustafa-wallpaper-init\nX-GNOME-Autostart-enabled=true\n")

with open(f"{CHROOT}/etc/lightdm/lightdm-gtk-greeter.conf", "w") as f:
    f.write("[greeter]\nbackground=/usr/share/mustafa/wallpaper-1920x1080.png\ndefault-user-image=/usr/share/mustafa/logo-round-256.png\ntheme-name=Arc-Dark\nicon-theme-name=Papirus-Dark\nposition=50%,center 50%,center\n")

with open(f"{CHROOT}/etc/default/zramswap", "w") as f:
    f.write("ALGO=lz4\nPERCENT=50\nPRIORITY=100\n")

with open(f"{CHROOT}/etc/sysctl.d/99-mustafa-speed.conf", "w") as f:
    f.write("vm.swappiness=100\nvm.vfs_cache_pressure=50\nvm.page-cluster=0\n")

with open(f"{CHROOT}/etc/sudoers.d/mustafa-turbo", "w") as f:
    f.write("%sudo ALL=(ALL) NOPASSWD: /usr/local/bin/mustafa-turbo\nuser ALL=(ALL) NOPASSWD: /usr/local/bin/mustafa-turbo\n")
os.chmod(f"{CHROOT}/etc/sudoers.d/mustafa-turbo", 0o440)

hook_path = "config/hooks/live/010-mustafa.hook.chroot"
with open(hook_path, "w") as f:
    f.write(f"""#!/bin/bash
set -e
ln -sf /usr/share/mustafa/wallpaper-1920x1080.png /etc/alternatives/desktop-background
ln -sf /usr/share/mustafa/wallpaper-1920x1080.png /usr/share/images/desktop-base/desktop-background
cp /usr/share/mustafa/logo-round-256.png /etc/skel/.face
echo "{SYS_SLUG}" > /etc/hostname
echo "Willkommen bei {SYS_NAME} (\\l)" > /etc/issue
sed -i 's/^PRETTY_NAME=.*/PRETTY_NAME="{SYS_NAME}"/' /etc/os-release || true
sed -i 's/^NAME=.*/NAME="{SYS_NAME}"/' /etc/os-release || true
if [ -f /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml ]; then
  sed -i 's/value="Adwaita"/value="Arc-Dark"/g' /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml || true
  sed -i 's/value="Adwaita-dark"/value="Arc-Dark"/g' /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml || true
  sed -i 's/value="gnome"/value="Papirus-Dark"/g' /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml || true
  sed -i 's/value="Tango"/value="Papirus-Dark"/g' /etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml || true
fi
chmod +x /usr/local/bin/mustafa-*
chmod 0440 /etc/sudoers.d/mustafa-turbo
""")
os.chmod(hook_path, 0o755)
print("Mustafa 1:1 Theme & Bootloader vorbereitet!")
