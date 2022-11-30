#!/bin/sh

sudo apt update
sudo apt -y install vino

mkdir -p ~/.config/autostart
cp /usr/share/applications/vino-server.desktop ~/.config/autostart

gsettings set org.gnome.Vino prompt-enabled false
gsettings set org.gnome.Vino require-encryption false
gsettings set org.gnome.Vino authentication-methods "['vnc']"
gsettings set org.gnome.Vino vnc-password $(echo -n 'capf'|base64)

echo "\n"
echo "以下を編集して自動login設定を行います。"
echo "ポイントは - WaylandEnable=false       を有効にする"
echo "           - AutomaticLoginEnable=true を有効にする"
echo "           - AutomaticLogin=           右辺にユーザ名を入力する"
echo '$ sudo nano /etc/gdm3/custom.conf'

echo "\n"
echo "＊ jetsonを使用する場合は、以下を編集して解像度を設定します。"
echo '$ sudo nano /etc/X11/xorg.conf'

echo "==============================================================="
echo "
    Section "Screen"
        Identifier    "Default Screen"
        Monitor       "Configured Monitor"
        Device        "Tegra0"
        SubSection "Display"
            Depth    24
            Virtual  1920 1080 # 1280 800 ... Modify the resolution by editing these values
        EndSubSection
    EndSection
"
echo "==============================================================="

echo "\n"
echo "最後にrebootしてセットアップ完了です。"
echo "困ったときは http://www1.meijo-u.ac.jp/~kohara/cms/technicalreport/remote-desktop-for-ubuntu18-04"
