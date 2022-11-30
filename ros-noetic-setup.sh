#!/bin/sh

echo -e "\n \e[33;41m------- ROS-NOETICのインストールを開始します --------\e[m \n"
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list';

echo -e "\n \e[33;41m---------- ros-source.listの設定完了 ----------\e[m \n"

sudo apt -y install curl;
echo -e "\n \e[33;41m---------- curlのインストール完了 ----------\e[m \n"

sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654;
echo -e "\n \e[33;41m-------------  鍵の設定完了 -------------\e[m \n"

sudo apt update;
echo -e "\n \e[33;41m-------------  apt update 完了 -------------\e[m \n"

sudo apt -y install ros-noetic-desktop-full;
echo -e "\n \e[33;41m------- ROS-NOETICのインストール完了🙌 ---------\e[m \n"


echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc ;
echo -e "\n \e[33;41m------- rosコマンドのパス記述完了 ---------\e[m \n"
source ~/.bashrc;

sudo apt -y install python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential;
echo -e "\n \e[33;41m----- パッケージ構築のための依存ツールのセットアップ完了 ------\e[m \n"

# sudo apt-get -y install python-rosdep;
sudo rosdep init;
rosdep update;
echo -e "\n \e[33;41m----- rosdepのインストール~初期化~アプデまで完了 ------\e[m \n"


mkdir -p ~/catkin_ws/src
echo -e "\n \e[33;41m------- ~/catkin_ws/src の作成完了 --------\e[m \n"



echo " ------------++++++++++++------------++++++++++++------------ "
echo " ++++++++++++------------++++++++++++------------++++++++++++ "
echo " ------------++++++++++++------------++++++++++++------------ "

echo "1. sourceコマンドを実行してください⌨️"
echo -e "\e[36m$ source ~/.bashrc\e[m \n\n"

echo "2. ~/catkin_ws/src 直下で以下を実行してください⌨️"
echo -e "\e[36m$ catkin_init_workspace\e[m \n\n"

echo "3. ~/catkin_ws 直下で、以下を順次実行してください⌨️"
echo -e "\e[36m$ catkin_make\e[m \n"
echo -e "\e[36m$ source devel/setup.bash\e[m \n\n"


echo "4. 以下を順次実行してください⌨️"
echo -e '\e[36m$ echo "source /home/ユーザ名/catkin_ws/devel/setup.bash" >> ~/.bashrc \e[m \n'
echo -e "\e[36m$ source ~/.bashrc\e[m \n\n"

echo " ------------++++++++++++------------++++++++++++------------ "

echo -e "\e[37;7mお疲れ様でした🍺 以上で全ての手順は完了です🙌 \n~/catkin_ws/src 直下に任意のROSパッケージをダウンロードし、catkin_makeしてみましょう。\e[m"
