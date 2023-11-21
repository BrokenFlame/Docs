# Install OpenSSl with FIPS enabled on MacOS

Check OpenSSL Blog for latest versions with FIPS 140 validation. (https://www.openssl.org/blog/blog/2023/10/12/osslfips-timeline/)

```sh
wget https://www.openssl.org/source/openssl-3.0.9.tar.gz
tar -xf openssl-3.0.9.tar.gz
cd openssl-3.0.9
./Configure enable-fips
make install
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
