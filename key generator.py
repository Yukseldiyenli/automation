import rsa

# Generate RSA keys
public_key, private_key = rsa.newkeys(2048)

# Save the private key
with open("private_key.pem", "wb") as private_file:
    private_file.write(private_key.save_pkcs1())

# Save the public key
with open("public_key.pem", "wb") as public_file:
    public_file.write(public_key.save_pkcs1())
