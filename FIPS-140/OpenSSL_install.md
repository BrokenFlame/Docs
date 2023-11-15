# Install OpenSSl with FIPS enabled on MacOS

```sh
wget https://www.openssl.org/source/openssl-3.1.4.tar.gz
tar -xf openssl-3.1.4.tar.gz
cd openssl-3.1.4
./Configure enable-fips
make install
```
