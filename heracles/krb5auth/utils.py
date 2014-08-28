
from mediakrb import kerberos

def build_server_principal():
    return kerberos.KerberosPrincipal('HTTP/qunn.media.su.ic.ac.uk', '/home/heracles/krb5.keytab')

def build_kauth(server_principal):
    return kerberos.KerberosAuth(server_principal, 'MEDIA.SU.IC.AC.UK')
