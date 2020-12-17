This directory contains the TLS key and certificate for running our tests.

## Generate TLS Key and Self-Signed Certificate Using GnuTLS

The key and certificate were generated as follows:

1. Run:

       $ certtool --generate-privkey --sec-param=high --outfile server.key
       $ certtool --generate-self-signed --load-privkey server.key --outfile server.pem

2. Answer:

       Generating a self signed certificate...
       Please enter the details of the certificate's distinguished name. Just press enter to ignore a field.
       Common name: localhost
       UID:
       Organizational unit name: CODAIT
       Organization name: IBM
       Locality name: CODAIT City
       State or province name:
       Country name (2 chars): US
       Enter the subject's domain component (DC):
       This field should not be used in new certificates.
       E-mail:
       Enter the certificate's serial number in decimal (default: 6906671526803292282):


       Activation/Expiration time.
       The certificate will expire in (days): 999999


       Extensions.
       Does the certificate belong to an authority? (y/N): y
       Path length constraint (decimal, -1 for no constraint):
       Is this a TLS web client certificate? (y/N):
       Will the certificate be used for IPsec IKE operations? (y/N):
       Is this a TLS web server certificate? (y/N): y
       Enter a dnsName of the subject of the certificate: localhost
       Enter a dnsName of the subject of the certificate:
       Enter a URI of the subject of the certificate:
       Enter the IP address of the subject of the certificate: 127.0.0.1
       Will the certificate be used for signing (DHE and RSA-EXPORT ciphersuites)? (Y/n):
       Will the certificate be used for encryption (RSA ciphersuites)? (Y/n):
       Will the certificate be used to sign OCSP requests? (y/N):
       Will the certificate be used to sign code? (y/N):
       Will the certificate be used for time stamping? (y/N):
       Will the certificate be used to sign other certificates? (y/N): y
       Will the certificate be used to sign CRLs? (y/N):
       Enter the URI of the CRL distribution point:
       X.509 Certificate Information:
               Version: 3
               Serial Number (hex): 5fd96d29176a407a
               Validity:
                       Not Before: Wed Dec 16 02:12:58 UTC 2020
                       Not After: Wed Nov 12 02:13:01 UTC 4758
               Subject: CN=localhost,OU=CODAIT,O=IBM,L=CODAIT City,C=US
               Subject Public Key Algorithm: RSA
               Algorithm Security Level: High (3072 bits)
                       Modulus (bits 3072):
                               00:9c:53:6c:dc:d3:8c:f2:70:67:af:d3:27:34:53:51
                               4d:6d:46:46:67:56:02:2c:53:ed:08:1f:65:81:3b:b8
                               69:2a:54:5b:b7:da:e4:79:65:d7:34:37:90:d4:5b:19
                               31:ad:4c:16:c8:ac:d4:16:b2:60:23:e2:05:f7:ca:3e
                               ca:c0:0c:3e:1d:36:ff:05:14:13:3d:59:8e:b0:27:65
                               97:6c:ce:23:f5:11:fa:7f:d5:64:f3:af:14:ba:bf:ef
                               a8:a3:73:9a:5a:38:1c:ff:08:28:c0:f6:2d:41:51:97
                               03:ee:db:4d:8c:4d:0b:a2:04:ff:97:4b:f4:7d:31:b8
                               13:aa:f6:83:22:b4:e6:56:e7:cf:9f:3f:b9:c7:d8:b8
                               a1:dc:68:78:e9:4a:57:45:d6:1a:e5:9a:af:68:ab:49
                               91:46:78:9b:87:29:21:b3:ec:8e:d8:2d:46:d6:d1:58
                               59:2b:25:5c:56:93:44:58:ca:79:9d:73:a5:4b:77:22
                               c0:6a:97:80:e9:12:84:83:36:6f:17:57:7d:f7:ad:66
                               88:9f:5d:56:43:ea:57:74:81:70:bc:70:0e:86:15:fe
                               21:49:28:3b:e9:bf:3e:73:57:2d:b6:a5:c4:ee:c8:fa
                               01:94:91:62:c5:67:f5:b7:53:86:de:e8:b6:e4:96:ea
                               3b:87:53:3a:5d:18:91:96:64:c6:c0:fa:b3:5d:aa:39
                               72:88:dc:6e:44:5e:4e:c1:24:ce:ce:8a:d5:97:7c:62
                               7f:09:08:03:62:ba:46:5e:67:b4:11:fc:fe:1e:df:fb
                               b5:67:81:ea:00:ac:ec:50:07:13:6c:4b:79:1d:97:bb
                               61:bc:cc:65:7e:d0:2f:c4:f5:3b:98:7b:c6:f7:c1:28
                               56:81:08:d9:b3:02:c7:4b:40:24:9f:d9:3e:ac:5d:83
                               d1:98:3b:35:2f:4a:5c:5b:bd:0b:ab:bd:4b:27:f2:26
                               66:fc:2d:78:fa:82:67:e7:2e:be:f1:ec:64:a8:0b:fb
                               35
                       Exponent (bits 24):
                               01:00:01
               Extensions:
                       Basic Constraints (critical):
                               Certificate Authority (CA): TRUE
                       Subject Alternative Name (not critical):
                               DNSname: localhost
                               IPAddress: 127.0.0.1
                       Key Purpose (not critical):
                               TLS WWW Server.
                       Key Usage (critical):
                               Digital signature.
                               Key encipherment.
                               Certificate signing.
                       Subject Key Identifier (not critical):
                               6642b5dc3f2b7f1f592aa3d18703aca02fe91592
       Other Information:
               Public Key ID:
                       6642b5dc3f2b7f1f592aa3d18703aca02fe91592
               Public key's random art:
                       +--[ RSA 3072]----+
                       |        .        |
                       |       o o       |
                       |      . o .      |
                       |     o   . .     |
                       |    E + S o o   .|
                       |     o * . o + .o|
                       |    ... . o B oo |
                       |    oo     = =. .|
                       |   ....   . .. ..|
                       +-----------------+

       Is the above information ok? (y/N): y

Reference: https://help.ubuntu.com/community/GnuTLS#Self-Signing
