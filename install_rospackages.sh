#!/bin/sh

sudo apt -y install ros-melodic-rosserial; sudo apt -y install ros-melodic-slam-gmapping; sudo apt -y install ros-melodic-navigation;
sudo apt-get -y install nano

echo -e "\n \e[33;41m----- 必要に応じて以下を実行してください。 ------\e[m \n"

echo -e '\e[36m ホームディレクトリのフォルダ名を英語化\n$ LANG=C xdg-user-dirs-gtk-update\e[m \n'

echo -e '\e[36m VNCの設定: https://zenn.dev/tunefs/articles/9774eb8f229e1bf97a8c \e[m \n'
