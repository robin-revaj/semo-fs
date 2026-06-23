#!/usr/bin/env bash

# semo-install
#   semo
#   tests
#   requirements.txt
#   setup.sh
#   semo_watcher.service

git clone https://github.com/robin-revaj/semo-fs.git

# semo-fs
#    semo
#        python files
#        setup.py
#        setup.sh
#    tests
#    requirements.txt
#    semo_watcher.service
#    README.md

if [ ! -d ~/.semo ]; then
    mkdir ~/.semo
fi

semopath=$HOME/.semo

mv $PWD/semo-fs/semo $semopath/semo
mv $PWD/semo-fs/tests $semopath/tests
mv $PWD/semo-fs/requirements.txt $semopath/requirements.txt
mv $PWD/semo-fs/semo_watcher.service $semopath/semo_watcher.service

pip install -r $semopath/requirements.txt

mkdir $semopath/databases
mkdir $semopath/mnt

dbname=$(read -p "Name your database file: " x)
watchpath=$(read -p "Choose directory to watch changes in: " x)

if [ ! -f ~/.bash_aliases ]; then
    touch ~/.bash_aliases
fi
echo "alias semo='python3 $semopath/semo'" >> ~/.bash_aliases

python3 $semopath/semo/setup.py $semopath $dbname $watchpath

echo "Exec=python3 $semopath/semo/semo_watcher.py" >> $semopath/semo_watcher.service
echo "" >> $semopath/semo_watcher.service
echo "[Install]" >> $semopath/semo_watcher.service
echo "WantedBy=multi-user.target" >> $semopath/semo_watcher.service

sudo cp $semopath/semo_watcher.service /etc/systemd/system/semo_watcher.service
sudo systemctl enable semo_watcher
sudo systemctl daemon-reload
#systemctl start semo_watcher

rmdir semo-fs
