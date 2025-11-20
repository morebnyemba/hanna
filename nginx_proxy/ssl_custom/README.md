# SSL Custom Configuration

This directory contains SSL configuration files for nginx.

## Files

### options-ssl-nginx.conf
Contains recommended SSL settings including protocols, ciphers, and session management.

### ssl-dhparams.pem
Diffie-Hellman parameters file for enhanced security.

## Generating ssl-dhparams.pem

If the `ssl-dhparams.pem` file doesn't exist, you need to generate it:

```bash
# Generate 2048-bit DH parameters (faster, still secure)
openssl dhparam -out nginx_proxy/ssl_custom/ssl-dhparams.pem 2048

# Or generate 4096-bit DH parameters (slower but more secure)
openssl dhparam -out nginx_proxy/ssl_custom/ssl-dhparams.pem 4096
```

**Note:** Generating DH parameters can take several minutes, especially for 4096-bit.

## Alternative: Comment Out DH Parameters

If you don't want to use DH parameters, you can comment out the line in `nginx_proxy/nginx.conf`:

```nginx
# ssl_dhparam /etc/nginx/ssl_custom/ssl-dhparams.pem;
```

This is acceptable for most use cases, as modern TLS protocols don't strictly require DH parameters.
