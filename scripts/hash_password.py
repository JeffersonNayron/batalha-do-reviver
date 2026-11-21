from getpass import getpass
from argon2 import PasswordHasher
password=getpass('Senha do administrador: ')
if len(password)<12: raise SystemExit('Use uma senha com ao menos 12 caracteres')
print('ADMIN_PASSWORD_HASH='+PasswordHasher().hash(password))
