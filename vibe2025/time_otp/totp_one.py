from time import sleep

import pyotp

if __name__ == '__main__':
    secret = pyotp.random_base32()
    print(secret)   # secret to be shaared between parties
    while True:
        totp = pyotp.TOTP(secret)
        # OTP to be passed from one party to the other (ensuring they know the secret)
        print(totp.now())
        sleep(2)