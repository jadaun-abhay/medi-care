from django.contrib.auth.models import UserManager

class CustomUserManager(UserManager):
    def create_user(self, email, password, **kwargs):
        if not email:
            raise ValueError("Must be a valid E-Mail")
        
        user = self.model(email = self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using = self._db)
        return user
    
    def create_super(self, email, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)

        return self.create_user(email = email, password = password, **kwargs)
    
    def create_patient(self, email, password, **kwargs):
        kwargs.setdefault("is_patient", True)

        return self.create_user(email = email, password = password, **kwargs)
    
    def create_doctor(self, email, password, **kwargs):
        kwargs.setdefault("is_doctor" ,True)

        return self.create_user(email = email, password = password, **kwargs)