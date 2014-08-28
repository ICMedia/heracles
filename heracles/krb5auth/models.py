from django.contrib.auth.models import AbstractUser
from django.db import models

class KerberosUser(AbstractUser):
    credential_cache_path = models.CharField(max_length=128)
