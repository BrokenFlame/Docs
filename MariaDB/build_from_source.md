# Build MariaDB 10.3

Install the Ubuntu build tools
```sh
sudo apt-get install software-properties-common devscripts equivs
```

Add the authentication key for the repository, then add the repository
```sh
sudo apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xF1656F24C74CD1D8
sudo add-apt-repository --update --yes --enable-source 'deb [arch=amd64] http://nyc2.mirrors.digitalocean.com/mariadb/repo/10.3/ubuntu '$(lsb_release -sc)' main'
```

Get MariaDB build dependancies
```sh
sudo apt-get build-dep mariadb-10.3
```

Clone the repository
```sh
git clone --branch 10.3 https://github.com/MariaDB/server.git
```

Build MariaDB
```sh
cd server/
./debian/autobake-deb.sh
```
