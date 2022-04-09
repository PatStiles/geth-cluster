#!/bin/sh

#Install Go note must have downleaded tar.gz
wget -c https://golang.org/dl/go1.18.linux-amd64.tar.gz
rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go1.18.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

#Install stable version of geth
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get update
sudo apt-get install ethereum

#Make Data Cache
mkdir data

#import in genesis.json

#Initialize geth node 
geth --networkid 666 --datadir data init genesis.json
nohup geth --allow-insecure-unlock --networkid 666 &
sleep 2
geth attach --exec "eth.blockNumber"
