# Install OpenSSl with FIPS enabled on MacOS

Check OpenSSL Blog for latest versions with FIPS 140 validation. (https://www.openssl.org/blog/blog/2023/10/12/osslfips-timeline/)

```sh
#FIPS validated OpenSSL
wget https://www.openssl.org/source/openssl-3.0.9.tar.gz
tar -xf openssl-3.0.9.tar.gz
cd openssl-3.0.9
./Configure enable-fips
make

# Test FIP Validated modules using Regular OpenSSL
wget https://www.openssl.org/source/openssl-3.1.4.tar.gz
tar -xf openssl-3.1.4.tar.gz
cd openssl-3.1.4
./Configure enable-fips
make
cp ../openssl-3.0.9/providers/fips.so providers/.
cp ../openssl-3.0.9/providers/fipsmodule.cnf providers/.
./util/wrap.pl -fips apps/openssl list -provider-path providers -provider fips -providers
make tests

#Install FIPS Validated OpenSSL v 3.0.9
cd ../openssl-3.0.9
sudo make install_fips

#Validate installation
./util/wrap.pl -fips apps/openssl list -provider-path providers -provider fips -providers
```

Check OpenSSL Directory: 
```sh
openssl version -d
```

Check OpenSSL version:
```sh
openssl version -v
```

Get OpenSSL Build info:
```sh
openssl version -a
```
